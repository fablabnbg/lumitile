#! /usr/bin/python
#
# (c) 2013 jnweiger@gmail.com, distribute under GPL-2.0 or ask.
#
# 2013-10-03, V0.1 jw -- initial draught, propedit() added.
#                        Sometimes my camera runs at 30fps, somtimes at 15fps
#                        no idea, how to control this.

import cv
import sys, time, string

def help():
      print "toggle display mode: (C)olor, (M)onochrome, (E)dge detect"
      print "show/edit capture properties: (P)"
      print "exit: (X), ESC, or any other key"

prop = {
  'bright':     [cv.CV_CAP_PROP_BRIGHTNESS],
  'contr':      [cv.CV_CAP_PROP_CONTRAST],
  'rgb':        [cv.CV_CAP_PROP_CONVERT_RGB],
  'expose':     [cv.CV_CAP_PROP_EXPOSURE],
  'format':     [cv.CV_CAP_PROP_FORMAT],
  'fourcc':     [cv.CV_CAP_PROP_FOURCC],
  'fps':        [cv.CV_CAP_PROP_FPS],
  'count':      [cv.CV_CAP_PROP_FRAME_COUNT],
  'height':     [cv.CV_CAP_PROP_FRAME_HEIGHT],
  'width':      [cv.CV_CAP_PROP_FRAME_WIDTH],
  'gain':       [cv.CV_CAP_PROP_GAIN],
  'hue':        [cv.CV_CAP_PROP_HUE],
  'mode':       [cv.CV_CAP_PROP_MODE],
  'rect':       [cv.CV_CAP_PROP_RECTIFICATION],
  'sat':        [cv.CV_CAP_PROP_SATURATION]
  }

cam = cv.CaptureFromCAM(-1)
idx = 0
for p in prop:
  x = cv.GetCaptureProperty(cam, prop[p][0])
  if x >= 0:
    idx += 1
    prop[p].append(idx)        # property exists
    prop[p].append(x)           # current value
    prop[p].append(x)           # initial value
  else:
    prop[p].append(0)

for p in prop:
  if prop[p][1]:
    print "property %s = '%s'" % (p, prop[p][2])

print "\n"
help()
print "\n"

def cv_readline(cv):
  s = ''
  while True:
    k = cv.WaitKey(0)
    if (k == 27 or k == 10 or k == 13): # enter
      sys.stderr.write("\n")
      return s
    elif (k == 8):                # backspace
      sys.stderr.write(chr(k)+" "+chr(k))
      s = s[:-1]
    elif (k > 0 and k < 255):
      sys.stderr.write(chr(k))
      s += chr(k)

def propedit():
  maxprop = 0
  for p in prop:
    if prop[p][1]:
      maxprop = prop[p][1]
      print "%d: %10s = %g (%g)" % (maxprop, p, prop[p][2], prop[p][3])

  print "Enter property number: [1..%d] " % maxprop
  r = cv_readline(cv)
  try:
    idx = string.atoi(r)
    for p in prop:
      if prop[p][1] == idx:
        print "Enter new value %s [%g]" % (p, prop[p][2])
        r = cv_readline(cv)
        try:
          val = string.atof(r)
          cv.SetCaptureProperty(cam, prop[p][0], val)
          val = cv.GetCaptureProperty(cam, prop[p][0])
          prop[p][2] = val
          print "prop num %d: %10s = %g" % (idx, p, prop[p][2])
        except:
          print "value unchanged"
          pass
  except:
    pass

# cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
# cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
## max 15fps
# fourcc = cv.CV_FOURCC('M', 'J', 'P', 'G')
## max 30fps
fourcc = cv.CV_FOURCC('Y', 'U', 'Y', 'V')
cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FOURCC, fourcc)

cv.NamedWindow('camera')
cv.MoveWindow('camera', 10, 10)

now = time.time()
sec = int(now)
mode = 'c'
fps_in = 0
fps_out = 0
dropcount = 0
while (True):
    
  img = cv.QueryFrame(cam)
  fps_in += 1
  dropcount += 1
  now = time.time()
  if int(now) != sec:
    print >> sys.stderr, " fps: in=%d out=%d       \r" % (fps_in, fps_out),
    fps_in = 0
    fps_out = 0
    sec = int(now)

  if (dropcount >= 2):
    dropcount = 0
  if (dropcount >= 1):
    # drop every third image, so that we stay clear of 100% cpu consumption
    # and keep the v4l buffers drained at low water. This counters excess latency.
    continue

  fps_out += 1
  if (mode in "gme"):
    gray = cv.CreateImage( (img.width, img.height), cv.IPL_DEPTH_8U, 1 );
    cv.CvtColor(img, gray, cv.CV_BGR2GRAY)
    if (mode == 'e'):
      cv.Canny(gray, gray, 50, 150, 3)
    cv.ShowImage('camera', gray)
  else:
    cv.ShowImage('camera', img)

  key = cv.WaitKey(1) & 0xff    # force into ascii range
  if (key != 255):
    # handle events, nonblocking, and also handle key presses
    if (chr(key) in "cgme"):
      mode = chr(key)
    elif (chr(key) == 'p'):
      propedit() 
    elif (chr(key) in "h?"):
      help()
    else:
      print ""
      if (key != 27 and chr(key) != 'x' and chr(key) != 'q'):
        print "undefined key %d" % key
      break
  
cv.DestroyWindow("camera")


