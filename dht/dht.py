from hashlib import sha1
from threading import Thread, Timer
from dht import dht_server
import requests
import sys
from flask.json import JSONEncoder, JSONDecoder

class DHTNode(object):
    def __init__(self, host, m):
        self.host = host
        self.m = m
        self.id = self.get_hash(self.host)
        self.predecessor = None
        self.successor = self.host
        self.finger_table = [self.id] * self.m
        self.stabalizer = Stabalizer(self)
        self.stabalizer.start()
        self.table = {}

    def join(self, addr):
        self.predecessor = None
        self.successor = self.__call_successor(addr, self.id)

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

    def is_successor(self, id):
        if id < self.id or self.id <= self.get_hash(self.successor):
            return True
        return False

    def notify(self, addr):
        n_prime = self.get_hash(addr)
        if self.predecessor is None or (n_prime > self.get_hash(self.predecessor) and n_prime < self.id): #n'∈(predecessor, n))
            self.predecessor = addr
            return True
        return False

    def closest_preceding_node(self, id):
        for i in range(self.m - 1, -1, -1):
            if self.id < self.finger_table[i] and self.finger_table[i] < id:
                return self.finger_table[i]
        return self.host

    def get_hash(self, key):
        return int.from_bytes(sha1(key.encode()).digest(), byteorder='big') % 2**self.m

    def get_finger_id(self, i):
        return (self.id + 2**(i-1)) % 2**self.m

    def __contruct_fingertable(self):
        finger_table = []
        for i in range(self.m):
            finger_table[i] = dht_server.__find_successor(self, self.get_finger_id(i))
        return finger_table

    def __call_successor(self, addr, id):
        url = "http://{0}/dht/find_successor?id={1}".format(addr, id)
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        raise ConnectionError

class Stabalizer(Thread):
    def __init__(self, node):
        Thread.__init__(self)
        self.node = node
        self.next = 0

    def run(self):
        self.stabilize(10)
        self.fix_fingers(10)
        self.check_predecessor(10)
    
    def stop(self):
        if self.stabilize_timer:
            self.stabilize_timer.cancel()

        if self.fix_fingers_timer:
            self.fix_fingers_timer.cancel()

        if self.check_predecessor_timer:
            self.check_predecessor_timer.cancel()

    def stabilize(self, interval):
        if self.node.successor != self.node.host:
            url = 'http://{0}/dht/get_predecessor'.format(self.node.successor)
            r = requests.get(url)
            if r.status_code == 200 or r.status_code == 307:
                x = r.text
                if x:
                    x_id = self.node.get_hash(x)
                    if x_id > self.node.id and x_id < self.node.get_hash(self.node.successor):
                        print("Successor updated to %s", x)
                        self.node.successor = x
                    url = 'http://{0}/dht/notify?addr={1}'.format(self.node.successor, self.node.host)
                    r = requests.post(url)
                    if r.status_code != 200:
                        print('Error notifying successor: {0}'.format(url), file=sys.stderr)
            else:
                print('Error getting predecessor for successor: {0}'.format(url), file=sys.stderr)
        self.stabilize_timer = Timer(interval, self.stabilize, [interval])
        self.stabilize_timer.run()

    def fix_fingers(self, interval):
        id = self.node.get_finger_id(self.next)
        next_entry = dht_server.__find_successor(self.node, id)
        if next_entry.status_code != 200 and next_entry.status_code != 307:
            print('Error fixing finger table', file=sys.stderr)
            return
        else:
            print("Updating entry %d to %s\n", self.next, next_entry)
            self.node.finger_table[self.next] = next_entry
        self.next = (self.next + 1) % self.node.m
        self.fix_fingers_timer = Timer(interval, self.fix_fingers, [interval])
        self.fix_fingers_timer.run()

    def check_predecessor(self, interval):
        if self.node.predecessor != None:
            url = "http://{0}/".format(self.node.predecessor)
            r = requests.get(url)
            if r.status_code != 200:
                print("Set predecessor to nil")
                self.node.predecessor = None
        self.check_predecessor_timer = Timer(interval, self.check_predecessor, [interval])
        self.check_predecessor_timer.run()