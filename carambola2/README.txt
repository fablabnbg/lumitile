				jw, Sun May 17 20:00:15 CEST 2015

The lumitile power supply is 48V. The usual LM2596 regulator cannot handle this input voltage.
We need the high voltage version LM2596HV for this.
See 20150517_192211.jpg and double check the markings on the chip to say HV or HVS and
also check the capacitors to say 63V or higher.

Adjust the output voltage to 3.3V -- this is the correct voltage for the carambola2 board.
The pollin 1.3MP webcam (Kameramodul) BN2DM5S8 is usually USB powered with 5V, but can also be powered
with 3.3V. See the black and red wires connected to a capacitor in the center of the PCB.
The 3-pin chip next to the capacitor is the voltage regulator.
See 20150517_191525.jpg

