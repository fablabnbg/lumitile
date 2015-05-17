				jw, Sun May 17 20:00:15 CEST 2015

The lumitile power supply is 48V. The usual LM2596 regulator cannot handle this input voltage.
We need the high voltage version LM2596HV for this.
See 20150517_192211.jpg and double check the markings on the chip to say HV or HVS and
also check the capacitors to say 63V or higher.
At the left hand side of the photo, an ATTINY2313 can be seen. The software for this chip is found
in ../avr/lumitile.c and ../avr/config.h -- 
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

Carambola2 pinout
-----------------

Numbering starts at the top left hand corner, if you place the antenna connector at the lower right.
1 .. 18 run downward the left hand side.
19 .. 27 bottom side, left to right, where 26 is the antenna connector.
28 .. 45 run along the right hand side, bottom to top.
46 .. 52 run along the top side, right to left.

We can use 
----------
1,22,25,27-32,34,42,45-49 GND
20	USB+
21	USB-
26	Antenna
50,51 	+3VD
43	UART RX (GPIO 9)
44	UART TX (GPIO 10)	yellow, pin 2 of ATTINY2313
35	LED6 (GPIO 17)
36	LED5 (GPIO 16)
37	LED4 (GPIO 15)
38	LED3 (GPIO 14)
39	LED2 (GPIO 13)
40	LED1 (GPIO 1)
41	LED0 (GPIO 0, WLAN LED)


initial bootstrap
-----------------

50 +3VD
45 GND USB dongle
44 TxD USB dongle
43 RxD USB dongle
26 antenna 6cm


# Connect usb first to your computer, start
screen /dev/ttyUSB0 115200
# The connect +3VD power supply, boot message start scrolling.


vi /etc/config/wireless

 config wifi-device wlan0
        option type mac80211
        option channel 11
        option hwmode 11ng
        option macaddr c4:93:00:00:ae:50
        option htmode HT20
        list ht_capab SHORT-GI-20
        list ht_capab SHORT-GI-40
        list ht_capab RX-STBC1
        list ht_capab DSSS_CCK-40
        option disabled 0

 config wifi-iface
        option device wlan0
        option network island
        option mode ap
        option ssid jw_lumitile
        option encryption none
ZZ

vi /etc/config/network
 ...
 config interface island
        option ifname   wlan0
        option proto    static
        option ipaddr   192.168.10.1
        option netmask  255.255.255.0

ZZ

vi /etc/config/dhcp
 ...
 config  dhcp island                
        option interface        island
        option start    100           
        option limit    150           
        option leasetime        12h   
ZZ

vi /etc/config/firewall
 ...
 config zone                                            
        option name             island                               
        option network          'island'               
        option input            ACCEPT                 
        option output           ACCEPT                 
        option forward          REJECT          
 ...
ZZ
vi /etc/config/system
 config system
	option hostname 'lumitile'
 ...
ZZ

# now you need a reboot to make it effective. 
## this is not enough ...
# /etc/init.d/network restart
# /etc/init.d/dnsmask restart
reboot

