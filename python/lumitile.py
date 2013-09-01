#! /usr/bin/python
#
# lumitile.py -- a driver class for Dirk Leber's LED tiles
#
# (c) 2013 Juergen Weigert jw@suse.de
# Distribute under GPL-2.0 or ask
#
# 2013-08-29, V0.1 jw -- inintial draught: 

import serial, time

__VERSION__ = '0.1'

class lumitile():
  """ A driver for Dirk Leber's LED Kacheln -- this
      uses a ATtiny2313 based signal converter from RS232 to RS458
  """
  def __init__(self, baud=115200, port="/dev/ttyUSB0", base=1):
    self.addr = 255             # broadcast
    self.base = base            # shift the addresses
    print "dev=", port, "   speed=", baud
    self.ser = serial.Serial(port, baud, timeout=1)
    print "serial port opened"
  
  def send(self, red=255, green=255, blue=255, addr=0, now=True, delay=0):
    if (addr == 0): addr = self.addr
    if (addr != 255): addr += self.base - 1;
    cmd = chr(addr)+chr(red)+chr(green)+chr(blue)
    if (now):
      self.ser.write("FS"+cmd)
    else:
      self.ser.write("FL"+cmd)
    time.sleep(0.001);           # wait, while the controller processes the command.
    # print "%d %d %d %d" % (addr, red, green, blue)
    if delay:
      time.sleep(delay)

  def addr(self, a):       self.addr = a
  def white(self, a=0):    send(255,255,255, self.addr)
  def black(self, a=0):    send(0,0,0, self.addr)
  def red(self, a=0):      send(255,0,0, self.addr)
  def green(self, a=0):    send(0,255,0, self.addr)
  def blue(self, a=0):     send(0,0,255, self.addr)
  def cyan(self, a=0):     send(0,255,255, self.addr)
  def magenta(self, a=0):  send(255,0,255, self.addr)
  def yellow(self, a=0):   send(255,255,0, self.addr)

