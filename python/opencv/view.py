#! /usr/bin/python
#
# (c) 2013 jnweiger@gmail.com, distribute under GPL-2.0 or ask.
#
import cv
import time

cam = cv.CaptureFromCAM(-1)
cv.SetCaptureProperty(cam,cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
cv.SetCaptureProperty(cam,cv.CV_CAP_PROP_FRAME_HEIGHT, 720)

cv.NamedWindow('camera')
cv.MoveWindow('camera', 10, 10)

while (True):
  image = cv.QueryFrame(cam)
  cv.ShowImage('camera', image)
  if (cv.WaitKey(1) != -1):
    # handle events, nonblocking
    break
  time.sleep(.1)

