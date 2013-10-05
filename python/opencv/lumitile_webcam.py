#! /usr/bin/python
#
# (c) 2013 jnweiger@gmail.com, distribute under GPL-2.0 or ask.
#
# 2013-10-03, V0.1 jw -- initial draught, propedit() added.
#                        Sometimes my camera runs at 30fps, somtimes at 15fps
#                        no idea, how to control this.
# 2013-10-04, V0.1 jw -- adding draw_panel(), navigation done.
# 2013-10-05, V0.2 jw -- get_panel() to compute the average per field. wip
# 2013-10-05, V0.3 jw -- send_panel() added.
#
# References:
# http://docs.opencv.org/modules/core/doc/drawing_functions.html

import cv
import sys, time, string
sys.path.append('..')
sys.path.append('.')
import lumitile

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]

def help():
      print "toggle display mode: (C)olor, (G)ray, (E)dge detect"
      print "navigate panel: (M)ove, then cursor keys; or (S)cale, then cursor keys"
      print "                If cursor keys do not work: H, J, K, L"
      print "                (+)/(-): Increase/Decrease steps"
      print "show/edit capture properties: (P), then N [Enter], Value [Enter]"
      print "exit: (X), (Q), ESC"

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

kachel = lumitile.lumitile(port=dev, base=0)
cam = cv.CaptureFromCAM(-1)
#cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH, 320)
#cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
# cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
# cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT, 720)

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

def get_panel(cv, img, x, y, w, h, xsubdiv=10, ysubdiv=2, color=(255,0,255)):
  vals = []
  xs = w/float(xsubdiv)
  ys = h/float(ysubdiv)
  for i in range(0,xsubdiv):
    xx = int(x+(i+.5)*xs+0.5)
    for j in range(0,ysubdiv):
      yy = int(y+(j+.5)*ys+0.5)
      # measure the square
      # http://docs.opencv.org/modules/core/doc/operations_on_arrays.html?highlight=avg#mean
      # cv.SetImageROI(img, (x, y, w, h))
      # cv.Avg()
      # cv.ResetImageROI(img)
      val = cv.Get2D(img, yy, xx)
      vals.append(val)
      cv.Set2D(img, yy, xx, (255,0,0))
  return vals

def draw_panel(cv, img, x, y, w, h, xsubdiv=10, ysubdiv=2, color=(255,0,255), vals=None):
  # http://docs.opencv.org/modules/core/doc/drawing_functions.html
  xs = w/float(xsubdiv)
  ys = h/float(ysubdiv)
  for i in range(0,xsubdiv+1):
    xx = int(x+i*xs+0.5)
    cv.Line(img, (xx,int(y+.5)), (xx,int(y+h+.5)), color, 1)
  for i in range(0,ysubdiv+1):
    yy = int(y+i*ys+0.5)
    cv.Line(img, (int(x+.5),yy), (int(x+w+.5),yy), color, 1)

  if (vals):
    l = list(reversed(vals))
    s = int(img.width*2/(3*xsubdiv))
    ww = int(s*.8)
    for i in range(xsubdiv):
      xx = int(0.2*ww+i*s)
      for j in range(ysubdiv):
        yy = int(img.height-(ysubdiv-j)*s)
        c = l.pop() # unshift, actually.
        cv.Rectangle(img, (xx,yy),(xx+ww,yy+ww),(c[0],c[1],c[2]), cv.CV_FILLED)

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

def send_panel_white(vals):
  c = vals[0]
  kachel.send(255,255,255, addr=4)

def send_panel(vals):
  v = list(vals)
  # v = list(reversed(vals))
  #for a in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20):
  for a in (2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17,20,19):
    c = v.pop()
    #             red          green         blue
    kachel.send(int(c[2]), int(c[1]), int(c[0]), addr=a, delay=0.002)
    

def move_panel(dir):
  if dir == 1:
    # left
    pan['x'] -= pan['step']
    if pan['x'] <= 0: pan['x'] = 0
  elif dir == 2:
    # up
    pan['y'] -= pan['step']
    if pan['y'] <= 0: pan['y'] = 0
  elif dir == 3:
    # right
    pan['x'] += pan['step']
    if pan['x']+pan['w'] >= img_width: pan['x'] = img_width - pan['w']
  elif dir == 4:
    # down
    pan['y'] += pan['step']
    if pan['y']+pan['h'] >= img_height: pan['y'] = img_height - pan['w']
  else:
    pass

def scale_panel(dir):
  if dir == 1:
    # left
    pan['w'] -= pan['step']
    if pan['w'] <= pan['min_w']: pan['w'] = pan['min_w']
  elif dir == 2:
    # up
    pan['h'] -= pan['step']
    if pan['h'] <= pan['min_h']: pan['h'] = pan['min_h']
  elif dir == 3:
    # right
    pan['w'] += pan['step']
    if pan['x']+pan['w'] >= img_width: pan['w'] = img_width - pan['x']
  elif dir == 4:
    # down
    pan['h'] += pan['step']
    if pan['y']+pan['h'] >= img_height: pan['h'] = img_height - pan['y']
  else:
    pass

## max 15fps
# fourcc = cv.CV_FOURCC('M', 'J', 'P', 'G')
## max 30fps
#fourcc = cv.CV_FOURCC('Y', 'U', 'Y', 'V')
#cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FOURCC, fourcc)

cv.NamedWindow('camera')
cv.MoveWindow('camera', 10, 10)
img_width  = cv.GetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH)
img_height = cv.GetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT)

# start centered, covering 1/3 of the image width, asuming square pixels.
pan = { 'x':img_width/3, 'y':img_height/2-img_width/30, 
        'w':img_width/3, 'h':img_width/(3*10/2), 
        'step':img_width/100, 'min_w':20, 'min_h':4 }

now = time.time()
sec = int(now)
mode = 'c'
nav = 'm'
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
    img = gray
  
  v = get_panel(cv, img, pan['x'], pan['y'], pan['w'], pan['h'])
  draw_panel(cv, img, pan['x'], pan['y'], pan['w'], pan['h'], vals=v)
  cv.ShowImage('camera', img)
  send_panel(v)

  key_raw = cv.WaitKey(1)
  # if (key_raw != -1): print key_raw
  key = key_raw & 0xff    # force into ascii range

  # 65364 84 = c_down
  # 65362 82 = c_up
  # 65361 81 = c_left
  # 65363 83 = c_right
  # 65513 233 = alt
  # 65505 225 = shift
  if (chr(key) == 'h'): key_raw = 65361
  if (chr(key) == 'j'): key_raw = 65364
  if (chr(key) == 'k'): key_raw = 65362
  if (chr(key) == 'l'): key_raw = 65363

  if (key != 255 and key != 225 and key != 233):       
    # handle events, nonblocking, and also handle key presses
    if (chr(key) in "cge"):
      mode = chr(key)
    elif (chr(key) == 'p'):
      propedit() 
    elif (chr(key) in "mrs"):
      nav = chr(key)
    elif (chr(key) in "?"):
      help()
    elif (chr(key) == "v"):
      print v
    elif (chr(key) == "+"):
      pan['step'] *= 2
      if pan['step'] > 32: pan['step'] = 32
      print pan['step']
    elif (chr(key) == "-"):
      pan['step'] *= .5
      if pan['step'] < .25: pan['step'] = .25
      print pan['step']
    elif key_raw in (65364, 65362, 65361, 65363):
      if (nav == 'm'):
        move_panel(key_raw-65360)
      else:
        scale_panel(key_raw-65360)

    elif key in (27, ord('x'), ord('q')):
      print ""
      break
    else:
      print "undefined key %d (%d)" % (key, key_raw)
  
cv.DestroyWindow("camera")


