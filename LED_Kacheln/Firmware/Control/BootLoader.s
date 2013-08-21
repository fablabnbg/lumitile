        .equ __30F4013, 1
        .include "p30f4013.inc"


		.equ	ACK, 0x6
		.equ	NAK, 0x15
		.equ	STX, 0x2
		.equ	ETX, 0x3
		.equ	V, 0x56
        .section _BootLoader,address(0x7E00),code

;	.text		; Diese ZEile, wenn der Bootloader direkt hinter das andere Programm gelinkt werden soll
        .global  _BootEntry
        .global  _BootEntryAdress
        .align   2
_BootEntryAdress:
		.word 	tbloffset(_BootEntry)
_BootEntry:  
; disable all Interrupts

	clr		IEC0			; disable Tx-Int, Rx-Int, Tim1-Int
	clr		IEC1			
	clr		IEC2	
		
	mov		#ACK, W0
	mov		W0, U1TXREG

InitLoopWaitRec:
	mov		#0xA00, W1		; Zeiger auf Beginn Rec-Buff
	mov		#0, W2			; Index

LoopWaitRec:
	clrwdt
	btst	U1STA, #URXDA
	bra		Z, LoopWaitRec

	mov		U1RXREG, W0
	CP.B	W0, #STX
	bra		Z,LoopWaitRec
	CP.B	W0, #ETX
	bra		Z, ProcessData

	Add		W1,W2,W3
	mov.b	W0,[W3]			; "Byte" abspeichern
	inc		W2,W2
	and		#0xFF,W2		; Überlaufschutz

	bra		LoopWaitRec	





ProcessData:

; Prüfsumme checken, wird noch implementiert
	mov		[W1], W0
	mov		#'V',W3
	CP.B  	W0, W3			; 1.Byte muß 'V', 'P' oder 'G' sein (verify, Program, Goto 0)
	bra		EQ, VerifyRow

	mov		#'P',W3
	CP.B  	W0, W3			; 1.Byte muß 'V', 'P' oder 'G' sein (verify, Program, Goto 0)
	bra		EQ, ProgramRow

	mov		#'G',W3
	CP.B  	W0, W3			; 1.Byte muß 'V', 'P' oder 'G' sein (verify, Program, Goto 0)
	bra		EQ, Restart
	bra		InitLoopWaitRec

VerifyRow:
	call	funcVerifyRow
	bra		InitLoopWaitRec

ProgramRow:
	call	funcProgramRow
	bra		InitLoopWaitRec

Restart:


	mov		#ACK, W0
	mov		W0, U1TXREG
	Goto 	0


;-----

funcVerifyRow:
	mov		#0x900, W0		; Zeiger auf Beginn Rec-Buff binär
	mov		#0xA01, W1		; Zeiger auf Beginn Rec-Buff hex (Ohne Kennung 'P' oder 'V')
	mov		#0, W2			; Index auf RecBuff Hex


	call	RowHexToBin
	mov		#0x20, W4		; Schleifenzähler, 32 Programminstruktionen (=96Bytes) 
	mov		0x900, W0		; zu vergleichende Adresse im dsPic Programm-Memory
	swap	W0				
	mov		#0x902,W1		; zu vergleichende Daten vom PC
funcVerifyRowLoop:

	clr		TBLPAG 			; High 8 bits, für Programm-Memory immer 0
							; W0 enthält die Adresse im Programm-Memory
	TBLRDH.B [W0],W5		; Read high byte to W3
	TBLRDL.B [W0++],W6		; Read low byte to W4
	TBLRDL.B [W0++],W7 		; Read middle byte to W5
	
	mov.b	[W1++], W2		
	cp.b	W2, W6			; low byte
	bra		NZ, VerifyError

	mov.b	[W1++], W2
	cp.b	W2, W7			; middle Byte
	bra		NZ, VerifyError

	mov.b	[W1++], W2
	cp.b	W2, W5			; high byte
	bra		NZ, VerifyError

	dec		W4,W4
	bra		NZ, funcVerifyRowLoop
VerifyOK:
	mov		#ACK, W0
	goto	endVerifyRowLoop

VerifyError:
	mov		#NAK, W0
	goto	endVerifyRowLoop


endVerifyRowLoop:
	mov		W0, U1TXREG
	return
;-----


;*************************
funcProgramRow:
	mov		#0x900, W0		; Zeiger auf Beginn Rec-Buff binär
	mov		#0xA01, W1		; Zeiger auf Beginn Rec-Buff hex (Ohne Kennung 'P' oder 'V')
	mov		#0, W2			; Index auf RecBuff Hex


	call	RowHexToBin

; erst Programm-Memory löschen

	MOV #0x4041,W0
	MOV W0,NVMCON
	; Setup address pointer
	
	clr		NVMADRU			; obere 8 Bits immer 0, da Programm-memory
	mov		0x900, W0		; zu programmierende Adresse im dsPic Programm-Memory
	swap	W0				
	MOV 	W0,NVMADR
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

WaitClearEnde:
	btst	NVMCON,#WR
	bra		NZ, WaitClearEnde

	mov		#0x20, W4		; Schleifenzähler, 32 Programminstruktionen (=96Bytes) 
	mov		#0x902,W1		; zu programmierende Daten vom PC

	clr		TBLPAG 			; High 8 bits, für Programm-Memory immer 0

	; Setup NVMCON to write 1 row of program memory
	MOV #0x4001,W0
	MOV W0,NVMCON

	mov		0x900, W0		; zu programmierende Adresse im dsPic Programm-Memory
	swap	W0				

cp 0
bra	z,funcProgramRowLoop
inc w0,w0
dec w0,w0

funcProgramRowLoop:

	mov.b	[W1++], W6		
	mov.b	[W1++], W7
	mov.b	[W1++], W5

							; W0 enthält die Adresse im Programm-Memory
	TBLWTH.B W5, [W0]		; Read high byte to W3
	TBLWTL.B W6, [W0++]		; Read low byte to W4
	TBLWTL.B W7, [W0++] 		; Read middle byte to W5
	

	dec		W4,W4
	bra		NZ, funcProgramRowLoop


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
WaitWriteEnde:
	btst	NVMCON,#WR
	bra		NZ, WaitWriteEnde

;	goto VerifyOK;$$$$

	call	funcVerifyRow





	return


;*************************
RowHexToBin:
	mov		#98, W4		; Schleifenzähler, 96Bytes +2 Adressbytes
	push.d	W0
RowHexToBinLoop:
	mov.b	[W1++], W5
	call	CharHexToBin
	SL		W5, #4, W6

	mov.b	[W1++], W5
	call	CharHexToBin
	ior.b		W5, W6, W5
	mov.b		W5, [W0++]

	dec		W4,W4
	bra		NZ, RowHexToBinLoop

	pop.d	W0
	return

;*************************
; zu übergebender Character in W5, Rückgabe auch

CharHexToBin:
	push	W0
	sub.b	W5,#0x30
	CP.B	W5,#9
	bra		LE, EndCharHexToBin
	sub.b		W5,#7
EndCharHexToBin:
	pop		W0
	return
.end
