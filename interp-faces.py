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

if len(sys.argv) < 8:
    print "Usage: info.pickle graph.pickle face1 face2 depth frames working-dir movie"
    exit(1)

infoFilePath = sys.argv[1]
graphFilePath = sys.argv[2]
face1 = sys.argv[3]
face2 = sys.argv[4]
depth = int(sys.argv[5])
frames = int(sys.argv[6])
workingDir = sys.argv[7]
movieFilePath = sys.argv[8]

#load the graph
graphFile = open(graphFilePath,"r")
graph = pickle.load(graphFile)
graphFile.close()

#load the info
infoFile = open(infoFilePath,"r")
info = pickle.load(infoFile)
infoFile.close()

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

def shortestPath(srcFace,dstFace,badNodes):
    heapElems = {}
    heap = []
    badNodes -= set([srcFace,dstFace])
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
            if j in badNodes:
                continue
            if heapElems[j].value > (graph[node][j] + heapElems[node].value) :
                 heapElems[j].value = graph[node][j] + heapElems[node].value
                 heapElems[j].back = node
            #print(graph[node][j])
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
    """Recursively expands paths by removing nodes and finding new shortest
    paths between adjacent nodes"""
    if depth <= 0:
        return faces
    result = []
    for i in xrange(0,len(faces)-1):
        graph[faces[i]][faces[i+1]] = float('inf')
        result = result[:-1] + expandPath(shortestPath(faces[i],faces[i+1],set(result)),depth-1)
    return result

def crossfade(src1,src2,output,percent):
    """Creates a cross faded image given a specific percent"""
    command = "composite -dissolve "+str(percent)+"% '"+src2+"' '"+src1+"' '"+output+"'"
    print command
    os.system(command)

def fadeSequence(src1,src2,n,workingDir,startIndex):
    """Creates a series of cross faded images starting naming with startIndex"""
    for i in range(n):
        crossfade(src1,src2,"%s/%04d.png"%(workingDir,startIndex+i),i*100.0/(n-1))

def fadeList(srcs,n,workingDir):
    index = 0
    for i in range(len(srcs)-1):
        fadeSequence(info[srcs[i]]['image'],info[srcs[i+1]]['image'],n,workingDir,index)
        index += n

#print graph.keys()
faces = expandPath(shortestPath(face1,face2,set([])),depth)
fadeList(faces,frames,workingDir)
os.system("ffmpeg -i '"+workingDir+"%04d.png' -vcodec mpeg4 '"+movieFilePath+"'")
print(faces)

