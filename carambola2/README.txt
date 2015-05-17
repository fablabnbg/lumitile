				jw, Sun May 17 20:00:15 CEST 2015

The lumitile power supply is 48V. The usual LM2596 regulator cannot handle this input voltage.
We need the high voltage version LM2596HV for this.
See 20150517_192211.jpg and double check the markings on the chip to say HV or HVS and
also check the capacitors to say 63V or higher.
At the left hand side of the photo, an ATTINY2313 can be seen. The software for this chip is found
in ../avr/lumitile.c and ../avr/lumitile.h -- 
The two thick black wires that pass behind the voltage regulator, are driven 
by 5 output pins each (compile time option POWER_BOARD=1). 
This allows for up to 100mA current loop on the RS485 protocol.
The thin yellow wire at the left edge of the photo connects to PD0 (RxD) RS232
driven by the carambola2 board. Baud rate is 115.2kbps. See the comment in lumitile.c for a 
description of available commands.

Adjust the output voltage to 3.3V -- this is the correct voltage for the carambola2 board.
The pollin 1.3MP webcam (Kameramodul) BN2DM5S8 is usually USB powered with 5V, but can also be powered
with 3.3V. See the black and red wires connected to a capacitor in the center of the PCB.
The 3-pin chip next to the capacitor is the voltage regulator.
See 20150517_191525.jpg

On the left hand side of the PCB a 5 pin connector is found. This is a USB connector.
The connector is easily unsoldered, it is SMD mounted. The pads are (from top to bottom)

1 +5V (red)
2 D-  (white)
3 D+  (green)
4 GND (black)
5 NC

We use pins 2,3,4. Pin 1 and 5 remain open.

