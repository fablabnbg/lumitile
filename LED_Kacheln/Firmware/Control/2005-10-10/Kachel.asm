	Processor 16F914

#include P16F914.inc   
;******************************************************************
; History
;******************************************************************
; Version 1.21	03.10.2005 Ga
; - Gateway für PC eingebaut
 
; Version 1.22	05.10.2005 Ga
; - Rundungsfehler (?) beseitigt, zählte bei hohen Farbunterschieden immer +2 bzw -2

; Version 1.23	10.10.2005 Ga
; - Default-Programm in Wahlschalterstellung 1 (Wiedergabe-Modus) ist jetzt Programm 4,
;   das individuelle erstellte Farbverlaufprogramm 
; - Fehler im Wiedergabemodus nach Reset (kein automatischer Anlauf) beseitigt

;******************************************************************
; Definitions
;******************************************************************
;

;------------------------------------------------------------------
; Register Definitions
;
PCLATH_TEMP	equ	0x21 ; Stack für PLATH-Register

TIM1_10MS	equ 0x22
TIM2_10MS	equ	0x23

AD0				equ	0x24	; Rot
AD1				equ	0x25	; Grün
AD2				equ	0x26	; Blau
AD3				equ	0x27	; Speed


TASTE_AKT		equ	0x28	; aktuell gedrückte Taste, Bit 7 = 1 wenn 
							; Drücken entdeckt, bei Repeat Bit 6=1
TASTE_LAST		equ	0x29	; zuletzt gedrückte Taste
TASTE_IDX		equ	0x2a	; Wert, der 10%, 30%, 40% usw in eine Zahl 0,1,2 usw wandelt
							; wird von TAST_DISPATCH beschrieben


TEMP			equ 0x2b	; temporäre Speicherplatz, nur in einem
					; call geschützt

TEMP1			equ 0x2c
TEMP2			equ 0x2d

SEKUNDEN_WERT		equ 0x2e	; Zeit bis zum nöchsten Farbtripel aus Tabelle
SEKUNDEN_COUNT		equ 0x2f	; Zeit bis zum nöchsten Farbtripel aus Tabelle

DISP_CNT		equ	0x30	; enthält die ANzahl auf Disp zu schreibende Zeichen
DISP_Z_FLAG		equ	0x31	; Bit0-> Zeile 1
							; Bit1-> Zeile 2 usw.
DISP_STAT		equ	0x32	; Bit3-> DisplayAusgabe steht an

ACC1_0			equ	0x33	;Rechenregister
ACC1_H			equ	0x34	;Rechenregister
ACC1_L			equ	0x35

ACC2_0			equ	0x36	;Rechenregister
ACC2_H			equ	0x37
ACC2_L			equ	0x38

TEMPFLAG		equ	0x39	; Temporäres Bitregister

DELAY			equ	0x3a
							; Bit6-> Anzeige On/Off 
TEMP3			equ	0x3b
TEMP4			equ	0x3c
TEMP5			equ	0x3d
AD_STATUS		equ 0x3f	; Bit 0-2 --> Neuer AD-Wert Kanal 0-2

FARBTAB			equ 0xA0	; 5 Farbtripel zum anfahren + Zeit
					; !!!! Registerbank 1 !!!
TASTBUFF		equ 0x40

DISP_BUFF		equ	0x50	; Display Buffer, 16 chars!!

ITOA_BUFF		equ	0x60	; Achtung!! 6 Bytes lang!!!!

TIMECOUNT		equ	0x66
HEX_AKT			equ	0x68	; Bit 0-3-> aktuelle Hex-Schalter Stellung
HEX_LAST		equ	0x69	; Bit 7=1-> Schalterstellung geändert

FARB_IDX_AKT		equ	0x6a
FARB_IDX_NEXT		equ	0x6b
FARB_COUNT		equ	0x6c
FARB_SPEICHER_IDX	equ	0x6d
TASTBUFF_IDX		equ	0x6e
RX_COUNT			equ	0x6f
W_TEMP			equ	0x7e ; Stack für W-register im Interrupt
STATUS_TEMP		equ	0x7f ; stack für STATUS im Interrupt



;===================================
PORT_TASTOUT	equ	PORTB	; TastaturSCan Out
PORT_TASTIN		equ	PORTD	; TastaturScan IN
ETX				equ 0x3
STX				equ 0x2



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


;,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
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

	bcf	STATUS,RP0
	bcf	STATUS,RP1


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
	movlw	b'11101111'	; Alles Eingänge
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
	movlw	b'10010000'		; SerialPort Enable. CREN ena (Continues Receive), 8Bit receive (wg. PC)
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

	movlw	0
	movwf	HEX_AKT
	movwf	FARB_SPEICHER_IDX

	movlw	0xC0		; Eigenes Farbprogramm
	call	EEpromRead
	clrf	FARB_IDX_AKT
	clrf	FARB_IDX_NEXT
	incf	FARB_IDX_NEXT,F
	clrf	SEKUNDEN_COUNT
	clrf	TIM2_10MS
	clrf	TIMECOUNT


	call	ClearTastBuff



;==========MainLoop

main
	call	HexScan				; HEx-Schalter nach HEX_AKT einlesen
	call 	TastScan			; Tastatur-Sac, Wert nach TASTE_AKT
	call 	ADconv				; AD.Wandlung beider Kanäle, Wert nach AD0 und AD1
	call	HEX1_Dispatch		; Automatik-Modus
	call	HEX2_Dispatch		; Gateway Funktion
	call	TastDispatch
;	call	display
	call	AdDispatch			; Wenn sich einer der D-Wert geändert hat

;	movlw	#2
;	movwf	TIM1_10MS

MainWaitLoop	
;	movf	TIM1_10MS,F
;	btfss	STATUS,Z
;	goto	MainWaitLoop


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
; DispGateway
;===================================================
DispGateway
	clrf	TEMP			; als ByteCount
	movlw	DISP_BUFF
	movwf	FSR			; 4
DispGateway_1
	movlw	HIGH GatewayData
	movwf	PCLATH
	movfw	TEMP
	call	GatewayData
	clrf	PCLATH
	movwf	INDF
	incf	FSR,F
	incf	TEMP,F
	btfss	TEMP,4
	goto	DispGateway_1
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
	bsf	DISP_Z_FLAG,0
	call	display

	call	ClearDispBuff

	movfw	AD0
	movwf	TEMP
	movlw	DISP_BUFF+0
	movwf	FSR
	call	sutoa

	movfw	AD1
	movwf	TEMP
	movlw	DISP_BUFF+4
	movwf	FSR
	call	sutoa

	movfw	AD2
	movwf	TEMP
	movlw	DISP_BUFF+d'8'
	movwf	FSR
	call	sutoa


	movfw	AD3
	movwf	TEMP
	movlw	DISP_BUFF+d'12'
	movwf	FSR
	call	sutoa


	bsf	DISP_Z_FLAG,1
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
	movfw	INDF
	movwf	TEMP3		; gelesenes Byte

	incf	FSR,F
	movfw	FSR
	movwf	TEMP		; Leseadresse speichern
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
	
	movfw	HEX_AKT
	andlw	0xf
	sublw	2			; Hex =2 --> Gateway-Funktion
	btfsc	STATUS,Z
	return


;--------  HEX-Drehschalters = 0 ? -------------

	movfw	HEX_AKT
	andlw	0xf
	sublw	0
	btfss	STATUS,Z
	return
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
; Dispatch_Hex1 für Drehschalter in STellung 1 (Automatik-Modus)
;===================================================
HEX1_Dispatch
	

;--------  HEX-Drehschalters = 1 ? -------------

	movfw	HEX_AKT
	andlw	0xf
	sublw	1
	btfss	STATUS,Z
	return

	movf	TIM2_10MS
	btfss	STATUS,Z
	return

	movfw	AD3		; Speed
	movwf	TIM2_10MS	

	decf	SEKUNDEN_COUNT,F
	btfss	STATUS,Z
	return

	movfw	SEKUNDEN_WERT
	movwf	SEKUNDEN_COUNT


	
	incf	TIMECOUNT,F
;	btfss	TIMECOUNT,7	; erweitert auf 8 bit mit nächster Zeile
	btfss	STATUS,Z
	goto	NormalWeiter

	clrf	TIMECOUNT

	incf	FARB_IDX_AKT,F
	incf	FARB_IDX_NEXT,F

; Ab hier neuen Farbwert ansteuern
; erst Index evtl. auf 0 setzen
	movlw	0x10
	subwf	FARB_IDX_AKT,W
	btfsc	STATUS,Z
	clrf	FARB_IDX_AKT

	movlw	0x10
	subwf	FARB_IDX_NEXT,W
	btfsc	STATUS,Z
	clrf	FARB_IDX_NEXT

; Wenn Zeit für FARB_IDX_NEXT = 7F, Dann FARB_IDX_NEXT = 0 (7F = Ende)
	movlw	4
	movwf	TEMP
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movfw	FARB_IDX_NEXT
	movwf	ACC2_L
	call	AddAccRep	
	movlw	FARBTAB
	addwf	ACC1_L,W
	addlw	3				; Zeit-Index
	movwf	FSR
	bsf	STATUS,RP0			; Bank 1
	movfw	INDF
	bcf	STATUS,RP0			; Bank 0
	sublw	0x7f
	btfss	STATUS,Z
	goto	ZEIT_FidxAktholen
	clrf	FARB_IDX_NEXT

; Zeit in SEKUNDEN_WERT transferieren
ZEIT_FidxAktholen
	movlw	4
	movwf	TEMP
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movfw	FARB_IDX_AKT
	movwf	ACC2_L
	call	AddAccRep	

; neue Farbe in Acc
	movlw	FARBTAB
	addwf	ACC1_L,W
	addlw	3				; Zeit-Index
	movwf	FSR
	bsf	STATUS,RP0			; Bank 1
	movfw	INDF
	bcf	STATUS,RP0			; Bank 0
	movwf	SEKUNDEN_WERT
	movwf	SEKUNDEN_COUNT
	sublw	0x7f
	btfss	STATUS,Z
	goto	Weiter_FIDX
	clrf	FARB_IDX_AKT
	goto	ZEIT_FidxAktholen
Weiter_FIDX
	call	LadeSekundenWert
	movf	SEKUNDEN_WERT,F
	btfss	STATUS,Z
	goto	NormalWeiter

	movlw	1
	movwf	TIM2_10MS
	movwf	SEKUNDEN_COUNT
	movlw	0x7F
	movwf	TIMECOUNT

; hier noch Index auf Farbtab Akt und Next ändern

NormalWeiter	; 
	clrf	FARB_COUNT
	call	FarbeSteppen
	movwf	AD0
	
	incf	FARB_COUNT,F
	call	FarbeSteppen
	movwf	AD1
	
	incf	FARB_COUNT,F
	call	FarbeSteppen
	movwf	AD2


	call	SendNewColor
	call	DispMainParam


	
NormalDispatchEnd

	return


;===================================================
; Dispatch_Hex1 für Drehschalter in Stllung 2 (Gateway)
;===================================================
HEX2_Dispatch
	

;--------  HEX-Drehschalters = 2? -------------

	movfw	HEX_AKT
	andlw	0xf
	sublw	2
	btfss	STATUS,Z
	return

	btfsc	PIR1, RCIF
	goto	RecByteAvailable	
	

	btfss	RCSTA, OERR
	return
	clrf	RX_COUNT
	bcf		RCSTA, CREN	; Reset evtl. Overflow
	bsf		RCSTA, CREN
	return

RecByteAvailable

	bcf		PIR1, RCIF  
	movf	TIM2_10MS,F	; Timeout?
	btfsc	STATUS,Z
	clrf	RX_COUNT

	movlw	2
	movwf	TIM2_10MS	; Timeout-Counter (30msec)

	
	movlw	TASTBUFF
	addwf	RX_COUNT,W
	movwf	FSR

	movfw	RCREG
	movwf	TEMP

	movwf	INDF
	incf	RX_COUNT,F
	movfw	RX_COUNT
	sublw	0x6
	btfss	STATUS,Z
	return	
; gerade Empfangenes Byte = ETX?

	movfw	TEMP
	sublw	ETX
	btfsc	STATUS,Z
	goto	SendToKachel
	clrf	RX_COUNT	
	return
SendToKachel
	movfw	TASTBUFF+2
	movwf	AD0
	movfw	TASTBUFF+3
	movwf	AD1
	movfw	TASTBUFF+4
	movwf	AD2
	
	call	SendNewColor
	return
;===================================================

FarbeSteppen

	movlw	4
	movwf	TEMP
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movfw	FARB_IDX_AKT
	movwf	ACC2_L
	call	AddAccRep	

; neue Farbe in Acc
	movlw	FARBTAB
	addwf	ACC1_L,W
	addwf	FARB_COUNT,W
	movwf	FSR
	bsf	STATUS,RP0			; Bank 1
	movfw	INDF
	bcf	STATUS,RP0			; Bank 0
	movwf	TEMP2	; Farbe aKT
	
; ------ NÄCHSTE fARBE	
	movlw	4
	movwf	TEMP
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movfw	FARB_IDX_NEXT
	movwf	ACC2_L
	call	AddAccRep	

; neue Farbe in Acc
	movlw	FARBTAB
	addwf	ACC1_L,W
	addwf	FARB_COUNT,W
	movwf	FSR
	bsf	STATUS,RP0			; Bank 1

	movfw	INDF
	bcf	STATUS,RP0			; Bank 0
	movwf	TEMP3	; Farbe Next

	bcf	TEMPFLAG,5	; Merker ob Differnez addiert o. subtr. werden muß
		

	movfw	TEMP2
	subwf	TEMP3,W
	btfsc	STATUS,C
	goto	KeinSwap

	movfw	TEMP3		; TEMP2 ist größer TEMP3
	subwf	TEMP2,W
	bsf	TEMPFLAG,5
KeinSwap

	movwf	ACC2_L
	clrf	ACC2_H
	clrf	ACC1_L
	clrf	ACC1_H
	movfw	TIMECOUNT
	movwf	TEMP
	call	AddAccRep
;	rlf	ACC1_L,F
;	rlf	ACC1_H,F
	
	
	movfw	ACC1_H
	btfss	TEMPFLAG,5
	goto	AddDifferenz
	subwf	TEMP2,W
	goto EndDifferenz
AddDifferenz
	addwf	TEMP2,W
EndDifferenz

	return







LadeSekundenWert

; Zeit in SEKUNDEN_WERT transferieren
	movlw	4
	movwf	TEMP
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movfw	FARB_IDX_AKT
	movwf	ACC2_L
	call	AddAccRep	

; neue Farbe in Acc
	movlw	FARBTAB
	addwf	ACC1_L,W
	addlw	3				; Zeit-Index
	movwf	FSR
	bsf	STATUS,RP0			; Bank 1
	movfw	INDF
	bcf	STATUS,RP0			; Bank 0
	movwf	SEKUNDEN_WERT
	movwf	SEKUNDEN_COUNT


	return






;===================================================
; TastDispatch
;===================================================

TastDispatch
	
	movfw	HEX_AKT
	andlw	0xf
	sublw	2			; Hex =2 --> Gateway-Funktion
	btfsc	STATUS,Z
	return


;--------  HEX-Drehschalters = 1 ? -------------



	movfw	HEX_AKT
	andlw	0xf
	sublw	1
	btfss	STATUS,Z
	goto	TestHex_0

	btfss	TASTE_AKT,7
	return

	bcf	TASTE_AKT,7
	bcf	TASTE_AKT,6
	movfw	TASTE_AKT

	movlw	1
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_2

	call 	Farbprogramm_1
	goto	EndTastDispatch

TestTaste_2
	movlw	2
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_3

	call 	Farbprogramm_2
	goto	EndTastDispatch


TestTaste_3
	movlw	3
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_4

	call 	Farbprogramm_3
	goto	EndTastDispatch
TestTaste_4
	movlw	4
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_5

	call 	Farbprogramm_4
	goto	EndTastDispatch
TestTaste_5

	goto	EndTastDispatch


;--------------------- Stellung HEX=0---------------
TestHex_0
	movfw	HEX_AKT
	andlw	0xf
	sublw	0
	btfss	STATUS,Z
	goto	EndTastDispatch

	btfss	TASTE_AKT,7
	return

 	bcf	TASTE_AKT,7
	bcf	TASTE_AKT,6
	movfw	TASTE_AKT

	sublw	0
	btfsc	STATUS,Z
	return	

	movfw	TASTE_AKT
	sublw	0x9
	btfss	STATUS,C
	goto	TestTaste_null

;Taste 1-9
	movfw	TASTE_AKT
	call	AddTastBuff
	goto	EndTastDispatch

TestTaste_null

	movlw	0xa
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_plus
	movlw	0
	call	AddTastBuff

	goto	EndTastDispatch


TestTaste_plus
	movlw	"+"
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	TestTaste_C

	call	AtoiDec
	movwf	ACC2_L
	clrf	ACC1_L
	clrf	ACC1_H
	clrf	ACC2_H
	movlw	4
	movwf	TEMP
	call	AddAccRep
	movlw	FARBTAB
	addwf	ACC1_L,W
	movwf	FSR
	movfw	AD0				; rot
	bsf	STATUS,RP0			; Bank 1
	movwf	INDF
	bcf	STATUS,RP0			; Bank 0
	incf	FSR,F

	movfw	AD1				; grün
	bsf	STATUS,RP0			; Bank 1
	movwf	INDF
	bcf	STATUS,RP0			; Bank 0
	incf	FSR,F

	movfw	AD2				; blau
	bsf	STATUS,RP0			; Bank 1
	movwf	INDF
	bcf	STATUS,RP0			; Bank 
	incf	FSR,F

	movfw	AD3				; Speed
	bsf	STATUS,RP0			; Bank 1
	movwf	INDF
	bcf	STATUS,RP0			; Bank 
	incf	FSR,F



	goto	EndTastDispatch

TestTaste_C
	movlw	0x23
	subwf	TASTE_AKT,W
	btfss	STATUS,Z
	goto	EndTastDispatch			; bzw. zu Test_nächste Taste

	call	EEpromWrite

	goto	EndTastDispatch

EndTastDispatch
	return

;---------------------------
AtoiDec		; wandelt TasBuff in Integer und decrementiert um
	movlw	0x30
	subwf	TASTBUFF,W
	movwf	TEMP
	clrf	ACC1_L

	clrf	ACC1_H
	movlw	0xa
	movwf	ACC2_L
	clrf	ACC2_H
	call	AddAccRep
	movlw	0x30
	subwf	TASTBUFF+1,W
	decf	ACC1_L,F	; !!!!
	addwf	ACC1_L,W
	return
;---------------------------
AddTastBuff
	addlw	0x30
	movwf	TEMP

	movfw	TASTBUFF_IDX
	sublw	2
	btfss	STATUS,Z
	goto	NoIdxReset
	clrf	TASTBUFF_IDX
	call	ClearTastBuff
NoIdxReset
	movfw	TASTBUFF_IDX
	addlw	TASTBUFF
	movwf	FSR

	movfw	TEMP
	movwf	INDF	
	incf	TASTBUFF_IDX,F
	movlw	TASTBUFF
	call	MoveToDispBuff
	bsf	DISP_Z_FLAG,2
	call	display
	
	return

;---------------------------

Farbprogramm_1
	movlw	0x0
	call	EEpromRead
		
	clrf	FARB_IDX_AKT
	clrf	FARB_IDX_NEXT
	incf	FARB_IDX_NEXT,F
	clrf	SEKUNDEN_COUNT
	clrf	TIM2_10MS
	clrf	TIMECOUNT



	return


Farbprogramm_2
	movlw	0x40
	call	EEpromRead
	clrf	FARB_IDX_AKT
	clrf	FARB_IDX_NEXT
	incf	FARB_IDX_NEXT,F
	clrf	SEKUNDEN_COUNT
	clrf	TIM2_10MS
	clrf	TIMECOUNT

	return




Farbprogramm_3
	movlw	0x80
	call	EEpromRead
	clrf	FARB_IDX_AKT
	clrf	FARB_IDX_NEXT
	incf	FARB_IDX_NEXT,F
	clrf	SEKUNDEN_COUNT
	clrf	TIM2_10MS
	clrf	TIMECOUNT
	return

Farbprogramm_4
	movlw	0xC0
	call	EEpromRead
	clrf	FARB_IDX_AKT
	clrf	FARB_IDX_NEXT
	incf	FARB_IDX_NEXT,F
	clrf	SEKUNDEN_COUNT
	clrf	TIM2_10MS
	clrf	TIMECOUNT
	return



;

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
	movfw	HEX_AKT
	andlw	0xf
	sublw	2				; Hex = 2 --> Gateway-Funktion
	btfsc	STATUS,Z
	return


	call 	TastScan1
	movfw	TEMP			; Ergebnis 1. Scan... 
	movwf	TEMP1			; ... zwischenspeichern
	
	movfw	TASTE_AKT
	andlw	0xf
	subwf	TEMP,F	
	btfsc	STATUS,Z
	goto	EndScan

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

	movlw	0x0
	andwf	PORT_TASTOUT,f		; Alle Scan-Lines High
	
	movlw	0x0
	movwf	TEMP
	movlw	0x1
	iorwf	PORT_TASTOUT,F		; Bit0 für ScanOut auf L
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast
	
	movlw	0x0
	andwf	PORT_TASTOUT,f		; Alle Scan-Lines High
	movlw	0x04
	movwf	TEMP
	movlw	0x2
	iorwf	PORT_TASTOUT,F		; Bit0 für ScanOut auf L
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	movlw	0x0
	andwf	PORT_TASTOUT,f		; Alle Scan-Lines High
	movlw	0x08
	movwf	TEMP
	movlw	0x4
	iorwf	PORT_TASTOUT,F		; Bit0 für ScanOut auf L
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	movlw	0x0
	andwf	PORT_TASTOUT,f		; Alle Scan-Lines High
	movlw	0xC
	movwf	TEMP
	movlw	0x8
	iorwf	PORT_TASTOUT,F		; Bit0 für ScanOut auf L
	call	CheckTastIn
	btfss	STATUS,Z
	goto	EndTast

	
	movlw	0
	movwf	TEMP
	movwf	TEMP1
EndTast
	addwf	TEMP,F
	movlw	HIGH TasteUmsetzen
	movwf	PCLATH

	movfw	TEMP
	
	call	TasteUmsetzen
	movwf	TEMP
	movwf	TEMP1

	return

;-------------------

CheckTastIn		; prüft die 3 Eingänge

	movlw	0x00
	btfsc	PORT_TASTIN,7
	movlw	1
	btfsc	PORT_TASTIN,6
	movlw	2
	btfsc	PORT_TASTIN,5
	movlw	3
	btfsc	PORT_TASTIN,4
	movlw	4
	iorlw	0		; Test WREG auf 0
	return	

;-----------------------

;===================================================
;  HexScan
;===================================================

HexScan
	movfw	PORTC
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

	call	ClearDispBuff
	bsf	DISP_Z_FLAG,2
	call	display
	bsf	DISP_Z_FLAG,1
	call	display
	clrf	TASTBUFF_IDX
	call	ClearTastBuff
	return

TestHex1
	movlw	0x1
	subwf	HEX_AKT,w
	btfss	STATUS,Z
	goto	TestHex2

	clrf	TIM2_10MS
	clrf	TIMECOUNT

	clrf	FARB_IDX_AKT
	movlw	1
	movwf	FARB_IDX_NEXT


	call	LadeSekundenWert


	bsf	STATUS,RP0
	movfw	FARBTAB
	bcf	STATUS,RP0
	movwf	AD0

	bsf	STATUS,RP0
	movfw	FARBTAB+1
	bcf	STATUS,RP0
	movwf	AD1


	bsf	STATUS,RP0
	movfw	FARBTAB+2
	bcf	STATUS,RP0
	movwf	AD2

	call	SendNewColor
	call	DispMainParam

	clrf	TASTBUFF_IDX


;	movlw	1
;	movwf	STEP_DATENLESEN

	clrf	TIMECOUNT
	call	ClearDispBuff
	bsf	DISP_Z_FLAG,2
	call	display

	return
TestHex2
	movlw	0x2
	subwf	HEX_AKT,w
	btfss	STATUS,Z
	goto	TestHex3
	call	ClearDispBuff
	bsf		DISP_Z_FLAG,1
	call	display
	bsf		DISP_Z_FLAG,2
	call	display
	call 	DispGateway
	clrf	RX_COUNT
	movfw	RCREG		; DUmmy zum Leeren des Rx-Fifos
	movfw	RCREG		; DUmmy zum Leeren des Rx-Fifos
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
	movfw	HEX_AKT
	andlw	0xf
	sublw	2			; Hex =2 --> Gateway-Funktion
	btfsc	STATUS,Z
	return



	movfw	HEX_AKT
	andlw	0xf
	sublw	0
	btfss	STATUS,Z
	goto	WandleKanal_3
; --- Kanal 0 -> ROT ----

	bcf	ADCON0, CHS0		; Kanal 0 -> rot
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
	bcf	ADCON0, CHS0		;  
	bsf	ADCON0, CHS1		; kanal 2-> Blau, 
	call	delay_ms1

	bsf	ADCON0, GO_DONE		; Start
ADLoop3
	btfsc	ADCON0, GO_DONE
	goto	ADLoop3

	movfw	ADRESH
	movwf	TEMP			

	subwf	AD2,W
	btfsc	STATUS,Z
	goto	WandleKanal_3
	bsf		AD_STATUS,2			; Flag , neuer WERT da
	movfw	TEMP
	movwf	AD2




;----- Kanal 3 Speed -----
WandleKanal_3
	bsf	ADCON0, CHS0		;  
	bsf	ADCON0, CHS1		; kanal 3->Speed, 
	call	delay_ms1

	bsf	ADCON0, GO_DONE		; Start
ADLoop4
	btfsc	ADCON0, GO_DONE
	goto	ADLoop4

	movfw	ADRESH

	movwf	TEMP			
	bcf		STATUS,C
	rrf		TEMP,F

;	movf	TEMP,F	; Wenn ADRESHH = 0, immer 1 laden
;	btfsc	STATUS,Z
;	bsf	TEMP,0		;

	movfw	TEMP

	subwf	AD3,W
	btfsc	STATUS,Z
	goto	EndAD
	bsf		AD_STATUS,3			; Flag , neuer WERT da
	movfw	TEMP
	movwf	AD3



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

;***************************************************************************
ClearTastBuff		; Display buffer (0x50) löschen
	movlw	0x10
	movwf	TEMP1
	movlw	TASTBUFF
	movwf	FSR
	movlw	0x20	; Leerzeichen
CTB
	movwf	INDF
	incf	FSR,f
	decfsz	TEMP1,F
	goto	CTB

	return

;============================================================
; EEpromWErite
; schreibt 64 Byte ab Adresse 0xA0 ins EEprom Adresse 0xC0
;============================================================

EEpromWrite
	movlw	FARBTAB
	movwf	TEMP		; SourceAdresse
	movlw	0xC0
	movwf	TEMP1		; TargetAdresse im EEprom
	movlw	d'64'
	movwf	TEMP2		; COunt
	BCF 	INTCON,GIE 	;Disable INTs.

EEPromWriteLoop
	BSF 	STATUS,RP1 	; Bank 3
	BSF 	STATUS,RP0
	BTFSC 	EECON1,WR 	;Wait for write
	GOTO $-1		;to complete

	BCF 	STATUS,RP1 	; Bank 0
	BCF 	STATUS,RP0
	MOVFW 	TEMP1		;Adresse im EEprom
	BSF 	STATUS,RP1 	; BANK 2
	
	MOVWF 	EEADRL 		;Address to write


	BCF 	STATUS,RP1 	; Bank 0
	BCF 	STATUS,RP0
	MOVFW 	TEMP		; Daten für EEprom
	movwf	FSR
	BSF 	STATUS,RP0	; Bank 1
	movfw	INDF
	BCF 	STATUS,RP0	; Bank 1
	BSF 	STATUS,RP1 	; BANK 2


	MOVWF 	EEDATL 		;to write
	BSF 	STATUS,RP0 	;Bank 3
	BCF 	EECON1,EEPGD 	;Point to DATA
	;memory
	BSF 	EECON1,WREN 	;Enable writes
	MOVLW 	0x55 ;
	MOVWF 	EECON2 		;Write 55h
	MOVLW 	0xAA 		;
	MOVWF 	EECON2 		;Write AAh
	BSF 	EECON1,WR 	;Set WR bit to
	;begin write
	BCF 	EECON1,WREN 	;Disable writes


	BCF 	STATUS,RP1 	;
	BCF 	STATUS,RP0
	incf	TEMP,F
	incf	TEMP1,F
	decfsz	TEMP2
	goto	EEPromWriteLoop 

	BSF 	INTCON,GIE 	;Enable INTs.

	return


;============================================================
; EEpromRead
; liest 64 Byte ab EEpromAdresse[TEMP]  nach Adresse 0xA0
;============================================================
EEpromRead
;	movlw	0xC0
	movwf	TEMP1		; TargetAdresse im EEprom
	movlw	FARBTAB
	movwf	TEMP		; SourceAdresse
	movlw	d'64'
	movwf	TEMP2		; COunt
EEPromReadLoop
	movfw	TEMP
	movwf	FSR
	movfw	TEMP1		; Adresse im EEprom
	BSF 	STATUS,RP1 ;
	BCF 	STATUS,RP0 ; Bank 2
	MOVWF 	EEADRL ; Address to read
	BSF 	STATUS,RP0 ; Bank 3
	BCF 	EECON1,EEPGD ; Point to Data
	; memory
	BSF 	EECON1,RD ; EE Read
	BCF 	STATUS,RP0 ; Bank 2
	MOVF 	EEDATL,W ; W = EEDATA
	BCF 	STATUS,RP1 	;
	BSF 	STATUS,RP0
	movwf	INDF
	BCF 	STATUS,RP0

	incf	TEMP,F
	incf	TEMP1,F
	decfsz	TEMP2
	goto	EEPromReadLoop 




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
	retlw	"2"
	retlw	"3"
	retlw	" "
	retlw	"/"
	retlw	" "


	retlw	"1"
	retlw	"0"
	retlw	"."
	retlw	"1"
	retlw	"0"
	retlw	"."
	retlw	"0"
	retlw	"5"

MainParamData
	addwf	2,1

	retlw	"r"
	retlw	"o"
	retlw	"t"
	retlw	" "
	retlw	"g"
	retlw	"r"
	retlw	" "


	retlw	" "
	retlw	"b"
	retlw	"l"
	retlw	" "
	retlw	" "
	retlw	"T"
	retlw	"e"
	retlw	"m"
	retlw	"p"

GatewayData
	addwf	2,1

	retlw	" "
	retlw	" "
	retlw	" "
	retlw	" "
	retlw	"G"
	retlw	"a"
	retlw	"t"
	retlw	"e"


	retlw	"w"
	retlw	"a"
	retlw	"y"
	retlw	" "
	retlw	" "
	retlw	" "
	retlw	" "
	retlw	" "


TasteUmsetzen
	addwf	2,1

	retlw	0
	retlw	"*"
	retlw	0xa		; die Null!!
	retlw	"#"
	retlw	"?"
	retlw	7
	retlw	8
	retlw	9
	retlw	"c"
	retlw	4
	retlw	5
	retlw	6
	retlw	"-"
	retlw	1	; 0xD
	retlw	2
	retlw	3
	retlw	"+"



;*******************************************************************************
;********************** EEPROM Bereich *****************************************
;*******************************************************************************
	org 2100	; EEPROM Bereich

;	DE	'V','2','F','A','0',' ','1','4','.','0','4','.','2','0','0','5'
	DE	0x10,0x0 ,0x0, 0x1
	DE	0x0 ,0x10,0x0, 0x1
	DE	0x0 ,0x0 ,0x10,0x0
	DE	0x80,0x0 ,0x0, 0x1
	DE	0x0, 0x0 ,0x0, 0x6
	DE	0x80,0x0 ,0x0, 0x7f


;%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	END
