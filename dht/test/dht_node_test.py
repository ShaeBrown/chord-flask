import unittest
from dht import DHTNode

class TestBetween(unittest.TestCase):
    def test_between_0(self):
        between = DHTNode.between(0, 100, 1)
        self.assertTrue(between)
    
    def test_between_1(self):
        between = DHTNode.between(10, 0, 11)
        self.assertTrue(between)

    def test_between_2(self):
        between = DHTNode.between(11, 0, 11)
        self.assertFalse(between)

    def test_between_right_inclusive(self):
        between = DHTNode.between_right_inclusive(11, 0, 11)
        self.assertTrue(between)

if __name__ == '__main__':
    unittest.main()