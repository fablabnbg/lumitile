#! /usr/bin/python
#
# Requires: python-pivy from repository 
# 'http://download.opensuse.org/repositories/KDE:/Extra/openSUSE_12.3'.
#
# see also: http://doc.coin3d.org/Coin/classes.html
#
# maintained at
#  svn+ssh://jw@innerweb.suse.de/suse/jw/repo.svn/src/python/pivy
#
# 2013-02-26 V0.1, jw   - Initial draught with SoTimerSensor()
#                         and nonblocking io.read().
#                         Could not find a way to hook into the main select.
# 2013-02-27 V0.2, jw   - Simple array of bulbs. Protocol relies on line
#                         termination at read boundaries. This works well
#                         when stdin.isatty(), but not when piped.
#                         SoComplexity() added and changing SoScale() when on.
# 2013-02-28 V0.3, jw   - protocol fixed using a real read buffer.
# 2013-02-28 V0.4, jw   - reversed numbers, added >, < shift commands, gray background

from pivy.sogui import *
from pivy.coin import *
import os, select, sys, math, re
from PyQt4 import QtGui         # QColor()

__version__ = '0.4'

def KeyboardCb(self,event_cb):
    event = event_cb.getEvent()
    char = event.getPrintableCharacter()
    pressed = event.isKeyPressEvent(event, event.getKey())
    if char == 'q': sys.exit(0)
    # return SoCallbackAction.PRUNE
    return SoCallbackAction.CONTINUE

def ledOnOff(leds, sensor):
  changed=False
  a=None
  if (select.select([sys.stderr],[],[],0)[0]!=[]):   
    a = os.read(sys.stderr.fileno(), 6)
    changed=True
    if   (a[0] != 'F'): return
    if   (a[1] != 'S'): return
    addr  = ord(a[2])
    red   = ord(a[3])
    green = ord(a[4])
    blue  = ord(a[5])
    print "FS %d %d %d %d" % (addr, red, green, blue)
    if (addr == 255):
      for i in range(len(leds.a)): leds.a[i].on = (red/255., green/255., blue/255.)
    else:
      leds.a[addr-1].on = (red/255., green/255., blue/255.)
  if changed: a=None
  
  if changed:
    for led in leds.a:
      if led.on:
        led.mat.ambientColor = led.on
        led.mat.diffuseColor = led.on
        led.sca.scaleFactor = (1.05,1.05,1.05)
      else:
        led.mat.ambientColor = leds.off_color
        led.mat.diffuseColor = leds.off_color
        led.sca.scaleFactor = (1.0,1.0,1.0)
ledOnOff.buffer = ''
    

def main():
    # Initialize Coin. This returns a main window to use.
    # If unsuccessful, exit.
    myWindow = SoGui.init(sys.argv[0])
    if myWindow == None: sys.exit(1)
    myWindow.resize(950,360)

    # Make a scene containing a red cone
    scene = SoSeparator()

    # quality of spheres and cones
    cplx = SoComplexity()
    cplx.value = 0.7            # default .5 has visible edges
    scene.addChild(cplx)

    kb_cb = SoEventCallback()
    kb_cb.addEventCallback(SoKeyboardEvent.getClassTypeId(),KeyboardCb) 
    scene.addChild(kb_cb)

    leds = SoSeparator()
    font = SoFont()
    font.setName('Sans:Bold')   # does not work???
    font.size = 1
    leds.addChild(font)

    leds.a = []
    leds.off_color = (.3,.3,.3)
    i = -1
    for x in range(10):
      for y in range(2):
        i += 1
        led = SoSeparator()
        led.mat = SoMaterial()
        led.addChild(led.mat)
        led.tra = SoTranslation()
        led.tra.translation = (2.1*x,2.1*y+1,0)
        led.addChild(led.tra)

        label = SoSeparator()
        txt = SoAsciiText()
        txt.justification = SoAsciiText.CENTER
        txt.string = repr(i+1)
        l_tra = SoTranslation()
        l_tra.translation = (0,-2.5,1)
        l_mat = SoMaterial()
        l_mat.diffuseColor = (.1,.1,.3)
        l_mat.ambientColor = (.1,.1,.3)
        label.addChild(l_tra)
        label.addChild(l_mat)
        label.addChild(txt)
        led.addChild(label)

        led.sca = SoScale()
        led.sca.scaleFactor = (1,1,1)
        led.addChild(led.sca)
        led.sphere=SoSphere()
        led.on = False
        led.addChild(led.sphere)
        leds.addChild(led)
        leds.a.append(led)

    scene.addChild(leds)

    colorSensor = SoTimerSensor(ledOnOff, leds)
    colorSensor.setInterval(0.002) # schedule at 500Hz
    colorSensor.schedule()

    col = SoBaseColor()
    col.rgb=(0,0,.5)
    ctr=SoTranslation()
    ctr.translation = (7.4,-.15,0) # use 8.75 with 2.5 spacing
    cube=SoCube()
    cube.width=2.1*8
    cube.height=.4
    cube.depth=1.6
    scene.addChild(col)
    scene.addChild(ctr)
    scene.addChild(cube)

    # Create a viewer in which to see our scene graph.
    viewer = SoGuiExaminerViewer(myWindow)

    # Put our scene into viewer, change the title
    viewer.setSceneGraph(scene)
    viewer.setTitle("Hello Leds")
    cam = viewer.getCamera()
    cam.scaleHeight(.4)

    viewer.setBackgroundColor(QtGui.QColor(180,180,180))
    viewer.show()

    SoGui.show(myWindow) # Display main window
    SoGui.mainLoop()     # Main Coin event loop

if __name__ == "__main__":
    main()

