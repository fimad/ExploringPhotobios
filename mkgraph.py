#!/usr/bin/python

import cv
import math
import os
import pickle
import sys
import math
import numpy as np

################################################################################
# Handle Command Line Args
################################################################################

if len(sys.argv) < 2:
    print "Usage: info.pickle graph.pickle"
    exit(1)

infoFilePath  = sys.argv[1]
graphFilePath = sys.argv[2]

#load the info
infoFile = open(infoFilePath,"r")
info = pickle.dump(infoFile)
infoFile.close()

################################################################################
# X2 Tests
################################################################################

def query(a,k):
    """Queries a dict for a value, returning 0 if it doesn't exist"""
    if k in a:
        return a[k]
    else:
        return 0

def x2(a,b):
    """Computes chi-squared between a and b where b is the ideal"""
    value = 0
    for k in set(a.keys() + b.keys()):
        diff = query(a,k) - query(b,k)
        value += diff*diff/(query(b,k) + 0.00001)
    return value

################################################################################
# Construct the graph
################################################################################

graph = {}

for v1 in info.keys():
    graph[v1] = {}
    for v2 in info.keys():
        if v1 == v2:
            continue
        print x2(v1['lbp-mouth'], v2['lbp-mouth'])

