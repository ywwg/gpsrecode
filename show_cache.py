#!/usr/bin/python

import pickle
import os
import math

f = open(os.getenv('HOME')+"/.gpswaypoints","r")
[contrib,waypoints] = pickle.load(f)
waypoints.sort()
print contrib
for w in waypoints:
	print w
