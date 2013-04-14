#!/usr/bin/python

import cv
import math
import pickle
import sys

################################################################################
# Handle Command Line Args
################################################################################

if len(sys.argv) < 3:
    print "Usage: info.pickle [output dir] [input files]*"
    exit(1)

mappingFile = sys.argv[1]
outputDir   = sys.argv[2]
inputFiles  = sys.argv[3:]

#Haar Classifiers
haarFace = cv.Load("haar/haarcascade_frontalface_default.xml")
haarLeftEye = cv.Load("haar/haarcascade_mcs_lefteye.xml")
haarRightEye = cv.Load("haar/haarcascade_mcs_righteye.xml")
haarMouth = cv.Load("haar/haarcascade_mcs_mouth.xml")
haarNose = cv.Load("haar/haarcascade_mcs_nose.xml")

################################################################################
# Main
################################################################################

class ObjectNotFound(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return repr("Could not find object!")

def inPercentRect(image, X,Y,W,H):
    """Useful predicate for mostLikelyHaar"""
    X *= image.width
    W *= image.width
    Y *= image.height
    H *= image.height
    return lambda ((x,y,w,h),n): (x+w/2>X and y+h/2>Y and x+w/2<X+W and y+h/2<Y+H)

def mostLikelyHaar(image, haar, pred=lambda a:True):
    #Find the most likely face
    objects = cv.HaarDetectObjects(image, haar, cv.CreateMemStorage())
    objects = [obj for obj in objects if pred(obj)]
    if len(objects) == 0:
        raise ObjectNotFound()
    return sorted(objects, key=lambda (a,n) : n, reverse=True)[0]

def drawCross(image, haar, color, pred=lambda a:True):
    (x,y,w,h),n = mostLikelyHaar(image,haar,pred)
    cv.Rectangle(image, (x,y), (x+w,y+h), color)
    cv.Line(image, (x+w/2,y), (x+w/2,y+h), color)
    cv.Line(image, (x,y+h/2), (x+w,y+h/2), color)

def drawPoint(image, point, color):
    (x,y) = point
    cv.Circle(image, (int(x),int(y)), 2, color)

def getPoints(image,haar,points,pred=lambda a:True):
    (x,y,w,h),n = mostLikelyHaar(image,haar,pred)
    result = []
    for (X,Y) in points:
        result.append((x+w*X,y+h*Y))
    return result

def rotate2d(angle, center, point):
    x = point[0] - center[0]
    y = point[1] - center[1]
    newX = x*math.cos(angle) - y*math.sin(angle)
    newY = y*math.cos(angle) + x*math.sin(angle)
    return (newX+center[0],newY+center[1])

def tiltPoints(angle, points):
    #find the center of the group of points
    centerX, centerY = (0,0)
    for (x,y) in points:
        centerX += x
        centerY += y
    centerX /= len(points)
    centerY /= len(points)

    #rotate each point about the center
    newPoints = []
    for p in points:
        newPoints.append(rotate2d(angle, (centerX,centerY), p))

    return newPoints



def preprocessImage(inputPath, outputPath):
    image = cv.LoadImage(inputPath, 0)

    #Find the most likely face
    (x,y,w,h),n = mostLikelyHaar(image, haarFace)
    croppedImage = cv.CreateImage( (w, h), image.depth, image.nChannels)
    src_region = cv.GetSubRect(image, (x, y, w, h) )
    cv.Copy(src_region, croppedImage)
    image = croppedImage

    #Find each ficudial point
    leftEye     = getPoints(image, haarLeftEye, [(.2,.5), (.8,.5)], inPercentRect(image, 0,0,.6,.5))
    rightEye    = getPoints(image, haarRightEye, [(.1,.5), (.9,.5)], inPercentRect(image,.4,0,1,.5))
    mouth       = getPoints(image, haarMouth, [(0,.3), (1,.3)], inPercentRect(image,0,.6,1,1))
    nose        = getPoints(image, haarNose, [(.2,.5), (.5,.5), (.8,.5)])

    #rotate each set of points by the tilt of the face
    tiltAngle   = math.atan2(rightEye[0][1] - leftEye[0][1], rightEye[0][0] - leftEye[0][0])
    leftEye     = tiltPoints(tiltAngle, leftEye)
    rightEye    = tiltPoints(tiltAngle, rightEye)
    mouth       = tiltPoints(tiltAngle, mouth)
    nose        = tiltPoints(tiltAngle, nose)


    for p in leftEye+rightEye+mouth+nose:
        drawPoint(image, p, 255)

    cv.SaveImage(outputPath, image)
    return True

outputId = 0
info = {}
for inputPath in inputFiles:
    print inputPath
    try:
        outputPath = outputDir + "/" + str(outputId) + ".png"
        preprocessImage(inputPath, outputPath)
        info[inputPath] = outputPath
        outputId = outputId + 1
    except ObjectNotFound:
        print "\tCould not find a face..."

#save the mapping
pickle.dump(info,open(mappingFile,"w"))
