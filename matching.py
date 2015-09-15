#
# Module with helper function to allow for easier usage of the Munkres
# module for bipartite matching.
# 

from munkres import Munkres
from numpy import zeros
from sys import maxint

# use Munkres solver to peform bipartite matching
solver = Munkres()


def match(G):
  """
  Performs minimum bi-partite matching on a graph G.

  Input:
   * G - list<(str,str,float)> - list of 3-element tuples representing graph data.
         This is a list of (id from set1 nodes, id from set2 nodes, distance)
                                 
  Output:
   returns the following:
    * 1st element - final matching list<str, str>
    * 2nd element - list of items not matched from set1
    * 3rd element - list of items not matched from set2
  """
  # create mapping from ids to indicies
  set1_ids = set(v1 for (v1, v2, value) in G)
  set2_ids = set(v2 for (v1, v2, value) in G)
  # determine the "null" value by finding the max value + 1
  # so that we can mark invalid edges.
  null_val = max(value for (v1, v2, value) in G) + 1

  s1_to_ind, ind_to_s1 = {}, {}
  s2_to_ind, ind_to_s2 = {}, {}
  for (ind, v) in enumerate(set1_ids):
    s1_to_ind[v] = ind
    ind_to_s1[ind] = v
  for (ind, v) in enumerate(set2_ids):
    s2_to_ind[v] = ind
    ind_to_s2[ind] = v

  nrows = len(s1_to_ind)
  ncols = len(s2_to_ind)
  maxdim = max(nrows, ncols)

  D = zeros((maxdim, maxdim)) + null_val
  for (v1, v2, value) in G:
    r1 = s1_to_ind[v1]
    r2 = s2_to_ind[v2]
    D[r1, r2] = value
  # perform matching on copy of D so that the values of D won't change
  matching = solver.compute(D.copy())
  
  # generate output values
  not_matched_s1 = []
  not_matched_s2 = []
  final_matching = []
  for (r1, r2) in matching:
    # ignore when dummy nodes match with each other
    if r1 not in ind_to_s1 and r2 not in ind_to_s2:
      continue
    # Handle case when the edge between r1 and r2 is INVALID.
    # This is the case if either r1 or r2 are dummy nodes, or if
    # there is no edge between r1 and r2.
    if D[r1,r2] == null_val:
      if r1 in ind_to_s1:
        not_matched_s1.append(ind_to_s1[r1])
      if r2 in ind_to_s2:
        not_matched_s2.append(ind_to_s2[r2])
    # add the matching to the final output only if the edge between
    # r1 and r2 is valid
    else:
      final_matching.append((ind_to_s1[r1], ind_to_s2[r2]))
  return final_matching, not_matched_s1, not_matched_s2


def full_left_match(G):
  """
  Performs matching on an un-balanced graph, until all nodes of Set1 ("the left set")
  have found a match.

  Input:
   * G - list<(str,str,float)> - list of 3-element tuples representing graph data.
         This is a list of (id from set1 nodes, id from set2 nodes, distance)
  Output:
   * list<(id from set1, id from set 2)> - list of matches
  """
  current_g = G
  res = []
  # iterate until all elements of s1 have matches
  while True:
    m,s1,s2 = match(current_g)
    res += m
    if not s1:
      break
    # filter out s1 that have been matched
    # so that we can match the remaining items
    current_g = filter(lambda (v1,v2,_): v1 in s1, current_g)
  return res
