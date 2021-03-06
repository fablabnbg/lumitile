#!/usr/bin/python
#
# v4l2capture-dots.py
#
# (c) 2013 jnweiger@gmail.com
# Distribute under GPL-2.0 or ask
#
# Requires: python-v4l2capture # from obs://home:jnweiger

import Image
import select
import v4l2capture
import sys
import lumitile

version='1.1'

width = 10
height = 2
led_dev="/dev/ttyUSB0"
vid_dev="/dev/video0"
if len(sys.argv) > 1: led_dev = sys.argv[1]
if len(sys.argv) > 2: vid_dev = sys.argv[2]
if len(sys.argv) > 3: width   = sys.argv[3]
if len(sys.argv) > 4: height  = sys.argv[4]

if len(sys.argv) > 1 and (sys.argv[1] == '-h' or sys.argv[1] == '-?' or sys.argv[1] == '--help'):
  print "v4l2capture_dots.py V"+version
  print "\nUsage: %s [led_dev [video_dev [width [height]]]]" % sys.argv[0]
  print "\ndefaults:\n\tled_dev=%s\n\tvideo_dev=%s\n\twidth=%d\n\theight=%d" % (led_dev, vid_dev, width, height)

# Open the LED_controller
kachel = lumitile.lumitile(port=led_dev, base=1)

# Open the video device.
video = v4l2capture.Video_device(vid_dev)

def image_to_dots(img, w=10, h=None, rows=2, pad=0, hflip=False, vflip=False):
  if h == None:
    # h = 3 * rows + 2    # we watch a third around the center. Two lines border minimum.
    h = int((2*pad+w)/4.*3.)
  strip=img.resize((w,h))
  # strip.save("image.jpg")
  # print "Saved image.jpg (Size: " + str(size_x) + " x " + str(size_y) + ")"
  min_rgb = 255
  max_rgb = 0

  y = int((h-rows)/2)

  for x in range(pad,pad+width):
    for r in range(rows):
      p = strip.getpixel((x,y+r))
      if (min_rgb > p[0]): min_rgb = p[0]
      if (min_rgb > p[1]): min_rgb = p[1]
      if (min_rgb > p[2]): min_rgb = p[2]
      if (max_rgb < p[0]): max_rgb = p[0]
      if (max_rgb < p[1]): max_rgb = p[1]
      if (max_rgb < p[2]): max_rgb = p[2]

  # scale_rgb = 256./(max_rgb+1-min_rgb)
  scale_rgb = 1
  # print min_r, min_g, min_b, max_r, max_g, max_b, scale_r, scale_g, scale_b

  range_width = range(pad,pad+width)
  range_rows = range(rows)
  if hflip: range_width.reverse()
  if vflip: range_rows.reverse()

  a = []
  for x in range_width():
    for r in range_rows():
      p = strip.getpixel((x,y+r))
      r = int((p[0]-min_rgb)*scale_rgb)
      g = int((p[1]-min_rgb)*scale_rgb)
      b = int((p[2]-min_rgb)*scale_rgb)
      a.append((r,g,b))
  return a


# Suggest an image size to the device. The device may choose and
# return another size if it doesn't support the suggested one.
size_x, size_y = video.set_format(320, 240)
# fps = video.set_fps(2)

# Create a buffer to store image data in. This must be done before
# calling 'start' if v4l2capture is compiled with libv4l2. Otherwise
# raises IOError.
video.create_buffers(10)

# Send the buffer to the device. Some devices require this to be done
# before calling 'start'.
video.queue_all_buffers()

# Start the device. This lights the LED if it's a camera that has one.
video.start()

data = None

x = 0
while (not kachel.getch()):
  # Wait for the device to fill the buffer.
  select.select((video,), (), ())

  # The rest is easy :-)
  data = video.read_and_queue()

  if 1: # (x % 3 == 0):
    image = Image.fromstring("RGB", (size_x, size_y), data)
    dots = image_to_dots(image, width, height, hflip=False, vflip=False)
    for a in range(0, len(dots)):
      kachel.send(dots[a][0], dots[a][1], dots[a][2], addr=a+1, delay=0.001)
  x += 1
    
    

video.close()
