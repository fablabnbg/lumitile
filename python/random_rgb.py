#! /usr/bin/python
import sys, lumitile, random as r

dev="/dev/ttyATH0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=0)

while (1):
  a = r.randint(1,20)
  if r.random() > 0.99: a = 0
  kachel.send(r.randint(0,255),
              r.randint(0,255),
              r.randint(0,255), addr=a, delay=r.random()*3)
  # colors are much nicher if we add this:
  for i in (range(r.randint(1,10))): r.randint(1,20)

