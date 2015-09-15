import unittest
import matching

class MatchingTester(unittest.TestCase):
  
  def test_matching(self):
    g = [("apple","banana",1), 
         ("peanut", "banana",2)]
    matches,left_remain,right_remain = matching.match(g) 
    self.assertTrue(matches == [("apple", "banana")])
    self.assertTrue(left_remain == ["peanut"])

  def test_full_left_matching(self):
    g = [("a","b",1),
         ("c","b",2),
         ("y","z",10),
         ("y","zz",100)]
    matches = matching.full_left_match(g)
    self.assertTrue(("a","b") in matches)
    self.assertTrue(("c","b") in matches)
    self.assertTrue(("y","z") in matches)
