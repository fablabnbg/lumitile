// - - - - -
// DmxSerial - A hardware supported interface to DMX.
// DMX2Lumitile.ino: A DMX interface for lumitile based on DmxSerial/examples/DmxSerialRecv.ino
//
// (c) 2013 jw@suse.de, Distribute under BSDv3.
//
// Copyright (c) 2011 by Matthias Hertel, http://www.mathertel.de
// This work is licensed under a BSD style license. See http://www.mathertel.de/License.aspx
// 
// Documentation and samples are available at http://www.mathertel.de/Arduino
//
// 2013-09-18, jw V0.1   - initial draught
// - - - - -

#define VERSION 0.1

#include <util/delay.h>			// needs F_CPU 
#include <DMXSerial.h>

#define KACHEL_FIRST	1
#define KACHEL_LAST	20

// atmega328p	<uno>
//  PD0 <D0>
//  PD1 <D1>
//  PB0 <D8>   // RS485 out +
//  PB1 <D9>   // RS485 out -
//  PB2 <D10>  
//  PB3 <D11>  
//  PB4 <D12>  
//  PB5 <D13>  

#if 1
# define RS485I_PORT PORTD
# define RS485I_DDR  DDRD
# define RS485I_BITS (1<<7)
# define RS485N_PORT PORTB
# define RS485N_DDR  DDRB
# define RS485N_BITS (1<<2)
#endif

void setup () {
  DMXSerial.init(DMXReceiver);
  
  // set some default values
  // DMXSerial.write(1, 80);
  // DMXSerial.write(2, 0);
  // DMXSerial.write(3, 0);
  
  // enable pwm outputs
  // pinMode(RedPin,   OUTPUT); // sets the digital pin as output
  // pinMode(GreenPin, OUTPUT);
  // pinMode(BluePin,  OUTPUT);

  RS485N_DDR = RS485N_BITS;		// RS485 out +
  RS485I_DDR = RS485I_BITS;		// RS485 out -
}

static void tx_bit_wait(uint8_t bit)
{
  if (bit)
    {
      RS485I_PORT &= ~RS485I_BITS;
      RS485N_PORT |=  RS485N_BITS;
    }
  else
    {
      RS485I_PORT |=  RS485I_BITS;
      RS485N_PORT &= ~RS485N_BITS;
    }
  _delay_us(17.0); 	// 40.0 @20Mhz, 34.0 @16Mhz, 17.0 @8Mhz; tune this to generate 57.6 kbps
}


static void tx_word_wait(uint16_t word)
{
  uint8_t bit;
  tx_bit_wait(0);	// start bit

  for (bit = 0; bit < 9; bit++)
    {
      tx_bit_wait(word & 0x01);
      word >>= 1;
    }

  tx_bit_wait(1);	// stop bit
  tx_bit_wait(1);	// stop bit
}

static uint8_t count_zeros(uint8_t Cw)
{
  uint8_t cnt = 0;
  uint8_t bitval = 0x80;

  while (bitval != 0)
    {
      if ((bitval & Cw) == 0)
        cnt++;
      bitval >>= 1;
    }
  return cnt;
}


static void send_lumitile(uint8_t addr, uint8_t red, uint8_t green, uint8_t blue, uint8_t now)
{
  uint8_t zcnt = 0;

  zcnt += count_zeros(red);
  zcnt += count_zeros(green);
  zcnt += count_zeros(blue);
  if (!now) zcnt |= 0x20;	// Bit 5 = 1--> Kachel speichert die
   // Farbwerte, zeigt sie erst dann
// an, wenn ein Broadcast mit bit5=1 erfolgt.
  tx_word_wait((uint16_t)addr | 0x100);	// Bit 9 wg. Adresse setzen
  tx_word_wait(red);
  tx_word_wait(green);
  tx_word_wait(blue);
  tx_word_wait(zcnt);
}

void loop() {
  // Calculate how long no data backet was received
  unsigned long lastPacket = DMXSerial.noDataSince();
  
  uint8_t k_id;
  uint8_t ch = 1;
  if (lastPacket < 5000) {
    // read recent DMX values and set pwm levels 
    for (k_id = KACHEL_FIRST; k_id <= KACHEL_LAST; k_id++)
      {
        uint8_t rval = DMXSerial.read(ch++);
        uint8_t gval = DMXSerial.read(ch++);
        uint8_t bval = DMXSerial.read(ch++);
        cli();
        send_lumitile(k_id, rval, gval, bval, 1);
        sei();
      }
  }
  else
  {
        cli();
        send_lumitile(255, 100, 0, 100, 1);
        sei();
    
  } // if
}

// End.
