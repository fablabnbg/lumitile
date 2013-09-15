#! /usr/bin/python
import sys, lumitile

dev="/dev/ttyUSB0"
if len(sys.argv) > 1: dev=sys.argv[1]
kachel = lumitile.lumitile(port=dev)

def interpolate_rgb(idx, cols=[(255,0,0),(0,0,255)], steps=10, sigma=1):
  """sigma=0 is a linear interpolator, sigma=1 is a soft curve, sigma=10 is a stronger curve,
     holding the given colors longer, and transiting faster. (Low sigma's are
     almost always in transit, and show the given colors only briefly).
  """
  top = steps * len(cols)
  idx = idx % top
  c1 = (idx / steps)

  def pseudo_sin(x, sigma=0.5):
    """ takes an x in the range [0..1], a sigma value in the range [0..1] and 
        returns a value in the range [0..1], with the following equations always true:
        pseudo_sin(0) == 0; pseudo_sin(0.5) == 0.5; pseudo_sin(1) == 1
        the first derivative is 0 for x=0 and x=1. (except for sigma == 0, where 
        the derivative is always 1). The first derivative in x=0.5 is directly controlled 
        by sigma. The curve is rotational symmetric around the point (0.5,0.5)
    """
    if (sigma <= 0.000001): return x
    if (sigma > 1): sigma = 1

    def strongest(x): return x*x*x*x
    def weakest(x):   return x
    if (x < 0.5): 
      xstrong = strongest(2*x)*0.5
      xweak   =   weakest(2*x)*0.5
    else:
      xstrong = 1 - strongest(2*(1-x))*0.5
      xweak   = 1 -   weakest(2*(1-x))*0.5

    return (1-sigma)*xweak + sigma*xstrong

  def test():
    for sigma in (0, 0.25,0.5, 0.75, 1):
      print "sigma=",sigma
      for xx in range(0, 21):
        x = xx * 0.05
        print "%.2f " % pseudo_sin(x, sigma),
      print " "

  test()
  sys.exit()
        

k = 19
j = 20
x = 0
while (not kachel.getch()):
  for i in (21,22,23,24,25,26,25,24,23,22):       # (1,3,5,7,9,11,13,15,17,19,20,18,16,14,12,10,8,6,4,2):
    # kachel.send(120,120,120, addr=i, delay=0.001)
    kachel.send(255,255,255, addr=j, delay=0.001)
    # kachel.send(120,120,120, addr=k, delay=0.02)
    if (x % 123 == 0):
      kachel.send(0,255,0, delay=.1)
    else:
      (bg_r,bg_g,bg_b) = interpolate_rgb(x, [(255,160,0),(255,255,0),(0,255,0),(0,255,255),(255,0,255)], 10);
      kachel.send(bg_r,bg_g,bg_b, delay=0.001)
    x += 1
    k = j
    j = i
