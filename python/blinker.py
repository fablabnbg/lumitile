#! /usr/bin/python
import sys, lumitile, time, termios, select

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev, base=40)

def getch():
  """a simple nonblocking keyboard poll
  """
  fd = sys.stdin.fileno()

  # do the input half of of tty.setraw() but keep ECHO and ICRNL, OPOST, etc
  mode = termios.tcgetattr(fd)
  # 0=IFLAG,1=OFLAG,2=CFLAG,3=LFLAG,4=ISPEED,5=OSPEED,6=CC
  mode[3] = mode[3] & ~termios.ICANON
  mode[6][termios.VMIN] = 1
  mode[6][termios.VTIME] = 0
  termios.tcsetattr(fd, termios.TCSADRAIN, mode)

  s = select.select([fd], [], [], 0)
  if len(s[0]):
    return sys.stdin.read(1)
  return 0

# for j in range(5):
if 0:
  for i in range(256): kachel.send(i, 0, 0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(255-i, 0, 0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0,     i, 0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0, 255-i, 0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0, 0,     i, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0, 0, 255-i, delay=0.005)
  if (getch()): break

  for i in range(256): kachel.send(i,     i,     0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(255-i, 255-i, 0, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0, i,     i,     delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(0, 255-i, 255-i, delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(i,     0, i,     delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(255-i, 0, 255-i, delay=0.005)
  if (getch()): break

  for i in range(256): kachel.send(i,    i,    i,     delay=0.005)
  if (getch()): break
  for i in range(256): kachel.send(255-i,255-i,255-i, delay=0.005)
  if (getch()): break

cmd_seen = 0
bl = 0
ye = 0
FADE_STEP = 5
bl_step = FADE_STEP
ye_step = 0

for j in range(20):
  for i in range(6):
    for k in range(20):
      cmd_seen = getch()
      if (cmd_seen): break
      l = i + 1
      kachel.send(255, ye, bl, addr=l);
      l = (l % 6) + 1
      kachel.send(ye,  ye, bl, addr=l);
      l = (l % 6) + 1
      kachel.send(ye,  ye, bl, addr=l);
      l = (l % 6) + 1
      kachel.send(ye, 255, bl, addr=l);
      l = (l % 6) + 1
      kachel.send(ye,  ye, bl, addr=l);
      l = (l % 6) + 1
      kachel.send(ye,  ye, bl, addr=l);
      l = (l % 6) + 1
      bl += bl_step;
      ye += ye_step;
      if (bl > 255):
        bl = 255
        bl_step = -FADE_STEP
      if (bl < 0):
        bl = 0
        bl_step = 0
        ye_step = FADE_STEP
      if (ye > 166):
        ye = 166
        ye_step = -FADE_STEP
      if (ye < 0):
        ye = 0
        ye_step = 0
        bl_step = FADE_STEP
      # time.sleep(0.020)	#  tune to 33bpm

    if (cmd_seen): break
  if (cmd_seen): break

while (not getch()):
  kachel.send(255,0,0, delay=0.1)
  kachel.send(0,255,0, delay=0.1)
  kachel.send(0,0,255, delay=0.1)

