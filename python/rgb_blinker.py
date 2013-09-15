#! /usr/bin/python
import sys, lumitile, time, termios, select

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=20)

while (not kachel.getch()):
  kachel.send(155,0,0, delay=0.03)
  kachel.send(0,155,0, delay=0.03)
  kachel.send(0,0,155, delay=0.03)

while (not kachel.getch()):
  for i in range(20): kachel.send(255,0,0, addr=i+1)
  time.sleep(0.33)
  for i in range(20): kachel.send(0,255,0, addr=i+1)
  time.sleep(0.33)
  for i in range(20): kachel.send(0,0,255, addr=i+1)
  time.sleep(0.33)

