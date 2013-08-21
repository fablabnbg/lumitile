;	Processor 16F88

; ********************************************************************************************
; **************************  LED-Wall RGB-Control  ******************************************
; ********************************************************************************************
; 14.09.2005
;	-Baudrate 19,2kbit, 9bit + 1 Stopbit
;	-9.Bit:	0=Wert 1=Adresse
;	-Pause von > 6ms startet eine Sequenz
;	-Sequenz: bis zu 128 mal (Adresse + R + G + B + Control)
;	-Adresse 255 meint alle Kacheln
; ********************************************************************************************
	LIST P=16F88
; ********************************************************************************************
#define	W		00
#define	F		01
#define	TMR0		01
#define	STATUS		03
#define	FSR		04
#define	PORTA		05
#define	PORTB		06
#define	PCLATH		0A
#define	INTCON		0B
#define	PIR1		0C
#define	PIE1		0C
#define	PIR2		0D
#define	PIE2		0D
#define	TMR1L		0E
#define	TMR1H		0F
#define	OSCCON		0F	; Oszillator Control Register 8FH

#define	T1CON		10	; T1Con Register
#define	OSCTUNE		10	; Oszi. 90H
#define	TXSTA		18	; Transmit Status Register
#define	RCSTA		18
#define	TXREG		19	; Transmit-Register
#define	RCREG		1A	; Receive-Register
#define	ANSEL		1B
#define	CMCON		1C	; Bank 1
#define	ADRESH		1E
#define	ADCON0		1F
#define	ADCON1		1F	; Bank 1

#define	ON_Time		20	; Messung der EIN-Zeit

#define	DEV_Adr		22	; lokale Adresse
#define	TMR_0		23	; Timer für seriellen Bus
#define	Count_L		24	; Counter für Byte-Gruppe
#define	Count_H		25	; Counter für Adresse
#define	RX_Status	26
;			26.0	1=Adresse ok

#define	RX_Rotate	2D
#define	RX_TempC	2E	; Temp-RX_Buffer
#define	RX_Buffer	2F
#define	RX_CS		30	; CS-Berechnung
#define	SOLL_R		31	; Sollwert für ROT
#define	SOLL_G		32	; Sollwert für GRUEN
#define	SOLL_B		33	; Sollwert für BLAU
#define	BEFEHL		34	; 4. Byte
#define	TEMP_R		35	; Reserve
#define	TEMP_G		36	; Reserve
#define	TEMP_B		37	; Reserve
#define	TEMP_R1		38	; Reserve
#define	TEMP_G1		39	; Reserve
#define	TEMP_G2		3A	; Reserve
#define	COLOR_R		3B	; Stellwert für Rot
#define	COLOR_G		3C	; Stellwert für Grün
#define	COLOR_B		3D	; Stellwert für Blau

; 70H .. 7FH in allen vier Bänken gleich!

#define	Stellwert	78	; IST-Stellwert (über Rampe)
#define	PWM		79	; Hilfs Merker für PWM
#define	PORT_B		7A


#define	W_TEMP		7D
#define	STATUS_TEMP	7E
#define	PCLATH_TEMP	7F

; ********************************************************************************************
; ********************************************************************************************
;16F628-Configs---------------------------------------------------------------------
	__IDLOCS	H'3580' ;       User ID
;-----------------------------------------------------------------------------------
;
_CONFIG1	EQU	H'2007'			    
_CONFIG2	EQU	H'2008'	
		    
	__CONFIG	_CONFIG1,  B'00111100110100'

;		  B'10011100110100'
;                   ||||||||||||||
;                   |||||||||+||++---FOSC 1xx11=RC R+C an RA7, RA6=CLKOUT
;                   |||||||||+||++---FOSC 1xx10=RC R+C an RA7
;                   |||||||||+||++---FOSC 1xx01=INTOSC RA6=CLKOUT
;                   |||||||||+||++---FOSC 1xx00=INTOSC
;                   |||||||||+||++---FOSC 0xx11=EX
;                   |||||||||+||++---FOSC 0xx10=HS	***
;                   |||||||||+||++---FOSC 0xx01=XT
;                   |||||||||+||++---FOSC 0xx00=LP
;                   ||||||||| ||     
;                   ||||||||| |+-----WDTE 0=disa 1=ena
;                   ||||||||| +------PWRT 0=ena  1=disa
;                   ||||||||+--------MCLR 0=din  1=ena
;                   |||||||+---------BOR  0=disa 1=ena
;                   ||||||+----------LVP  0=HV   1=RB4 LVP
;                   |||||+-----------CPD  0=prod 1=CPD off
;                   |||++------------WRT  00= 000..FFF write protected
;                   |||++------------WRT  01= 000..7FF write protected
;                   |||++------------WRT  10= 000..0FF write protected
;                   |||++------------WRT  11= Write prod. OFF
;                   ||+--------------ICD  0=ena  1=dis
;                   |+---------------CCP1 0=RB3  1=RB0
;                   +----------------CP   0=prod 1=CPF off
;
	__CONFIG	_CONFIG2,  B'11111111111110'
;
;-----------------------------------------------------------------------------------
;=============================================================================================
; PROGRAMM
;=============================================================================================

	NOP			; für ICD2 freihalten
	NOP			; für ICD2 freihalten
	goto	start

; ********************************************************************************************
; ********************       ISR     *********************************************************
; ********************************************************************************************
	org	004
; ********************************************************************************************
	MOVWF	W_TEMP		;Copy W to TEMP register
	SWAPF	STATUS, W	;Swap status to be saved into W
	CLRF	STATUS		;bank 0, regardless of current bank, Clears IRP,RP1,RP0
	MOVWF	STATUS_TEMP	;Save status to bank zero STATUS_TEMP register

BOISR
	btfss	PIR2, 6
	goto	TMR0_ISR	; Timer0 INT

	bcf	PORTB, 4	; ausschalten

	bsf	STATUS, 5
	movf	CMCON, W
	bcf	STATUS, 5

	movf	TMR0, W
	movwf	ON_Time

	bcf	PIR2, 6		; Comparator Bit
	btfss	INTCON, 2
	goto	EOISR

TMR0_ISR
	bcf	PORTB, 4	; spätestens jetzt ausschalten
	movlw	d'208'		; 50us
;	movlw	d'195'		; 63us
	addwf	TMR0, F
	bcf	INTCON, 2	; TMR0 INT

;	incf	PWM, F
	
	incfsz	TMR_0, F
	goto	TMR0_ISRn
	decf	TMR_0, F	; 12,6ms bis 255

TMR0_ISRn
	movf	Stellwert, W
;	subwf	PWM, W
	addwf	PWM, F
	btfsc	STATUS, 0	; immer einschalten, wenn C
	bsf	PORTB, 4	; einschalten

EOISR
	SWAPF	STATUS_TEMP, W	; Swap STATUS_TEMP register into W
				; (sets bank to original state)
	MOVWF	STATUS 		; Move W into STATUS register
	SWAPF	W_TEMP, F	; Swap W_TEMP
	SWAPF	W_TEMP, W	; Swap W_TEMP into W
	RETFIE			; sofort zurück nach INT

; ********************************************************************************************
; ************** Initialisierung beginnt hier *******************
; ********************************************************************************************

start
	clrwdt
	nop

;=============================================================================================
; Register 20H bis 7FH löschen
;=============================================================================================
	movlw	20	; beginne bei Register 20H
	movwf	FSR	; FSR


	clrf	0
	incf	FSR, F
	btfss	FSR, 7	; wenn REGISTER 80H erreicht
	goto	$-3

;=============================================================================================
; INIT Ports, OPTIN, INTCON
;=============================================================================================

;>>>	OSCCON (8Fh)
	
	BSF	STATUS, 5
	movlw	b'01111110'
	movwf	OSCCON
	clrf	OSCTUNE		; abgestimmt auf Mittenfrequenz
	BCF	STATUS, 5

;>>>	OPTION (81H)

	bsf	STATUS, 5	; Bank 1
	movlw	b'10000000'	; no RBPull-Up, falling edge, noWDT, 000=1:2
	movwf	1
	bcf	STATUS, 5	; Bank 0

;>>>	Ports

;	>>> ANSEL
	bsf	STATUS, 5
	movlw	b'00010110'	; AN4 = RA4
	movwf	ANSEL		; ANSEL
	bcf	STATUS, 5

	clrf	PORTA		; Port A
	clrf	PORTB		; Port B

; ADCON0	(1Fh)

	movlw	b'10100001'	; AN4, ON, FOSC/16
	movwf	ADCON0

; ADCON1	(9Fh)

	bsf	STATUS, 5	; Bank 1
	movlw	b'01000000'	; Left Adj., OSZ/2 REF=VDD + VSS
	movwf	ADCON1

; TRISA		(85h)
	movlw	b'11111111'	; 
	movwf	PORTA		; RA0..RA4,RB6,RB7=IN  RB5=MCLR
	
	movlw	b'11101111'	; 
	movwf	PORTB		; RB4=OUT RB0..3,6,7=IN RB5=TX
	bcf	STATUS, 5	; Bank 0

	clrf	PORTA		; Port A
	clrf	PORTB		; Port B

;>>>	INTCON (0BH)

	movlw	b'01100000'	; PEIE, TMR0-Int
	movwf	INTCON
	
;>>>	PIE1 (8CH)
	
	bsf	STATUS, 5
	movlw	b'00000000'	; 
	movwf	PIE1
	bcf	STATUS, 5
	
	clrf	PIR1

;>>>	PIE2 (8DH)
	
	bsf	STATUS, 5
	movlw	b'01000000'	; Comparator IE
	movwf	PIE2
	bcf	STATUS, 5

	clrf	PIR2

; CMCON		(9Ch)

	bsf	STATUS, 5
	movlw	b'00100101'	; V- = RA1, VRef = RA2
	movwf	CMCON

; CVRON		(9Dh)

;	movlw	b'00000000'
	movlw	b'00100010'
	movwf	0x1D		; CVRON
	bcf	STATUS, 5

	;>>> T1CON (10H)

	movlw	b'00100101'	; OSZ/4, Prescaler 1:4, TMR1ON=1
	movwf	T1CON

	;>>> TXSTA (98H)
	
	bsf	STATUS, 5
	movlw	b'01000101'	; Transmit DIS, asynchron, 9-bit, high speed
;	movlw	b'00000000'
	movwf	TXSTA
	bcf	STATUS, 5
	
	;>>> RCSTA (18H)
	
	movlw	b'11010000'	; asychron, 9-bit, cont. Receive
	movwf	RCSTA

	;>>> SPBRG (99H)
	
	bsf	STATUS, 5
	movlw	d'025'		; Baudrate: 19,2kBaud
	movwf	19
	bcf	STATUS, 5

	call	delay_100us

; hier die eigene Adresse abfragen
	movlw	0x7F
	movwf	DEV_Adr		; alles auf HIGH setzen

	btfss	PORTA, 3
	bcf	DEV_Adr, 0
	btfss	PORTB, 0
	bcf	DEV_Adr, 1
	btfss	PORTB, 3
	bcf	DEV_Adr, 2
	btfss	PORTB, 7
	bcf	DEV_Adr, 3
	btfss	PORTB, 6
	bcf	DEV_Adr, 4
	btfss	PORTB, 6
	bcf	DEV_Adr, 5
	btfss	PORTA, 6
	bcf	DEV_Adr, 6

	bsf	INTCON, 7	; Comparator als einziger Int.
	
	movf	RCREG, W
	movwf	RX_Buffer	; schon mal das Byte abholen
	
;***************************************************************************************************
;***************************************************************************************************
;***************************************************************************************************

; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
; %%%%%% Hauptprogramm LOOP Begin  %%%%%%%%%
; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

main
	clrwdt
	nop

	movlw	0x07		; NULL ist lokaler Betrieb
	xorwf	DEV_Adr, W
	andlw	0x07

	btfss	STATUS, 2
	goto	RS232
	
	btfsc	ADCON0, 2
	call	delay_100us
	
;	goto	main		; AD-Wandlung noch nicht fertig

	movf	ADRESH, W
	movwf	COLOR_R
	movwf	SOLL_R
	movwf	COLOR_G
	movwf	SOLL_G
	movwf	COLOR_B
	movwf	SOLL_B

	bsf	ADCON0, 2	; AD-Wandlung wieder starten
	
main_Stell
	movf	COLOR_R, W	; A6=0, A7=0 vorbelegen mit ROT holen
	btfsc	PORTA, 7	; 
	movf	COLOR_B, W	; wenn A7=1, dann Blau holen
	btfsc	PORTA, 6	; 
	movf	COLOR_G, W	; wenn A6=1, dann Grün holen

	movwf	Stellwert
	goto	main		; nichts tun
	

;***************************************************************************************************
; hierher nur, wenn DEV_Adr NICHT 255
; Protokoll: Pause > 13ms, 1..127 mal vier Bytes
; vier Bytes:	SOLL_R + SOLL_G + SOLL_B + Byte
; Zeit:	bei 19,2Baud -> ca. 0,5ms/Zeichen -> 2ms pro Adresse -> ca. 250ms/Loop
; Zeit: bei 1m * 3m -> 4*12 = 48 Kacheln -> ca. 100ms/Loop

RS232
	btfsc	RCSTA, 1
	bcf	RCSTA, 4
	bsf	RCSTA, 4

	btfss	PIR1, 5		; wenn 1, dann Transfer eines Bytes ist komplett
	goto	main

	movf	RCREG, W
	movwf	RX_Buffer	; schon mal das Byte abholen

	btfsc	TMR_0, 7	; TimeOut > 6,375ms
	clrf	Count_L		; nach TimeOut den Zähler auf NULL setzen
	clrf	TMR_0

; kam eine Adresse?
	btfsc	RCSTA, 0	; wenn 9.Bit=HIGH, dann Adresse
	call	RS232_Adr
	
	btfsc	RX_Status, 0
	goto	RS232_Addr		; wenn eine Adresse kam, zurück	

	movlw	d'11'		; maximal 10 Bytes sollen empfangen werden
	subwf	Count_L, W
	btfsc	STATUS, 0
	goto	main		; hier noch nicht stellen

	movlw	SOLL_R
	addwf	Count_L, W
	movwf	FSR
	
	movlw	d'03'		; Anzahl der Nullen zählen
	subwf	Count_L, W
	btfss	STATUS, 0
	call	RS232_Nullen	; über R, G und B die Nullen zählen

	movlw	03
	xorwf	Count_L, W	; 4. Byte = CS
	btfsc	STATUS, 2
	call	RS232_CS
	
	movf	RX_Buffer, W
	movwf	0

	incf	Count_L, F
	goto	main_Stell	; 

RS232_Addr
	bcf	RX_Status, 0
	goto	main

RS232_Adr
	bcf	RX_Status, 0	; Addr ok erst mal löschen
	clrf	Count_L		; Byte-Counter auf NULL setzen
	movlw	0xFF		; Sammel-Adresse
	xorwf	RX_Buffer, W
	btfsc	STATUS, 2
	bsf	RX_Status, 0	; Adresse ist ok

	movf	DEV_Adr, W	; lokale Adresse holen
	xorwf	RX_Buffer, W
	btfsc	STATUS, 2
	bsf	RX_Status, 0	; Adresse ist ok
	return

RS232_Nullen
	movf	Count_L, F
	btfsc	STATUS, 2
	clrf	RX_CS
	
	movf	RX_Buffer, W
	movwf	RX_TempC
	
	movlw	0x08
	movwf	RX_Rotate
	
	RRF	RX_TempC, F
	btfss	STATUS, 0
	incf	RX_CS, F	; wenn kein C, dann NULL
	decfsz	RX_Rotate, F
	goto	$-4
	return

RS232_CS
	movf	RX_Buffer, W
	andlw	b'00011111'	; mit 31 verunden (kann nur kleiner 25 sein!)
	xorwf	RX_CS, W
	btfss	STATUS, 2	; wenn Anz. Nullen = CS, Daten übernehmen
	return
	
	movf	SOLL_R, W
	movwf	COLOR_R
	movf	SOLL_G, W
	movwf	COLOR_G
	movf	SOLL_B, W
	movwf	COLOR_B
	return	
	
;***************************************************************************************************
delay_100us
	movlw	d'217'
	movwf	7B
	
	clrwdt
	nop
	
	incfsz	7B, F
	goto	$-3

	return

;***************************************************************************************************
;***************************************************************************************************

;***************************************************************************************************
	END
