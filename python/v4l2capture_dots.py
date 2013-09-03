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

# Open the video device.
video = v4l2capture.Video_device("/dev/video0")
width = 32
if len(sys.argv) > 1: width = int(sys.argv[1])

def image_to_dots(img, w=32, h=5):
  strip=img.resize((w,h))
  min_r = 255
  min_g = 255
  min_b = 255
  max_r = 0
  max_g = 0
  max_b = 0
  for x in range(width):
    p = strip.getpixel((x,2))
    if (min_r > p[0]): min_r = p[0]
    if (min_g > p[1]): min_g = p[1]
    if (min_b > p[2]): min_b = p[2]
    if (max_r < p[0]): max_r = p[0]
    if (max_g < p[1]): max_g = p[1]
    if (max_b < p[2]): max_b = p[2]

  scale_r = 256./(max_r+1-min_r)
  scale_g = 256./(max_g+1-min_g)
  scale_b = 256./(max_b+1-min_b)
  # print min_r, min_g, min_b, max_r, max_g, max_b, scale_r, scale_g, scale_b

  a = []
  for x in range(width):
    p = strip.getpixel((x,2))
    r = int((p[0]-min_r)*scale_r)
    g = int((p[1]-min_g)*scale_g)
    b = int((p[2]-min_b)*scale_b)
    a.append((r,g,b))
  return a

# strip.save("image.jpg")
# print "Saved image.jpg (Size: " + str(size_x) + " x " + str(size_y) + ")"

# Suggest an image size to the device. The device may choose and
# return another size if it doesn't support the suggested one.
size_x, size_y = video.set_format(320, 240)

# Create a buffer to store image data in. This must be done before
# calling 'start' if v4l2capture is compiled with libv4l2. Otherwise
# raises IOError.
video.create_buffers(1)

# Send the buffer to the device. Some devices require this to be done
# before calling 'start'.
video.queue_all_buffers()

# Start the device. This lights the LED if it's a camera that has one.
video.start()

data = None

for i in range(500):
  # Wait for the device to fill the buffer.
  select.select((video,), (), ())

  # The rest is easy :-)
  data = video.read_and_queue()
  image = Image.fromstring("RGB", (size_x, size_y), data)
  a = image_to_dots(image, width)
  print a

video.close()
