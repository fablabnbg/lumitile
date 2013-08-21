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
; 29.09.2005
;	-Versuch, unter 200 gleichzeitig die Periodendauer zu verlängern!
; 04.10.2005
;	-Bis Stellwert 255 die Periodendauer linear verlängern
;	-mit Anfangsstellwert und 255 Stufen auf Rest verteilen
; 18.01.2006
;	-erweitert auf alle drei Farben !!!
;	-mit Abgleich, jede Farbe seperat (0,414V = 20mA)
;	-feste Einschaltdauer pro Farbe, aus Abgleich
;	-Frequenz = 20MHz, Timer-Loop = 50us
;
; ********************************************************************************************
	LIST P=16F88
; ********************************************************************************************
#define	W		00
#define	F		01
#define	TMR0		01
#define	PCL		02
#define	STATUS		03
#define	FSR		04
#define	PORTA		05
#define R_FET		PORTA, 0
#define G_FET		PORTA, 1
#define B_FET		PORTA, 2
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
#define	ADRESL		1E	; Bank 1
#define	ADCON0		1F
#define	ADCON1		1F	; Bank 1

#define	ON_Time		20	; Messung der EIN-Zeit

#define	DEV_Adr		22	; lokale Adresse
#define	TMR_0		23	; Timer für seriellen Bus
#define	Count_L		24	; Counter für Byte-Gruppe
#define	Count_H		25	; Counter für Adresse
#define	RX_Status	26
;			26.0	1=Adresse ok

#define	Hilfs_RegL	27	; Hilfs Register
#define	Hilfs_RegH	28	; Hilfs Register

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

#define	DELAY_0		3F	; Counter für Delay_100us

#define	StellWert_R	40	; IR Stellwert für Rot
#define	StellWert_G	41	; IR Stellwert für Grün
#define	StellWert_B	42	; IR Stellwert für Blau
#define	PWM_R		43	; PWM-Wert (Ringzähler)
#define	PWM_G		44	; PWM-Wert (Ringzähler)
#define	PWM_B		45	; PWM-Wert (Ringzähler)
#define	Stell_HW_R	46	; berechneter Stellwert
#define	Stell_HW_G	47	; berechneter Stellwert
#define	Stell_HW_B	48	; berechneter Stellwert
#define	CounterT_R	49	; berechneter Counter Wert
#define	CounterT_G	4A	; berechneter Counter Wert
#define	CounterT_B	4B	; berechneter Counter Wert

#define	RAMPE		4C	; für Abgleich
#define R_COUNTER	4D	; Counter für Rampe

; 70H .. 7FH in allen vier Bänken gleich!
#define	ROT		71
#define GRUEN		72
#define	BLAU		73

#define	W_ROT		74
#define W_GRUEN		75
#define	W_BLAU		76

#define	W_TEMP		7D
#define	STATUS_TEMP	7E
#define	PCLATH_TEMP	7F

#define	Time_50us	d'132'	; kürzester Timer Wert (50us)
#define	SCHWELLE	d'085'	; Analogwert am Abgleich-Eingang

; ********************************************************************************************
; ********************************************************************************************
;16F628-Configs---------------------------------------------------------------------
	__IDLOCS	H'3590' ;       User ID
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
	bcf	INTCON, 2	; TMR0 INT

	movf	StellWert_R, W
	addwf	PWM_R, F
	btfsc	STATUS, 0	; immer einschalten, wenn C
	bsf	R_FET		; einschalten
	btfss	STATUS, 0	; immer ausschalten, wenn nicht C
	bcf	R_FET		; bleibt ausgeschalten

	movf	StellWert_G, W
	addwf	PWM_G, F
	btfsc	STATUS, 0	; immer einschalten, wenn C
	bsf	G_FET		; einschalten
	btfss	STATUS, 0	; immer ausschalten, wenn nicht C
	bcf	G_FET		; bleibt ausgeschalten

	movf	StellWert_B, W
	addwf	PWM_B, F
	btfsc	STATUS, 0	; immer einschalten, wenn C
	bsf	B_FET		; einschalten
	btfss	STATUS, 0	; immer ausschalten, wenn nicht C
	bcf	B_FET		; bleibt ausgeschalten

	incf	TMR_0, F
	btfsc	STATUS, 2
	decf	TMR_0, F	; Timer für seriellen BUS Sync

	movlw	Time_50us	; Wert für 50us
	addwf	TMR0, F

; R G B nach einer Zeit wieder abschalten
ISR_Loop
	movfw	ROT
	subwf	TMR0, W
	btfsc	STATUS, 0
	bcf	R_FET

	movfw	GRUEN
	subwf	TMR0, W
	btfsc	STATUS, 0
	bcf	G_FET

	movfw	BLAU
	subwf	TMR0, W
	btfsc	STATUS, 0
	bcf	B_FET

	movlw	b'00000111'
	andwf	PORTA, W
	btfss	STATUS, 2	; wenn NULL, dann haben alle drei abgeschaltet
	goto	ISR_Loop

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
	movlw	b'00011000'	; AN3 = PWM	AN4 = Helligkeit
	movwf	ANSEL		; ANSEL
	bcf	STATUS, 5

	clrf	PORTA		; Port A
	clrf	PORTB		; Port B

; ADCON0	(1Fh)

	movlw	b'10011001'	; AN3, ON, FOSC/16
	movwf	ADCON0

; ADCON1	(9Fh)

	bsf	STATUS, 5	; Bank 1
	movlw	b'01000000'	; Left Adj., OSZ/2 REF=VDD + VSS
	movwf	ADCON1

; TRISA		(85h)
	movlw	b'11111000'	; 
	movwf	PORTA		; RA0..RA2 = OUT RA3..RA7=IN  RB5=MCLR
	
	movlw	b'11111111'	; 
	movwf	PORTB		; RB0..7=IN RB5=TX
	bcf	STATUS, 5	; Bank 0

	clrf	PORTA		; Port A
	clrf	PORTB		; Port B

;>>>	INTCON (0BH)

	movlw	b'00100000'	; nur TMR0-Int
	movwf	INTCON
	
;>>>	PIE1 (8CH)
	
	bsf	STATUS, 5
	movlw	b'00000000'	; keinen PERIPHERAL Interrupt erlauben
	movwf	PIE1
	bcf	STATUS, 5
	
	clrf	PIR1

;>>>	PIE2 (8DH)
	
	bsf	STATUS, 5
	movlw	b'00000000'	; keinen PERIPHERAL Interrupt erlauben
	movwf	PIE2
	bcf	STATUS, 5

	clrf	PIR2

; CMCON		(9Ch)

	bsf	STATUS, 5
	movlw	b'00000111'	; Comperator OFF
	movwf	CMCON

; CVRON		(9Dh)

	movlw	b'00000000'
	movwf	0x1D		; CVRON
	bcf	STATUS, 5

	;>>> T1CON (10H)

	movlw	b'00100101'	; OSZ/4, Prescaler 1:4, TMR1ON=1
	movwf	T1CON

	;>>> TXSTA (98H)
	
	bsf	STATUS, 5
	movlw	b'01000101'	; Transmit DIS, asynchron, 9-bit, high speed
	movwf	TXSTA
	bcf	STATUS, 5
	
	;>>> RCSTA (18H)
	
	movlw	b'11010000'	; asychron, 9-bit, cont. Receive
	movwf	RCSTA

	;>>> SPBRG (99H)
	
	bsf	STATUS, 5
	movlw	d'064'		; Baudrate: 19,2kBaud
	movwf	19
	bcf	STATUS, 5

	call	delay_100us

; hier die eigene Adresse abfragen
	movlw	0x7F
	movwf	DEV_Adr		; alles auf HIGH setzen

	btfss	PORTB, 0
	bcf	DEV_Adr, 0
	btfss	PORTB, 1
	bcf	DEV_Adr, 1
	btfss	PORTB, 3
	bcf	DEV_Adr, 2
	btfss	PORTB, 4
	bcf	DEV_Adr, 3
	btfss	PORTB, 5
	bcf	DEV_Adr, 4
	btfss	PORTB, 6
	bcf	DEV_Adr, 5
	btfss	PORTB, 7
	bcf	DEV_Adr, 6

	bsf	INTCON, 7	; Comparator als einziger Int.
	
	movf	RCREG, W
	movwf	RX_Buffer	; schon mal das Byte abholen
	
; ROT, GRUEN und BLAU vorbelegen
	movlw	d'008'		; minimale Einschaltdauer für ROT
	movwf	ROT
	movlw	d'008'		; minimale Einschaltdauer fur GRUEN
	movwf	GRUEN
	movlw	d'008'		; minimale Einschaltdauer fur BLAU
	movwf	BLAU	

;***************************************************************************************************
;***************************************************************************************************

; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
; %%%%%% Hauptprogramm LOOP Begin  %%%%%%%%%
; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

main
	clrwdt
	nop

	movlw	0x7F		; NULL ist lokaler Betrieb
	xorwf	DEV_Adr, W
	andlw	0x7F
	
	btfss	STATUS, 2
	goto	RS232
	
	btfsc	ADCON0, 2
	call	delay_100us

	clrf	COLOR_G
	clrf	COLOR_R
	clrf	COLOR_B

; mit POTI: ROT 0..255, GRUEN 0..255, BLAU 0..255, WEISS 0..255
; XXXX XXHH LLLL LLLL
;        00 LLLL LLLL	ROT
;        01 LLLL LLLL	GRUEN
;        10 LLLL LLLL	BLAU
;        11 LLLL LLLL	WEISS

	bsf	STATUS, 5
	movfw	ADRESL
	bcf	STATUS, 5
	
	btfsc	ADRESH, 1
	goto	main_BW
	btfsc	ADRESH, 0
	goto	main_G
	movwf	COLOR_R
	goto	main_end_L

main_G
	movwf	COLOR_G
	goto	main_end_L

main_BW
	movwf	COLOR_B
	btfss	ADRESH, 0
	goto	main_end_L
	movwf	COLOR_R
	movwf	COLOR_G

main_end_L
	bsf	ADCON0, 2	; AD-Wandlung wieder starten
	
main_Stell
	call	Stell
	goto	main		; nichts tun

;***************************************************************************************************
;***************************************************************************************************
; wenn abgeglichen werden soll, dann jede Farbe getrennt erfassen und Wert
; nach ROT, GRUEN oder BLAU schreiben;

;#define RAMPE		4C	; für Abgleich
;#define R_COUNTER	4D	; Counter für Rampe

Abgleich
	movlw	Time_50us
	movwf	ROT
	movwf	GRUEN
	movwf	BLAU
	
	clrf	R_COUNTER
	clrf	RAMPE
	
	bsf	STATUS, 5	; Bank 1
	movlw	b'11000000'	; Right Adjust
	movwf	ADCON1
	bcf	STATUS, 5	; Bank 0

	movlw	b'10011001'	; AN3 starten
	movwf	ADCON0
	
	movlw	0xFF
	movwf	Stell_HW_R

Abgleich_R
	incf	ROT, F

	movlw	d'224'
	subwf	ROT, W
	btfsc	STATUS, 0	; dieser Wert darf nicht überschritten werden
	goto	Abgleich_G

	call	delay_100us
	incfsz	R_COUNTER, F	
	goto	$-2

	call	READ_AN3
	
	bsf	STATUS, 5
	movlw	SCHWELLE
	subwf	ADRESL, W
	bcf	STATUS, 5
	
	btfss	STATUS, 0
	goto	Abgleich_R
	
	clrf	Stell_HW_R

	movlw	0xFF
	movwf	Stell_HW_G
	call	Wait_1s

Abgleich_G
	incf	GRUEN, F

	movlw	d'224'
	subwf	GRUEN, W
	btfsc	STATUS, 0	; dieser Wert darf nicht überschritten werden
	goto	Abgleich_B

	call	delay_100us
	incfsz	R_COUNTER, F	
	goto	$-2

	call	READ_AN3
	
	bsf	STATUS, 5
	movlw	SCHWELLE
	subwf	ADRESL, W
	bcf	STATUS, 5
	
	btfss	STATUS, 0
	goto	Abgleich_G
	
	clrf	Stell_HW_G

	movlw	0xFF
	movwf	Stell_HW_B
	call	Wait_1s

Abgleich_B
	incf	BLAU, F

	movlw	d'224'
	subwf	BLAU, W
	btfsc	STATUS, 0	; dieser Wert darf nicht überschritten werden
	goto	Abgleich_B

	call	delay_100us
	incfsz	R_COUNTER, F	
	goto	$-2

	call	READ_AN3
	
	bsf	STATUS, 5
	movlw	SCHWELLE
	subwf	ADRESL, W
	bcf	STATUS, 5
	
	btfss	STATUS, 0
	goto	Abgleich_B
	clrf	Stell_HW_B

Abgleich_End
; AD-Wandler auf AN4 und left Adjust stellen

	bsf	STATUS, 5	; Bank 1
	movlw	b'11000000'	; right Adjust
	movwf	ADCON1
	bcf	STATUS, 5	; Bank 0

	movlw	b'10100001'	; AN4 starten
	movwf	ADCON0
	return	

;***************************************************************************************************
SPIEL_1
	movlw	0xFF
	movwf	Stell_HW_B
	call	Wait_1s		; Blau 1 Sekunde EIN
	clrf	Stell_HW_B

	movlw	0xFF
	movwf	Stell_HW_G
	call	Wait_1s		; GRUEN 1 Sekunde EIN
	clrf	Stell_HW_G

	movlw	0xFF
	movwf	Stell_HW_R
	call	Wait_1s		; ROT 1 Sekunde EIN
	clrf	Stell_HW_R

	return
	
;***************************************************************************************************
SPIEL_2
	movlw	0xFF
	movwf	Stell_HW_B
	call	Wait_1s		; Blau 1 Sekunde EIN
	clrf	Stell_HW_B

	movlw	0xFF
	movwf	Stell_HW_G
	call	Wait_1s		; GRUEN 1 Sekunde EIN
	clrf	Stell_HW_G

	movlw	0xFF
	movwf	Stell_HW_R
	call	Wait_1s		; ROT 1 Sekunde EIN
	clrf	Stell_HW_R

	return

;***************************************************************************************************
;***************************************************************************************************
READ_AN3
	bsf	ADCON0, 2	; starten
	btfsc	ADCON0, 2
	goto	$-1
	return

;***************************************************************************************************
;***************************************************************************************************
Wait_1s
	clrf	RAMPE
	call	delay_100us
	incfsz	R_COUNTER, F	
	goto	$-2
	incf	RAMPE, F
	btfss	RAMPE, 4
	goto	$-5
	return

;***************************************************************************************************
Stell
	movlw	HIGH Tab_Wert+1
	movwf	PCLATH
	movfw	COLOR_R		; Rot holen
	call	Tab_Wert
	clrf	PCLATH	
	movwf	Stell_HW_R

	movlw	HIGH Tab_Wert+1
	movwf	PCLATH
	movfw	COLOR_G		; Grün holen
	call	Tab_Wert
	clrf	PCLATH	
	movwf	Stell_HW_G

	movlw	HIGH Tab_Wert+1
	movwf	PCLATH
	movfw	COLOR_B		; Blau holen
	call	Tab_Wert
	clrf	PCLATH	
	movwf	Stell_HW_B

	movlw	HIGH Tab_Timer+1
	movwf	PCLATH
	movfw	COLOR_R		; Rot holen
	call	Tab_Timer
	clrf	PCLATH	
	movwf	CounterT_R

	movlw	HIGH Tab_Timer+1
	movwf	PCLATH
	movfw	COLOR_G		; Grün holen
	call	Tab_Timer
	clrf	PCLATH	
	movwf	CounterT_G
	
	movlw	HIGH Tab_Timer+1
	movwf	PCLATH
	movfw	COLOR_B		; Blau holen
	call	Tab_Timer
	clrf	PCLATH	
	movwf	CounterT_B

	return

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
	movlw	d'158'
	movwf	DELAY_0
	
	clrwdt
	nop
	
	incfsz	DELAY_0, F
	goto	$-3

	return

;***************************************************************************************************
;***************************************************************************************************
	org	4FF
;***************************************************************************************************
Tab_Wert
	addwf	PCL, F
	retlw 	d'16'	; 0
	retlw 	d'16'	; 1
	retlw 	d'17'	; 2
	retlw 	d'18'	; 3
	retlw 	d'19'	; 4
	retlw 	d'20'	; 5
	retlw 	d'21'	; 6
	retlw 	d'22'	; 7
	retlw 	d'23'	; 8
	retlw 	d'24'	; 9
	retlw 	d'25'	; 10
	retlw 	d'26'	; 11
	retlw 	d'27'	; 12
	retlw 	d'28'	; 13
	retlw 	d'29'	; 14
	retlw 	d'30'	; 15
	retlw 	d'31'	; 16
	retlw 	d'31'	; 17
	retlw 	d'32'	; 18
	retlw 	d'33'	; 19
	retlw 	d'34'	; 20
	retlw 	d'35'	; 21
	retlw 	d'36'	; 22
	retlw 	d'37'	; 23
	retlw 	d'38'	; 24
	retlw 	d'39'	; 25
	retlw 	d'40'	; 26
	retlw 	d'41'	; 27
	retlw 	d'42'	; 28
	retlw 	d'43'	; 29
	retlw 	d'44'	; 30
	retlw 	d'45'	; 31
	retlw 	d'46'	; 32
	retlw 	d'46'	; 33
	retlw 	d'47'	; 34
	retlw 	d'48'	; 35
	retlw 	d'49'	; 36
	retlw 	d'50'	; 37
	retlw 	d'51'	; 38
	retlw 	d'52'	; 39
	retlw 	d'53'	; 40
	retlw 	d'54'	; 41
	retlw 	d'55'	; 42
	retlw 	d'56'	; 43
	retlw 	d'57'	; 44
	retlw 	d'58'	; 45
	retlw 	d'59'	; 46
	retlw 	d'60'	; 47
	retlw 	d'61'	; 48
	retlw 	d'61'	; 49
	retlw 	d'62'	; 50
	retlw 	d'63'	; 51
	retlw 	d'64'	; 52
	retlw 	d'65'	; 53
	retlw 	d'66'	; 54
	retlw 	d'67'	; 55
	retlw 	d'68'	; 56
	retlw 	d'69'	; 57
	retlw 	d'70'	; 58
	retlw 	d'71'	; 59
	retlw 	d'72'	; 60
	retlw 	d'73'	; 61
	retlw 	d'74'	; 62
	retlw 	d'75'	; 63
	retlw 	d'76'	; 64
	retlw 	d'76'	; 65
	retlw 	d'77'	; 66
	retlw 	d'78'	; 67
	retlw 	d'79'	; 68
	retlw 	d'80'	; 69
	retlw 	d'81'	; 70
	retlw 	d'82'	; 71
	retlw 	d'83'	; 72
	retlw 	d'84'	; 73
	retlw 	d'85'	; 74
	retlw 	d'86'	; 75
	retlw 	d'87'	; 76
	retlw 	d'88'	; 77
	retlw 	d'89'	; 78
	retlw 	d'90'	; 79
	retlw 	d'91'	; 80
	retlw 	d'91'	; 81
	retlw 	d'92'	; 82
	retlw 	d'93'	; 83
	retlw 	d'94'	; 84
	retlw 	d'95'	; 85
	retlw 	d'96'	; 86
	retlw 	d'97'	; 87
	retlw 	d'98'	; 88
	retlw 	d'99'	; 89
	retlw 	d'100'	; 90
	retlw 	d'101'	; 91
	retlw 	d'102'	; 92
	retlw 	d'103'	; 93
	retlw 	d'104'	; 94
	retlw 	d'105'	; 95
	retlw 	d'106'	; 96
	retlw 	d'106'	; 97
	retlw 	d'107'	; 98
	retlw 	d'108'	; 99
	retlw 	d'109'	; 100
	retlw 	d'110'	; 101
	retlw 	d'111'	; 102
	retlw 	d'112'	; 103
	retlw 	d'113'	; 104
	retlw 	d'114'	; 105
	retlw 	d'115'	; 106
	retlw 	d'116'	; 107
	retlw 	d'117'	; 108
	retlw 	d'118'	; 109
	retlw 	d'119'	; 110
	retlw 	d'120'	; 111
	retlw 	d'121'	; 112
	retlw 	d'121'	; 113
	retlw 	d'122'	; 114
	retlw 	d'123'	; 115
	retlw 	d'124'	; 116
	retlw 	d'125'	; 117
	retlw 	d'126'	; 118
	retlw 	d'127'	; 119
	retlw 	d'128'	; 120
	retlw 	d'129'	; 121
	retlw 	d'130'	; 122
	retlw 	d'131'	; 123
	retlw 	d'132'	; 124
	retlw 	d'133'	; 125
	retlw 	d'134'	; 126
	retlw 	d'135'	; 127
	retlw 	d'136'	; 128
	retlw 	d'136'	; 129
	retlw 	d'137'	; 130
	retlw 	d'138'	; 131
	retlw 	d'139'	; 132
	retlw 	d'140'	; 133
	retlw 	d'141'	; 134
	retlw 	d'142'	; 135
	retlw 	d'143'	; 136
	retlw 	d'144'	; 137
	retlw 	d'145'	; 138
	retlw 	d'146'	; 139
	retlw 	d'147'	; 140
	retlw 	d'148'	; 141
	retlw 	d'149'	; 142
	retlw 	d'150'	; 143
	retlw 	d'151'	; 144
	retlw 	d'151'	; 145
	retlw 	d'152'	; 146
	retlw 	d'153'	; 147
	retlw 	d'154'	; 148
	retlw 	d'155'	; 149
	retlw 	d'156'	; 150
	retlw 	d'157'	; 151
	retlw 	d'158'	; 152
	retlw 	d'159'	; 153
	retlw 	d'160'	; 154
	retlw 	d'161'	; 155
	retlw 	d'162'	; 156
	retlw 	d'163'	; 157
	retlw 	d'164'	; 158
	retlw 	d'165'	; 159
	retlw 	d'166'	; 160
	retlw 	d'166'	; 161
	retlw 	d'167'	; 162
	retlw 	d'168'	; 163
	retlw 	d'169'	; 164
	retlw 	d'170'	; 165
	retlw 	d'171'	; 166
	retlw 	d'172'	; 167
	retlw 	d'173'	; 168
	retlw 	d'174'	; 169
	retlw 	d'175'	; 170
	retlw 	d'176'	; 171
	retlw 	d'177'	; 172
	retlw 	d'178'	; 173
	retlw 	d'179'	; 174
	retlw 	d'180'	; 175
	retlw 	d'181'	; 176
	retlw 	d'181'	; 177
	retlw 	d'182'	; 178
	retlw 	d'183'	; 179
	retlw 	d'184'	; 180
	retlw 	d'185'	; 181
	retlw 	d'186'	; 182
	retlw 	d'187'	; 183
	retlw 	d'188'	; 184
	retlw 	d'189'	; 185
	retlw 	d'190'	; 186
	retlw 	d'191'	; 187
	retlw 	d'192'	; 188
	retlw 	d'193'	; 189
	retlw 	d'194'	; 190
	retlw 	d'195'	; 191
	retlw 	d'196'	; 192
	retlw 	d'196'	; 193
	retlw 	d'197'	; 194
	retlw 	d'198'	; 195
	retlw 	d'199'	; 196
	retlw 	d'200'	; 197
	retlw 	d'201'	; 198
	retlw 	d'202'	; 199
	retlw 	d'203'	; 200
	retlw 	d'204'	; 201
	retlw 	d'205'	; 202
	retlw 	d'206'	; 203
	retlw 	d'207'	; 204
	retlw 	d'208'	; 205
	retlw 	d'209'	; 206
	retlw 	d'210'	; 207
	retlw 	d'211'	; 208
	retlw 	d'211'	; 209
	retlw 	d'212'	; 210
	retlw 	d'213'	; 211
	retlw 	d'214'	; 212
	retlw 	d'215'	; 213
	retlw 	d'216'	; 214
	retlw 	d'217'	; 215
	retlw 	d'218'	; 216
	retlw 	d'219'	; 217
	retlw 	d'220'	; 218
	retlw 	d'221'	; 219
	retlw 	d'222'	; 220
	retlw 	d'223'	; 221
	retlw 	d'224'	; 222
	retlw 	d'225'	; 223
	retlw 	d'226'	; 224
	retlw 	d'226'	; 225
	retlw 	d'227'	; 226
	retlw 	d'228'	; 227
	retlw 	d'229'	; 228
	retlw 	d'230'	; 229
	retlw 	d'231'	; 230
	retlw 	d'232'	; 231
	retlw 	d'233'	; 232
	retlw 	d'234'	; 233
	retlw 	d'235'	; 234
	retlw 	d'236'	; 235
	retlw 	d'237'	; 236
	retlw 	d'238'	; 237
	retlw 	d'239'	; 238
	retlw 	d'240'	; 239
	retlw 	d'241'	; 240
	retlw 	d'241'	; 241
	retlw 	d'242'	; 242
	retlw 	d'243'	; 243
	retlw 	d'244'	; 244
	retlw 	d'245'	; 245
	retlw 	d'246'	; 246
	retlw 	d'247'	; 247
	retlw 	d'248'	; 248
	retlw 	d'249'	; 249
	retlw 	d'250'	; 250
	retlw 	d'251'	; 251
	retlw 	d'252'	; 252
	retlw 	d'253'	; 253
	retlw 	d'254'	; 254
	retlw 	d'255'	; 255

;***************************************************************************************************
;***************************************************************************************************
	org	6FF
;***************************************************************************************************
Tab_Timer
	addwf	PCL, F
	
	retlw 	d'0'	; 0
	retlw 	d'1'	; 1
	retlw 	d'2'	; 2
	retlw 	d'3'	; 3
	retlw 	d'4'	; 4
	retlw 	d'4'	; 5
	retlw 	d'5'	; 6
	retlw 	d'6'	; 7
	retlw 	d'7'	; 8
	retlw 	d'8'	; 9
	retlw 	d'8'	; 10
	retlw 	d'9'	; 11
	retlw 	d'10'	; 12
	retlw 	d'11'	; 13
	retlw 	d'12'	; 14
	retlw 	d'13'	; 15
	retlw 	d'13'	; 16
	retlw 	d'14'	; 17
	retlw 	d'15'	; 18
	retlw 	d'16'	; 19
	retlw 	d'17'	; 20
	retlw 	d'17'	; 21
	retlw 	d'18'	; 22
	retlw 	d'19'	; 23
	retlw 	d'20'	; 24
	retlw 	d'21'	; 25
	retlw 	d'21'	; 26
	retlw 	d'22'	; 27
	retlw 	d'23'	; 28
	retlw 	d'24'	; 29
	retlw 	d'25'	; 30
	retlw 	d'26'	; 31
	retlw 	d'26'	; 32
	retlw 	d'27'	; 33
	retlw 	d'28'	; 34
	retlw 	d'29'	; 35
	retlw 	d'30'	; 36
	retlw 	d'30'	; 37
	retlw 	d'31'	; 38
	retlw 	d'32'	; 39
	retlw 	d'33'	; 40
	retlw 	d'34'	; 41
	retlw 	d'34'	; 42
	retlw 	d'35'	; 43
	retlw 	d'36'	; 44
	retlw 	d'37'	; 45
	retlw 	d'38'	; 46
	retlw 	d'39'	; 47
	retlw 	d'39'	; 48
	retlw 	d'40'	; 49
	retlw 	d'41'	; 50
	retlw 	d'42'	; 51
	retlw 	d'43'	; 52
	retlw 	d'43'	; 53
	retlw 	d'44'	; 54
	retlw 	d'45'	; 55
	retlw 	d'46'	; 56
	retlw 	d'47'	; 57
	retlw 	d'47'	; 58
	retlw 	d'48'	; 59
	retlw 	d'49'	; 60
	retlw 	d'50'	; 61
	retlw 	d'51'	; 62
	retlw 	d'52'	; 63
	retlw 	d'52'	; 64
	retlw 	d'53'	; 65
	retlw 	d'54'	; 66
	retlw 	d'55'	; 67
	retlw 	d'56'	; 68
	retlw 	d'56'	; 69
	retlw 	d'57'	; 70
	retlw 	d'58'	; 71
	retlw 	d'59'	; 72
	retlw 	d'60'	; 73
	retlw 	d'60'	; 74
	retlw 	d'61'	; 75
	retlw 	d'62'	; 76
	retlw 	d'63'	; 77
	retlw 	d'64'	; 78
	retlw 	d'65'	; 79
	retlw 	d'65'	; 80
	retlw 	d'66'	; 81
	retlw 	d'67'	; 82
	retlw 	d'68'	; 83
	retlw 	d'69'	; 84
	retlw 	d'69'	; 85
	retlw 	d'70'	; 86
	retlw 	d'71'	; 87
	retlw 	d'72'	; 88
	retlw 	d'73'	; 89
	retlw 	d'73'	; 90
	retlw 	d'74'	; 91
	retlw 	d'75'	; 92
	retlw 	d'76'	; 93
	retlw 	d'77'	; 94
	retlw 	d'78'	; 95
	retlw 	d'78'	; 96
	retlw 	d'79'	; 97
	retlw 	d'80'	; 98
	retlw 	d'81'	; 99
	retlw 	d'82'	; 100
	retlw 	d'82'	; 101
	retlw 	d'83'	; 102
	retlw 	d'84'	; 103
	retlw 	d'85'	; 104
	retlw 	d'86'	; 105
	retlw 	d'86'	; 106
	retlw 	d'87'	; 107
	retlw 	d'88'	; 108
	retlw 	d'89'	; 109
	retlw 	d'90'	; 110
	retlw 	d'91'	; 111
	retlw 	d'91'	; 112
	retlw 	d'92'	; 113
	retlw 	d'93'	; 114
	retlw 	d'94'	; 115
	retlw 	d'95'	; 116
	retlw 	d'95'	; 117
	retlw 	d'96'	; 118
	retlw 	d'97'	; 119
	retlw 	d'98'	; 120
	retlw 	d'99'	; 121
	retlw 	d'99'	; 122
	retlw 	d'100'	; 123
	retlw 	d'101'	; 124
	retlw 	d'102'	; 125
	retlw 	d'103'	; 126
	retlw 	d'104'	; 127
	retlw 	d'104'	; 128
	retlw 	d'105'	; 129
	retlw 	d'106'	; 130
	retlw 	d'107'	; 131
	retlw 	d'108'	; 132
	retlw 	d'108'	; 133
	retlw 	d'109'	; 134
	retlw 	d'110'	; 135
	retlw 	d'111'	; 136
	retlw 	d'112'	; 137
	retlw 	d'112'	; 138
	retlw 	d'113'	; 139
	retlw 	d'114'	; 140
	retlw 	d'115'	; 141
	retlw 	d'116'	; 142
	retlw 	d'117'	; 143
	retlw 	d'117'	; 144
	retlw 	d'118'	; 145
	retlw 	d'119'	; 146
	retlw 	d'120'	; 147
	retlw 	d'121'	; 148
	retlw 	d'121'	; 149
	retlw 	d'122'	; 150
	retlw 	d'123'	; 151
	retlw 	d'124'	; 152
	retlw 	d'125'	; 153
	retlw 	d'125'	; 154
	retlw 	d'126'	; 155
	retlw 	d'127'	; 156
	retlw 	d'128'	; 157
	retlw 	d'129'	; 158
	retlw 	d'130'	; 159
	retlw 	d'130'	; 160
	retlw 	d'131'	; 161
	retlw 	d'132'	; 162
	retlw 	d'133'	; 163
	retlw 	d'134'	; 164
	retlw 	d'134'	; 165
	retlw 	d'135'	; 166
	retlw 	d'136'	; 167
	retlw 	d'137'	; 168
	retlw 	d'138'	; 169
	retlw 	d'138'	; 170
	retlw 	d'139'	; 171
	retlw 	d'140'	; 172
	retlw 	d'141'	; 173
	retlw 	d'142'	; 174
	retlw 	d'143'	; 175
	retlw 	d'143'	; 176
	retlw 	d'144'	; 177
	retlw 	d'145'	; 178
	retlw 	d'146'	; 179
	retlw 	d'147'	; 180
	retlw 	d'147'	; 181
	retlw 	d'148'	; 182
	retlw 	d'149'	; 183
	retlw 	d'150'	; 184
	retlw 	d'151'	; 185
	retlw 	d'151'	; 186
	retlw 	d'152'	; 187
	retlw 	d'153'	; 188
	retlw 	d'154'	; 189
	retlw 	d'155'	; 190
	retlw 	d'156'	; 191
	retlw 	d'156'	; 192
	retlw 	d'157'	; 193
	retlw 	d'158'	; 194
	retlw 	d'159'	; 195
	retlw 	d'160'	; 196
	retlw 	d'160'	; 197
	retlw 	d'161'	; 198
	retlw 	d'162'	; 199
	retlw 	d'163'	; 200
	retlw 	d'164'	; 201
	retlw 	d'164'	; 202
	retlw 	d'165'	; 203
	retlw 	d'166'	; 204
	retlw 	d'167'	; 205
	retlw 	d'168'	; 206
	retlw 	d'169'	; 207
	retlw 	d'169'	; 208
	retlw 	d'170'	; 209
	retlw 	d'171'	; 210
	retlw 	d'172'	; 211
	retlw 	d'173'	; 212
	retlw 	d'173'	; 213
	retlw 	d'174'	; 214
	retlw 	d'175'	; 215
	retlw 	d'176'	; 216
	retlw 	d'177'	; 217
	retlw 	d'177'	; 218
	retlw 	d'178'	; 219
	retlw 	d'179'	; 220
	retlw 	d'180'	; 221
	retlw 	d'181'	; 222
	retlw 	d'182'	; 223
	retlw 	d'182'	; 224
	retlw 	d'183'	; 225
	retlw 	d'184'	; 226
	retlw 	d'185'	; 227
	retlw 	d'186'	; 228
	retlw 	d'186'	; 229
	retlw 	d'187'	; 230
	retlw 	d'188'	; 231
	retlw 	d'189'	; 232
	retlw 	d'190'	; 233
	retlw 	d'190'	; 234
	retlw 	d'191'	; 235
	retlw 	d'192'	; 236
	retlw 	d'193'	; 237
	retlw 	d'194'	; 238
	retlw 	d'195'	; 239
	retlw 	d'195'	; 240
	retlw 	d'196'	; 241
	retlw 	d'197'	; 242
	retlw 	d'198'	; 243
	retlw 	d'199'	; 244
	retlw 	d'199'	; 245
	retlw 	d'200'	; 246
	retlw 	d'201'	; 247
	retlw 	d'202'	; 248
	retlw 	d'203'	; 249
	retlw 	d'203'	; 250
	retlw 	d'204'	; 251
	retlw 	d'205'	; 252
	retlw 	d'206'	; 253
	retlw 	d'207'	; 254
	retlw 	d'208'	; 255

;***************************************************************************************************
;***************************************************************************************************
;***************************************************************************************************
;***************************************************************************************************
	END
