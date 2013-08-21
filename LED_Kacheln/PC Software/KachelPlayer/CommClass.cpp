#include "stdafx.h"
#include <windows.h>
#include <stdio.h>
//#include "KachelCtrlDlg.h"

#include "CommClass.h"

COMM::COMM()	// Konstruktor
{
	memset(&ctmo,0,sizeof(ctmo) );
	memset(&ovr,0,sizeof(ovr) );
	memset(&ovw,0,sizeof(ovw) );
	hComm = NULL;
  
}

COMM::~COMM()	// Destruktor
{

	if (hComm != NULL)
	{
		CloseHandle(hComm);
		hComm = NULL;
	}
}

int COMM::Init(int com, int baud)
{

char sCom[20];
char temp[STRLEN+1];


	sprintf(sCom,"COM%d",com);

	hComm = CreateFile( sCom, GENERIC_READ | GENERIC_WRITE,0, NULL,
									 OPEN_EXISTING, 
										FILE_ATTRIBUTE_NORMAL, 0);
/*
	hComm = CreateFile( sCom, GENERIC_READ | GENERIC_WRITE,0, NULL,
									 OPEN_EXISTING, 
										FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH, 0);
*/
	if (hComm == INVALID_HANDLE_VALUE)
	{
		sprintf(temp,"Kann Schnittstelle %s nicht öffnen",sCom);
		MessageBox(NULL,temp,"ERROR", MB_ICONEXCLAMATION | MB_OK);
		return -1;
	}
	GetCommTimeouts(hComm, &ctmo);
	GetCommState(hComm,&dcb);
	strcpy(temp,"baud=9600 parity=N data=8 stop=2 TO=OFF");
	if (!BuildCommDCBAndTimeouts(temp,&dcb , &ctmo) )
		return -1;
	if (baud == 9600)
		dcb.BaudRate = CBR_9600;

	if (baud == 19200)
		dcb.BaudRate = CBR_19200;
	if (baud == 38400)
		dcb.BaudRate = CBR_38400;
	dcb.fOutxCtsFlow = FALSE;
	dcb.fOutxDsrFlow = FALSE;
	dcb.fDsrSensitivity = FALSE;

	dcb.DCBlength = sizeof(dcb);
	dcb.XonLim = 10;		// Dummy, weil sonst Fehler unter NT bei SetCommState()
	dcb.XoffLim = 10;		// Dummy, weil sonst Fehler unter NT bei SetCommState()

	ctmo.ReadIntervalTimeout = 1;
	ctmo.ReadTotalTimeoutMultiplier = 1;
	ctmo.ReadTotalTimeoutConstant = 0;
	ctmo.WriteTotalTimeoutConstant = 0;
	ctmo.WriteTotalTimeoutMultiplier = 0;

	if ( !SetCommTimeouts(hComm, &ctmo) )
		return -1;
	if ( !SetCommState(hComm,&dcb) )
		return -1;
/*
char test[960];
DWORD count;
BOOL ret;
	ret =	WriteFile(hComm,test,960,&count,&ovw);

*/
	return 0;
}

// ****************************************************************
// COMM:Tx(char +buff, int count) sendet count Bytes über die 
// serielle Schnittstelle (wie in Parameter angegeben).
// Nacktes Senden, keine Verarbeitung

// ****************************************************************

int COMM::Tx(char *Buff, int count)
{
DWORD cnt;

	if (WriteFile(hComm,Buff,(DWORD) count,&cnt,&ovw) == 0)
		return -1;
//	Sleep(500);

	return 0;
}

// ****************************************************************
// COMM:Tx(char +buff, int count) sendet count Bytes über die 
// serielle Schnittstelle (wie in Parameter angegeben).
// Die Daten werden komprimiert.

// ****************************************************************

int COMM::TxKachelInfo(char *Buff, int count)
{
DWORD cnt;
unsigned char temp[STRLEN];
unsigned char buff[STRLEN];

// Erst auf 7 bit umbauen
	memcpy(buff,Buff,count);
	temp[0] = buff[1] | 0x80;	// Adresse | 0x80
	temp[1] = buff[2] & 0x7f;	// rot
	temp[2] = buff[3] & 0x7f;	// grün
	temp[3] = buff[4] & 0x7f;	// blau
	temp[4] = (buff[2]>>7) | ((buff[3]>>6) & 0x2) | ((buff[4]>>5) & 0x4) ;

	if (WriteFile(hComm,temp,(DWORD) 5,&cnt,&ovw) == 0)
		return -1;
//	Sleep(500);

	return 0;
}

// ****************************************************************
// COMM:Tx(char +buff, int count) sendet count Bytes über die 
// serielle Schnittstelle (wie in Parameter angegeben).
// Die Daten werden komprimiert.

// ****************************************************************

int COMM::Rx(char *buff, DWORD *count, int MaxChar)
{




	if (ReadFile(hComm,buff,(DWORD) 0x80,count,NULL) == 0)
		return -1;

	return 0;
}

void COMM::EmptyRxBuff(void)
{
DWORD count;
char buff[STRLEN+1];

	while(1)
	{
		ReadFile(hComm,buff,(DWORD) 0x80,&count,NULL);
		if (count == 0)
			break;
	}

	return;
}

// ****************************************************************
//	Komprimieren(KompBuff,&KompCount,buff,count) 

// ****************************************************************
void COMM::Komprimieren(char *KompBuff,int *KompCount,char *buff,int count)
{
int SrcIdx = 0;
int DestIdx = 0;
int LoopIdx;
char LoopChar;


#define ONEBYTE (char)0x81	// nächstes Byte gibt an, wie oft übernächstes Byte vorkommt
#define TWOBYTE (char)0x82	// nächste 2 Byte geben an, wie oft überübernächstes Byte vorkommt
#define ONEBYTEBLANKS (char)0x91	// nachfolgendes Byte gibt in EINEM Byte die Anzahl Blanks an
#define TWOBYTEBLANKS (char)0x92	// nachfolgendes Byte gibt in 2 Bytes die ANzahl Blanks an

//	KompBuff[DestIdx++] = STX;
	while(1)
	{
		if ( SrcIdx >= count)
			break;
		LoopChar = buff[SrcIdx];
		LoopIdx = 1;
		while (1)
		{
			if ( (SrcIdx + LoopIdx) >= count)
				break;
			if (LoopChar == buff[SrcIdx+LoopIdx] )
				LoopIdx++;
			else
				break;

		}
		if (LoopIdx >= 3)		// erst ab 3 Character lohnt sich Komprimieren
		{
			if (LoopChar == 0x20)
			{
				if (LoopIdx > 128)
				{
					KompBuff[DestIdx++] = TWOBYTEBLANKS;
					KompBuff[DestIdx++] = (LoopIdx & 0x3f80) >> 7;
					KompBuff[DestIdx++] = (LoopIdx & 0x7f) ;

				}
				else
				{
					KompBuff[DestIdx++] = ONEBYTEBLANKS;
					KompBuff[DestIdx++] = LoopIdx;
				}
			}
			else
			{
				if (LoopIdx > 128)
				{
					KompBuff[DestIdx++] = TWOBYTE;
					KompBuff[DestIdx++] = (LoopIdx & 0xff80) >> 7;
					KompBuff[DestIdx++] = (LoopIdx & 0x7f);
					KompBuff[DestIdx++] = LoopChar;

				}
				else
				{
					KompBuff[DestIdx++] = ONEBYTE;
					KompBuff[DestIdx++] = LoopIdx;
					KompBuff[DestIdx++] = LoopChar;
				}
			}
			SrcIdx += LoopIdx;
		}
		else
		{
			KompBuff[DestIdx++] = buff[SrcIdx++];
		}
	
	}	


	KompBuff[DestIdx++] = 0x1a;	//?????????
	*KompCount = DestIdx;
	return;
}
