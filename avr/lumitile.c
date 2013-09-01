/* lumitile.c -- simple lumitile controller
 *
 * Copyright (C) 2013, jw@suse.de, distribute under GPL, use with mercy.
 *
 * Board config:
#if POWER_BOARD
 *   PD0:	RxD RS232 from USB
 *   PD2:	OUT RS485 not inverted
 *   PD3:	OUT RS485 not inverted
 *   PD4:	OUT RS485 not inverted
 *   PD5:	OUT RS485 not inverted
 *   PD6:	OUT RS485 not inverted
 *   PB0:	OUT RS485 inverted
 *   PB1:	OUT RS485 inverted
 *   PB2:	OUT RS485 inverted
 *   PB3:	OUT RS485 inverted
 *   PB4:	OUT RS485 inverted
 *   PA0:	OUT green LED low active
#else // !POWER_BOARD
 *   PD0:	RxD RS232 from USB
 *   PD1:	TxD RS232 to USB
 *   PB0:	IN right switch n-c
 *   PB1:	IN stop switch n-c
 *   PB2:	IN left switch n-c
 *   PB4:	OUT RS485 inverted
 *   PD2:	OUT RS485 not inverted
 *   PD3:	IN (aka INT1)
 *   PD4:	OUT red LED
 *   PD5:	OUT green LED
#endif
 *
 * Protocoll:
 *
 * RS485: 5 bytes: 1 start, 9 data, no parity, 2 stop bits each.
 *        lsb first.
 *        0: addr,  1: red, 2: green, 3: blue, 4: checksum 5bits+ command 1bit
 *
 * RS232: 6 bytes: 1 start, 8 data, even parity, 1 stop bit each.
 *        msb first
 *        0: Magic 'F'	// short for 'FabLab'
 *        1: Command 'S': direct set or 'L': load only, waiting for broadcast set.
 *        2: addr, 3: red, 4: green, 5: blue
 * 
 * The input command on RS232 has 66bits, while the output on RS485 has 60.
 * thus the host can saturate RS232, and we still have some headroom to 
 * convert everything without need for handshake.
 *   
 * 2013-08-21, V0.1, jw - initial draught. 
 *		Crude bit banging.
 *              Collect command "aNNN rNNN gNNN bNNN<CR>"
 *              Execute upon pressing enter.
 * 		For the timing, see https://www.dropbox.com/home/Photos/Fablab/LED-Kacheln
 * 2013-08-22, V0.2 WAVE_PATTERN compiletime flag, aborts, when any key is pressed.
 * 2013-09-01, V0.3 Support for POWER_BOARD added, protocol redefined.
 *		Command is now "FS%c%c%c%c" % (addr,red,green,blue)
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

#define RS232_BAUD      57600
#define RS485_BAUD      57600
#define T0TOP     (F_CPU/RS485_BAUD)+10	// 8000000/57600 = 137

#if POWER_BOARD
# define LED_PORT PORTA
# define LED_DDR  DDRA
# define GREEN_LED_BIT	(1<<PA0)
# define LED_BITS	(GREEN_LED_BIT)

# define RS485I_PORT PORTB
# define RS485I_DDR  DDRB
# define RS485I_BITS ((1<<PB0)|(1<<PB1)|(1<<PB2)|(1<<PB3)|(1<<PB4))
# define RS485N_PORT PORTD
# define RS485N_DDR  DDRD
# define RS485N_BITS ((1<<PD2)|(1<<PD3)|(1<<PD4)|(1<<PD5)|(1<<PD6))

#else
# define LED_PORT PORTD
# define LED_DDR  DDRD
# define RED_LED_BIT	(1<<PD4)
# define GREEN_LED_BIT	(1<<PD5)
# define LED_BITS	(RED_LED_BIT|GREEN_LED_BIT)

# define RS485I_PORT PORTB
# define RS485I_DDR  DDRB
# define RS485I_BITS (1<<PB4)
# define RS485N_PORT PORTD
# define RS485N_DDR  DDRD
# define RS485N_BITS (1<<PD2)

#endif

#define T0_STATE_IDLE	0
#define T0_STATE_PREP	1
#define T0_STATE_ADDR	2
#define T0_STATE_RED	3
#define T0_STATE_GREEN	4
#define T0_STATE_BLUE	5
#define T0_STATE_CS	6

// taken from rs232.c
#if defined(__AVR_ATtiny2313__)
#define USART0_RX_vect   USART_RX_vect
#define USART0_UDRE_vect USART_UDRE_vect
#define USART0_TX_vect   USART_TX_vect
#define UMSEL0 UMSEL
#endif

#if USART0_RX_vect < TIMER0_OVF_vect
# error "TIMER0_OVF_vect cannot interrupt USART0_RX_vect"
#endif

static void tx_bit(uint8_t bit)
{
  if (bit)
    {
      LED_PORT |= GREEN_LED_BIT;	// LED on
      RS485I_PORT &= ~RS485I_BITS;
      RS485N_PORT |=  RS485N_BITS;
    }
  else
    {
      LED_PORT &= ~GREEN_LED_BIT;	// LED off
      RS485I_PORT |=  RS485I_BITS;
      RS485N_PORT &= ~RS485N_BITS;
    }
}

static volatile uint8_t cmd_buf[5];		// 0 addr, 1-3 colors, 4 csum

static volatile uint16_t tick_counter = 0;	// just increment to keep main happy.
static volatile uint16_t tx_word = 0;		// mask 0xc00 is stop bits, 0x001 is start bit.
static volatile uint8_t tx_bits = 0;		// stat with 11, end with 0 -- try next byte then.
static volatile uint8_t tx_bytes = 5;		// bytes sent for this command. 5=all done;

// Load a start bit, 9 databits, 2 stop bits into a 16bit word.
// Backwards, as we shift down for each bit.
#define TX_QUEUE_WORD(val) \
  do { tx_word = ((val)<<1)| 0xc00; tx_bits = 12; } while (0)

ISR(TIMER0_OVF_vect)	// TOV0
{
  LED_PORT |= (RED_LED_BIT);
  if (tx_bits)
    {
      tx_bit(tx_word & 0x0001);
      tx_bits--;
      tx_word >>= 1;
    }
  if (tx_bits == 0)	// exhausted current word, try to load next one.
    {
      if (tx_bytes == 0)
        {
          // PIND |= (1<<PD2);
	  TX_QUEUE_WORD(cmd_buf[0]|0x100);	// address value
          tx_bytes = 1;
	}
      else if (tx_bytes < 5)
        {
	  uint8_t val = cmd_buf[tx_bytes++];
	  TX_QUEUE_WORD(val);	// color or csum value
	}
    }
  LED_PORT &= ~(RED_LED_BIT);
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


static volatile uint8_t cmd_bytes_seen = 0;
ISR(USART0_RX_vect)
{
  if (1)	// (UCSRA & (1<<UPE)) == 0)		// else parity error.
    {
      uint8_t byte = UDR;

      if (cmd_bytes_seen == 0)
	{
	  if (byte == 'F')
	    cmd_bytes_seen++;		// else protocol error.
	}
      else if (cmd_bytes_seen == 1)
	{
	  if (byte == 'S')
	    { 
	      cmd_bytes_seen++;
	      cmd_buf[4] = 0x00;
	    }
	  else if (byte == 'L')
	    {
	      cmd_bytes_seen++;
	      cmd_buf[4] = 0x20;
	    }
	  else
	    cmd_bytes_seen = 0;		// protocol error.
	}
      else if (cmd_bytes_seen < 6)		// 2,3,4,5
	{
	  cmd_buf[cmd_bytes_seen-2] = byte;
	  cmd_bytes_seen++;			// 3,4,5,6
	  if (cmd_bytes_seen == 6)
	    {
	      cmd_bytes_seen = 0;		// Get ready for next command.
	      tx_bytes = 0;			// Restart the transmitter.
	    }
	  else if (cmd_bytes_seen > 3)	// don't csum the addr!
	    { 
	      cmd_buf[4] += count_zeros(byte);
	    }
	}
    }
}

static void timer_init()
{
  /*
   * Init T0 in Fast PWM Mode, prescaler 1.
   * Mode 7: ovfl vect enabled, nothing else.
   *
   */
# if (CPU_MHZ != 8)
#  error "must run at 8Mhz"
# endif

  OCR0A = T0TOP;				// fixed 57.6 khz

  TCCR0A = (0<<COM0A1)|(0<<COM0A0)|		// OC0A disconnected
           (0<<COM0B1)|(0<<COM0B0)|		// OC0B disconnected
	   (1<<WGM01)|(1<<WGM00);		// Mode 7.

  TCCR0B = (1<<WGM02)|(0<<CS02)|(0<<CS01)|(1<<CS00);

  TIMSK = (1<<TOIE0);				// enable TOV0
}

int main()
{
  RS485N_DDR = RS485N_BITS;		// RS485 out +
  RS485I_DDR = RS485I_BITS;		// RS485 out -
  LED_DDR |= LED_BITS;			// LED pins out

  rs232_init(UBRV(RS232_BAUD));		// even parity!
  timer_init();

  tx_bit(1);	// high idle
  _delay_ms(300);
  _delay_ms(300);
  _delay_ms(300);

  for (;;)
    {
#if 0
  cmd_buf[4] = 0;
  cmd_buf[0] = 255;
  cmd_buf[1] = 100; cmd_buf[4] += count_zeros(cmd_buf[1]);
  cmd_buf[2] = 0;   cmd_buf[4] += count_zeros(cmd_buf[2]);
  cmd_buf[3] = 0;   cmd_buf[4] += count_zeros(cmd_buf[3]);
  tx_bytes = 0;			// Restart the transmitter.
#endif
      _delay_ms(100);
    }
}
