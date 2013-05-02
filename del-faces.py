#!/usr/bin/python

import cv
import math
import os
import pickle
import sys
import math
import heapq
import numpy as np


################################################################################
# Handle Command Line Args
################################################################################

if len(sys.argv) < 3:
    print "Usage: graph.pickle faces*"
    exit(1)

graphFilePath = sys.argv[1]
faces = sys.argv[2:]

graphFile = open(graphFilePath,"r")
graph = pickle.load(graphFile)
graphFile.close()

################################################################################
# Main
################################################################################

#Remove top level
for face in faces:
    if face in graph:
        del graph[face]

#Remove pointed to references
for root in graph.keys():
    for face in faces:
        if face in graph[root]:
            del graph[root][face]

pickle.dump(graph,open(graphFilePath,"w"))
