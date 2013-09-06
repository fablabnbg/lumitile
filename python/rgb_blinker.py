#! /usr/bin/python
import sys, lumitile, time, termios, select

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=1)

while (not kachel.getch()):
  kachel.send(255,0,0, delay=0.33)
  kachel.send(0,255,0, delay=0.33)
  kachel.send(0,0,255, delay=0.33)

