import unittest
import scheduler as sh
import datetime as dt

from time import mktime

class SchedulerTester(unittest.TestCase):
  
  def test_has_food_overlap(self):
    # test for simple overlaps
    self.assertTrue(sh.has_food_overlap({"foodtype": 2}, {"accepts": 3}))
    self.assertFalse(sh.has_food_overlap({"foodtype": 8}, {"accepts": 3}))
  
  def test_can_deliver_timely(self):
    # create provider for:
    # * (2015/3/30 @ 7am) is a Monday
    # * lng/lat = 0,0
    p1 = {"time": mktime(dt.datetime(2015, 3, 30, 7).timetuple()),
          "coordinate": {"lat": 0.0, "lng": 0.0}}

    # test for when schedules do not match
    # * create recipient that does not open until 10am on monday
    # (represented as the number 16 in bit format)
    r1 = {"availability": {"monday": 16},
          "coordinate": {"lat": 100.0, "lng": 100.0}}
    can_deliver_1, dist_1 = sh.can_deliver_timely(p1, r1)
    self.assertFalse(can_deliver_1)

    # * create recipient that does not open at all on tuesday
    r2 = {"availability": {"monday": 0},
          "coordinate": {"lat": 100.0, "lng": 100.0}}
    can_deliver_2, dist_2 = sh.can_deliver_timely(p1, r2)
    self.assertFalse(can_deliver_2)
