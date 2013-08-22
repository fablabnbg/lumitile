#define TX2BUF_LEN 256

unsigned int Tx2Buff[TX2BUF_LEN];	// Größe nicht verändern wg. Tx2-Interrupt
int	Tx2WrPtr;
int	Tx2RdPtr;

//***************************************************
void SendKachel(int adr, int rot, int gruen, int blau, int Anzeige)
{
int zcnt;
int i;

	zcnt = 0;
	zcnt += CountZeros(rot & 0xFF);
	zcnt += CountZeros(gruen & 0xFF);
	zcnt += CountZeros(blau & 0xFF);
	if (Anzeige != SHOW_IMMEDIATE)
		zcnt |= 0x20;				// Bit 5 = 1--> Kachel speichert die Farbwerte, zeigt sie erst dann
									// an, wenn ein Broadcast mit bit5=1 erfolgt.
	
	Tx2Word(adr | 0x100);		// Bit 9 wg. Adresse setzen
	Tx2Word(rot);
	Tx2Word(gruen);
	Tx2Word(blau);
	Tx2Word(zcnt);
}
//***************************************************
int CountZeros(int Cw)
{
int cnt = 0;
unsigned char Maske = 0x80;

	while(Maske != 0)
	{
		if ( (Maske & Cw) == 0)
			cnt++;
		Maske = Maske >> 1; 		
	}
	return cnt;
}

void Tx2Word(int Txwort)
{

	Tx2Buff[ Tx2WrPtr++] = Txwort;
	Tx2WrPtr &= (TX2BUF_LEN - 1);

	return;
}


ASM()
{
// see Interrupt.s for complete code

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
	...
}
