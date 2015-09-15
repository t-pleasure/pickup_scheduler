import json, csv, sys
from collections import defaultdict
from datetime import datetime as dt
from geopy.distance import vincenty
from matching import uni_matching

# Mapping from integer to day of week
num2day = {0: "monday", 
           1: "tuesday", 
           2: "wednesday",
           3: "thursday",
           4: "friday",
           5: "saturday",
           6: "sunday"}


def has_food_overlap(p, r):
  """
  Checks to see if recipient can accept food from provider. To do so,
  this function checks to see if the provider and recipient have any
  matching food bits as specified by provider's "foodtype" field and 
  recipient's "accepts" field.

  Inputs:
    p (dict) - provider
    r (dict) - recipient
  Output:
    True if recipient can accept a foodtype provided by provider. Otherwise, False.
  """
  return bool(p["foodtype"] & r["accepts"])

def compute_distance(p, r):
  """
  Computes the distance (in miles) between p and r using the vincenty method

  Inputs:
    p (dict) - provider
    r (dict) - recipient
  Output:
    The distance (float) between p and r. 
  """
  plat = p["coordinate"]["lat"]
  plng = p["coordinate"]["lng"]
  rlat = r["coordinate"]["lat"]
  rlng = r["coordinate"]["lng"]
  return vincenty((plat,plng),(rlat,rlng)).miles

def can_deliver_timely(p, r):
  """
  Determines whether or not a delivery can be made from the provider's location
  to the recipient's location with respects to their time availabilities. 
  This function will take into account the estimated arrival and drop-off windows.

  Inputs:
    p (dict) - provider
    r (dict) - recipient
  Output:
    2 item tuple containing:
    * first elemnt (boolean) indicates whether or not the delivery can be made based on the
      provider and recipient's time availabilities.
    * second element (float) represents the distance from the provider to recipient (in miles).
  """

  # compute distance in miles (using vincenty method) from provider to recipient
  distance = compute_distance(p, r)

  # compute estimated duration of trip (in hours) given average travel speed is 35mi/h
  duration = distance * (1/35.0)

  # extract pickup timestamp from provider
  pickup_dt = dt.fromtimestamp(p["time"])

  # compute earliest and latest estimated times of arrival
  earliest_promised_time = pickup_dt.hour + (pickup_dt.minute / 60.0)
  earliest_eta = earliest_promised_time + duration
  latest_eta = earliest_promised_time + 1 + duration
  
  # determine day of week that provider can provide food
  pickup_day = num2day[pickup_dt.weekday()]

  # find the schedule of the recipient for day that the provider can provide food.
  receiver_sched = r["availability"][pickup_day]

  # compute whether or not receiver is open during earliest_eta and latest_eta
  can_deliver = ((2 ** (int(earliest_eta) - 7)) & receiver_sched and 
                 (2 ** (int(latest_eta) - 7)) & receiver_sched)

  return (can_deliver, distance)




################################################################
# Driver section of code (only invoked when called as script) #
#                                                             #
################################################################
if __name__ == "__main__":
  # read in data
  providers = dict((p["id"], p) for p in json.load(open("data/pickups.json")))
  recipients = dict((r["id"], r) for r in json.load(open("data/recipients.json")))

  # -- Greate Graph Data --
  # create a connection from (provider -> recipient) if
  # their food types match and the delivery time from provider
  # to recipient is acceptable.
  G = {}
  for p in providers.values():
    for r in recipients.values():
      (can_deliver, dist) = can_deliver_timely(p, r)
      if has_food_overlap(p, r) and can_deliver and dist <= 15:
        G[(p["id"], r["id"])] = dist

  # convert graph data to flattened list of tuples form
  glist = [(p,r,d) for ((p,r), d) in G.items()]
  # perform matching on graph
  matches = uni_matching(glist)

  ##########################
  # -- generate outputs -- #
  ##########################

  #####################################################
  # Helper functions to create human readable outputs #
  #####################################################
  def bits2food(bs):
    # converts bits in the "foodtype" and "accepts" field
    # to a human readable string.
    ret = []
    for (ind, food) in enumerate(["Raw", "Prepared", "Dairy", "Packaged", "Baked", "Meat"]):
      if (bs & (2**ind)):
        ret.append(food)
    return ", ".join(ret)

  def bits2hours(bs):
    # converts bits in the "availability" field to a human
    # readable string.
    ret = []
    for ind in range(16):
      if (bs & (2**ind)):
        ret.append("%dh00"%(ind + 7))
    return ",".join(ret)

  def address_str(addr):
    # generates a string from a address dictionary
    return ",".join(map(lambda k: addr[k], ["street", "city", "state", "zip"]))

  def hr_str(hr):
    # converts hour float to str representation
    mn = (hr - int(hr))*60
    return "%02dh%02d"%(hr, mn)

  ####################################
  # create output                    #
  ####################################

  headers = ["pickup_id", "pickup_address", "pickup_foodtype", "pickup_date", "pickup_time", 
             "pickup_day", "recipient_id", "recipient_address", "recipient_accepts", 
             "recipient_hours_on_day_of_pickup", "trip_distance", "trip_duration", "estimated_delivery_window"]
  out = csv.DictWriter(sys.stdout, headers, quoting=csv.QUOTE_ALL)
  out.writeheader()

  # iterate through matches and write to output
  for (pid, rid) in matches:
    # ignore invalid matches (this is an artifact of the bipartite-matching library's attempt at over-assigning)
    if (pid, rid) not in G:
      continue

    p = providers[pid]
    r = recipients[rid]
    pickup_dt = dt.fromtimestamp(p["time"])
    pickup_hr = pickup_dt.hour + (pickup_dt.minute / 60.0)
    pickup_weekday = num2day[pickup_dt.weekday()] 
    distance = G[(pid,rid)]
    duration = distance * (1/35.0)
    data = {"pickup_id": p["id"],
            "pickup_address": address_str(p["address"]),
            "pickup_foodtype": bits2food(p["foodtype"]),
            "pickup_date": pickup_dt.strftime("%m/%d/%Y"),
            "pickup_time": "%s-%s"%(hr_str(pickup_hr), hr_str(pickup_hr+1)),
            "pickup_day": pickup_weekday, 
            "recipient_id": r["id"],
            "recipient_address": address_str(r["address"]),
            "recipient_accepts": bits2food(r["accepts"]),
            "recipient_hours_on_day_of_pickup": bits2hours(r["availability"][pickup_weekday]),
            "trip_distance": "%f miles"%distance,
            "trip_duration": hr_str(duration),
            "estimated_delivery_window":  "%s-%s"%(hr_str(pickup_hr + duration), hr_str(pickup_hr + 1 + duration))}
    out.writerow(data)
