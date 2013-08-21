	Processor 16F914

#include P16F914.inc   
;******************************************************************
; History
;******************************************************************
; Version 1.00	21.09.2005 Ga


;******************************************************************
; Definitions
;******************************************************************
;

;------------------------------------------------------------------
; Register Definitions
;
W_TEMP		equ	0x20 ; Stack für W-register im Interrupt
PCLATH_TEMP	equ	0x21 ; Stack für PLATH-Register

TIM1_10MS	equ 0x22
TIM2_10MS	equ	0x23

AD0				equ	0x24	; Bit 7 bei Wechsel = AD1				equ	0x2a	; Bit 7 bei Wechsel = 1
AD1				equ	0x25	; Bit 7 bei Wechsel = AD1				equ	0x2a	; Bit 7 bei Wechsel = 1
AD2				equ	0x26	; Bit 7 bei Wechsel = AD1				equ	0x2a	; Bit 7 bei Wechsel = 1


TASTE_AKT		equ	0x28	; aktuell gedrückte Taste, Bit 7 = 1 wenn 
							; Drücken entdeckt, bei Repeat Bit 6=1
TASTE_LAST		equ	0x29	; zuletzt gedrückte Taste
TASTE_IDX		equ	0x2a	; Wert, der 10%, 30%, 40% usw in eine Zahl 0,1,2 usw wandelt
							; wird von TAST_DISPATCH beschrieben


TEMP			equ 0x2e	; temporäre Speicherplatz, nur in einem
					; call geschützt

TEMP1			equ 0x2f
TEMP2			equ 0x30

DISP_CNT		equ	0x30	; enthält die ANzahl auf Disp zu schreibende Zeichen
DISP_Z_FLAG		equ	0x31	; Bit0-> Zeile 1
							; Bit1-> Zeile 2 usw.
DISP_STAT		equ	0x32	; Bit3-> DisplayAusgabe steht an
							; Bit6-> Anzeige On/Off 
TEMP3			equ	0x3b
TEMP4			equ	0x3c
TEMP5			equ	0x3d
AD_STATUS		equ 0x3f	; Bit 0-2 --> Neuer AD-Wert Kanal 0-2


ACC1_0			equ	0x40	;Rechenregister
ACC1_H			equ	0x41	;Rechenregister
ACC1_L			equ	0x42

ACC2_0			equ	0x43	;Rechenregister
ACC2_H			equ	0x44
ACC2_L			equ	0x45

TEMPFLAG		equ	0x46	; Temporäres Bitregister

DELAY			equ	0x47

HEX_AKT			equ	0x49	; Bit 0-3-> aktuelle Hex-Schalter Stellung
HEX_LAST		equ	0x4A	; Bit 7=1-> Schalterstellung geändert

DISP_BUFF		equ	0x50	; Display Buffer, 16 chars!!

ITOA_BUFF		equ	0x60	; Achtung!! 6 Bytes lang!!!!

PORT_TASTOUT		equ	0x66	; Tastatur/LED-Port Out
PORT_TASTIN		equ	0x67	; Tastatur/Hex-Schalter IN

STATUS_TEMP		equ	0x7f ; stack für STATUS im Interrupt

;16F914-Configs---------------------------------------------------------------------
;	__IDLOCS	H'3012' ;       User ID
;-----------------------------------------------------------------------------------
;16F914 ************************************************************************
	__CONFIG  B'10000011100010'		;zum debuggen
;	__CONFIG  B'11000000100010'		
;                   ||||||||||||||
;                   |||||||||||+++---FOSC 111=RC R+C an RA5, RA4=CLKOUT
;                   |||||||||||+++---FOSC 110=RC R+C an RA5
;                   |||||||||||+++---FOSC 101=INTOSC RA4=CLKOUT
;                   |||||||||||+++---FOSC 100=INTOSC RA4, RA5 = I/O
;                   |||||||||||+++---FOSC 011=EC
;                   |||||||||||+++---FOSC 010=HS
;                   |||||||||||+++---FOSC 001=XT
;                   |||||||||||+++---FOSC 000=LP
;                   |||||||||||     
;                   ||||||||||+------WDTE 0=disa 1=ena
;                   |||||||||+-------PWRT 0=ena  1=disa
;                   ||||||||+--------MCLR 0=din  1=ena
;                   |||||||+---------CP  ROM 0=CPena 1=CPdis
;                   ||||||+----------CPD RAM 0=CPena 1=CPdis
;                   ||||++-----------BOR 00=BOR disabled
;                   ||||++-----------BOR 01=BOR controlled by SBOREN
;                   ||||++-----------BOR 10=BOR enabled: operation dis.: sleep
;                   ||||++-----------BOR 11=BOR enabled
;                   |||+-------------IESO 0=dis   1=ena
;                   ||+--------------FCMEN 0=dis  1=ena
;                   |+---------------DEBUG 0=ena  1=dis
;
;***************************************************************
;
        IFNDEF __16F914
           MESSG "Eingestellter Prozessor ist nicht 16F914 - Überprüfe Einstellungen"
        ENDIF
;=============================================================================================
; PROGRAMM
;=============================================================================================
	org	000
;RST CODE 0x0
 	clrf PCLATH

	goto	start

;=============================================================================================
; ISR
;=============================================================================================

;=============================================================================================
;IV CODE 0x4
	org	004
	goto 	Interrupt		

; ****************************************************************************

;TAB CODE 0x8
	org	008

Interrupt

	movwf	W_TEMP		; Accu sichern
	swapf	STATUS,W	; Status nach Accu laden
	clrf	STATUS		; nach Bank 0 umschalten
	movwf	STATUS_TEMP	; Status im Temp-Register ablegen

	movfw	PCLATH
	movwf	PCLATH_TEMP
	clrf	PCLATH

	btfsc	PIR1, TMR2IF
	goto	Timer2Int
	btfsc	PIR1, TMR1IF
	goto	Timer1Int
	goto 	EndInt

;---------------------------------------	
Timer1Int			; PWM-Timer


EndTimer1Int
	bcf		PIR1, TMR1IF
	bsf		T1CON,	TMR1ON
	goto	EndInt
;----------------------------------------
Timer2Int			; 10msec-Timer
	bsf	PORTC,0
	bcf		PIR1,TMR2IF
	movf	TIM1_10MS,F		; TEst auf 0
	btfss	STATUS,Z
	decf	TIM1_10MS,F

	movf	TIM2_10MS,F		; TEst auf 0
	btfss	STATUS,Z
	decf	TIM2_10MS,F
	bcf	PORTC,0

	
	
	goto	EndInt	
;----------------------------------------
EndInt

	movfw	PCLATH_TEMP
	movwf	PCLATH
	swapf	STATUS_TEMP,W
	movwf	STATUS
	swapf	W_TEMP,F
	swapf	W_TEMP,W	

	retfie




;==================================================
;INIT CODE 
;==================================================

start


	clrwdt
	nop

;====== Register 20H bis 7FH löschen ======

	movlw	20	; beginne bei Register 20H
	movwf	04	; FSR

loop_1
	clrf	0
	incf	04,1
	btfss	04,7	; wenn REGISTER 80H erreicht
	goto loop_1

	clrwdt
	nop

;======= Timer 2 INIT ========

	movlw	b'1001110'	; T2on, Prescale 16, Postscale 10
	movwf	T2CON
	bsf	STATUS,RP0			; Bank 1
	bsf	PIE1, TMR2IE	; Timer 2 Interrupt enable
	movlw	d'250'			; 
	movwf	PR2
	bcf		STATUS,RP0			; Bank 1


;======== Timer 1 INIT =========
	bcf		3,5
	movlw	b'100001'
	movwf	T1CON

	
	bsf		3,5
;	bsf		PIE1, TMR1IE
	bcf		PIE1, TMR1IE

;======= Port A init =============
	bcf		TRISA,4		; D0 für Display

;======= Port D init =============

;	movlw	b'000000000'	; Alles Ausgänge
	movlw	b'11111000'		; Bit 0-2 = Controlbits für Display
	movwf	TRISD

;======== Port B init ============

;	movlw	b'11000110'		; Tastatur Scanner
	movlw	b'11000000'		; Bit 0-5 = D2-7 für Display
	movwf	TRISB
	bsf		OPTION_REG, 7	; Pull-Ups für PORT B einschalten

;======== Port C init ============

;	movlw	b'00111000'		; Daten CS-Generator '138 (Bit 0-2)
					; PWM-IN (Bit 3-5)
	movlw	b'11101110'	; Alles Eingänge
	movwf	TRISC
	BCF 	STATUS,RP0 	;Bank 2
	BSF 	STATUS,RP1 	;
	CLRF 	LCDCON 		;Disable VLCD<3:1>
	BSF 	STATUS,RP0	;Bank 0
	BCF 	STATUS,RP1
;======== Port E init ============

;	movlw	b'00000000'		; Daten für Display
	movlw	b'11111011'		; Bit 2 = D1 für Display
	movwf	TRISE


;======== Serial Port Init ============

	movlw	d'51'
	movwf	SPBRG			; Serial Port Baudrategenerator (Wert aus Tabelle = 19200 Baud)


	movlw	b'01100101'		; 8Bit-Transm., TxEnable, Asynch.Mode, High Baudrate
	movwf	TXSTA			; TRANSMIT STATUS AND CONTROL REGISTER 

	bcf		3,5
	movlw	b'10000000'		; SerialPort Enable
	movwf	RCSTA			; ;RCSTA: RECEIVE STATUS AND CONTROL REGISTER

;=========  A/D-Wandler INIT =====

	bsf		3,5

	movlw	b'00001111'		; Kanal AN0-3 sind benutzt
	movwf	ANSEL

	movlw	b'01100000'		; Fosc /64
	movwf	ADCON1
	

	bcf		3,5
	bcf		3,6

	movlw	b'00000001'		; Left justified, VREF=Versorgung, ADON
	movwf	ADCON0

	bsf		INTCON, PEIE
	bsf		INTCON, GIE

	clrf	AD_STATUS	; = kein neuer AD-Wert da

	movlw	0x4
	movwf	TASTE_IDX
	movlw	0x5
	movwf	TASTE_LAST

	clrf	AD0
	clrf	AD1
	bsf	PORTC,4		; Data Enable für RS485-Transceiver
	
	call	display_init
	clrf	DISP_STAT
	bsf	DISP_STAT,6		; Display on
	call	display

	movlw	d'30'
	movwf	TIM2_10MS

DispInitLoop	
	movf	TIM2_10MS,F
	btfss	STATUS,Z
	goto	DispInitLoop	

	call	DispVersion
	movlw	d'200'
	movwf	TIM2_10MS
	
VersLoop
	movf	TIM2_10MS,F
	btfss	STATUS,Z
	goto	VersLoop

;==========MainLoop

main
;	call	HexScan				; HEx-Schalter nach HEX_AKT einlesen
;	call 	TastScan			; Tastatur-Sac, Wert nach TASTE_AKT
	call 	ADconv				; AD.Wandlung beider Kanäle, Wert nach AD0 und AD1
;	call	TastDispatch_Hex0		; wenn Taste gedrückt, Tasten-Aktionen einleiten Hex-Schalterstellung 0
;	call	TastDispatch_Hex1		; wenn Taste gedrückt, Tasten-Aktionen einleiten
;	call	display
	call	AdDispatch			; Wenn sich einer der D-Wert geändert hat

	movlw	#2
	movwf	TIM1_10MS

MainWaitLoop	
	movf	TIM1_10MS,F
	btfss	STATUS,Z
	goto	MainWaitLoop


	goto 	main


;===================================================
; DispVersion
;===================================================
DispVersion
	clrf	TEMP			; als ByteCount
	movlw	DISP_BUFF
	movwf	FSR			; 4
DispVersion_1
	movlw	HIGH VersionData
	movwf	PCLATH
	movfw	TEMP
	call	VersionData
	clrf	PCLATH
	movwf	INDF
	incf	FSR,F
	incf	TEMP,F
	btfss	TEMP,4
	goto	DispVersion_1

	bsf	DISP_Z_FLAG,0
	call	display

	return

;===================================================
; DispMainParam
;===================================================
DispMainParam
	clrf	TEMP			; als ByteCount
	movlw	DISP_BUFF
	movwf	FSR			; 4
DispMainParam_1
	movlw	HIGH MainParamData
	movwf	PCLATH
	movfw	TEMP
	call	MainParamData
	clrf	PCLATH
	movwf	INDF
	incf	FSR,F
	incf	TEMP,F
	btfss	TEMP,4
	goto	DispMainParam_1

	movfw	AD0
	movwf	TEMP
	movlw	DISP_BUFF+1
	movwf	FSR
	call	sutoa

	movfw	AD1
	movwf	TEMP
	movlw	DISP_BUFF+6
	movwf	FSR
	call	sutoa

	movfw	AD2
	movwf	TEMP
	movlw	DISP_BUFF+d'11'
	movwf	FSR
	call	sutoa


	bsf	DISP_Z_FLAG,0
	call	display

	return

;----------------------------------------
wait_3ms
	call	wait_750us
wait_22zms
	call	wait_750us

wait_15zms
	call	wait_750us
wait_750us
	bcf	T1CON,0		; Timer1 stoppen	
	clrf	TMR1L		; TMR1L			
	clrf	TMR1H		; TMR1H			
	bsf	T1CON,0		; Timer1 starten	
	movlw	d'3'
	subwf	TMR1H,0
	btfss	STATUS,2	; 
	goto	$-2		; auf Bit warten	
	return			; mit Aufruf		



;===================================================
; V24Send
; Gibt WREG an TX-Buffer aus und wartet 3ms
;===================================================

V24Send
	bsf	3,5
WaitTxBufferleer
	btfss	TXSTA,TRMT
	goto	WaitTxBufferleer
	bcf	3,5
	movwf	TXREG

	return

;===================================================
; MoveToDispBuff
; Verschiebt ab Adresse in WREG 16 Bytes nach DispBuff
;===================================================

MoveToDispBuff
	movwf	TEMP		; LeseAdresse
	movlw	DISP_BUFF
	movwf	TEMP1		; Schreibadresse
	movlw	0x10		; Zähler
	movwf	TEMP2

MoveToDispBuff1

	movfw	TEMP		; Lese-Adresse
	movwf	FSR
	bsf	STATUS,RP0
	movfw	INDF
	bcf	STATUS,RP0
	movwf	TEMP3		; gelesenes Byte
	call	V24Send
	incf	FSR,F
	movfw	FSR
	movwf	TEMP		; Leseadresse speicher
	movfw	TEMP1		; Schreibadr.
	movwf	FSR
	movfw	TEMP3		; gelesenes Byte
	movwf	INDF
	incf	FSR,F
	movfw	FSR		; Schreibadr
	movwf	TEMP1	

	decfsz	TEMP2,F
	goto	MoveToDispBuff1

	return

;===================================================
; BinToHex8
; Wandelt 8 Bytes ab Adress (WREG) in ASCII HEX nach DISP_BUFF
;===================================================

BinToHex8
	movwf	TEMP		; LeseAdresse
	movlw	DISP_BUFF
	movwf	TEMP1		; Schreibadresse
	movlw	0x8		; Zähler
	movwf	TEMP2

BinToHex81

	movfw	TEMP		; Lese-Adresse
	movwf	FSR
	bsf	STATUS,RP0
	movfw	INDF
	bcf	STATUS,RP0
	movwf	TEMP3		; gelesenes Byte
	incf	FSR,F
	movfw	FSR
	movwf	TEMP		; Leseadresse speicher
	movfw	TEMP1		; Schreibadr.
	movwf	FSR

	swapf	TEMP3,W		; gelesenes Byte, High Nibble
	andlw	0xf	
	call	BinToHex
	call	V24Send

	movwf	INDF
	incf	FSR,F

	movfw	TEMP3		; gelesenes Byte Low Nibble
	andlw	0xf	
	call	BinToHex
	call	V24Send

	movwf	INDF
	incf	FSR,F


	movfw	FSR		; Schreibadr
	movwf	TEMP1	

	decfsz	TEMP2,F
	goto	BinToHex81

	return



BinToHex
	movwf	TEMP4

	movlw	HIGH BinToHexTab
	movwf	PCLATH
	movfw	TEMP4
	call	BinToHexTab
	clrf	PCLATH


	return

;===================================================
; Zeigt den Text "Keine Funktion in Zeile 1 an
;===================================================

DispKeineFunktion
; ZEile 1
	clrf	TEMP			; als ByteCount
	movlw	DISP_BUFF
	movwf	FSR			; 4
DispKeineFunktionLoop	
	movlw	HIGH DatenKeineFunktion
	movwf	PCLATH
	movfw	TEMP

	call	DatenKeineFunktion
	clrf	PCLATH
	movwf	INDF
	incf	FSR,F
	incf	TEMP,F
	btfss	TEMP,4
	goto	DispKeineFunktionLoop

	bsf	DISP_Z_FLAG,0
	call	display
	return



;===================================================
; AdDispatch
; ADconv (mainloop) signalisiert in AD0 und AD1 Bit 7 = 1,
; daß sich ein Wert verändert hat.
;===================================================
AdDispatch
	
;--------  HEX-Drehschalters = 0 ? -------------

;	movfw	HEX_AKT
;	andlw	0xf
;	sublw	0
;	btfss	STATUS,Z
;	return
	movf	AD_STATUS
	btfsc	STATUS,Z
	return

	clrf	AD_STATUS	

	call	SendNewColor
	call	DispMainParam
	return

;===================================================
; SendNewColor gibt die neue Farbe an die Kachel aus
;===================================================
SendNewColor
	movlw	0xFF		; Adresse Broadcast
	bsf	3,5
	bsf	TXSTA, TX9D	; 9. Bit (= Adressabyte) setzen
	bcf	3,5
	call	V24Send

	movfw	AD0		; ROT-Wert
	bsf	3,5
	bcf	TXSTA, TX9D	; 9. Bit (= Adressabyte) setzen
	bcf	3,5
	call	V24Send

	movfw	AD1		; Gruen-Wert
	call	V24Send

	movfw	AD2		; Gruen-Wert
	call	V24Send

	clrf	TEMP
	
	movfw	AD0
	call	ZeroCount

	movfw	AD1
	call	ZeroCount

	movfw	AD2
	call	ZeroCount

	movfw	TEMP
	call	V24Send

	return

;----
ZeroCount
	movwf	TEMP1		; Byte, in dem die Nullen gezählt werden
	movlw	#8
	movwf	TEMP2		;Schleifenzähler	
ZeroCountLoop
	rrf	TEMP1
	btfss	STATUS,C
	incf	TEMP		; Zähler für die Nullen

	decfsz	TEMP2
	goto	ZeroCountLoop
	return

;===================================================
; TastDispatch_Hex0 für Drehschalter in STellung 0
;===================================================
TastDispatch_Hex0
	
	btfss	TASTE_AKT,7		; Flag "Neue Taste gedrückt"
	return

;--------  HEX-Drehschalters = 0 ? -------------

	movfw	HEX_AKT
	andlw	0xf
	sublw	0
	btfss	STATUS,Z
	return

	bcf		TASTE_AKT,7
	movfw	TASTE_AKT
	andlw	0xf
	movwf	TEMP		; Akt.Taste wird zuletzt gedrückte Taste	


	movf	TEMP,F		; TEst auf Z, 
	btfsc	STATUS,Z		
	return		

	movlw	0xA
	subwf	TEMP,w
	btfsc	STATUS,C
	return

; Anzeige löschen, Zeile 2,3,4
	call	ClearDispBuff
	bsf	DISP_Z_FLAG,1
	bsf	DISP_Z_FLAG,2
	bsf	DISP_Z_FLAG,3
	call	display



	movfw	TEMP				; gedrückte Taste
	movwf	TASTE_LAST
	movwf	TASTE_IDX
	decf	TASTE_IDX,F			; index muß mit 0 beginnen


	
NormalDispatchEnd

	return




;===================================================
; AddAcc
; Addiert die 16Bit Accus ACC1 und ACC1 
; Ergebnis in ACC1
; ACC2 bleibt unverändert
; Caryy wird gesetzt
;===================================================
AddAcc

	movfw	ACC2_L
	addwf	ACC1_L,F
	btfsc	STATUS,C	
	incf	ACC1_H,F
	
	movfw	ACC2_H
	addwf	ACC1_H,F
	
	return
;===================================================
; dAddAcc
; Addiert die 24Bit Accus ACC1 und ACC2 
; Ergebnis in ACC1
; ACC2 bleibt unverändert
; Caryy wird gesetzt
;===================================================
dAddAcc

	movfw	ACC2_L
	addwf	ACC1_L,F
	btfss	STATUS,C
	goto	dAddAcc1	
	incf	ACC1_H,F
	movf	ACC1_H,F		; = 0?
	btfsc	STATUS,Z
	incf	ACC1_0,f	
	
dAddAcc1
	movfw	ACC2_H
	addwf	ACC1_H,F
	btfsc	STATUS,C	
	incf	ACC1_0,F
	
	movfw	ACC2_0
	addwf	ACC1_0,F
	
	return
;===================================================
; SubAcc
; Subtrahiert die 16Bit Accus ACC1 und ACC1 
; Ergebnis in ACC1
; ACC2 bleibt unverändert
;===================================================
SubAcc
	bcf	TEMPFLAG,1
	movfw	ACC2_L
	subwf	ACC1_L,F
	btfsc	STATUS,C
	goto	SubAcc1	
	movf	ACC1_H,F
	btfsc	STATUS,Z
	bsf	TEMPFLAG,1
	decf	ACC1_H,F

SubAcc1
	movfw	ACC2_H
	subwf	ACC1_H,F
	
	btfsc	TEMPFLAG,1
	bcf	STATUS,C
	
	return

;===================================================
; dSubAcc
; Subtrahiert die 24Bit Accus ACC1 und ACC1 
; Ergebnis in ACC1
; ACC2 bleibt unverändert
;===================================================
dSubAcc
	bcf	TEMPFLAG,1
	movfw	ACC2_L
	subwf	ACC1_L,F
	btfsc	STATUS,C
	goto	dSubAcc1	
	decf	ACC1_H,F
	movlw	0xff
	subwf	ACC1_H,W
	btfss	STATUS,Z
	goto	dSubAcc1
	movf	ACC1_0,F
	btfsc	STATUS,Z
	bsf	TEMPFLAG,1
	decf	ACC1_0,F
	

dSubAcc1
	movfw	ACC2_H
	subwf	ACC1_H,F
	btfsc	STATUS,C
	goto	dSubAcc2	
	movf	ACC1_0,F
	btfsc	STATUS,Z
	bsf	TEMPFLAG,1
	decf	ACC1_0,F



dSubAcc2
	movfw	ACC2_0
	subwf	ACC1_0,F
	
	btfsc	TEMPFLAG,1
	bcf	STATUS,C
	
	return


;===================================================
; AddAccRep
; Addiert die 16Bit Accus ACC1 und ACC1 n-mal
; n steht in TEMP, TEMP wird verändert
; Ergebnis in ACC1
; ACC2 bleibt unverändert
;===================================================
AddAccRep

	movf	TEMP,F
	btfsc	STATUS,Z
	goto	EndAccAdd
	movfw	ACC2_L
	addwf	ACC1_L,F
	btfsc	STATUS,C	
	incf	ACC1_H,F

	decf	TEMP,F
	goto	AddAccRep
EndAccAdd
	return
;===================================================
; SubAccRep
; Subtrahiert die 16Bit Accus ACC1 und ACC1 n-mal (ACC1-ACC2)
; n steht in TEMP, TEMP wird verändert
; Ergebnis in ACC1
; ACC2 bleibt unverändert
;===================================================
SubAccRep
	movf	TEMP,F
	btfsc	STATUS,Z
	goto	EndAccSub
	movfw	ACC2_L
	subwf	ACC1_L,F
	btfss	STATUS,C	
	decf	ACC1_H,F

	decf	TEMP,F
	goto	SubAccRep
EndAccSub
	return


;===================================================
; sutoa  (short unsigend to ASCII) wandelt 8bit unsigned nach ASCII
; Quelle ist in TEMP
; Ziel ist in FSR
; benutze Register: TEMP und TEMP1 
;===================================================
sutoa
	movfw	TEMP
	movwf	TEMP1
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	d'100'
sutoa1					; Hunderter-Schleife
	subwf	TEMP,F
	btfss	STATUS,C
	goto 	sutoa2
	incf	INDF,F
	goto 	sutoa1
sutoa2					; 
	addwf	TEMP,F		; einmal zuviel subtrahiert
	incf	FSR,f			; nächste Stelle im Display-Ram
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	d'10'
sutoa3					; Zehner Schleife
	subwf	TEMP,F
	btfss	STATUS,C
	goto 	sutoa4
	incf	INDF,F
	goto 	sutoa3
sutoa4
	addwf	TEMP,F		; einmal zuviel subtrahiert
	movlw	0x30
	addwf	TEMP,W
	incf	FSR,f
	movwf	INDF

	return

;===================================================
; lutoa  (long unsigend to ASCII) wandelt 16bit unsigned nach ASCII
; Quelle ist in ACC1 (wird überschrieben)
; Ziel ist in FSR
; benutze Register: ACC2 
;===================================================
lutoa
	movwf	FSR
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	HIGH d'10000'
	movwf	ACC2_H
	movlw	LOW d'10000'
	movwf	ACC2_L

lutoa1					; 10000er-Schleife
	call	SubAcc		; 16Bit-Subtraktion
	btfss	STATUS,C
	goto 	lutoa2
	incf	INDF,F
	goto 	lutoa1
lutoa2					; 
	call	AddAcc		; einmal zuviel subtrahiert
lutoa_sub
	incf	FSR,f			; nächste Stelle im Display-Ram
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	HIGH d'1000'
	movwf	ACC2_H
	movlw	LOW d'1000'
	movwf	ACC2_L

lutoa3					; Tausender Schleife
	call	SubAcc
	btfss	STATUS,C
	goto 	lutoa4
	incf	INDF,F
	goto 	lutoa3
lutoa4
	call	AddAcc		; einmal zuviel subtrahiert
	incf	FSR,f			; nächste Stelle im Display-Ram
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	HIGH d'100'
	movwf	ACC2_H
	movlw	LOW d'100'
	movwf	ACC2_L

lutoa5					; Hunderter Schleife
	call	SubAcc
	btfss	STATUS,C
	goto 	lutoa6
	incf	INDF,F
	goto 	lutoa5
lutoa6
	call	AddAcc		; einmal zuviel subtrahiert
	incf	FSR,f			; nächste Stelle im Display-Ram
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	HIGH d'10'
	movwf	ACC2_H
	movlw	LOW d'10'
	movwf	ACC2_L

lutoa7					; Zehner Schleife
	call	SubAcc
	btfss	STATUS,C
	goto 	lutoa8
	incf	INDF,F
	goto 	lutoa7

lutoa8

	call	AddAcc		; einmal zuviel subtrahiert
	movlw	0x30
	addwf	ACC1_L,W
	incf	FSR,f
	movwf	INDF

	return


;===================================================
; Dutoa  (long unsigend to ASCII) wandelt 16bit unsigned nach ASCII
; Quelle ist in ACC1 (wird überschrieben)
; Ziel ist in FSR
; benutze Register: ACC2 
;===================================================
dutoa
	movwf	FSR
	movlw	0x30		; ASCII 0
	movwf	INDF
	movlw	0x1
	movwf	ACC2_0
	movlw	0x86
	movwf	ACC2_H
	movlw	0xa0		; 0x186A0 = 100.000
	movwf	ACC2_L

dutoa1					; 100000er-Schleife
	call	dSubAcc		; 16Bit-Subtraktion
	btfss	STATUS,C
	goto 	dutoa2
	incf	INDF,F
	goto 	dutoa1
dutoa2					; 
	call	dAddAcc		; einmal zuviel subtrahiert
	incf	FSR,f			; nächste Stelle im Display-Ram



	movlw	0x30		; ASCII 0
	movwf	INDF
	clrf	ACC2_0
	movlw	HIGH d'10000'
	movwf	ACC2_H
	movlw	LOW d'10000'
	movwf	ACC2_L

dutoa3					; 10000er-Schleife
	call	dSubAcc		; 16Bit-Subtraktion
	btfss	STATUS,C
	goto 	dutoa4
	incf	INDF,F
	goto 	dutoa3
dutoa4
	call	dAddAcc		; einmal zuviel subtrahiert

	call	lutoa_sub



	return



;===================================================
;  TAST-SCAN
;===================================================

TastScan
	call 	TastScan1
	movfw	TEMP			; Ergebnis 1. Scan... 
	movwf	TEMP1			; ... zwischenspeichern
	movlw	1				; 30msec
	movwf	TIM1_10MS
TstScLoop
	bsf	INTCON,GIE
	movf	TIM1_10MS,F
	btfss	STATUS,Z

	goto	TstScLoop

	call 	TastScan1

	movfw	TEMP
	subwf	TEMP1,W
	btfss	STATUS,Z		; Z= 2 identische Scans
	goto	EndScan			; 2 Scans lieferten keine gleichen Ergebnisse

	movfw	TASTE_AKT
	andlw	0xf
	subwf	TEMP,W
	btfss	STATUS,Z		; Z=Alte Taste noch immer gedrückt-> Repeat
	goto	NeueTaste
RepeatTaste
	bsf	TASTE_AKT,6
	goto	EndScan

NeueTaste

	movfw	TEMP
	movwf	TASTE_AKT	
	bsf	TASTE_AKT,7		; = Flag "Taste gedrückt"

EndScan
	return

;-------------------
TastScan1		; setzt nacheinander die drei Ausgänge

	movlw	0x0f
	iorwf	PORT_TASTOUT,f		; Alle Scan-Lines High
	
	movlw	0x0
	movwf	TEMP
	bcf	PORT_TASTOUT,0		; Bit0 für ScanOut auf L
	call	PortTastOut	
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast
	
	movlw	0x03
	movwf	TEMP
	bsf	PORT_TASTOUT,0		; Bit0 für ScanOut auf L
	bcf	PORT_TASTOUT,1
	call	PortTastOut	
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	movlw	0x06
	movwf	TEMP
	bsf	PORT_TASTOUT,1		; Bit0 für ScanOut auf L
	bcf	PORT_TASTOUT,2
	call	PortTastOut	
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	movlw	0x09
	movwf	TEMP
	bsf	PORT_TASTOUT,2		; Bit0 für ScanOut auf L
	bcf	PORT_TASTOUT,3
	call	PortTastOut	
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	
	movlw	0
	movwf	TEMP
	movwf	TEMP1
EndTast
	addwf	TEMP,F
	return

;-------------------

CheckTastIn		; prüft die 3 Eingänge

	call	PortTastIn
	movlw	0x00
	btfss	PORT_TASTIN,2
	movlw	1
	btfss	PORT_TASTIN,1
	movlw	2
	btfss	PORT_TASTIN,0
	movlw	3
	iorlw	0		; Test WREG auf 0
	return	

;-----------------------

PortTastOut
	movfw	PORT_TASTOUT
	movwf	PORTD

;- ChipSelect generieren --

	movlw	0x6			; CS6 aktiv
	iorwf	PORTC,F

	movlw	0xf8			; CS6 inaktiv
	andwf	PORTC,F


	return

;-----------------------

PortTastIn
	bsf		3,5
	movlw	b'11111111'	; Alles Eingänge
	movwf	TRISD
	bcf	3,5
	bcf	3,6
	movlw	0x5
	iorwf	PORTC,F		; CS5 generieren
	movfw	PORTD
	movwf	PORT_TASTIN

	movlw	0xf0		; CS5 weg
	andwf	PORTC,F

	bsf		3,5
	movlw	b'00000000'	; Alles Ausgänge
	movwf	TRISD
	bcf	3,5
	bcf	3,6

	return
;===================================================
;  HexScan
;===================================================

HexScan
	call	PortTastIn
	swapf	PORT_TASTIN,W
	xorlw	0xf	; wg. Invertierung durch Pull-Ups
	andlw	0xf
	movwf	HEX_AKT	
	subwf	HEX_LAST,W
	btfsc	STATUS,Z
	return				; keine Änderung
	movfw	HEX_AKT
	movwf	HEX_LAST	


	movlw	0x0
	subwf	HEX_AKT,w
	btfss	STATUS,Z
	goto	TestHex1
	return

TestHex1
	movlw	0x1
	subwf	HEX_AKT,w
	btfss	STATUS,Z
	goto	TestHex2
;	movlw	1
;	movwf	STEP_DATENLESEN
	return
TestHex2
	movlw	0x2
	subwf	HEX_AKT,w
	btfss	STATUS,Z
	goto	TestHex3
;	movlw	1
;	movwf	STEP_DAUERBETRIEB
	return
TestHex3	
;	call	DispKeineFunktion

	return



;===================================================
;  Wait10ms
;  Übergabe: keine
; Unterprogramm kehrt nach 10msec zurück

Wait10ms
	movlw	1
	movwf	TIM1_10MS
WaitLoop
	movf	TIM1_10MS,F
	btfss	STATUS,Z
	goto	WaitLoop
	return


;===================================================

;===================================================
;  ADconv
;  Übergabe: keine
;  wandelt Kanal 1 und 2, 
;===================================================
ADconv
;--------  HEX-Drehschalters = 0 ? -------------

;	movfw	HEX_AKT
;	andlw	0xf
;	sublw	0
;	btfss	STATUS,Z
;	return
; --- Kanal 0 -> ROT ----

	bcf	ADCON0, CHS0	
	bcf	ADCON0, CHS1	
	bsf	ADCON0, GO_DONE		; Start
ADLoop1
	btfsc	ADCON0, GO_DONE
	goto	ADLoop1

	movfw	ADRESH
	movwf	TEMP			; AD-Wert nach TEMP

	subwf	AD0,W
	btfsc	STATUS,Z
	goto	WandleKanal_1
	bsf		AD_STATUS,0			; Flag , neuer WERT da
	movfw	TEMP
	movwf	AD0

;----- Kanal 1 gruen -----
WandleKanal_1
	bsf	ADCON0, CHS0		; kanal 1->Grün, 
	call	delay_ms1

	bsf	ADCON0, GO_DONE		; Start
ADLoop2
	btfsc	ADCON0, GO_DONE
	goto	ADLoop2

	movfw	ADRESH
	movwf	TEMP			

	subwf	AD1,W
	btfsc	STATUS,Z
	goto	WandleKanal_2
	bsf		AD_STATUS,1			; Flag , neuer WERT da
	movfw	TEMP
	movwf	AD1

;----- Kanal 2 blau -----
WandleKanal_2
	bcf	ADCON0, CHS0		; kanal 1->Grün, 
	bsf	ADCON0, CHS1		; kanal 1->Grün, 
	call	delay_ms1

	bsf	ADCON0, GO_DONE		; Start
ADLoop3
	btfsc	ADCON0, GO_DONE
	goto	ADLoop3

	movfw	ADRESH
	movwf	TEMP			

	subwf	AD2,W
	btfsc	STATUS,Z
	goto	EndAD
	bsf		AD_STATUS,2			; Flag , neuer WERT da
	movfw	TEMP
	movwf	AD2


EndAD
	bcf		ADCON0, CHS0	
	bcf		ADCON0, CHS1	


	return









;================ D I S P L A Y =================================

; ***************************************************************************
display
;	btfss	DISP_STAT,3		; soll ausgegeben werden?
;	return

	bcf		DISP_STAT,3
	btfss	DISP_STAT,6		; Anzeigen oder ausschalten
	call	display_on

; welche Zeile soll geschrieben werden?

	btfsc	DISP_Z_FLAG,0		; Zeile 1
	call	display_z1
	btfsc	DISP_Z_FLAG,1		; Zeile 2
	call	display_z2
	btfsc	DISP_Z_FLAG,2		; Zeile 3
	call	display_z3
	btfsc	DISP_Z_FLAG,3		; Zeile 4
	call	display_z4
	return

display_z1
	movlw	80		; DD-Adresse im Display für Zeile 1
	call	display_zout
	bcf		DISP_Z_FLAG,0
	return

display_z2
	movlw	0xc0
	call	display_zout
	bcf		DISP_Z_FLAG,1
	return
display_z3
	movlw	90		; DD-Adresse im Display für Zeile 3
	call	display_zout
	bcf		DISP_Z_FLAG,2
	return
display_z4
	movlw	0xd0		; DD-Adresse im Display für Zeile 4
	call	display_zout
	bcf		DISP_Z_FLAG,3
	return



; ***************************************************************************
; ***************************************************************************
display_zout


	bcf	PORTD,2		; RS = 0
	bcf	PORTD,0		; R/W = 0

	call	display_write

; hier 16 Bytes füllen

	movlw	10		; 16 Zeichen ausgeben
	movwf	DISP_CNT	
	
	movlw	50					; Zeilenbuffer im Ram
	movwf	04					;!Indir Addr
	
display_zout0			; Display-Zeile beschreiben
	bsf	PORTD,2
	bcf	PORTD,0
	movf	0,0
	call	display_write
	incf	04,1
	decfsz	DISP_CNT,1
	goto	display_zout0
	return

display_off
	call	display_clr
	call	delay_ms
	movlw	b'00001000'	; Display OFF
	bcf	PORTD,2
	bcf	PORTD,0
	call	display_write
	return

display_clr
	movlw	b'00000001'	; Clear Display
	bcf	PORTD,2
	bcf	PORTD,0
	call	display_write
	return
	
display_on
	movlw	b'00001100'
	bcf	PORTD,2
	bcf	PORTD,0
	call	display_write
	return

display_CB
	movlw	b'00001101'	; Cursor blinken lassen
	bcf		PORTD,2
	bcf		PORTD,0
	call	display_write
	return

display_init
	call	Wait10ms
	call	Wait10ms

	movlw	b'11111000'	; Bit 9.0..9.2 löschen
	andwf	PORTD,F
	
	movlw	3F
	call	display_write

	call	Wait10ms

	movlw	3F
	call	display_write

	call	delay_ms

	movlw	3F
	call	display_write

	movlw	b'00111000'	; ab hier SET-Mode
	call	display_write

	movlw	b'00001100'	; Display ON
	call	display_write
	
	movlw	b'00000001'	; Display CLEAR
	call	display_write

	movlw	b'00000110'	; ENTER Mode SET Increment
	call	display_write
	return

;***************************************************************************
display_write
	movwf	TEMP
	clrf	PORTB
	bcf		PORTE,2
	bcf		PORTA,4

	btfsc	TEMP,0
	bsf		PORTA,4
	btfsc	TEMP,1
	bsf		PORTE,2
	btfsc	TEMP,2
	bsf		PORTB,5
	btfsc	TEMP,3
	bsf		PORTB,4
	btfsc	TEMP,4
	bsf		PORTB,3
	btfsc	TEMP,5
	bsf		PORTB,2
	btfsc	TEMP,6
	bsf		PORTB,1
	btfsc	TEMP,7
	bsf		PORTB,0

	bsf	PORTD,1
	nop
	nop
	bcf	PORTD,1		; Wert übernehmen

	call delay_ms
	return
	
;***************************************************************************
ClearDispBuff		; Display buffer (0x50) löschen
	movlw	0x10
	movwf	TEMP1
	movlw	0x50
	movwf	FSR
	movlw	0x20	; Leerzeichen
CDP
	movwf	INDF
	incf	FSR,f
	decfsz	TEMP1,F
	goto	CDP

	return

;============================================================
; delay_ms
; kehrt anch 1 msec zurück
;============================================================
delay_ms			; delay ca. 1ms
;	clrf	DELAY
	movlw	0x40
	movwf	DELAY
delay_ms1
;	clrwdt
	nop
	decfsz	DELAY,F
	goto	delay_ms1
	return

;============================================================
; Datenbereich
;=============================================================
; ***************************************************************************
;	org	0x7d0
; ***************************************************************************



	org 0x700

DatenKeineFunktion
	addwf	2,1

	retlw	" "
	retlw	"K"
	retlw	"e"
	retlw	"i"
	retlw	"n"
	retlw	"e"
	retlw	" "
	retlw	"F"
	retlw	"u"
	retlw	"n"
	retlw	"k"
	retlw	"t"
	retlw	"i"
	retlw	"o"
	retlw	"n"
	retlw	" "


BinToHexTab
	addwf	2,1

	retlw	"0"
	retlw	"1"
	retlw	"2"
	retlw	"3"
	retlw	"4"
	retlw	"5"
	retlw	"6"
	retlw	"7"
	retlw	"8"
	retlw	"9"
	retlw	"A"
	retlw	"B"
	retlw	"C"
	retlw	"D"
	retlw	"E"
	retlw	"F"


VersionData
	addwf	2,1

	retlw	"V"
	retlw	"1"
	retlw	"."
	retlw	"0"
	retlw	"0"
	retlw	" "
	retlw	"/"
	retlw	" "


	retlw	"2"
	retlw	"2"
	retlw	"."
	retlw	"0"
	retlw	"9"
	retlw	"."
	retlw	"0"
	retlw	"5"

MainParamData
	addwf	2,1

	retlw	"R"
	retlw	"0"
	retlw	"0"
	retlw	"0"
	retlw	" "
	retlw	"G"
	retlw	"0"
	retlw	"0"


	retlw	"0"
	retlw	" "
	retlw	"B"
	retlw	"0"
	retlw	"0"
	retlw	"0"
	retlw	" "
	retlw	" "



;*******************************************************************************
;********************** EEPROM Bereich *****************************************
;*******************************************************************************
;	org 2100	; EEPROM Bereich

;	DE	'V','2','F','A','0',' ','1','4','.','0','4','.','2','0','0','5'



;%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	END
