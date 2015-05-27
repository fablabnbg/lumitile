#! /usr/bin/python
import sys, lumitile, time, termios, select

dev="/dev/ttyATH0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=20)

d=0.04
while (not kachel.getch()):
  kachel.send(255,255,255, delay=d)
  kachel.send(0,0,10, delay=d)
  
while (not kachel.getch()):
  kachel.send(255,0,0, delay=d)
  kachel.send(0,255,0, delay=d)
  kachel.send(0,0,255, delay=d)
  kachel.send(255,255,0, delay=d)
  kachel.send(0,255,255, delay=d)
  kachel.send(255,0,255, delay=d)
  kachel.send(255,255,255, delay=d)

while (not kachel.getch()):
  for i in range(20): kachel.send(255,0,0, addr=i+1)
  time.sleep(0.33)
  for i in range(20): kachel.send(0,255,0, addr=i+1)
  time.sleep(0.33)
  for i in range(20): kachel.send(0,0,255, addr=i+1)
  time.sleep(0.33)

