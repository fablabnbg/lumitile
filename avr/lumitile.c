/*
 * lumitile.c -- simple lumitile controller
 *
 * Copyright (C) 2013, jw@suse.de, distribute under GPL, use with mercy.
 *
 * Board config:
 *   PB0:	IN right switch n-c
 *   PB1:	IN stop switch n-c
 *   PB2:	IN left switch n-c
 *   PB4:	OUT RS485 not inverted
 *   PD2:	OUT RS485 inverted
 *   PD3:	IN (aka INT1)
 *   PD4:	OUT red LED
 *   PD5:	OUT green LED
 *
 * 2013-08-21, V0.1, jw - initial draught. 
 *		Crude bit banging.
 *              Collect command "aNNN rNNN gNNN bNNN<CR>"
 *              Execute upon pressing enter.
 * 		For the timing, see https://www.dropbox.com/home/Photos/Fablab/LED-Kacheln
 */

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#if __INT_MAX__ == 127
# error "-mint8 crashes stdio in avr-libc-1.4.6"
#endif
#include <avr/io.h>
#include <avr/interrupt.h>		// sei()

#include "config.h"
#include "cpu_mhz.h"
#include "version.h"
#include "rs232.h"
#include <util/delay.h>			// needs F_CPU from cpu_mhz.h

#define LED_PORT PORTD
#define LED_DDR  DDRD
#define RED_LED_BITS	(1<<4)
#define GREEN_LED_BITS	(1<<5)
#define LED_BITS	(RED_LED_BITS|GREEN_LED_BITS)


#define CMD_STATE_ADDR	0
#define CMD_STATE_RED	1
#define CMD_STATE_GREEN	2
#define CMD_STATE_BLUE	3
#define CMD_STATE_DONE  0x80
static uint8_t cmd_state = CMD_STATE_ADDR;
static uint8_t cmd_buf[4];
static uint8_t fieldnames[] = "argb";

static uint16_t hall_counter = 0;
ISR(INT1_vect)
{
  hall_counter++;
}

static uint8_t cmd_seen = 0;	
static void rs232_recv(uint8_t byte)
{
  // just an echo back dummy.
  rs232_send('=');
  rs232_send(byte);
  cmd_seen = byte;
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

static void tx_bit(uint8_t bit)
{
  if (bit)
    {
      PORTD |= (1<<PD5);	// LED on
      PORTB |= (1<<PB4);
      PORTD &= ~(1<<PD2);
    }
  else
    {
      PORTD &= ~(1<<PD5);	// LED off
      PORTB &= ~(1<<PB4);
      PORTD |= (1<<PD2);
    }
  _delay_us(15.0); 		// tune this to generate 57.6 kbps
  // _delay_ms(100.0); 		// slow food for debugging
}

static void tx_word(uint16_t word)
{
  tx_bit(0);	// start bit
  uint8_t bit;

  for (bit = 0; bit < 8; bit++)
    {
      tx_bit(word & 0x01);
      word >>= 1;
    }

  tx_bit(1);	// high idle
}

static void send_lumitile(uint8_t now)
{
  uint8_t zcnt = 0;

  zcnt += count_zeros(cmd_buf[1]);
  zcnt += count_zeros(cmd_buf[2]);
  zcnt += count_zeros(cmd_buf[3]);
  if (now) zcnt |= 0x20;	// Bit 5 = 1--> Kachel speichert die 
  				// Farbwerte, zeigt sie erst dann
				// an, wenn ein Broadcast mit bit5=1 erfolgt.
  tx_word(cmd_buf[0] | 0x100);	// Bit 9 wg. Adresse setzen
  tx_word(cmd_buf[1]);
  tx_word(cmd_buf[2]);
  tx_word(cmd_buf[3]);
  tx_word(zcnt);
}

int main()
{
  DDRB = 0;
  DDRD = 0;
  LED_DDR |= LED_BITS;			// LED pins out
  DDRB |= (1<<PB4);			// RS485 out +
  DDRD |= (1<<PD2);			// RS485 out -
  PORTB	= (1<<PB0)|(1<<PB1)|(1<<PB2);	// pullups for switches

#define BAUD      19200
  rs232_init(UBRV(BAUD), &rs232_recv);

  tx_bit(1);	// high idle

  for (;;)
    {
      if (cmd_seen) rs232_send(cmd_seen);	  
      _delay_ms(0.1);
      if (cmd_seen == '\n' || cmd_seen == '\r')
        {
          rs232_send('\r');	  
          rs232_send('\n');	  
          rs232_send_hex(cmd_buf[0]);	  
          rs232_send_hex(cmd_buf[1]);	  
          rs232_send_hex(cmd_buf[2]);	  
          rs232_send_hex(cmd_buf[3]);	  
          rs232_send('\r');	  
          rs232_send('\n');	  
	  send_lumitile(1);
          cmd_state = CMD_STATE_DONE;	// allow repeated ENTER to resend.
	  cmd_seen = 0;
	  continue;
	}
      else if (cmd_seen && cmd_state == CMD_STATE_DONE)
        {
	  cmd_buf[0] = cmd_buf[1] = cmd_buf[2] = cmd_buf[3] = 0;
	  cmd_state = CMD_STATE_ADDR;
          rs232_send(fieldnames[cmd_state]);	  
	}

      if (cmd_seen >= '0' && cmd_seen <= '9')
        {
	  cmd_buf[cmd_state] = 10 * cmd_buf[cmd_state] + cmd_seen - '0';
	}
      else if (cmd_seen == '\t' || cmd_seen == ' ')
        {
	  cmd_state++;
	  if (cmd_state > CMD_STATE_BLUE) cmd_state = CMD_STATE_ADDR;
          rs232_send(fieldnames[cmd_state]);	  
	}
      else if (cmd_seen == 'a' || cmd_seen == 'A')
        {
	  cmd_state = CMD_STATE_ADDR;
          rs232_send(fieldnames[cmd_state]);	  
	}
      else if (cmd_seen == 'r' || cmd_seen == 'R')
        {
	  cmd_state = CMD_STATE_RED;
          rs232_send(fieldnames[cmd_state]);	  
	}
      else if (cmd_seen == 'g' || cmd_seen == 'G')
        {
	  cmd_state = CMD_STATE_GREEN;
          rs232_send(fieldnames[cmd_state]);	  
	}
      else if (cmd_seen == 'b' || cmd_seen == 'B')
        {
	  cmd_state = CMD_STATE_BLUE;
          rs232_send(fieldnames[cmd_state]);	  
	}
      cmd_seen = 0;
    }
}
