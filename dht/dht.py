from hashlib import sha1
from threading import Thread, Lock
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
        self.pred_lock = Lock()
        self.successor = self.host
        self.succ_lock = Lock()
        self.finger_table = [self.host] * self.m
        self.stabalizer = Stabalizer(self)
        self.stabalizer.run()
        self.table = {}

    def join(self, addr):
        self.update_successor(self.__call_successor(addr, self.id))
        self.update_predecessor(self.host)
        Stabalizer.stabalize_node(self)

    def leave(self):
        self.stabalizer.stop()
        succ = self.get_successor()
        for key in list(self.table):
            ok = self.transfer(int(key), succ)
            if not ok:
                return False
        pred = self.get_predecessor()
        try:
            url = "http://" + pred + '/dht/set_successor?addr=' + succ
            res = requests.post(url)
            if res.status_code != 200:
                return False
            url = "http://" + succ + '/dht/set_predecessor?addr=' + pred
            res = requests.post(url)
            if res.status_code != 200:
                return False
        except Exception:
            print()
            return False
        return True

    def transfer(self, hash, addr):
        if addr == self.host:
            return True
        data = self.table[str(hash)]
        url = "http://" + addr + '/db/hash/' + str(hash)
        res = requests.post(url, data=str.encode(str(data)))
        if res.status_code != 200:
            return False
        else:
            del self.table[str(hash)]
            return True
    
    def update_successor(self, succ):
        self.succ_lock.acquire()
        self.successor = succ
        self.succ_lock.release()
        if succ == self.host:
            return
        url = "http://" + succ + "/db/transfer?addr=" + self.host
        res = requests.post(url)
        if res.status_code != 200:
            print("Keys failed to transfer")

    def get_successor(self):
        self.succ_lock.acquire()
        succ = self.successor
        self.succ_lock.release()
        return succ
    
    def get_predecessor(self):
        self.pred_lock.acquire()
        pred = self.predecessor
        self.pred_lock.release()
        return pred
    
    def update_predecessor(self, pred):
        self.pred_lock.acquire()
        self.predecessor = pred
        self.pred_lock.release()

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
        del self.table[str(h)]

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
        pred = self.get_predecessor()
        if pred == self.host or DHTNode.between(n_prime, self.get_hash(pred), self.id):
            self.update_predecessor(addr)
            return True
        return False

    def closest_preceding_node(self, id_):
        for i in range(self.m - 1, -1, -1):
            finger_id = self.get_hash(self.finger_table[i])
            if DHTNode.between(finger_id, self.id, id_):
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
        self.stabalize = True

    def run(self):
        self.stabilize_thread = Thread(target = self.stabilize, args=(2,))
        self.finger_thread = Thread(target=self.fix_fingers, args=(1,))
        self.check_predecessor_thread = Thread(target=self.check_predecessor, args=(10,))
        self.stabilize_thread.start()
        self.finger_thread.start()
        self.check_predecessor_thread.start()
    
    def stop(self):
        self.stabalize = False
        self.check_predecessor_thread.join()
        self.stabilize_thread.join()
        self.finger_thread.join()

    @staticmethod
    def stabalize_node(node):
        succ = node.get_successor()
        pred = node.get_predecessor()
        if succ != node.host:
            url = 'http://{0}/dht/get_predecessor'.format(succ)
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    x = r.text
                else:
                    print('Error getting predecessor for successor: {0}'.format(url))
                    return
            except Exception:
                print('Error getting predecessor for successor: {0}'.format(url))
                return
        elif pred != node.host:
            x = pred
        else:
            return
        x_id = node.get_hash(x)
        succ_id = node.get_hash(node.get_successor())
        if DHTNode.between(x_id, node.id, succ_id):
            node.update_successor(x)
        url = 'http://{0}/dht/notify?addr={1}'.format(node.get_successor(), node.host)
        r = requests.post(url)
        if r.status_code != 200:
            print('Error notifying successor: {0}'.format(url),)

    def stabilize(self, interval):
        while self.stabalize:
            Stabalizer.stabalize_node(self.node)
            time.sleep(interval)

    def fix_fingers(self, interval):
        from dht import dht_server
        while self.stabalize:
            id = self.node.get_finger_id(self.next)
            try:
                next_entry = dht_server._find_successor(self.node, id)
            except Exception:
                print('Error fixing finger table')
                time.sleep(interval)
                continue
            if type(next_entry) != str and next_entry.status_code != 200:
                print('Error fixing finger table')
                time.sleep(interval)
                continue
            else:
                if type(next_entry) != str:
                    next_entry = next_entry.text
                self.node.finger_table[self.next] = next_entry
                if self.next == 0:
                    self.node.update_successor(next_entry)
            self.next = (self.next + 1) % self.node.m
            time.sleep(interval)

    def check_predecessor(self, interval):
        while self.stabalize:
            pred = self.node.get_predecessor()
            if pred != self.node.host:
                url = "http://{0}/".format(pred)
                try:
                    r = requests.get(url)
                    if r.status_code != 200:
                        self.node.update_predecessor(self.node.host)
                except Exception:
                    self.node.update_predecessor(self.node.host)  
            time.sleep(interval)