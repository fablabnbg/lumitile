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
 * 2013-08-22, V0.2 WAVE_PATTERN compiletime flag, aborts, when any key is pressed.
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

#define WAVE_PATTERN 3			// 3 is okayish.

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

#define T0TOP  139		// 8000000/57600
#define T0_STATE_IDLE	0
#define T0_STATE_PREP	1
#define T0_STATE_ADDR	2
#define T0_STATE_RED	3
#define T0_STATE_GREEN	4
#define T0_STATE_BLUE	5
#define T0_STATE_CS	6

static uint8_t cmd_state = CMD_STATE_ADDR;
static uint8_t cmd_buf[4];
static uint8_t fieldnames[] = "argb";

static uint8_t cmd_seen = 0;	

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

// taken from rs232.c
#if defined(__AVR_ATtiny2313__)
#define USART0_RX_vect   USART_RX_vect
#define USART0_UDRE_vect USART_UDRE_vect
#define USART0_TX_vect   USART_TX_vect
#define UMSEL0 UMSEL
#endif

#if USE_POLLING

ISR(USART0_RX_vect)
{
  uint8_t byte = UDR;
  // just an echo back dummy.
  rs232_send(byte);
  cmd_seen = byte;
}

static void tx_bit(uint8_t bit)
{
  if (bit)
    {
      PORTD |= (1<<PD5);	// LED on
      PORTB &= ~(1<<PB4);
      PORTD |= (1<<PD2);
    }
  else
    {
      PORTD &= ~(1<<PD5);	// LED off
      PORTB |= (1<<PB4);
      PORTD &= ~(1<<PD2);
    }
  _delay_us(16.7); 		// tune this to generate 57.6 kbps
  // _delay_ms(100.0); 		// slow food for debugging
}

static void tx_word(uint16_t word)
{
  uint8_t bit;
  tx_bit(0);	// start bit

  for (bit = 0; bit < 9; bit++)
    {
      tx_bit(word & 0x01);
      word >>= 1;
    }

  tx_bit(1);	// stop bit
  tx_bit(1);	// stop bit
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
  cli();
  tx_word(addr | 0x100);	// Bit 9 wg. Adresse setzen
  tx_word(red);
  tx_word(green);
  tx_word(blue);
  tx_word(zcnt);
  sei();
}

#else	// !USE_POLLING

#if USART0_RX_vect < TIMER0_OVF_vect
# error "TIMER0_OVF_vect cannot interrupt USART0_RX_vect"
#endif

ISR(USART0_RX_vect)
{
  uint8_t byte = UDR;
  // just an echo back dummy.
  rs232_send(byte);
  cmd_seen = byte;
}

#define TX_BUF_SZ 16	// can put 16 commands in the outbound buffer.
struct tx_cmd
{
  uint8_t add, red, green, blue, cs;
};
static struct tx_cmd tx_buf[TX_BUF_SZ];	// 16*5 = 80 bytes.
static uint8_t tx_buf_head = 0;
static uint8_t tx_buf_tail = 0;

static void send_lumitile(uint8_t addr, uint8_t red, uint8_t green, uint8_t blue, uint8_t now)
{
}

static uint8_t tick_counter = 0;

ISR(TIMER0_OVF_vect)	// TOV0
{
  tick_counter++;
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
#endif	// USE_POLLING


int main()
{
  DDRB = 0;
  DDRD = 0;
  LED_DDR |= LED_BITS;			// LED pins out
  DDRB |= (1<<PB4);			// RS485 out +
  DDRD |= (1<<PD2);			// RS485 out -
  PORTB	= (1<<PB0)|(1<<PB1)|(1<<PB2);	// pullups for switches

#define BAUD      38400
  rs232_init(UBRV(BAUD));

  tx_bit(1);	// high idle

  uint16_t i;
  uint8_t j;

  cmd_seen = 0;

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
	  send_lumitile(cmd_buf[0], cmd_buf[1], cmd_buf[2], cmd_buf[3], 1);
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
#if 0
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
#endif
      cmd_seen = 0;
    }
}
