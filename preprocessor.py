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

if len(sys.argv) < 3:
    print "Usage: info.pickle used-images output-dir input-files*"
    exit(1)

mappingFile     = sys.argv[1]
usedImageDir    = sys.argv[2]
outputDir       = sys.argv[3]
inputFiles      = sys.argv[4:]

#Haar Classifiers
haarFace = cv.Load("haar/haarcascade_frontalface_default.xml")
haarLeftEye = cv.Load("haar/haarcascade_mcs_lefteye.xml")
haarRightEye = cv.Load("haar/haarcascade_mcs_righteye.xml")
haarMouth = cv.Load("haar/haarcascade_mcs_mouth.xml")
haarNose = cv.Load("haar/haarcascade_mcs_nose.xml")

#Ideal Face
#idealPoints = map(lambda (a,b): (a/103.0, b/103.0), [(19.80104218826367, 37.63465878965536), (37.198957811736335, 37.36534121034464), (52.101485417755114, 37.19192747031339), (76.8985145822449, 36.80807252968661), (29.002156251580004, 75.8786043923904), (64.99784374842, 75.32139560760959), (36.601006250737335, 63.13001538311552), (45.0, 63.0), (53.39899374926267, 62.86998461688448)])
idealPoints = map(lambda (a,b): (a/134.0, b/134.0), [(29.35313707306181, 51.35855960855365), (54.55313707306181, 51.35855960855365), (76.04257994764151, 51.57699155268393), (108.04257994764151, 51.57699155268392), (39.47082505954222, 106.25436184985874), (63.4708250595, 106.25436184985874), (87.47082505954222, 106.25436184985874), (54.10990610322404, 83.90063630466794), (64.90990610322403, 83.90063630466793), (75.70990610322403, 83.90063630466794)])
def getIdealPoints(width,height):
    return map(lambda (a,b): (a*width,b*height), idealPoints)

################################################################################
# Feature Detection
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

    def getTuple(self):
        return (self.x, self.y, self.w, self.h)

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

################################################################################
# LBP
################################################################################

def cellUnion(a,b):
    """More efficient if the smaller dictionary is second"""
    result = a
    for k in b.keys():
        if k in a:
            result[k] = a[k] + b[k]
        else:
            result[k] = b[k]
    return result


def calcLBPPixel(image, x, y):
    result = 0
    bit = 1
    for X in range(x-1,x+2):
        for Y in range(y-1,y+2):
            if x == X and y == Y:
                continue
            if image[x,y] > image[X,Y]:
                result = result | bit
            bit = bit << 1
    return result

def calcLBPCell(image, cellX, cellY):
    result = {}
    for x in range(cellX,cellX+16):
        for y in range(cellY,cellY+16):
            w,h = cv.GetSize(image)
            if x-1 >=0 and y-1>=0 and x+1<w and y+1<h:
                result = cellUnion(result, {calcLBPPixel(image,x,y) : 1})
    return result

def calcLBP(image, feature):
    cellsW = int(math.ceil(feature.w/16.0))
    cellsH = int(math.ceil(feature.h/16.0))
    result = {}
    for w in range(cellsW):
        for h in range(cellsH):
            result = cellUnion(result, calcLBPCell(image,feature.x+w*16, feature.y+h*16))
    return result

################################################################################
# Draw
################################################################################

def drawCross(image, haar, color, pred=lambda a:True):
    (x,y,w,h),n = mostLikelyHaar(image,haar,pred)
    cv.Rectangle(image, (x,y), (x+w,y+h), color)
    cv.Line(image, (x+w/2,y), (x+w/2,y+h), color)
    cv.Line(image, (x,y+h/2), (x+w,y+h/2), color)

def drawRect(image, obj):
    color = 1
    cv.Rectangle(image, (obj.x,obj.y), (obj.x+obj.w,obj.y+obj.h), color)

def drawPoint(image, point, color):
    (x,y) = point
    cv.Circle(image, (int(x),int(y)), 2, color)

################################################################################
# Main
################################################################################

def getPinnedPoint(x,y):
    return "  "+str(x)+","+str(y)+" "+str(x)+","+str(y)+"  "

def getPinnedCorners(w,h):
    return getPinnedPoint(0,0) + getPinnedPoint(w,0) + getPinnedPoint(w,h) + getPinnedPoint(0,h)

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

def rotateImage(image, angle, center):
    rot_mat = cv.CreateMat(2,3,cv.CV_32FC1)
    cv.GetRotationMatrix2D(center,angle*180/3.14159,1.0,rot_mat)
    result = cv.CloneImage(image)
    cv.WarpAffine(image, result, rot_mat)
    return result

def preprocessImage(inputPath, outputPath):
    image = cv.LoadImage(inputPath, 0)

    #Find the most likely face
    (x,y,w,h),n = mostLikelyHaar(image, haarFace)
    croppedImage = cv.CreateImage( (w, h), image.depth, image.nChannels)
    scaledImage = cv.CreateImage( (256, 256), image.depth, image.nChannels)
    src_region = cv.GetSubRect(image, (x, y, w, h) )
    cv.Copy(src_region, croppedImage)
    cv.Resize(croppedImage,scaledImage)
    image = scaledImage

    #Find each ficudial point
    leftEye         = ImageObject(image, haarLeftEye, inPercentRect(image, 0,0,.6,.5))
    leftEyePoints   = leftEye.getPoints([(.2,.5), (.8,.5)])
    rightEye        = ImageObject(image, haarRightEye, inPercentRect(image,.4,0,1,.5))
    rightEyePoints  = rightEye.getPoints([(.2,.5), (.8,.5)])
    mouth           = ImageObject(image, haarMouth, inPercentRect(image,0,.6,1,1))
    mouthPoints     = mouth.getPoints([(0,.3), (.5,.3) , (1,.3)])
    nose            = ImageObject(image, haarNose)
    nosePoints      = nose.getPoints([(.2,.5), (.5,.5), (.8,.5)]);

    #rotate each set of points by the tilt of the face
    tiltAngle       = math.atan2(rightEyePoints[0][1] - leftEyePoints[0][1], rightEyePoints[0][0] - leftEyePoints[0][0])
    leftEyePoint    = tiltPoints(tiltAngle, leftEyePoints)
    rightEyePoints  = tiltPoints(tiltAngle, rightEyePoints)
    mouthPoints     = tiltPoints(tiltAngle, mouthPoints)
    nosePoints      = tiltPoints(tiltAngle, nosePoints)

    image = rotateImage(image, tiltAngle, (w/2,h/2))

    leftEye         = ImageObject(image, haarLeftEye, inPercentRect(image, 0,0,.6,.5))
    rightEye        = ImageObject(image, haarRightEye, inPercentRect(image,.4,0,1,.5))
    mouth           = ImageObject(image, haarMouth, inPercentRect(image,0,.6,1,1))
    nose            = ImageObject(image, haarNose)

    rotation        = math.log(leftEye.w)-math.log(rightEye.w)
    print rotation

    info = {
                'image' : outputPath
            ,   'lbp-left-eye' : calcLBP(image, leftEye)
            ,   'left-eye' : leftEye.getTuple()
            ,   'lbp-right-eye' : calcLBP(image, rightEye)
            ,   'right-eye' : rightEye.getTuple()
            ,   'lbp-mouth' : calcLBP(image, mouth)
            ,   'mouth' : mouth.getTuple()
            ,   'tilt' : tiltAngle
            ,   'rotation' : rotation
    }

    #save image of the cropped face
    cv.SaveImage(outputPath, image)

    return info

#Don't actually warp for now
#    points = leftEye+rightEye+mouth+nose
#    points = map(lambda p: rotate2d(-tiltAngle,(w/2,h/2),p), points)
#    print(points)
#    #for p in points:
#    #    drawPoint(image, p, 255)
#
#    #use image magick to warp the face to a neutral pose
#    idealPoints = getIdealPoints(w,h)
#    magickPoints = getPinnedCorners(w,h)
#    magickPoints = ""
#    for i in xrange(len(idealPoints)):
#        current = points[i]
#        target = idealPoints[i]
#        magickPoints += "  "+str(current[0])+","+str(current[1])+" "
#        magickPoints += " "+str(target[0])+","+str(target[1])+"  "
#
#    #os.system("convert %s -virtual-pixel Black -define shepards:power=0.1 -distort Shepards '%s' %s.warp.png" % (outputPath, magickPoints, outputPath))
#
#    return True

outputId = 0
info = {}
for inputPath in inputFiles:
    a,ext = os.path.splitext(inputPath)
    if ext == ".gif":
        continue
    outputPath = outputDir + "/" + str(outputId) + ".png"
    copyPath = usedImageDir + "/" + os.path.basename(str(outputId)) + ext
    print inputPath + " -> " + outputPath
    try:
        #preprocessImage(inputPath, outputPath)
        info[copyPath] = preprocessImage(inputPath, outputPath)
        outputId = outputId + 1
        os.system("cp '"+inputPath+"' '"+copyPath+"'")
    except (ObjectNotFound, IOError):
        print "\tCould not find a face..."

#save the mapping
pickle.dump(info,open(mappingFile,"w"))
