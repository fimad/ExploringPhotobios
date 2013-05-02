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
    print "Usage: movie working-dir images*"
    exit(1)

movie       = sys.argv[1]
workingDir  = sys.argv[2]
images      = sys.argv[3:]
