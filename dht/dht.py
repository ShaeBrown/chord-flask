from hashlib import sha1
from threading import Thread
import requests
import sys
import time
from flask.json import JSONEncoder, JSONDecoder

class DHTNode(object):
    def __init__(self, host, m):
        self.host = host
        self.m = m
        self.id = self.get_hash(self.host)
        self.predecessor = self.host
        self.successor = self.host
        self.finger_table = [self.host] * self.m
        self.stabalizer = Stabalizer(self)
        self.stabalizer.run()
        self.table = {}

    def join(self, addr):
        self.successor = self.__call_successor(addr, self.id)
        print("Successor updated to: ", str(self.get_hash(self.successor)))
        if self.predecessor == self.host:
            print("Predecessor updated to: ", str(self.get_hash(self.successor)))
            self.predecessor = self.successor

    def leave(self):
        self.stabalizer.stop()

    def get_key(self, key):
        h = str(self.get_hash(key))
        if h in self.table:
            return self.table[h]
        return ""
    
    def set_key(self, key, value):
        h = self.get_hash(key)
        self.table[str(h)] = value
    
    def delete_key(self, key):
        h = self.get_hash(key)
        del self.table[h]

    @staticmethod
    def between(x, a, b):
        if a > b:
            return x > a or x < b
        elif a < b:
            return a < x and b > x
        else:
            return x !=a and x!=b

    @staticmethod
    def between_right_inclusive(x, a, b):
        if a > b:
            return a < x or b >= x
        elif a < b:
            return a < x and b >= x
        else:
            return a !=x

    def notify(self, addr):
        n_prime = self.get_hash(addr)
        if self.predecessor == self.host or DHTNode.between(n_prime, self.get_hash(self.predecessor), self.id):
            print("Predecessor updated to: ", n_prime)
            self.predecessor = addr
            return True
        return False

    def closest_preceding_node(self, id):
        for i in range(self.m - 1, -1, -1):
            finger_id = self.get_hash(self.finger_table[i])
            if DHTNode.between(finger_id, self.id, id):
                return self.finger_table[i]
        return self.host

    def get_hash(self, key):
        return int(int.from_bytes(sha1(key.encode()).digest(), byteorder='big') % 2**self.m)

    def get_finger_id(self, i):
        return (self.id + 2**i) % 2**self.m

    def __call_successor(self, addr, id):
        url = "http://{0}/dht/find_successor?id={1}".format(addr, id)
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        raise ConnectionError

class Stabalizer(object):
    def __init__(self, node):
        self.node = node
        self.next = 0

    def run(self):
        self.stabilize_thread = Thread(target = self.stabilize, args=(2,))
        self.finger_thread = Thread(target=self.fix_fingers, args=(2,))
        self.check_predecessor_thread = Thread(target=self.check_predecessor, args=(2,))
        self.stabilize_thread.start()
        self.finger_thread.start()
        self.check_predecessor_thread.start()
    
    def stop(self):
        raise NotImplementedError

    def stabilize(self, interval):
        while True:
            if self.node.successor != self.node.host:
                url = 'http://{0}/dht/get_predecessor'.format(self.node.successor)
                r = requests.get(url)
                if r.status_code == 200 or r.status_code == 307:
                    x = r.text
                else:
                    print('Error getting predecessor for successor: {0}'.format(url))
                    time.sleep(interval)
                    continue
            elif self.node.predecessor != self.node.host:
                x = self.node.predecessor
            else:
                time.sleep(interval)
                continue
            x_id = self.node.get_hash(x)
            succ_id = self.node.get_hash(self.node.successor)
            if DHTNode.between(x_id, self.node.id, succ_id):
                print("Successor updated to {0}".format(x_id))
                self.node.successor = x
            url = 'http://{0}/dht/notify?addr={1}'.format(self.node.successor, self.node.host)
            r = requests.post(url)
            if r.status_code != 200:
                print('Error notifying successor: {0}'.format(url),)
            time.sleep(interval)

    def fix_fingers(self, interval):
        from dht import dht_server
        while True:
            id = self.node.get_finger_id(self.next)
            next_entry = dht_server._find_successor(self.node, id)
            if type(next_entry) != str and next_entry.status_code != 200 and next_entry.status_code != 307:
                print('Error fixing finger table')
                return
            else:
                if type(next_entry) != str:
                    next_entry = next_entry.text
                if self.node.finger_table[self.next] != next_entry:
                    print("Updating entry {0} to {1}".format(self.next, next_entry))
                self.node.finger_table[self.next] = next_entry
                if self.next == 0:
                    print("Updated successor to {0}".format(self.node.get_hash(next_entry)))
                    self.node.successor = next_entry
            self.next = (self.next + 1) % self.node.m
            time.sleep(interval)

    def check_predecessor(self, interval):
        while True:
            if self.node.predecessor != None:
                url = "http://{0}/".format(self.node.predecessor)
                r = requests.get(url)
                if r.status_code != 200:
                    print("Set predecessor to nil")
                    self.node.predecessor = None
            time.sleep(interval)