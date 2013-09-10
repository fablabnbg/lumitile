#! /usr/bin/python
import sys, lumitile

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev)

k = 19
j = 20
while (not kachel.getch()):
  for i in (1,3,5,7,9,11,13,15,17,19,20,18,16,14,12,10,8,6,4,2):
    kachel.send(120,40,0, delay=0.001)
    kachel.send(0,0,120, addr=i, delay=0.001)
    kachel.send(0,0,255, addr=j, delay=0.001)
    kachel.send(0,0,120, addr=k, delay=0.02)
    k = j
    j = i

