#!/usr/bin/python

import cv
import math
import os
import pickle
import sys
import math
import numpy as np

################################################################################
# ImageObject
################################################################################

class ImageObject:
    """An object in an image that records the bounding box"""
    def findPoints(self, image,haar,points,pred):
        (x,y,w,h),n = mostLikelyHaar(image,haar,pred)
        result = []
        for (X,Y) in points:
            result.append((x+w*X,y+h*Y))
        return result

    def __init__(self, image, haar, pred=lambda a:True):
        points = self.findPoints(image, haarLeftEye, [(0,0), (1,1)], pred)
        self.x = points[0][0]
        self.y = points[0][1]
        self.w = points[1][0] - self.x
        self.h = points[1][1] - self.y

    def getPoints(self, points):
        result = []
        for (X,Y) in points:
            result.append((self.x+self.w*X,self.y+self.h*Y))
        return result

################################################################################
# Handle Command Line Args
################################################################################

if len(sys.argv) < 4:
    print "Usage: info.pickle graph.pickle power"
    exit(1)

infoFilePath  = sys.argv[1]
graphFilePath = sys.argv[2]
power = float(sys.argv[3])
mouthWeight = .8
eyeWeight = .2

#load the info
infoFile = open(infoFilePath,"r")
info = pickle.load(infoFile)
infoFile.close()

################################################################################
# Normalizing
################################################################################

def getStats(lst):
    mean = 0
    stddev = 0
    for l in lst:
        mean += l
    mean /= float(len(lst))

    for l in lst:
        stddev += (l-mean)*(l-mean)
    stddev = math.sqrt(stddev/float(len(lst)))

    return mean, stddev

def normalize(graph, field):
    values = [ graph[k1][k2][field] for k1 in graph.keys() for k2 in graph[k1].keys()]
    mean, stddev = getStats(values)
    for k1 in graph.keys():
        for k2 in graph[k1].keys():
            graph[k1][k2][field] = 1/(1 + math.exp(-math.log(99)*(graph[k1][k2][field]-mean)/stddev))

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
    aNorm = float(sum([a[i] for i in a.keys()]))
    bNorm = float(sum([b[i] for i in b.keys()]))
    for k in set(a.keys() + b.keys()):
        diff = query(a,k)*bNorm/aNorm - query(b,k)
        value += diff*diff/(query(b,k)+query(a,k)*bNorm/aNorm)
    return value

################################################################################
# Construct the graph
################################################################################

graph = {}

#Calculate the X2 values
for v1 in info.keys():
    graph[v1] = {}
    for v2 in info.keys():
        if v1 == v2:
            continue
        graph[v1][v2] = {}
        graph[v1][v2]['mouth'] = x2(info[v1]['lbp-mouth'], info[v2]['lbp-mouth'])
        graph[v1][v2]['left-eye'] = x2(info[v1]['lbp-left-eye'], info[v2]['lbp-left-eye'])
        graph[v1][v2]['right-eye'] = x2(info[v1]['lbp-right-eye'], info[v2]['lbp-right-eye'])
        graph[v1][v2]['tilt'] = abs(info[v1]['tilt']-info[v2]['tilt'])

    normalize(graph, 'tilt')
    normalize(graph, 'mouth')
    normalize(graph, 'left-eye')
    normalize(graph, 'right-eye')

for v1 in info.keys():
    for v2 in info.keys():
        if v1 == v2:
            continue
        
        app = 1 - (1-mouthWeight*graph[v1][v2]['mouth'])*(1-.5*eyeWeight*graph[v1][v2]['right-eye'])*(1-.5*eyeWeight*graph[v1][v2]['left-eye'])
        print app
        graph[v1][v2] = math.pow(1 - (1-app)*(1-graph[v1][v2]['tilt']), power)
        #graph[v1][v2] = math.pow(1 - (1-graph[v1][v2]['tilt']), power)

pickle.dump(graph,open(graphFilePath,"w"))
