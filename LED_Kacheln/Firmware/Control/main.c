#include "p30f4013.h"
#include "math.h"
#include "stdlib.h"
#include "string.h"
#include "Display.h"
//******************************************************************************
//                                                                             *
//    Author              :  S. Gassner                                        *
//    Company             :  Leber Systemtechnik                               *
//    Filename            :  main.c                                            *
//    Date                :  04/05/2006                                        *
//    Program Version     :  3.00                                              *
//                                                                             *
//    Other Files Required: p30F4013.gld, p30f4013.h, Portdef.h                *
//    Tools Used:MPLAB GL : 7.31                                               *
//               Compiler : 1.31                                               *
//               Assembler: 1.31                                               *
//               Linker   : 1.31                                               *
//                               
//    Änderungen:
//    
//    Vers. 2.02 / 05.04.2006 Ga
//    - Freier Speicher für Szenen-Download (in Versionsabfrage) wurde nicht 
//      korrekt übertragen                           
//                               
//    Vers. 3.00 / 04.05.2006 Ga
//    - Zeitintervall durch 10 gteilt, d.h. eine 1 aus KachelEdit enstpricht jetzt 100msec 
//    - Kachel-Baudrate auf 57.6 Kbaud erhöht
//    - Temporegler: Eine Änderung setzt nicht den Counter für die aktuelle Szene zurück, 
//		sondern wird anteilig eingerechnet-> kein Blitzen mehr bei Jitter
//              Es werden keine kleineren Zeiten als 100msec eingetragen. Ergibt eine Be-
//		rechnung eine Zeit < 100msec, wird 100msec verwendet.
//    - Tx2Buff (KachelSend) erhöht, es können die Daten für 50 Kacheln in einem Rutsch berechnet und
//		rausgeschickt werden, nächster Send erst wieder, wenn Tx2Buff emtpy.
//	
//    - Optimierung: RxBuff und Rx1Buff werden im PlayFile-Modus dazu verwendet, den letzten
//		Stand und den aktuellen Stand (Farben) der Kacheln abzuspeichern. Gesendet wird nur an die
//		Kacheln, bei denen eine Farbänderung stattgefunden hat.
//    - Optimierung: CalcFarbeShort() eingebaut, wie CalcFarbe(), jedoch werden 2 Variablen,
//		die für alle Kacheln die gleichen sind, zuvor berechnet (nur einmal)
//	  - Firmwareupdate: Text in der Anzeige ergänzt um "und Enter drücken"
//******************************************************************************


//******************************************
//          Constants im Progr-Memory
//*********************************'***

const char __attribute__ ((space(auto_psv))) StartScreen[4][17] = {"  Kachel-Ctrl  ", "  Version 3.00  ", "   04.05.06     ","               "};
//const char __attribute__ ((space(auto_psv))) StartScreen[4][17] = {"  Kachel-Ctrl  ", "  TEST UPLOAD   ", "   02.03.06     ","               "};
const char __attribute__ ((space(auto_psv))) IRTexte[5][17] = { "Druecke Rot..   ", 
																"Druecke Gruen.. ", 
																"Druecke Blau..  ",
																"Druecke Heller..",
																"Druecke Dunkler."};

const char __attribute__ ((space(auto_psv))) FunkTexte[6][17] = { "Druecke Rot--   ", 
																"Druecke Rot++   ", 
																"Druecke Gruen-- ",
																"Druecke Gruen++ ",
																"Druecke Blau--  ",
																"Druecke Blau++  "};

//*********************************
//          Defines
//*********************************

#define DEBUG 0
#define VERSION 300				// Vers. 300
#define FLASH_BASEADR	0x5000	// ab hier wird ein Downoad-File gespeichert
#define IR_BASEADR		FLASH_BASEADR - 0x600	// ab hier werden die IR KeyCodes gespeichert (Länge 6x 0xC0)
#define FUNK_BASEADR		IR_BASEADR - 0x600	// ab hier werden die Funk KeyCodes gespeichert (Länge 6x 0xC0)



#define MAX_KACHEL	50			// Max anzahl Kacheln
#define SEND_DELAY 4

#define MIT_NULL 0		//für die Routine OwnItoa: 0x0 anhängen
#define NO_NULL 1		//für die Routine OwnItoa: kein 0x0 anhängen

#define MIT_LEAD_ZERO 0	// keine führende 0-Unterdrückung
#define NO_LEAD_ZERO  1	// führende 0-Unterdrückung

#define ON  1
#define OFF 0


#define STX 0x2		//ctrl-B
#define ETX 0x3		//ctrl-C
#define ACK 0x6		//ctrl-F
#define NAK 0x15	//ctrl-U
#define ESC 0x1B	//Escape
#define CR  0xD		//Carriage Return
#define LF  0xA		//Line Feed

#define LINE_LEN	16


#define CHAR_Y		16	// 16 Pixel Höhe pro Character
#define CHAR_X		11	// 11 Pixel Breite pro Character
#define X_POS		3
#define Y_POS		16



#define RX1BUF_LEN	256
#define TO_RX1		20	// Timout COM1 (mesec)
#define RXBUF_LEN	256

#define TX1BUF_LEN 16
#define TX2BUF_LEN 256

//------------ Tasten-Defines ----------

#define TAST_COL0_PIN	PORTFbits.RF0
#define TAST_COL1_PIN	PORTFbits.RF1
#define TAST_COL2_PIN	PORTFbits.RF6
#define TAST_COL3_PIN	PORTDbits.RD2


#define TAST_COL0	PORTFbits.RF0
#define TAST_COL1	PORTFbits.RF1
#define TAST_COL2	PORTFbits.RF6
#define TAST_COL3	PORTDbits.RD2

// TastenCodes

#define CUR_UP 		0xA
#define CUR_DOWN 	0xB
#define CUR_LEFT	0xC
#define CUR_RIGHT	0xD
#define ENTER		0xE
#define CLEAR		0xF

// Hex-Schalter Codes

#if DEBUG == 0
	#define MANUELL			0
	#define WIEDERGABE		1
	#define GATEWAY			2
	#define PLAYFILE		3
	#define DOWNLOADFILE	4
	#define FUNKSTEUERN		5
	#define IRSTEUERN		6	
	#define FBLERNEN		7
	#define FIRMWAREUPDATE	8
#else
	
	#define MANUELL			0
	#define WIEDERGABE		1
	#define GATEWAY			7
	#define PLAYFILE		3
	#define DOWNLOADFILE	2
	#define FUNKSTEUERN		9
	#define IRSTEUERN		6	
	#define FBLERNEN		4
	#define FIRMWAREUPDATE	8
#endif
//------------ Farben-Defines ----------
#define ROT 0
#define GRUEN 1
#define BLAU 2

//------------ HexSchalter-Defines ----------
#define HEX0_PIN TRISCbits.TRISC14	
#define HEX1_PIN TRISCbits.TRISC13	
#define HEX2_PIN TRISBbits.TRISB7	
#define HEX3_PIN TRISBbits.TRISB6	

#define HEX0 PORTCbits.RC14	
#define HEX1 PORTCbits.RC13	
#define HEX2 PORTBbits.RB7	
#define HEX3 PORTBbits.RB6	

//------------ UART-Defines ----------
#define TX2ENA_PIN	TRISDbits.TRISD8
#define TX2ENA		PORTDbits.RD8

//------------ IR-Fernbedienung ----------

#define PULSTOLERANZ_IR 400
#define TC_REPEAT_DETECT_IR 100
#define TC_REPEAT_DETECT_FUNK 330

#define TC_EE_WRITE		10000

#define RED	0
#define GREEN 1
#define BLUE 2
#define HELLER 3
#define DUNKLER 4

//------------ FUNK-Fernbedienung ----------
#define PULSTOLERANZ_FUNK 400
#define RED_DUNKLER	0
#define RED_HELLER	1
#define GREEN_DUNKLER	2
#define GREEN_HELLER	3
#define BLUE_DUNKLER	4
#define BLUE_HELLER	5

//*********************************
//          Globale Variablen
//*********************************



//*********************************
//          Funktionsprotoypen
//*********************************


void Tx1Char(char byte);
void Tx2Word(int Txwort);
void ZeichenUmsetzen(char *string,int len);
void InitAD(void);
void InitTimer1(void);
void InitHexSchalter(void);
void InitUart1(void);
void InitUart2(void);
void InitInputCapture2(void);

void TastScan(void);
void TastSetRow(char row);
char TastGetCol(void);
void TastSetColPins(int dir);

void AdScan(void);
void HexScan(void);
void HexDispatch(void);
void Wiedergabe(void);
void Manuell(void);
void GateWay(void);
void FirmwareUpdate(void);
void DownloadFile(void);
void PlayFile(void);
void FBlernen(void);
void IR_InitBuffers(void);
void IRSteuern(void);
void FunkSteuern(void);

void OwnItoa(char *str, int Value, int Stellen, int AppendNull, int SupressLeadingZeros);
void strnfill(char *str, char fill, int cnt);
void SendKachel(int adr, int rot, int gruen, int blau, int Anzeige);
	#define SHOW_IMMEDIATE 0
	#define STORE_COL_ONLY 1

int CountZeros(int );
void MenuStateMachine(void);
void DisplayMenu(void);
void IncCursorPos(void);
void DecCursorPos(void);
int OwnAtoi(char *str);
unsigned char CalcFarbe(unsigned char FarbeAkt, unsigned char FarbeNext);
unsigned char CalcFarbeShort(unsigned char FarbeAkt, unsigned char FarbeNext); // wie CalcFarbe(), aber fTransMsec und
																				// proz sind schon berechnet (Zeitersparnis!)
int iRunden(int zahl);

// Receive COM1 (serielle Schnittetelle zum PC)
int ReadCharCom1(char *zeichen);
void UcharToHex(char Byte, char *Dest);
unsigned char  HexToUchar(char HighNibble, char LowNibble);
int CheckPruefSumme(void);
void CheckRx1(void);
void SendNAK(void);
void SendACK(void);
void CommandDispatch(void);
void ConvertToBin(void);

void FlashRead(void *, int);
void FlashWrite(void *, int);

long GetPlayTimer(void);
void SetPlayTimer(long int);
void IncSzeneNr(unsigned char *Nr);
void SendNewCol(void);
void ShowFarbWerte(void);		// Für IR und Funk
long CalcDauer(int);
long CalcTrans(int);


#if DEBUG == 1
		char Dummy[60];
#endif

unsigned int Tx2Buff[TX2BUF_LEN];	// Größe nicht verändern wg. Tx2-Interrupt
int	Tx2WrPtr;
int	Tx2RdPtr;


unsigned char Tx1Buff[TX1BUF_LEN];	// Größe nicht verändern wg. Tx2-Interrupt
int	Tx1WrPtr;
int	Tx1RdPtr;


int	Rx1WrPtr;
int	Rx1RdPtr;

unsigned char Rx1Buff[RX1BUF_LEN];	// Größe nicht verändern wg. IC1-Interrupt

unsigned char RxBuff[RXBUF_LEN];		// Der Receivebuffer für C-Routinen
unsigned char RxStatus;				// 0-> Kein Receive in progress = Warten auf STX
							// 1-> STX empfangen = Warten auf weitere Characters oder ETX
							// 2-> ETX empfangen
int RxBuffCnt;				// Schreib-Zeiger auf RxBuff

#define AktKachelCol	Rx1Buff
#define LastKachelCol	RxBuff
//----- Variablen für Automatik-Betrieb -------------

typedef struct tagAutoSzene{int Dauer;
							int Trans;
							unsigned char Farbe[3];
							unsigned char reseve;} _AutoSzene;

typedef struct tagPlaySzene{int Dauer;
							int Trans;
							unsigned char Kachel[MAX_KACHEL][3];
							} _PlaySzene;

_AutoSzene 	AutoSzeneAkt;
_AutoSzene 	AutoSzeneNext;
_AutoSzene 	AutoSzeneTemp;

_PlaySzene 	PlaySzeneAkt;
_PlaySzene 	PlaySzeneNext;

long DauerMsec;
long TransMsec;
long OldDauerMsec;
long OldTransMsec;
long PlayTimer;


float fTransMsec;			// Für CalcFarbe()
float proz;


//&--------------------------------------

unsigned int Timer0;		// Für Receive-Timeout
unsigned int Timer1;		// Für Clear-Display, Tasten entprellen
unsigned int Timer2;		// 
unsigned int Timer3;		// 
unsigned int Rx1Timer;		// Receive COM1 (= PC) TimeOut u.ä.

char temp[32];
struct  tagParam{
		int Farben[3];
		
		unsigned char dummy[32];
		} Param;

//---- Variablen für Tastatur ----
char TastAkt;
char TastOld;
char TastFlag;				// = 1-> Neue Taste gedrückt
char TastStatus;			// für die StateMachine in TastScan()
int TastTimer;				// Timer nur für Tasten-Routinen
char TastTab[] = {-1, 7,8,9,CUR_UP,   4,5,6,CUR_DOWN,   1,2,3,CLEAR,   CUR_LEFT,0,CUR_RIGHT,ENTER};
char TastTemp;

//---- Variablen für Potis (Farben) ----
unsigned char FarbenAkt[3];
unsigned char FarbenOld[3];
int AdTimer;
char FarbFlag;			// = 1-> Farbänderung an den Potis

int OldAdcBuff3;
char TempoAkt;
char TempoOld;
char TempoFlag;
unsigned char TempoTab[] = {1,1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,60,70,80,90,100,-1};
//---- Variablen für HexSchalter ----

char HexAkt;
char HexOld;
char HexStatus;
char HexFlag;
int HexScanTimer;
//---- Variablen für Menü ----

typedef struct tagMenuItem{	unsigned char  len;
					unsigned char pos;
					char text[5];} MenuItem;
MenuItem Menu[4];
unsigned char MenuStatus;
unsigned char MenuIdx;
unsigned char MenuLine;
unsigned char MenuCurIdx;	// CursorPosition innerhalb eines Eingabefeldes
unsigned char MenuCurX;		// CursorPosoition in der Zeile

char MenuCursorOnOff;		// 1 = On, 0 = off;



void WriteEEPROM(_AutoSzene *, int SzeneNr);
void ReadEEPROM(_AutoSzene*, int SzeneNr);

unsigned char SzeneNrAkt;
unsigned char SzeneNrNext;

// Variablen für Play File

unsigned char AnzKacheln;
unsigned char AnzSzenen;
unsigned char KachelList[MAX_KACHEL];
char FileName[10];
void LadeSzeneNr(int Nr, void *data );
int AktKachel;		


// Variablen für Input Cpature
unsigned int ICTimer;		// InputCapture Timer
int KeyIdx;
int SampleTrigger;
int Error;
int SampleOK;
int AktCol;
int RepeatTimerTabIR[] = {500,300,200,100,100,0};
int IncDecTabIR[] = {1,5,10,10,10,10,0};
int RepeatTimerIdx;
int IRwrEE_Timer;
char IRwrEE_TimerFlag;

// Funk
int RepeatTimerTabFunk[20] = {300,300,200,200,100,0};
int IncDecTabFunk[20] = {2,5,10,10,20,20,0};

//*********************************************
//          Externe Variablen (Assembler)
//*********************************************

extern int BootEntryAdress;

//***************************************************

int main(void)
{

int i;

	TastOld = -1;				// damit beim 1. Scan eine Äbderung festegetellt wird
	TastFlag = 0;
	TastStatus = 0;
	TastTimer = 0;
	SampleTrigger = 0;
	for (i = 0; i < 3; i++)
	{
		FarbenAkt[i] = 0;
		FarbenOld[i] = 255;
	}
	FarbFlag = 0;
	AdTimer = 0;
	TempoAkt = 0;
	TempoOld = -1;
	TempoFlag = 0;
	OldAdcBuff3 = -1;

	HexAkt = 0;
	HexOld = -1;
	HexStatus = 0;
	HexFlag = 0;

	Tx2WrPtr = 0;
	Tx2RdPtr = 0;
	Rx1RdPtr = 0;
	Rx1WrPtr = 0;
	RxStatus = 0;
	RxBuffCnt = 0;
	MenuCursorOnOff = OFF;		// Cursor OFF 
	InitAD();					// Timer/UART-Init, enable Interrupts
	InitTimer1();
	InitHexSchalter();
	InitUart1();
	InitUart2();
	InitInputCapture2();
	DisplayInit();
	HexScanTimer = 0;

	for (i = 0; i < 4; i++)
	{
		strcpy(temp,&StartScreen[i][0]);
		DisplayWriteLine(i,0,temp);
	}
	Timer0 = 1200;
	while (Timer0);

	while(1)
	{
		TastScan();
		AdScan();
		HexScan();

		HexDispatch();

		asm ("clrwdt");			// Clear Wtchdog-Timer, die einzige Stelle im gesamten Programm!
	}
	return 0;
}
//***************************************************

void HexDispatch(void)
{

	if (HexFlag == 1)
	{
		U1MODEbits.UARTEN = 1;			// *** Uart-Enable, war evtl auf 0 aus IR-Lernen ***
		U1STAbits.UTXEN = 1;	
		Rx1WrPtr = 0;
		Rx1RdPtr = 0;

		IEC0bits.IC2IE = 0;				// Interrupt Disable	Input-Capture
		HexFlag = 0;
		HexStatus = 0;
		DisplayClear();
		MenuCursorOnOff = OFF;
		SetCursor(MenuCursorOnOff);
		TastFlag = 0;
		SampleTrigger = 0;
	}	

	switch(HexAkt)
	{
	case MANUELL:
		Manuell();
		break;
	case WIEDERGABE:
		Wiedergabe();
		break;
	case GATEWAY:
		GateWay();
		break;
	case DOWNLOADFILE:
		DownloadFile();
		break;
	case PLAYFILE:
		PlayFile();
		break;
	case FUNKSTEUERN:
		FunkSteuern();		// Kacheln mit IR ansteuern
		break;
	case IRSTEUERN:
		IRSteuern();		// Kacheln mit IR ansteuern
		break;
	case FBLERNEN:
		FBlernen();			// Lerne Fernbedienung (Funk/IR)
		break;
	case FIRMWAREUPDATE:
		FirmwareUpdate();
		break;
	default:
		strcpy(temp,"nicht belegt");
		DisplayWriteLine(0,0,temp);

	}

}



//***************************************************
void FunkSteuern(void)
{
unsigned int *IRBuff, *KeyBuff;
int i, k;
	IRBuff = (unsigned int *)Rx1Buff;
	KeyBuff = (unsigned int *)RxBuff;

	switch(HexStatus)
	{
	case 0:
		U1MODEbits.UARTEN = 0;			// *** Uart-Disable, war evtl auf 0 aus IR-Lernen ***
		IEC0bits.IC2IE = 1;				// Interruptenable	Input-Capture
		IR_InitBuffers();
		ReadEE(0x7f, 0xFFE0, &Param, 16);
		if (Param.Farben[ROT] == -1)		// Wenn Chip neu programmiert
		{
			Param.Farben[ROT] = 0;
			Param.Farben[GRUEN] = 0;
			Param.Farben[BLAU] = 0;
		}

		strcpy(temp," Funk Steuern");
		DisplayWriteLine(0,0,temp);
		AktCol = -1;
		IRwrEE_Timer = 0;
		IRwrEE_TimerFlag = 0;
		HexStatus++;
		Timer1 = 0;
		Timer2 = 0;
		Timer3 = 0;
		SendNewCol();
		break;
	case 1:				// 
		ShowFarbWerte();

		if (Timer3 == 0)
		{
			Timer3 = 300;
			strcpy(temp,"rot gruen blau  ");
			DisplayWriteLine(1,0,temp);
			strnfill(temp,0x20,16);	
			OwnItoa(temp,Param.Farben[ROT],3, NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(&temp[5],Param.Farben[GRUEN],3,NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(&temp[10],Param.Farben[BLAU],3,NO_NULL, NO_LEAD_ZERO);
			DisplayWriteLine(2,0,temp);
			
		}


		if (IRwrEE_TimerFlag == 1 && IRwrEE_Timer == 0)
		{
			IRwrEE_TimerFlag = 0;
			EraseEE(0x7f, 0xFFE0, 16);
			WriteEE(&Param, 0x7f, 0xFFE0, 16);

		}	
		
		if ( Rx1WrPtr != Rx1RdPtr && ICTimer == 0)
		{	
			Error = 0;
			SampleTrigger = 0;	

			if (Rx1WrPtr > 71  && Rx1WrPtr < 74 && Error == 0)
			{
				SampleOK = 1;
				Rx1WrPtr = 0;
				Rx1RdPtr = 0;
				Error = 0;
			}
			else
			{
				IR_InitBuffers();
			}
		}
		if (SampleOK)
		{
			for (KeyIdx = 0; KeyIdx < 6; KeyIdx++)
			{
				for (i = 0; i < 3; i++)
				{
					FlashRead(&RxBuff[i*48], FUNK_BASEADR + KeyIdx*0xC0 + i*0x40);
				}
				Error = 0;
				i = 2;
				while(KeyBuff[i] != 0 && i < 150)
				{
					if (i == 149)
						Error = 1;
					if ( (IRBuff[i] > (KeyBuff[i] + PULSTOLERANZ_FUNK)) || (IRBuff[i] < (KeyBuff[i] - PULSTOLERANZ_FUNK))  )
					{
						Error = 1;
					}
					i++;
				}
				if (Error == 0)
				{
					if (Timer1 != 0 && ( KeyIdx >= RED_DUNKLER && KeyIdx <= BLUE_HELLER) )
					{
						IRwrEE_Timer = TC_EE_WRITE;
						IRwrEE_TimerFlag = 1;

						if (Timer2 == 0)
						{
							Timer2 = RepeatTimerTabFunk[RepeatTimerIdx];
							if (RepeatTimerTabFunk[RepeatTimerIdx] != 0)
								RepeatTimerIdx++;
						}
					}
					else
					{
						RepeatTimerIdx = 0;											
						Timer2 = RepeatTimerTabFunk[RepeatTimerIdx];
					}

					Timer1 = TC_REPEAT_DETECT_FUNK;

					switch(KeyIdx)
					{
						case RED_HELLER:
							AktCol = RED;
							KeyIdx = HELLER;
							break;

						case RED_DUNKLER:
							AktCol = RED;
							KeyIdx = DUNKLER;
							break;

						case GREEN_HELLER:
							AktCol = GREEN;
							KeyIdx = HELLER;
							break;

						case GREEN_DUNKLER:
							AktCol = GREEN;
							KeyIdx = DUNKLER;
							break;

						case BLUE_HELLER:
							AktCol = BLUE;
							KeyIdx = HELLER;
							break;

						case BLUE_DUNKLER:
							AktCol = BLUE;
							KeyIdx = DUNKLER;
							break;
					}


					switch(KeyIdx)
					{
						case HELLER:
							if (Param.Farben[AktCol] != 255 && AktCol != -1)
							{
								Param.Farben[AktCol] += IncDecTabFunk[RepeatTimerIdx];
								if (Param.Farben[AktCol] > 255)
									Param.Farben[AktCol] = 255;
								SendNewCol();
							}
							goto EndSample;
							break;
						case DUNKLER:
							if (Param.Farben[AktCol] != 0 && AktCol != -1)
							{
								Param.Farben[AktCol] -= IncDecTabFunk[RepeatTimerIdx];
								if (Param.Farben[AktCol] < 0)
									Param.Farben[AktCol] = 0;
								SendNewCol();
							}
							goto EndSample;
							break;
					}




				}

			}
EndSample:
			IR_InitBuffers();
		}
		break;		
	}

}


//***************************************************
void ShowFarbWerte(void)
{
	if (Timer3 == 0)
	{
		Timer3 = 300;
		strcpy(temp,"rot gruen blau  ");
		DisplayWriteLine(1,0,temp);
		strnfill(temp,0x20,16);	
		OwnItoa(temp,Param.Farben[ROT],3, NO_NULL, NO_LEAD_ZERO);	
		OwnItoa(&temp[5],Param.Farben[GRUEN],3,NO_NULL, NO_LEAD_ZERO);	
		OwnItoa(&temp[10],Param.Farben[BLAU],3,NO_NULL, NO_LEAD_ZERO);
		DisplayWriteLine(2,0,temp);
		
	}
}
//***************************************************
void IRSteuern(void)
{
unsigned int *IRBuff, *KeyBuff;
int i, k;
	IRBuff = (unsigned int *)Rx1Buff;
	KeyBuff = (unsigned int *)RxBuff;

	switch(HexStatus)
	{
	case 0:
		U1MODEbits.UARTEN = 0;			// *** Uart-Disable, 
		IEC0bits.IC2IE = 1;				// Interruptenable	Input-Capture
		IR_InitBuffers();
		ReadEE(0x7f, 0xFFE0, &Param, 16);
		if (Param.Farben[ROT] == -1)		// Wenn Chip neu programmiert
		{
			Param.Farben[ROT] = 0;
			Param.Farben[GRUEN] = 0;
			Param.Farben[BLAU] = 0;
		}

		strcpy(temp,"   IR Steuern");
		DisplayWriteLine(0,0,temp);
		AktCol = -1;
		IRwrEE_Timer = 0;
		IRwrEE_TimerFlag = 0;
		HexStatus++;
		Timer1 = 0;
		Timer2 = 0;
		Timer3 = 0;
		SendNewCol();
		break;
	case 1:				// 
		ShowFarbWerte();
		if (IRwrEE_TimerFlag == 1 && IRwrEE_Timer == 0)
		{
			IRwrEE_TimerFlag = 0;
			EraseEE(0x7f, 0xFFE0, 16);
			WriteEE(&Param, 0x7f, 0xFFE0, 16);

		}	
		
		if ( Rx1WrPtr != Rx1RdPtr && ICTimer == 0)
		{	
			Error = 0;
			SampleTrigger = 0;	

			if (Rx1WrPtr > 4  && Rx1WrPtr < 60 && Error == 0)
			{
				SampleOK = 1;
				Rx1WrPtr = 0;
				Rx1RdPtr = 0;
				Error = 0;
			}
			else
			{
				IR_InitBuffers();
			}
		}
		if (SampleOK)
		{
			for (KeyIdx = 0; KeyIdx < 5; KeyIdx++)
			{
				for (i = 0; i < 3; i++)
				{
					FlashRead(&RxBuff[i*48], IR_BASEADR + KeyIdx*0xC0 + i*0x40);
				}
				Error = 0;
				i = 2;
				while(KeyBuff[i] != 0 && i < 128)
				{
					if (i == 127)
						Error = 1;
					if ( (IRBuff[i] > (KeyBuff[i] + PULSTOLERANZ_IR)) || (IRBuff[i] < (KeyBuff[i] - PULSTOLERANZ_IR))  )
					{
						Error = 1;
					}
					i++;
				}
				if (Error == 0)
				{
					if (Timer1 != 0 && ( KeyIdx == HELLER || KeyIdx == DUNKLER) )
					{
						IRwrEE_Timer = TC_EE_WRITE;
						IRwrEE_TimerFlag = 1;

						if (Timer2 == 0)
						{
							Timer2 = RepeatTimerTabIR[RepeatTimerIdx];
							if (RepeatTimerTabIR[RepeatTimerIdx] != 0)
								RepeatTimerIdx++;
						}
					}
					else
					{
						RepeatTimerIdx = 0;											
						Timer2 = RepeatTimerTabIR[RepeatTimerIdx];
					}

					Timer1 = TC_REPEAT_DETECT_IR;
					switch(KeyIdx)
					{
						case RED:
							AktCol = RED;
							break;
						case GREEN:
							AktCol = GREEN;
							break;
						case BLUE:
							AktCol = BLUE;
							break;
						case HELLER:
							if (AktCol == -1 )
								break;
							if (Param.Farben[AktCol] != 255)
							{
								Param.Farben[AktCol] += IncDecTabIR[RepeatTimerIdx];
								if (Param.Farben[AktCol] > 255)
									Param.Farben[AktCol] = 255;
								SendNewCol();
							}
							break;
						case DUNKLER:
							if (AktCol == -1)
								break;
							if (Param.Farben[AktCol] != 0)
							{
								Param.Farben[AktCol] -= IncDecTabIR[RepeatTimerIdx];
								if (Param.Farben[AktCol] < 0)
									Param.Farben[AktCol] = 0;
								SendNewCol();
							}
							break;

					}
				}

			}
			IR_InitBuffers();
		}
		break;		
	}

}
//***************************************************

void SendNewCol(void)
{

	SendKachel(0xFF,Param.Farben[ROT],
					Param.Farben[GRUEN],
					Param.Farben[BLAU], SHOW_IMMEDIATE);

	return;
}


//***************************************************
void FBlernen(void)
{
int k;
int i;

	switch(HexStatus)
	{
	case 0:
		strcpy(temp,"IR/Funk lernen");
		DisplayWriteLine(0,0,temp);
		strcpy(temp,"Druecke..");
		DisplayWriteLine(1,0,temp);
		strcpy(temp,"1-> IR lernen");
		DisplayWriteLine(2,0,temp);
		strcpy(temp,"2-> Funk lernen");
		DisplayWriteLine(3,0,temp);
		HexStatus++;
		break;
	case 1:				// 
		if (TastFlag == 1)
		{
			TastFlag = 0;
			if (TastAkt == 1)			// Infrarot lernen
				HexStatus = 2;		 
			if (TastAkt == 2)			// Funk lernen
				HexStatus = 6;		 
		}
		break;
	case 2:				// 
		U1MODEbits.UARTEN = 0;			// *** Uart-Disable, ***
		IEC0bits.IC2IE = 1;		// Interruptenable	
		DisplayClear();
		strcpy(temp,"Infrarot lernen ");
		DisplayWriteLine(0,0,temp);
		KeyIdx = 0;
		Timer0 = 0;
		HexStatus++;
		break;

	case 3:
		strcpy(temp,IRTexte[KeyIdx]);
		DisplayWriteLine(1,0,temp);
		HexStatus++;
		IR_InitBuffers();
		if (KeyIdx > 5)
			HexStatus = 5;
		break;
	case 4:
		if ( Rx1WrPtr != Rx1RdPtr && ICTimer == 0)	
		{	
			SampleTrigger = 0;	

			if (Rx1WrPtr > 4  && Rx1WrPtr < 60 && Error == 0)
			{
				Timer0 = 700;
				DisplayClearLine(1);
				strcpy(temp,"OK!");
				DisplayWriteLine(1,0,temp);
				while (Timer0 != 0)
					;
				DisplayClearLine(1);
	
				for (i = 0; i < 3; i++)
				{
					FlashWrite(&Rx1Buff[i*48], IR_BASEADR + KeyIdx*0xC0 + i*0x40);
				}

				KeyIdx++;
				HexStatus = 3;
				if (KeyIdx == 5)
				{
					DisplayClearLine(1);
					strcpy(temp,"Fertig!");
					DisplayWriteLine(1,0,temp);
					HexStatus = 15;
				}
				else
					SampleTrigger = 2;	
			}
			else
			{
				Timer0 = 700;
				DisplayClearLine(1);
				strcpy(temp,"Fehler!  ");
				DisplayWriteLine(1,0,temp);

				while (Timer0 != 0)
				{}
				DisplayClearLine(1);
				SampleTrigger = 2;	
				HexStatus = 3;

			}
		}
		
		break;
	case 5:		// Lernen Ende
		SampleTrigger = 0;
		break;
	case 6:		// FunkLernen
		U1MODEbits.UARTEN = 0;			// *** Uart-Disable***
		IEC0bits.IC2IE = 1;		// Interruptenable	
		DisplayClear();
		strcpy(temp,"   Funk lernen ");
		DisplayWriteLine(0,0,temp);
		KeyIdx = 0;
		Timer0 = 0;
		HexStatus++;
		break;

	case 7:
		strcpy(temp,FunkTexte[KeyIdx]);
		DisplayWriteLine(1,0,temp);
		HexStatus++;
		IR_InitBuffers();
		if (KeyIdx > 6)
			HexStatus = 6;
		break;
	case 8:
		if ( Rx1WrPtr != Rx1RdPtr && ICTimer == 0)	
		{	
			SampleTrigger = 0;	

			if (Rx1WrPtr > 70  && Rx1WrPtr < 76 && Error == 0)
			{
				Timer0 = 700;
				DisplayClearLine(1);
				strcpy(temp,"OK!");
				DisplayWriteLine(1,0,temp);
				while (Timer0 != 0)
					;
				DisplayClearLine(1);
	
				for (i = 0; i < 3; i++)
				{
					FlashWrite(&Rx1Buff[i*48], FUNK_BASEADR + KeyIdx*0xC0 + i*0x40);
				}

				KeyIdx++;
				HexStatus = 7;
				if (KeyIdx == 6)
				{
					DisplayClearLine(1);
					strcpy(temp,"Fertig!");
					DisplayWriteLine(1,0,temp);
					HexStatus = 15;
				}
				else
					SampleTrigger = 2;	
			}
			else
			{
				Timer0 = 300;
				DisplayClearLine(1);
				strcpy(temp,"Fehler!  ");
				DisplayWriteLine(1,0,temp);

				while (Timer0 != 0)
				{}
				DisplayClearLine(1);
				SampleTrigger = 2;	
				HexStatus = 7;

			}
		}
		

		break;
	}
}
//***************************************************
void IR_InitBuffers(void)
{
int i;
	for (i = 0; i < RX1BUF_LEN; i++)
		Rx1Buff[i] = 0;
	for (i = 0; i < RXBUF_LEN; i++)
		RxBuff[i] = 0;
	Rx1WrPtr = 0;
	Rx1RdPtr = 0;
	Error = 0;
	SampleTrigger = 2;	
	SampleOK = 0;;

	return;
}
//***************************************************
void PlayFile(void)
{
int k, m;
int itemp;

	k = 0;

	if (TempoFlag)
	{
		if (HexStatus == 2)
		{
			if (OldDauerMsec != 0)
				proz = (float) GetPlayTimer() / (float) OldDauerMsec;
			else
				proz = 0.5;
			DauerMsec = CalcDauer(PlaySzeneAkt.Dauer);
			SetPlayTimer((long)( (float)DauerMsec * proz)) ;
		}
		else
		{
			if (OldTransMsec != 0)
				proz = (float) GetPlayTimer() / (float) OldTransMsec;
			else
				proz = 0.5;
			TransMsec = CalcTrans(PlaySzeneAkt.Trans);
			SetPlayTimer((long)( (float)TransMsec * proz)) ;
		}
		TempoFlag = 0;
		OwnItoa(temp,TempoAkt,3,MIT_NULL, NO_LEAD_ZERO);	
		DisplayWriteLine(1,2,temp);
	}

	if (Timer1 == 0 && HexStatus != 0)
	{
		Timer1 = 200;
		strcpy(temp,"Sakt=   Snext=  ");
		OwnItoa(&temp[5],SzeneNrAkt,2,NO_NULL, NO_LEAD_ZERO);	
		OwnItoa(&temp[14],SzeneNrNext,2,NO_NULL, NO_LEAD_ZERO);	
		DisplayWriteLine(2,0,temp);


		strcpy(temp,"D=    . Sec     ");
		itemp = (int)(GetPlayTimer()/1000);
		OwnItoa(&temp[2],itemp,4,NO_NULL, NO_LEAD_ZERO);	
		itemp = (int)(GetPlayTimer()/100)%10;
		OwnItoa(&temp[7],itemp,1,NO_NULL, NO_LEAD_ZERO);	
		if (HexStatus == 2)
			temp[0] = 'D';
		else
			temp[0] = 'T';

		DisplayWriteLine(3,0,temp);
	
	}

	switch(HexStatus)
	{
	case 0:
		FlashRead(&RxBuff[0], FLASH_BASEADR + k * 0x40);
		AnzKacheln = RxBuff[3];
		if (AnzKacheln <= MAX_KACHEL)
		{
			for (k = 0; k < AnzKacheln; k++)
				KachelList[k] = RxBuff[k+12];
			strnfill(FileName,0x0,9);
			strncpy(FileName, &RxBuff[4],8);
			AnzSzenen = RxBuff[2];
		}
		else
		{
			strcpy(temp,"Play - Fehler:");
			DisplayWriteLine(0,0,temp);
			strcpy(temp,"Kein File da.");
			DisplayWriteLine(1,0,temp);

			break;
		}
		strcpy(temp,"Play ");
		DisplayWriteLine(0,0,temp);
		DisplayWriteLine(0,5,FileName);

		strcpy(temp,"T=   % S=   K=  ");
		OwnItoa(&temp[2],TempoAkt,3,NO_NULL, NO_LEAD_ZERO);	
		OwnItoa(&temp[9],AnzSzenen,2,NO_NULL, NO_LEAD_ZERO);	
		OwnItoa(&temp[14],AnzKacheln,2,NO_NULL, NO_LEAD_ZERO);	
		DisplayWriteLine(1,0,temp);

		SzeneNrAkt = AnzSzenen;
		SzeneNrNext = 0;
		Timer1 = 0;
		HexStatus++;
		break;
	case 1:				// Dauer
		IncSzeneNr(&SzeneNrAkt);
		IncSzeneNr(&SzeneNrNext);
		LadeSzeneNr(SzeneNrAkt, &PlaySzeneAkt);
		LadeSzeneNr(SzeneNrNext, &PlaySzeneNext);
		AktKachel = 0;
		DauerMsec = CalcDauer(PlaySzeneAkt.Dauer );
		TransMsec = CalcTrans(PlaySzeneAkt.Trans );
		SetPlayTimer(DauerMsec);
		Timer0 = SEND_DELAY;
		HexStatus++;
		break;
	case 2:				// Alle kacheln durchfahren
		if (GetPlayTimer() == 0)
		{
			SetPlayTimer(TransMsec);
			AktKachel = 0;
			HexStatus++;
			break;
		}
		if (Timer0 != 0)
			break;
		Timer0 = SEND_DELAY;
		SendKachel(KachelList[AktKachel], PlaySzeneAkt.Kachel[AktKachel][ROT],
										PlaySzeneAkt.Kachel[AktKachel][GRUEN],
										PlaySzeneAkt.Kachel[AktKachel][BLAU], SHOW_IMMEDIATE);
		AktKachel++;
		if (AktKachel >= AnzKacheln)
			AktKachel = 0;

		break;

	case 3:

/*
		if (Timer0 != 0)
			break;
		Timer0 = SEND_DELAY;
*/
		if (Tx2WrPtr != Tx2RdPtr)
			break;

		if (GetPlayTimer() == 0)
		{
			HexStatus = 1;
			break;
		}

// die nächsten beiden Berechnungen werden in CalcFarbeShort() benötigt
		fTransMsec = (float) TransMsec;
		proz = (fTransMsec -(float)GetPlayTimer()) / fTransMsec; // Wert zwischen 0.0 und 1.0


// Errechnete Farben erst In AktKachelCol (= Rx1Buff !) speichern
		for (m = 0; m < AnzKacheln; m++)
		{
			for (k = 0; k < 3; k++)
				AktKachelCol[m*3+k] = CalcFarbeShort( PlaySzeneAkt.Kachel[m][k], 
													PlaySzeneNext.Kachel[m][k]);
		}

// Dann errechnete Farben mit den im letzten Durchlauf errechneten Farben vergleichen und bei Ungleichheit
// senden 
		for (m = 0; m < AnzKacheln; m++)
		{
			if (LastKachelCol[m*3+0] != AktKachelCol[m*3+0]
             || LastKachelCol[m*3+1] != AktKachelCol[m*3+1]
             || LastKachelCol[m*3+2] != AktKachelCol[m*3+2])
			{
				SendKachel(KachelList[m], AktKachelCol[m*3+0],
										  AktKachelCol[m*3+1],
										  AktKachelCol[m*3+2], STORE_COL_ONLY);
			}
		}
// Aktuell errechnete Farben nach LastKacheCol (= RxBuff) kopieren
		for (k = 0; k < AnzKacheln * 3; k++)
			LastKachelCol[k] = AktKachelCol[k];


		SendKachel(0xFF, 0,0,0,STORE_COL_ONLY);	// Broadcast, bringt die nur gespeicherten Farben in
												// den Kacheln zur Anzeige

		break;
	}
}
//***************************************************
void LadeSzeneNr(int Nr, void *data )
{
int offset, k, m, idx,p;
int cnt;
int HeaderLen;

	HeaderLen = 12 + AnzKacheln;
	cnt = 4 + AnzKacheln * 3;					// ANzahl Byte / Datensatz, 4 Header, für jede Kache 3 Farben
	offset = HeaderLen + Nr * cnt;		// 

	
	k = offset/0x60;
	m = offset % 0x60;
	idx = 0;
	FlashRead(RxBuff, FLASH_BASEADR + k * 0x40);
	memcpy(data, RxBuff+m, 0x60-m);
	cnt -= (0x60 - m);
	idx = 0x60 - m;
	if( (cnt / 0x60) > 0)
	{
		FlashRead(RxBuff, FLASH_BASEADR + (++k) * 0x40);
		memcpy(data + idx, RxBuff, 0x60);
		cnt -= 0x60;
		idx += 0x60;
	}
	if (cnt > 0)
	{
		FlashRead(RxBuff, FLASH_BASEADR + (++k) * 0x40);
		memcpy(data + idx, RxBuff, cnt);
	}
	return;
}
//***************************************************
void IncSzeneNr(unsigned char *Nr)
{
	(*Nr)++;
	if (*Nr >= AnzSzenen)
		*Nr = 0;
	return;
}
//***************************************************
void DownloadFile(void)
{
int k;

	switch(HexStatus)
	{
	case 0:
		strcpy(temp,"Download File");
		DisplayWriteLine(0,0,temp);
		strcpy(temp,"Warten auf PC...");
		DisplayWriteLine(1,0,temp);
		HexStatus++;
		RxStatus = 0;
		break;
	case 1:				// 
		CheckRx1();
//		if (
		break;
	}
}
//***************************************************
void FirmwareUpdate(void)
{
int k;

	switch(HexStatus)
	{
	case 0:
		strcpy(temp,"Firmware-Update");
		DisplayWriteLine(0,0,temp);
		strcpy(temp,"4711 eingeben  ");
		DisplayWriteLine(1,0,temp);
		strcpy(temp,"und Enter:     ");
		DisplayWriteLine(2,0,temp);
		HexStatus++;
		MenuStatus = 0; MenuIdx = 0; MenuCurX = 0; MenuLine = 3;
		Menu[0].len = 4; Menu[0].pos = 0; strcpy(Menu[0].text,"....");
		Menu[1].len = 0; 		//Ende
		break;
	case 1:				// 
		MenuStateMachine();
		break;
	case 2:				// 
		if (!strcmp("4711",Menu[0].text) )
			HexStatus++;
		else
			HexStatus = 0;
		break;
	case 3:	
		MenuCursorOnOff = OFF;
		SetCursor(MenuCursorOnOff);

		DisplayClear();
		strcpy(temp,"Auf keinen Fall");
		DisplayWriteLine(0,0,temp);

		strcpy(temp,"ausschalten!");
		DisplayWriteLine(1,0,temp);
		strcpy(temp,"Warten bis Down-");
		DisplayWriteLine(2,0,temp);
 		strcpy(temp,"load fertig.");
		DisplayWriteLine(3,0,temp);

		BootEntry();		
		break;
	}
}

//***************************************************
void Wiedergabe(void)		// Im Controler selbst erstelltes Programm, nur Broadcast
{
int k;

	if (TempoFlag)
	{
		if (HexStatus == 2)
		{
			if (OldDauerMsec != 0)
				proz = (float) GetPlayTimer() / (float) OldDauerMsec;
			else
				proz = 0.5;
			DauerMsec = CalcDauer(AutoSzeneAkt.Dauer);
			SetPlayTimer((long)( (float)DauerMsec * proz)) ;
		}
		else
		{
			if (OldTransMsec != 0)
				proz = (float) GetPlayTimer() / (float) OldTransMsec;
			else
				proz = 0.5;
			TransMsec = CalcTrans(AutoSzeneAkt.Trans);
			SetPlayTimer((long)( (float)TransMsec * proz)) ;
		}
		TempoFlag = 0;
		OwnItoa(temp,TempoAkt,3,MIT_NULL, NO_LEAD_ZERO);	
		DisplayWriteLine(0,7,temp);
	}

	if (Timer1 == 0)
	{
		Timer1 = 200;
		OwnItoa(temp,SzeneNrAkt,2,MIT_NULL, NO_LEAD_ZERO);	
		DisplayWriteLine(0,14,temp);
	
		for (k = 0; k < 3; k++)
		{
			strcpy(temp,"   ->   ->   ");
			OwnItoa(temp,AutoSzeneAkt.Farbe[k],3,NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(temp+5,AutoSzeneTemp.Farbe[k],3,NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(temp+10,AutoSzeneNext.Farbe[k],3,NO_NULL, NO_LEAD_ZERO);	
			DisplayWriteLine(k+1, 2 ,temp);
		}
		
	}
	switch(HexStatus)
	{
	case 0:
		strcpy(temp,"Play T=   % S:");
		DisplayWriteLine(0,0,temp);
		strcpy(temp,"R:   ->   ->   ");
		DisplayWriteLine(1,0,temp);
		temp[0] = 'G';
		DisplayWriteLine(2,0,temp);
		temp[0] = 'B';
		DisplayWriteLine(3,0,temp);

		SzeneNrAkt = 0;
		SzeneNrNext = 1;
		TempoFlag = 1;
		HexStatus++;
		SetPlayTimer(0);
		break;
	case 1:				// 
		ReadEEPROM(&AutoSzeneAkt, SzeneNrAkt);
		if ( (AutoSzeneAkt.Dauer == 0 && AutoSzeneAkt.Trans == 0) ||
			 (AutoSzeneAkt.Dauer == 0xFFFF || AutoSzeneAkt.Trans == 0xFFFF) )
		{
			SzeneNrAkt = 0;
			ReadEEPROM(&AutoSzeneAkt, SzeneNrAkt);

		}
		ReadEEPROM(&AutoSzeneNext, SzeneNrNext);
		if ( (AutoSzeneNext.Dauer == 0 && AutoSzeneNext.Trans == 0) ||
			 (AutoSzeneNext.Dauer == 0xFFFF || AutoSzeneNext.Trans == 0xFFFF) )
		{
			SzeneNrNext = 0;
			ReadEEPROM(&AutoSzeneNext, SzeneNrNext);

		}
		DauerMsec = CalcDauer(AutoSzeneAkt.Dauer);

		SendKachel(0xFF, AutoSzeneAkt.Farbe[ROT],
						AutoSzeneAkt.Farbe[GRUEN],
						AutoSzeneAkt.Farbe[BLAU], SHOW_IMMEDIATE);

		AutoSzeneTemp.Farbe[ROT] = AutoSzeneAkt.Farbe[ROT];
		AutoSzeneTemp.Farbe[GRUEN] = AutoSzeneAkt.Farbe[GRUEN];
		AutoSzeneTemp.Farbe[BLAU] = AutoSzeneAkt.Farbe[BLAU];
		SetPlayTimer(DauerMsec);
		HexStatus++;
		break;
	case 2:				// 	Alles lassen bis Dauer abgelaufen
		if (GetPlayTimer() == 0)
		{
			TransMsec = CalcTrans(AutoSzeneAkt.Trans);
			SetPlayTimer(TransMsec);
			HexStatus++;
		}
		break;
	case 3:				// 	Jetzt Übergänge berechnen
/* Alt
		if (Timer0 != 0)
			break;
		else
			Timer0 = SEND_DELAY;
*/

		if (Tx2RdPtr != Tx2WrPtr)
			break;
		if ( GetPlayTimer() == 0)
		{
			SzeneNrAkt++; SzeneNrNext++;
			if (SzeneNrAkt > 99)
				SzeneNrAkt = 0;		
			if (SzeneNrNext > 99)
				SzeneNrNext = 0;		
			HexStatus = 1;
		}
		else
		{

			for (k = 0; k < 3; k++)
				AutoSzeneTemp.Farbe[k] = CalcFarbe( AutoSzeneAkt.Farbe[k], AutoSzeneNext.Farbe[k]);

			SendKachel(0xFF, AutoSzeneTemp.Farbe[ROT],
							AutoSzeneTemp.Farbe[GRUEN],
							AutoSzeneTemp.Farbe[BLAU], SHOW_IMMEDIATE);
		}
		break;
	}
}


//***************************************************
long CalcDauer(int zeit)
{
float ZeitTemp;

	if (zeit == 0)
		return 0;

	ZeitTemp = ( ((float)zeit) * 100.0 * (float)TempoAkt*0.01 );
	if (ZeitTemp < 100.0)
		ZeitTemp = 100.0;

	OldDauerMsec = (long) ZeitTemp;

	return OldDauerMsec;
}
//***************************************************
long CalcTrans(int zeit)
{
float ZeitTemp;

	if (zeit == 0)
		return 0;

	ZeitTemp = ( ((float)zeit) * 100.0 * (float)TempoAkt*0.01 );
	if (ZeitTemp < 100.0)
		ZeitTemp = 100.0;

	OldTransMsec = (long) ZeitTemp;

	return OldTransMsec;
}

//***************************************************
unsigned char CalcFarbe(unsigned char FarbeAkt, unsigned char FarbeNext)
{
int result;
int idiff ;
float fdiff;

	if (TransMsec == 0)
		return FarbeNext;				// wg. Division durch 0

	fTransMsec = (float) TransMsec;
	proz = (fTransMsec -(float)GetPlayTimer()) / fTransMsec; // Wert zwischen 0.0 und 1.0
	idiff = (int)FarbeNext - (int) FarbeAkt;
	fdiff = (float)idiff;
	result = (int) (( fdiff * proz) * 10.0);
	result = iRunden(result);
	result += FarbeAkt;



	return (unsigned char)result;
}
//***************************************************
unsigned char CalcFarbeShort(unsigned char FarbeAkt, unsigned char FarbeNext)
{
int result;
int idiff ;
float fdiff;

	if (TransMsec == 0)
		return FarbeNext;				// wg. Division durch 0

	idiff = (int)FarbeNext - (int) FarbeAkt;
	fdiff = (float)idiff;
	result = (int) (( fdiff * proz) * 10.0);
	result = iRunden(result);
	result += FarbeAkt;



	return (unsigned char)result;
}
//***************************************************
void GateWay(void)
{
int k;
char RxByte;

	switch(HexStatus)
	{
	case 0:
		strcpy(temp,"Gateway");
		DisplayWriteLine(0,4,temp);
		HexStatus++;
		break;
	case 1:				// Warte auf Adresse (Bit 7 = 1)
		if (Rx1WrPtr != Rx1RdPtr)
		{
			RxByte = Rx1Buff[Rx1RdPtr++];
			Rx1RdPtr &= (RX1BUF_LEN -1);
			if (RxByte & 0x80)
			{
				RxBuff[0] = RxByte;
				RxBuffCnt = 1;
				HexStatus++;
			}
		}
		break;
	case 2:				// Warte auf 3 Farben
		if (Rx1WrPtr != Rx1RdPtr)
		{
			RxByte = Rx1Buff[Rx1RdPtr++];
			Rx1RdPtr &= (RX1BUF_LEN -1);
			if (RxByte & 0x80)
			{
				RxBuff[0] = RxByte & 0x7F;
				RxBuffCnt = 1;
			}
			else
			{
				if (RxBuffCnt < 4)
				{
					RxBuff[RxBuffCnt++] = RxByte;
					
				}
				else
				{
					
					RxBuff[0] &= 0x7F;
					if (RxByte & 0x1)
						RxBuff[1] |= 0x80;
					if (RxByte & 0x2)
						RxBuff[2] |= 0x80;
					if (RxByte & 0x4)
						RxBuff[3] |= 0x80;
					SendKachel(RxBuff[0], RxBuff[1], RxBuff[2], RxBuff[3], SHOW_IMMEDIATE);
					RxBuffCnt = 0;
					HexStatus = 1;
				}
			}
		}
		break;
	}
}

//***************************************************
void Manuell(void)
{
int k;
	switch(HexStatus)
	{
	case 0:
		MenuCursorOnOff = OFF;
		strcpy(temp,"rot gruen blau  ");
		DisplayWriteLine(0,0,temp);
		strcpy(temp,"Step Dauer Trans");
		DisplayWriteLine(2,0,temp);
		FarbFlag = 1;		// zwingend die Werte-Anzeige
		HexStatus++;
		MenuStatus = 0; MenuIdx = 0; MenuCurX = 0; MenuLine = 3;
		Menu[0].len = 2; Menu[0].pos = 0; strcpy(Menu[0].text,"..");
		Menu[1].len = 4; Menu[1].pos = 5; strcpy(Menu[1].text,"....");
		Menu[2].len = 4; Menu[2].pos = 11; strcpy(Menu[2].text,"....");
		Menu[3].len = 0; 		//Ende
		break;
	case 1:
		if (FarbFlag != 0 || TempoFlag != 0)
		{
			k = 0;
			FarbFlag = 0;
			TempoFlag = 0;
			strnfill(temp,0x20,16);	
			OwnItoa(temp,FarbenAkt[ROT],3, NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(&temp[5],FarbenAkt[GRUEN],3,NO_NULL, NO_LEAD_ZERO);	
			OwnItoa(&temp[10],FarbenAkt[BLAU],3,NO_NULL, NO_LEAD_ZERO);
//			OwnItoa(&temp[12],TempoAkt,3,NO_NULL);
			SendKachel(0xff, FarbenAkt[0], FarbenAkt[1], FarbenAkt[2], SHOW_IMMEDIATE);
			DisplayWriteLine(1,0,temp);
		}
		MenuStateMachine();
		break;
	}
}
//***************************************************
void MenuStateMachine(void)
{
	switch(MenuStatus)
	{
	case 0:
		MenuStatus++;
		DisplayMenu();
		MenuCursorOnOff = ON;
		MenuCurIdx = 0; MenuCurX = 0;
		SetCursor(MenuCursorOnOff);
		break;
	case 1:
		if (TastFlag)
		{
			TastFlag = 0;
			if (TastAkt >=0 && TastAkt <= 9)		// nprmale Eingabe
			{
				Menu[MenuIdx].text[MenuCurIdx] = TastAkt+0x30;
				IncCursorPos();
//				SetCursorPos(MenuCurX, MenuLine);

				DisplayMenu();
			}
			if (TastAkt == CLEAR)
			{
				HexStatus = 0;
				MenuStatus = 0;
			}
			if (TastAkt == ENTER)
			{
				if (HexAkt == MANUELL)
				{
					int temp = OwnAtoi(Menu[0].text);				
					AutoSzeneAkt.Dauer = OwnAtoi(Menu[1].text);
					AutoSzeneAkt.Trans = OwnAtoi(Menu[2].text);
					AutoSzeneAkt.Farbe[ROT] = FarbenAkt[ROT];
					AutoSzeneAkt.Farbe[GRUEN] = FarbenAkt[GRUEN];
					AutoSzeneAkt.Farbe[BLAU] = FarbenAkt[BLAU];
					WriteEEPROM(&AutoSzeneAkt, temp);
					ReadEEPROM(&AutoSzeneTemp, temp);
					if (temp < 99)
						temp++;
					OwnItoa(Menu[0].text, temp, 2, MIT_NULL, MIT_LEAD_ZERO);	
					MenuIdx = 1; MenuCurIdx = 0; MenuCurX = Menu[1].pos;
					DisplayMenu();
				}
				if (HexAkt == FIRMWAREUPDATE)
				{
					HexStatus++;
				}	
			}
			if (TastAkt == CUR_LEFT)
			{
				DecCursorPos();
			}
			if (TastAkt == CUR_RIGHT)
			{
				IncCursorPos();
			}
		}
		break;
	case 2:
		break;
	
	}
}

//**********
void IncCursorPos(void)
{
	MenuCurIdx++;
	if (MenuCurIdx >= Menu[MenuIdx].len)
	{
		MenuIdx++; MenuCurIdx = 0;
		if (Menu[MenuIdx].len == 0)
		{
			MenuIdx--; MenuCurIdx = Menu[MenuIdx].len -1;
		}  
	}
	MenuCurX = Menu[MenuIdx].pos + MenuCurIdx;
	SetCursorPos(MenuCurX, MenuLine);
}

void DecCursorPos(void)
{
	MenuCurIdx--;
	if (MenuCurIdx == 255)
	{
		MenuCurIdx = 0;
		if (MenuIdx > 0)
		{
			MenuIdx--; MenuCurIdx = Menu[MenuIdx].len - 1;
		}
	}
	MenuCurX = Menu[MenuIdx].pos + MenuCurIdx;
	SetCursorPos(MenuCurX, MenuLine);
}

//***************************************************
void DisplayMenu(void)
{
int i,k,idx;
	i = 0;
	strnfill(temp,0x20,16);
	while (Menu[i].len != 0)
	{
		idx = Menu[i].pos;
		for (k = 0; k < Menu[i].len; k++)
		{
			temp[idx++] = Menu[i].text[k];
		}
		i++;
	}	
	DisplayWriteLine(MenuLine,0,temp);
}
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


/*
	for (i = 0; i < 49; i++)
	{
		adr = i;
		
		zcnt = 0;
		zcnt += CountZeros(rot & 0xFF);
		zcnt += CountZeros(gruen & 0xFF);
		zcnt += CountZeros(blau & 0xFF);
		zcnt |= 0x20;
		Tx2Word(adr | 0x100);		// Bit 9 wg. Adresse setzen
		Tx2Word(rot);
		Tx2Word(gruen);
		Tx2Word(blau);
		Tx2Word(zcnt);


	}
		
	adr = 0xff;
	zcnt = 0;
	zcnt += CountZeros(rot & 0xFF);
	zcnt += CountZeros(gruen & 0xFF);
	zcnt += CountZeros(blau & 0xFF);
	zcnt |= 0x20;
	Tx2Word(0xFF | 0x100);		// Bit 9 wg. Adresse setzen
	Tx2Word(rot);
	Tx2Word(gruen);
	Tx2Word(blau);
	Tx2Word(zcnt);
*/		
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
//***************************************************
void AdScan(void)
{
float ftemp;
int i;
int itemp;
int FarbenTemp[3];

	if (AdTimer == 0)
	{
		AdTimer = 30;		//msec
		FarbenTemp[0] = ADCBUF0;
		FarbenTemp[1] = ADCBUF1;
		FarbenTemp[2] = ADCBUF2;

		for (i = 0; i < 3; i++)
		{
			itemp = (int)((float)FarbenTemp[i]) * (255.0 / 4095.0) * 10.0;	
			FarbenAkt[i] = (unsigned char)iRunden(itemp);
			
			if (FarbenAkt[i] != FarbenOld[i])
			{
				FarbFlag = 1;
				FarbenOld[i] = FarbenAkt[i];
			}	
		}	

		if (OldAdcBuff3 > (ADCBUF3 + 30) || OldAdcBuff3 < (ADCBUF3 - 30) )
		{
			OldAdcBuff3 = ADCBUF3;
			i = (int) (((float)ADCBUF3) * (23.0 / 4095.0) * 10.0);
			i = (unsigned char)iRunden(i);
			TempoAkt = TempoTab[i];
			if (TempoAkt  != TempoOld )
			{
				TempoFlag = 1;	
				TempoOld = TempoAkt;
			}
		}
	}
	else
		return;

i = 0;
}
//***************************************************
void HexScan(void)
{
char HexTemp = 0;
	
	if (HexScanTimer != 0)
		return;
	HexScanTimer = 60;

	if (HEX0 == 0)
		HexTemp += 1;

	if (HEX1 == 0)
		HexTemp += 2;
#if DEBUG == 0
	if (HEX2 == 0)
		HexTemp += 4;
	if (HEX3 == 0)
		HexTemp += 8;
#endif

		HexAkt = HexTemp;
		if (HexAkt != HexOld)
		{
			HexOld = HexAkt;
			HexFlag = 1;
		}

}
//***************************************************
void TastScan(void)
{
int row, col;

	switch(TastStatus)
	{
	case 0:
		SetDispDatabusDir(OUTPUT);
		TastSetColPins(INPUT);
		for (row = 0; row < 4; row++)
		{
			TastSetRow(row);
//			int i; for (i = 0; i < 200; i++);;
			col = TastGetCol();
			if (col != 0)
			{
				TastTemp = row * 4 + col;
				goto EndScan1;
			}
		}
		TastTemp = 0;
EndScan1:
		TastStatus++;			
		TastSetColPins(INPUT);
		break;
	case 1:
		TastTimer = 20;
		TastStatus++;
		break;
	case 2:
		if (TastTimer == 0)
			TastStatus++;
		break;
	case 3:
		SetDispDatabusDir(OUTPUT);
		TastSetColPins(INPUT);
		for (row = 0; row < 4; row++)
		{
			TastSetRow(row);
//			int i; for (i = 0; i < 200; i++);;
			col = TastGetCol();
			if (col != 0)
			{
				if (TastTemp == row * 4 + col)
				{
					goto EndScan2;
				}			
			}
		}
		TastTemp = 0;
EndScan2:
		TastStatus++;
		TastSetColPins(INPUT);
		break;
	case 4:
		TastAkt = TastTab[TastTemp];
		if (TastOld != TastAkt)
		{
			TastOld = TastAkt;
			TastFlag = 1;
		}
		TastStatus = 0;
		break;
	}
}

void TastSetRow(char row)
{
	DISP_RW = 0;
	DISP_D4_PIN = 0;
	DISP_D5_PIN = 0;
	DISP_D6_PIN = 0;
	DISP_D7_PIN = 0;
	PORTD &= 0xFFFC;
	PORTB &= 0xE7FF;
	switch(row)
	{
	case 0:
		DISP_D4 = 1;
		break;
	case 1:
		DISP_D5 = 1;
		break;
	case 2:
		DISP_D6 = 1;
		break;
	case 3:
		DISP_D7 = 1;
		break;
		}		
}

char TastGetCol(void)
{
char col = 0;
	if (TAST_COL0 == 1)
		col = 1;
	if (TAST_COL1 == 1)
		col = 2;
	if (TAST_COL2 == 1)
		col = 3;
	if (TAST_COL3 == 1)
		col = 4;

	return col;
}

void TastSetColPins(int dir)
{
int IOrow = dir;
	TAST_COL0_PIN = IOrow;
	TAST_COL1_PIN = IOrow;
	TAST_COL2_PIN = IOrow;
	TAST_COL3_PIN = IOrow;
}
//***************************************************
void InitTimer1(void)
{

	PR1 = 16000;		
	T1CONbits.TON = 1;
	IPC0bits.T1IP = 5;
	IEC0bits.T1IE = 1;

}
//***************************************************
void InitAD(void)
{
#define AD_CHANNELS 0B1111	// Bitmuster, für jeden benutzten 
								// AN-Kanal eine 1 

	ADCON1 = 0; 				// A/D Control Register 1
	ADCON2 = 0; 				// A/D Control Register 2
	ADCON3 = 0; 				// A/D Control Register 3
	ADCHS  = 0; 				// A/D Input Channel Select Register
	ADPCFG = 0xffff;			// A/D Port Configuration Register
	ADCSSL = 0x0; 				// A/D Input Scan Selection Register		

	ADCON1bits.FORM = 0x0;		// integer (= 0000dddddddddddd)
	ADCON1bits.SSRC = 0b111;	// Internal counter ends sampling and starts conversion (auto convert)
	ADCON1bits.ASAM = 1;		// Sampling begins immediately after last conversion completes. SAMP bit is auto set


	ADCON2bits.VCFG = 0b111;	// Voltage Referenze = AVCC und AGND
	ADCON2bits.SMPI = 0b110;	// Voltage Referenze = AVCC und AGND
	ADCON2bits.CSCNA = 1;		// Do automatic Input Scan


	ADCON3bits.SAMC = 4;		// Autosample bits (# of TADs to Sampling Time)
								// = 3.5 usec SampleTime
	ADCON3bits.ADCS = 13;		// A/D Conversion Clock Select bits 
								// = 0.875usec TAD
								// = 12.25usec ConversionTime (ohne Sampling)
								// = 16 us * 6 = < 100usec für alle 6 Kanäle

	ADCHSbits.CH0NA = 0;		// Channel 0 negative input is VREF
//	ADCON2bits.CHOSA = egal		// weil Input Scan

	ADPCFG &= ~AD_CHANNELS;		// AN0-AN5 sind Analog-Eingänge
	ADCSSL = AD_CHANNELS;		// Input Scan Select (alle)

	ADCON1bits.ADON = 1;		// Start 

	return;
}
//***************************************************
void InitHexSchalter(void)
{
	HEX0_PIN = INPUT;
	HEX1_PIN = INPUT;
#if DEBUG == 0
	HEX2_PIN = INPUT;
	HEX3_PIN = INPUT;
#endif
	
}
//***************************************************
void InitUart1(void)
{

	U1BRG = 51;					// = 19.200 Bauf bei 16MHz CPU-Clock (fosc = 64MHz)
	U1MODEbits.UARTEN = 1;		// UART Module Enable
	U1MODEbits.STSEL = 0;		// 1 Stopbits
	U1MODEbits.PDSEL = 0;		// 8 bits, kein Parity
	U1STAbits.UTXISEL = 1;		// TxInt wenn interner Buffer leer
	U1STAbits.ADDEN = 0;		// Kein Adress-Modus
	U1STAbits.UTXEN = 1;		// Transmitter enable

	IPC2bits.U1RXIP = 3;		// Priorität 3
	IPC2bits.U1TXIP = 3;		// Priorität 3
	IEC0bits.U1RXIE = 1;			// enable Rx-Int
	IEC0bits.U1TXIE = 1;			// enable Tx-Int

}
//***************************************************
void InitUart2(void)
{

	U2BRG = 17;					// = 19.200 Bauf bei 16MHz CPU-Clock (fosc = 64MHz)
	U2MODEbits.UARTEN = 1;		// UART Module Enable
	U2MODEbits.STSEL = 1;		// 2 Stopbits
	U2MODEbits.PDSEL = 0B11;	// 9 bits, kein Parity
	U2STAbits.UTXISEL = 1;		// TxInt wenn interner Buffer leer
	U2STAbits.ADDEN = 1;		// 9bit-Übertragung
	U2STAbits.UTXEN = 1;		// Transmitter enable

	IPC6bits.U2TXIP = 3;		// Priorität 3
	IEC1bits.U2TXIE = 1;			// enable Tx-Int

	TX2ENA_PIN = 0;
	TX2ENA = 1;					// TX-Enable am RS485-Treiber-Baustein


	return;
}
//***************************************************
void InitInputCapture2(void)
{
//-------- Timer 2 Init -----------

T2CONbits.TON = 1;		
T2CONbits.TCKPS = 1; 	// Prescale 8

	TRISDbits.TRISD9 = 1;	// input
	IC2CONbits.ICTMR = 1;	// Timer 2
	IC2CONbits.ICM = 1;		// Interrupt auf jede Flanke
	IPC1bits.IC2IP = 6;		// Interrupt-Priority
	IFS0bits.IC2IF = 0;		// Clear Interruptflag	
	IEC0bits.IC2IE = 1;		// Interruptenable	

	return;
}
//***************************************************
void DummyFunc(void)
{

	return;
}
//***************************************************
int iRunden(int zahl)
{	
int res;
	if ((zahl % 10) >= 5)	
		res = zahl/10 + 1;
	else
		res = zahl / 10;

	return res;
}
//***************************************************
void ZeichenUmsetzen(char *string,int len)
{
int i;

	for (i = 0; i < len; i++)
	{
		switch(string[i])
		{
			case 0x15:		// Omega
				string[i] = 0x91;
				break;
			case 0x16:		// Alpha
				string[i] = 0x85;
				break;
			case 0x17:		// Grad
				string[i] = 0xA0;
				break;
			case 0x18:		// mue
				string[i] = 0xA5;
				break;
			case 0x19:		// Beta
				string[i] = 0xDF;
				break;
		}
	}

	return;
}
//***************************************************
void Tx2Word(int Txwort)
{

	Tx2Buff[ Tx2WrPtr++] = Txwort;
	Tx2WrPtr &= (TX2BUF_LEN - 1);

	return;
}
//***************************************************
void Tx1Char(char byte)
{

	Tx1Buff[ Tx1WrPtr++] = byte;
	Tx1WrPtr &= (TX1BUF_LEN - 1);

	return;
}
//***************************************************/

void OwnItoa(char *str, int Value, int Stellen, int AppendNull, int SupressLeadingZeros)
{
unsigned int iValue;
int idx;
unsigned int temp;
char NotZeroFlag;

	iValue = (unsigned) Value;
	NotZeroFlag = 0;
	idx = 0;
	
	if (Stellen == 1)
		goto EineStelle;
	if (Stellen == 2)
		goto ZweiStellen;
	if (Stellen == 3)
		goto DreiStellen;
	if (Stellen == 4)
		goto VierStellen;

// Zehntausender
	temp = iValue / 10000;
	if (temp != 0)
	{
		str[idx++] = temp + 0x30;
		NotZeroFlag = 1;
	}
	if (temp > 9)
		temp++;
VierStellen:
// Tausender
	temp = (iValue % 10000) / 1000;
	str[idx++] = temp + 0x30;

DreiStellen:
// Hunderter
	temp = (iValue % 1000) / 100;
	str[idx++] = temp + 0x30;

ZweiStellen:
// Zehner
	temp = (iValue % 100) / 10;
	str[idx++] = temp + 0x30;
EineStelle:
//Hundertstel
	temp = (iValue % 10) ;
	str[idx++] = temp + 0x30;

// Stringende
	if (AppendNull == MIT_NULL)
		str[idx++] = 0;

// führende 0-Unterdrückung

	if (SupressLeadingZeros == NO_LEAD_ZERO && Stellen > 1)
	{
		for (idx = 0; idx < Stellen-1; idx++)
		{
			if (str[idx] != 0x30)
				break;
			else
				str[idx] = 0x20;		// Blank
		}
	}

	return;
}
//***************************************************
void strnfill(char *str, char fill, int cnt)
{
int i;

	for (i = 0; i < cnt; i++)
		str[i] = fill;

	str[cnt] = 0x0;	
} 

//***************************************************
void WriteEEPROM( _AutoSzene *data , int SzeneNr)
{
int adr;
#if DEBUG == 1
	SzeneNr+=0;		// wg. defektem EEPROM
#endif

	adr = (SzeneNr/4) * 0x20 + 0xFC00;

	ReadEE(0x7f, adr, temp, 16);
	memcpy( &temp[(SzeneNr%4)*8], data, 8);
	EraseEE(0x7f, adr, 16);

	WriteEE(temp, 0x7f, adr, 16);

}
//***************************************************
void ReadEEPROM(_AutoSzene *data, int SzeneNr)
{
int adr;
#if DEBUG == 1
	SzeneNr +=0;		// wg. defektem EEPROM
#endif

	adr = (SzeneNr/4) * 0x20 + 0xFC00;

	/*Read array named "fooArrayinDataEE" from DataEEPROM and place the result into*/
	/*array in RAM named, "fooArray2inRAM" */
	ReadEE(0x7f, adr, temp, 16);
	memcpy(data, &temp[(SzeneNr%4)*8], 8);

}
//***************************************************
int OwnAtoi(char *str)
{
int k;
int start = 1;
int result = 0;

	k = strlen(str) - 1;
	while (k >= 0)
	{
		if (str[k] >= 0x30 && str[k] <= 0x39)
		{
			result += (str[k] - 0x30) * start;
			start *= 10;
		}
		k--;
	}
	return result;
}
//***************************************************
void CheckRx1(void)
{
char RxByte;
int CharReceived;

	CharReceived = ReadCharCom1(&RxByte);
	switch(RxStatus)
	{
		case 0:				// Warten auf STX
			if (RxByte == STX)
			{
				Rx1Timer = TO_RX1;	// msec
				RxStatus++;		// = Receive Characters und Wait ETX
			}
			else
			{
				return;
			}
			break;
		case 1:			  // Receive Characters + Warten auf ETX + Watch Rx-Timeout
			if (Rx1Timer == 0)
			{
				RxStatus = 3;	// Status zurücksetzen da TimeOut, kein NAK
			}
			if (RxByte == ETX)
			{
				RxStatus++;		// Telegramm verarbeiten
				Rx1Timer = 0;		// Timer Reset
				break;
			}
			if (RxBuffCnt == 210)	// Overrun, keine Telegramme > 128 erlaubt
			{
				RxStatus = 3;	// Status zurücksetzen
				Rx1Timer = 0;		// Timer Reset
				break;
			}
			if (CharReceived)
			{
				RxBuff[ RxBuffCnt++] = RxByte;
				Rx1Timer = TO_RX1;		// Timer Restart
			}
			break;
		case 2:					// Telegramm empfangen, Checksumme prüfen und verarbeiten
			if ( CheckPruefSumme() == -1)	// -1 = Fehler
				SendNAK();
			else
				CommandDispatch();

			RxStatus++;			// Nächster Schritt = Ende
			break;
		case 3:					// Ende StateMachine Receive Telegram
			RxStatus = 0;		// Warte auf STX
			RxBuffCnt = 0;		// Write-Ptr für C-internen Speicher rücksetzen
			break;
	}
	return;
}
//***************************************************

void CommandDispatch(void)
{int i,k;
int MaxFileSize;

	switch(RxBuff[0])
	{
	case 'I':		// Version zurückschicken
		Tx1Char('I');	
		Tx1Char( (char) (VERSION & 0xFF ) );		// Low Word	
		Tx1Char( (char) ((VERSION >>8)& 0xFF) );		// High Word

		MaxFileSize = 0x7fff - FLASH_BASEADR - 0x200;		// Max. verfügbarer Speicherplatz
		Tx1Char( (char) ((MaxFileSize >>8)& 0xFF) );		// High Word
		Tx1Char( (char) (MaxFileSize & 0xFF ) );		// Low Word	

		Tx1Char( (char) (MAX_KACHEL & 0xFF) );		// Max. Anzahl Kacheln

				

		strnfill(temp,0x20,16);
		temp[16] = 0;
		DisplayWriteLine(2,0,temp);
		
		break;
	case 'D':		// Play-File Daten
		SendACK();
		ConvertToBin();	// Hex to bin

		if (RxBuff[0] == 0)
		{
			strcpy(temp,"Empf->");
			strncpy(&temp[6], &RxBuff[5],8); 
			DisplayWriteLine(0,0,temp);
			
		}

		strnfill(temp,0x20,16);
		temp[16] = 0;
		for (i = 0; i < RxBuff[0] % 14; i++)
			temp[i] = '-';
		temp[i] = '>';
		DisplayWriteLine(1,0,temp);
		FlashWrite(&RxBuff[1], FLASH_BASEADR + ((int)RxBuff[0]) * 0x40);
		break;
	case 'E':		// Ende der Übertragung
		SendACK();
		strcpy(temp,"fertig, 0 Errors");
		DisplayWriteLine(2,0,temp);
		break;	


	}

}
//***************************************************

void SendACK(void)
{
	Tx1Char(ACK);
	return;
}
//***************************************************

void SendNAK(void)
{
	Tx1Char(NAK);
	return;
}

//***************************************************

int CheckPruefSumme(void)
{
int i;
int CalcPruefSum;	// errechnete Prüsumme
int RecPruefSum;

	CalcPruefSum = 0;						// Startwert
	for (i = 0; i < RxBuffCnt-2; i++)		// RxBuffCnt-2 weil letzte 2 Byte (hex!) ist die Checksumme, geht nicht in die Berechnung ein
	{
		CalcPruefSum ^= RxBuff[i];			// ^ ist der XOR-Operator in C
	}

	RecPruefSum = HexToUchar (RxBuff[RxBuffCnt-2], RxBuff[RxBuffCnt-1] );

	if (CalcPruefSum == RecPruefSum  )
		return 0;
	else
		return -1;
}
//***************************************************
unsigned char  HexToUchar(char HighNibble, char LowNibble)
{

	unsigned char  ReturnValue;

	if (HighNibble >= '0' && HighNibble <= '9')
		ReturnValue = (HighNibble - 0x30) * 16;
	else
		ReturnValue = (HighNibble - 55) * 16;


	if (LowNibble >= '0' && LowNibble <= '9')
		ReturnValue += LowNibble - 0x30;
	else
		ReturnValue += LowNibble - 55;


	return ReturnValue;
}
//***************************************************
void ConvertToBin(void)
{
int i;
unsigned char byte;

	for (i = 1; i < RxBuffCnt -3; i++)	// RxCount - 3 wg: 'P' am Anfang und Pruefsumme am Ende
	{
		byte = HexToUchar(RxBuff[i], RxBuff[i+1]);		
		RxBuff[i/2] = byte;
		i++;
	}	
	return;
}
//***************************************************
void UcharToHex(char Byte, char *Dest)
{
int temp;

	temp = Byte/16;
	temp = temp &0xf;
	if ( temp  < 0xA)
		*Dest++ = temp + 0x30;
	else
		*Dest++ = temp + 55;


	if ( (Byte & 0xF) < 0xA)
		*Dest++ = (Byte & 0xF) + 0x30;
	else
		*Dest++ = (Byte & 0xF) + 55;

	*Dest++ = ETX;
	*Dest = 0x0;

	return;
}
//***************************************************

int ReadCharCom1(char *zeichen)
{
	if(Rx1WrPtr == Rx1RdPtr)
	{
		*zeichen = 0;
		return 0;
	}
	*zeichen = Rx1Buff[ Rx1RdPtr++ ];

	Rx1RdPtr &= RX1BUF_LEN-1;
	return 1;
}
//***************************************************
long GetPlayTimer(void)
{
	asm ("disi #10");			// Interrupt Disable für 10 Zyklen wg. 32-Bit Zugriff!
	return PlayTimer;	

}
//***************************************************
void SetPlayTimer(long int value)
{
	asm ("disi #20");			// Interrupt Disable für 10 Zyklen wg. 32-Bit Zugriff!
	PlayTimer = value;
	return;	

}
