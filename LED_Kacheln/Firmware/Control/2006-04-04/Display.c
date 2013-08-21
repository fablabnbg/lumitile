#include "Display.h"
#include <p30f3014.h>


extern char MenuCursorOnOff;		// 1 = On, 0 = off;
extern char MenuCurX;
extern char MenuLine;
extern char temp[];

//***************************************************
int Zeile;
int Spalte;


void DisplayClearLine(int line)
{
	strcpy(temp,"                ");
	DisplayWriteLine(line,0,temp);
	return;
}

void DisplayWriteLine(int line, int col, char *str)
{
int i;

	SetCursor(0);				// Cursor Off
	SetCursorPos(col, line);
	str[LINE_LENGTH] = 0x0;
	for (i =0; i < strlen(str); i++)
	{
		DisplayWrite(str[i]);
	}
	SetCursorPos(MenuCurX, MenuLine);
	SetCursor(MenuCursorOnOff);
}
//***************************************************
void SetCursorPos(char col, char line)
{
char DDRamAdress;

	switch(line)
	{
	case 0:
		DDRamAdress = 0x80;
		break;
	case 1:
		DDRamAdress = 0xC0;
		break;
	case 2:
		DDRamAdress = 0x80 + LINE_LENGTH;	// stimmt nur bei 4-zeiligen Displays
		break;
	case 3:
		DDRamAdress = 0xC0 + LINE_LENGTH;	// stimmt nur bei 4-zeiligen Displays
		break;
	}
	DDRamAdress += col;

	DISP_REGSEL = 0;
	DISP_RW = 0;
	DisplayWrite(DDRamAdress);
	
	DISP_REGSEL = 1;

	return;
}
//***************************************************
void SetCursor(char OnOff)
{
	DispSetPinsForCommand();
	if (OnOff == 0)
		DisplayWrite(0xC);		// Cursor Off
	else
		DisplayWrite(0xF);		// Cursor On + Blink
	return;
}

//***************************************************

void DisplayWrite(char Byte)
{
	DoWhileDisplayBusy();

	DISP_D0 = Byte & 0x1; Byte >>= 1;
	DISP_D1 = Byte & 0x1; Byte >>= 1;
	DISP_D2	= Byte & 0x1; Byte >>= 1;
	DISP_D3	= Byte & 0x1; Byte >>= 1;
	DISP_D4	= 1;

	DISP_D4	= Byte & 0x1; Byte >>= 1;


	DISP_D5	= Byte & 0x1; Byte >>= 1;
	DISP_D6	= Byte & 0x1; Byte >>= 1;
	DISP_D7	= Byte & 0x1; Byte >>= 1;

	DISP_ENA = 1;
	DispDelay(DISP_DELAY);
	DISP_ENA = 0;		//  Wert übernehmen

	return;
}

//***************************************************

void DoWhileDisplayBusy(void)
{
int TempFlag;

	TempFlag = DISP_REGSEL;

	SetDispDatabusDir(INPUT);	// Alles Eingänge

	DISP_RW = 1;
	DISP_REGSEL = 0;
	

	while (1)
	{
		DISP_ENA = 1;	
		DispDelay(DISP_DELAY);
		if (DISP_D7 == 0)
			break;
		DISP_ENA = 0;	
		DispDelay(DISP_DELAY);
	}

	
	DISP_ENA = 0;
	
	SetDispDatabusDir(OUTPUT);	// Alles Ausgänge

	DISP_RW = 0;
	DISP_REGSEL = TempFlag;
	

	return;
}

//***************************************************


void DispSetPinsForCommand(void)
{
	DISP_REGSEL_PIN	= OUTPUT;		// Register-Select
	DISP_RW_PIN	= OUTPUT;			// Read/Write
	DISP_ENA_PIN = OUTPUT;			// Enable 
	DISP_ENA = 0;
	DISP_RW = 0;
	DISP_REGSEL = 0;

}
//***************************************************


void DisplayClear(void)
{
	DispSetPinsForCommand();

	DisplayWrite(0x1);		// Display Clear

}
//***************************************************


void DisplayInit(void)
{

	DispSetPinsForCommand();

	DisplayWrite(0x3e);
	DisplayWrite(0x8);

	DisplayWrite(0x38);

	DisplayWrite(0xc);		// Display ON Cursor Off

	DisplayWrite(0x1);		// Display Clear


	DisplayWrite(0x6);		// ENTER Mode SET Increment

	Zeile = 0;
	Spalte = 0;
	return;
}

//**********************
void DispDelay( int TC)
{
int i;

	for (i = 0; i < TC; i++)
		i = i;
	return;

}
//**********************
void SetDispDatabusDir(int dir)
{
int IOdir;

	IOdir = dir;
	DISP_D0_PIN = IOdir;
	DISP_D1_PIN = IOdir;
	DISP_D2_PIN = IOdir;
	DISP_D3_PIN = IOdir;
	DISP_D4_PIN = IOdir;
	DISP_D5_PIN = IOdir;
	DISP_D6_PIN = IOdir;
	DISP_D7_PIN = IOdir;


}
