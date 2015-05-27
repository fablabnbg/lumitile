#! /usr/bin/python
import sys, lumitile, hyperion, random as r

dev="/dev/ttyATH0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=0)
hyp = hyperion.server()

dorand=1
while (1):
  if (hyp.poll()):
    rgb = hyp.color()
    if rgb:               
      # print "r=%d, g=%d, b=%d" % (rgb[0], rgb[1], rgb[2])
      kachel.send(rgb[0], rgb[1], rgb[2], delay=.01)
      dorand=0
    else:
      # print "off"
      dorand=1
  if dorand:                                 
    a = r.randint(1,20)
    if r.random() > 0.997: a = 0
    kachel.send(r.randint(0,255),
                r.randint(0,255),
                r.randint(0,255), addr=a, delay=r.random()*5)
    # colors are much nicher if we add this:
    for i in (range(r.randint(1,10))): r.randint(1,20)

