;******************************************************************************
;                                                                             *
;    Author              :                                                    *
;    Company             :                                                    *
;    Filename            :  tmp6014.s                                         *
;    Date                :  01/25/2005                                        *
;    File Version        :  1.30                                              *
;                                                                             *
;    Other Files Required: p30F6014.gld, p30f6014.inc                         *
;    Tools Used:MPLAB GL : 7.01                                               *
;               Compiler : 1.30                                               *
;               Assembler: 1.30                                               *
;               Linker   : 1.30                                               *
;                                                                             *
;******************************************************************************

        .equ __30F4013, 1
        .include "p30f4013.inc"

;..............................................................................
;Configuration bits:
;..............................................................................

        config __FOSC, CSW_FSCM_OFF & XT_PLL4    ;Turn off clock switching and
                                            ;fail-safe clock monitoring and
                                            ;use the External Clock as the
                                            ;system clock

 ;       config __FWDT, WDT_ON              ;Turn off Watchdog Timer
        config __FWDT, WDT_OFF              ;Turn off Watchdog Timer

        config __FBORPOR, PBOR_OFF & BORV_27 & PWRT_OFF & MCLR_EN
                                            ;Set Brown-out Reset voltage and
                                            ;and set Power-up Timer to 16msecs
                                            
        config __FGS, CODE_PROT_ON         ;Set Code Protection Off for the 
                                            ;General Segment

;..............................................................................
;Program Specific Constants (literals used in code)
;..............................................................................

;       .equ SAMPLES, 64         ;Number of samples


;..............................................................................
;Global Declarations:
;..............................................................................

        .global _wreg_init       ;Provide global scope to _wreg_init routine
                                 ;In order to call this routine from a C file,
                                 ;place "wreg_init" in an "extern" declaration
                                 ;in the C file.

        .global __reset          ;The label for the first line of code. 

        .global __T1Interrupt    ;Declare Timer 1 ISR name global
        .global __U1RXInterrupt  ;Declare Rx1 ISR name global
        .global __U1TXInterrupt  ;Declare Tx1 ISR name global
        .global __U2TXInterrupt  ;Declare Tx2 ISR name global
		.global __IC2Interrupt

		.global __StackError
		.global _Flashread
		.global _Flashwrite

.bss


TimerMain:			.word 1		; Wird im Timer1-Int (alle 25usec) hochgezählt,
								; bei erreichen von 40 werden die C-Timer Timer0-Timer4 decrementiert bis 0



;..............................................................................
;Code Section in Program Memory
;..............................................................................

.text    

__StackError:

	return


;..............................................................................
;Timer 1 Interrupt Service Routine
;Example context save/restore in the ISR performed using PUSH.D/POP.D
;instruction. The instruction pushes two words W4 and W5 on to the stack on
;entry into ISR and pops the two words back into W4 and W5 on exit from the ISR
;..............................................................................

__T1Interrupt:
	PUSH 	SR

	PUSH.D 	W0                  
;----- BEGIN Testbit (RD0) toggeln (für Scope)---
;	btst 	PORTE,#1
;	bra		Z,SET1
;	bclr 	PORTE,#1

;	goto 	SETEND
SET1:
;	bset 	PORTE,#1

SETEND:


;----- END Testbit (RD0) toggeln ---


;------- Timer-Verwaltung ----------------


	CP0		_Timer0
	btss	SR, #Z
	dec		_Timer0

	CP0		_Timer1
	btss	SR, #Z
	dec		_Timer1

	CP0		_Timer2
	btss	SR, #Z
	dec		_Timer2

	CP0		_Timer3
	btss	SR, #Z
	dec		_Timer3

	CP0		_Rx1Timer
	btss	SR, #Z
	dec		_Rx1Timer

	CP0		_TastTimer
	btss	SR, #Z
	dec		_TastTimer

	CP0		_AdTimer
	btss	SR, #Z
	dec		_AdTimer

	CP0		_ICTimer
	btss	SR, #Z
	dec		_ICTimer

	CP0		_IRwrEE_Timer 
	btss	SR, #Z
	dec		_IRwrEE_Timer 

	CP0		_HexScanTimer 
	btss	SR, #Z
	dec		_HexScanTimer  




	CP0		_PlayTimer		; Low Word von 32bit counter
	btss	SR,#Z		
	goto	DecPlayTimer
	CP0		_PlayTimer+2	; high word
	btsc	SR,#Z
	goto	NextTimer
DecPlayTimer:
	dec		_PlayTimer		; dec Low Word
	btsc	SR, #C			; Carry Clear wenn Überlauf 0000->FFFF!!
	goto	NextTimer		; wenn nicht
	CP0		_PlayTimer+2	; high wordnur dec wenn != 0
	bra		Z, NextTimer		; high word = 0
	dec		_PlayTimer+2	; wenn nicht



NextTimer:



; ---- Test ob Tx2-Int angestoßen werden muß
	mov		_Tx2WrPtr, W0
	mov		_Tx2RdPtr, W1
	cp		W0, W1
	bra		Z, NextTest
	btst	U2STA, #TRMT	; 1-->Tx-Schieberegister leer
	bra		Z,NextTest
	bset 	IFS1, #U2TXIF	; Tx2-Interrupt flag Statusbit.
		
; ---- Test ob Tx1-Int angestoßen werden muß
NextTest:
	mov		_Tx1WrPtr, W0
	mov		_Tx1RdPtr, W1
	cp		W0, W1
	bra		Z, EndTim1Int
	btst	U2STA, #TRMT	; 1-->Tx-Schieberegister leer
	bra		Z,EndTim1Int
	bset 	IFS0, #U1TXIF	; Tx2-Interrupt flag Statusbit.

EndTim1Int:
	disi	#2
	BCLR IFS0, #T1IF		;Clear the Timer1 Interrupt flag Status
							;bit.
	POP.D W0                   
	POP SR
	RETFIE					;Return from Interrupt Service routine
;------------------------------------------

__U1RXInterrupt:
	push	SR
	push.d	W0
	push.d	W2

	mov		U1RXREG, W0

	mov		_Rx1WrPtr, W1
	mov		#_Rx1Buff, W2
	Add		W1,W2,W2
	mov.b	W0,[W2]
	inc		W1,W1
	and		#0xFF,W1		;
	mov		W1, _Rx1WrPtr

	disi	#2
	BCLR IFS0, #U1RXIF		;Clear Rx1-Interrupt flag Statusbit.
	pop.d	W2                   
	pop.d	W0                   
	pop		SR
	retfie					;Return from Interrupt Service routine

;------------------------------------------

__U2TXInterrupt:
	push	SR
	push.d	W0
	push.d	W2

	mov		U2RXREG, W0

	mov		_Tx2WrPtr, W2
	mov		_Tx2RdPtr, W3
	cp		W3, W2
	bra		Z, EndTx2Int


	mov		#_Tx2Buff, W2
	sl		W3, W1			; TxBuff ist 16-bit-Puffer (wg. 9. Datenbit)
	Add		W1, W2, W2
	mov		[W2], W0
	inc		W3, W3
	and		#0xFF,W3		;
	mov		W3, _Tx2RdPtr

	mov		W0, U2TXREG

EndTx2Int:
	disi	#2
	BCLR 	IFS1, #U2TXIF		;Clear Rx1-Interrupt flag Statusbit.
	pop.d	W2                   
	pop.d	W0                   
	pop		SR
	retfie					;Return from Interrupt Service routine

;------------------------------------------

__U1TXInterrupt:
	push	SR
	push.d	W0
	push.d	W2


	mov		_Tx1WrPtr, W2
	mov		_Tx1RdPtr, W3
	cp		W3, W2
	bra		Z, EndTx1Int


	mov		#_Tx1Buff, W2
	mov		W3, W1			; TxBuff ist 16-bit-Puffer (wg. 9. Datenbit)
	Add		W1, W2, W2
	mov.b	[W2], W0
	inc		W3, W3
	and		#0xF,W3		;
	mov		W3, _Tx1RdPtr

	mov		W0, U1TXREG

EndTx1Int:
	disi	#2
	BCLR 	IFS0, #U1TXIF		;Clear Rx1-Interrupt flag Statusbit.
	pop.d	W2                   
	pop.d	W0                   
	pop		SR
	retfie					;Return from Interrupt Service routine



;************** Input Capture Interrupt ***************
__IC2Interrupt:
	PUSH 	SR
	clr		TMR2
;	clr		TMR3
	PUSH.D 	W0                  
	PUSH.D 	W2                  
	
	mov		_SampleTrigger,W0
	cp0		W0
	bra		z, EndIC2Int
	cp		W0,#1
	bra		z, BuffNotEmpty
	mov		#1, W0
	mov		W0, _SampleTrigger


	clr		_Rx1WrPtr
	clr		_Rx1RdPtr
;	clr		_PulsCount
;	clr		_PulsBreitenSumme
;	clr		_PulsBreitenSummeCount
 	goto	EndIC2Int

BuffNotEmpty:
	mov		IC2BUF, W3
;	mov		TMR3, W0
	btst	IC2CON, #ICBNE 
	bra		NZ, BuffNotEmpty		

; Write Pointer generieren

	mov		#_Rx1Buff, W1
	mov		_Rx1WrPtr, W2
	Sl		W2,W2
	AND		#0x0ff,W2
	add		W1,W2,W1

; High oder Low-Flanke?

	btst	PORTD,#9	
	bra		NZ, HighPulse
	bset	W3,#15
; Pulsbreite abspeichern 	
HighPulse:
	mov		W3,[W1++]

; Write-Pointer erhöhen
	mov		_Rx1WrPtr, W2
	inc		W2,W2
	and		#0xff,W2
	mov		W2, _Rx1WrPtr

EndIC2Int:
	mov	#0xA, W0
	mov	W0, _ICTimer			; TimeOut
	BCLR IFS0, #IC2IF		;Clear the Timer1 Interrupt flag Status
	POP.D W2
	POP.D W0                   
	POP SR
	RETFIE					;Return from Interrupt Service routine



;*************** Flash Read/write ***************************

.global	_FlashWrite

_FlashWrite:
	push.d	W0				; Datenadresse im Ram

; erst Programm-Memory löschen

	MOV #0x4041,W0
	MOV W0,NVMCON
	; Setup address pointer
	
	clr		NVMADRU			; obere 8 Bits immer 0, da Programm-memory
	MOV 	W1,NVMADR
	; Disable interrupts,
	PUSH SR
	MOV #0x00E0,W0
	IOR SR
	; Write the KEY sequence
	MOV #0x55,W0
	MOV W0, NVMKEY
	MOV #0xAA, W0
	MOV W0, NVMKEY
	; Start the erase operation
	BSET NVMCON,#WR
	; Insert two NOPs after
	NOP
	NOP
	; Re-enable interrupts,
	POP SR
L8: btsc    NVMCON, #WR
	bra		L8


	mov		#0x20, W4		; Schleifenzähler, 32 Programminstruktionen (=96Bytes) 
	clr		TBLPAG 			; High 8 bits, für Programm-Memory immer 0

	; Setup NVMCON to write 1 row of program memory
	MOV #0x4001,W0
	MOV W0,NVMCON

	pop.d		W0

WriteTableLoop:

	mov.b	[W0++], W6		
	mov.b	[W0++], W7
	mov.b	[W0++], W5

							; W0 enthält die Adresse im Programm-Memory
	TBLWTH.B W5, [W1]		; Read high byte to W3
	TBLWTL.B W6, [W1++]		; Read low byte to W4
	TBLWTL.B W7, [W1++] 		; Read middle byte to W5
	

	dec		W4,W4
	bra		NZ, WriteTableLoop


	; Disable interrupts, if enabled
	PUSH SR
	MOV #0x00E0,W0
	IOR SR
	; Write the KEY sequence
	MOV #0x55,W0
	MOV W0,NVMKEY
	MOV #0xAA,W0
	MOV W0,NVMKEY
	; Start the programming sequence
	BSET NVMCON,#WR
	; Insert two NOPs after programming
	NOP
	NOP
	; Re-enable interrupts, if required
	POP SR
    nop
    nop
L9: btsc    NVMCON, #WR
	bra		L9

	return;


;********************

.global _FlashRead


_FlashRead:
	push.d	W4
	push.d	W6

	mov		#0x20,W4

FlashReadLoop:
	clr		TBLPAG 			; High 8 bits, für Programm-Memory immer 0
							; W0 enthält die Adresse im Programm-Memory
	TBLRDH.B [W1],W5		; Read high byte to W3
	TBLRDL.B [W1++],W6		; Read low byte to W4
	TBLRDL.B [W1++],W7 		; Read middle byte to W5
	
	mov.b	W6, [W0++]		

	mov.b	W7, [W0++]

	mov.b	W5, [W0++]

	dec		W4,W4
	bra		NZ, FlashReadLoop

	pop.d	W6
	pop.d	W4


	return



;*************** EEPROM Read/write ***************************

.equ    EE_WORD_ERASE_CODE, 0x4044
.equ    EE_WORD_WRITE_CODE, 0x4004
.equ    EE_ROW_ERASE_CODE, 0x4045
.equ    EE_ROW_WRITE_CODE, 0x4005
.equ    EE_ALL_ERASE_CODE, 0x4046
.equ    CONFIG_WORD_WRITE_CODE, 0x4006

.global _ReadEE
.global _EraseEE
.global _WriteEE

.section .text
/* DATA EEPROM Read Routines */
_ReadEE:
        push    TBLPAG
        mov     w0, TBLPAG
        cp      w3, #1
        bra     z, L0
        cp      w3, #16
        bra     z, L0
        mov     #-1, w0
        bra     L1
L0:     tblrdl  [w1++],[w2++]
        dec     w3, w3
        bra     nz, L0
L1:     pop     TBLPAG
        return

/* DATA EEPROM Erase Routines */
_EraseEE:
        push.d  w4
        bclr    SR, #Z
        mov     #EE_WORD_ERASE_CODE, W4
        cp      w2, #1
        bra     z, L2
        mov     #EE_ROW_ERASE_CODE, W4
        cp      w2, #16
        bra     z, L2
        mov     #EE_ALL_ERASE_CODE, W4
        mov     #0xFFFF, w5
        cp      w2, w5
        bra     z, L2
        mov     #-1, w0
        pop.d   w4
        return
L2:
        push    TBLPAG
        mov     W0, NVMADRU
        mov     W1, NVMADR
        mov     W4, NVMCON
        push    SR
        mov     #0xE0, W0
        ior     SR
        mov     #0x55, W0
        mov     W0, NVMKEY
        mov     #0xAA, W0
        mov     W0, NVMKEY
        bset    NVMCON, #WR
        nop
        nop
L3:     btsc    NVMCON, #WR
        bra     L3
        clr     w0
        pop     SR
L4:     pop     TBLPAG
        pop.d   w4
        return


/* DATA EEPROM Write Routines */
_WriteEE:
        push    w4
        bclr    SR, #Z
        mov     #EE_WORD_WRITE_CODE, W4
        cp      w3, #1
        bra     z, L5
        mov     #EE_ROW_WRITE_CODE, W4
        cp      w3, #16
        bra     z, L5
        pop     w4
        mov     #-1, w0
        return

L5:     push    TBLPAG
        mov     W1, TBLPAG
        push    W2
L6:     tblwtl  [W0++],[W2++]
        dec     w3, w3
        bra     nz, L6

        mov     W1, NVMADRU
        pop     W2
        mov     W2, NVMADR
        mov     W4, NVMCON
        push    SR
        mov     #0xE0, W0
        ior     SR
        mov     #0x55, W0
        mov     W0, NVMKEY
        mov     #0xAA, W0
        mov     W0, NVMKEY
        bset    NVMCON, #WR
        nop
        nop
L7:     btsc    NVMCON, #WR
        bra     L7
        clr     w0
        pop     SR
        pop     TBLPAG
        pop     w4
        return




;--------End of All Code Sections ---------------------------------------------





.end                               ;End of program code in this file


