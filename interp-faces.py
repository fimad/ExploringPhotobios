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

if len(sys.argv) < 4:
    print "Usage: graph.pickle face1 face2"
    exit(1)

graphFilePath = sys.argv[1]
face1 = sys.argv[2]
face2 = sys.argv[3]

#load the graph
graphFile = open(graphFilePath,"r")
graph = pickle.load(graphFile)
graphFile.close()

#Error checkin'
if not face1 in graph:
    print face1 + " is not a valid image."
if not face2 in graph:
    print face2 + " is not a valid image."

################################################################################
# Main
################################################################################

class elem:
    def __init__(self, face, value):
        self.face = face
        self.value = value
        self.back = None
    def __cmp__(self, other):
        return cmp(self.value,other.value)

def shortestPath(srcFace,dstFace):
    heapElems = {}
    heap = []
    for k in graph.keys():
        e = elem(k,float('inf'))
        if k == srcFace :
            e.value = 0
        heapElems[k] = e
        heapq.heappush(heap,e)
#   for a in range(len(graph)) :
    while(len(heap) > 0):
        node = heapq.heappop(heap).face
        for j in graph[node].keys() :
            if heapElems[j].value > (graph[node][j] + heapElems[node].value) :
                 heapElems[j].value = graph[node][j] + heapElems[node].value
                 heapElems[j].back = node
            print(graph[node][j])
        heapq.heapify(heap)
    found = False
    lst = [dstFace]
    current = dstFace
    while not found :
        lst = [heapElems[current].back] + lst
        current = heapElems[current].back
        if current == srcFace :
            found = True
    return lst
    
def expandPath(faces, depth=0):
    if depth <= 0:
        return faces
    result = []
    for i in xrange(0,len(faces)-1):
        graph[faces[i]][faces[i+1]] = float('inf')
        result = result[:-1] + expandPath(shortestPath(faces[i],faces[i+1]),depth-1)
    return result
    
faces = expandPath(shortestPath(face1,face2),1)
print(faces)
