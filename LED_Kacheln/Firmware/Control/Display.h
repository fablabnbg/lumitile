// Display-Konstanten

#define LINE_LENGTH 16
#define DISP_DELAY 20		// Zählerschleife, damit Signal ENA für Display > 1usec

#define DISP_REGSEL		PORTAbits.RA11	// Register-Select
#define DISP_RW		PORTDbits.RD3	// Read/Write
#define DISP_ENA	PORTBbits.RB5	// Enable 

#define DISP_REGSEL_PIN		TRISAbits.TRISA11	// Register-Select
#define DISP_RW_PIN		TRISDbits.TRISD3	// Read/Write
#define DISP_ENA_PIN	TRISBbits.TRISB5	// Enable 

#define INPUT 1
#define OUTPUT 0

#define DISP_D0	PORTBbits.RB4
#define DISP_D1	PORTBbits.RB8
#define DISP_D2	PORTBbits.RB9
#define DISP_D3	PORTBbits.RB10
#define DISP_D4	PORTBbits.RB11
#define DISP_D5	PORTBbits.RB12
#define DISP_D6	PORTDbits.RD0
#define DISP_D7	PORTDbits.RD1

#define DISP_D0_PIN	TRISBbits.TRISB4
#define DISP_D1_PIN	TRISBbits.TRISB8
#define DISP_D2_PIN	TRISBbits.TRISB9
#define DISP_D3_PIN	TRISBbits.TRISB10
#define DISP_D4_PIN	TRISBbits.TRISB11
#define DISP_D5_PIN	TRISBbits.TRISB12
#define DISP_D6_PIN	TRISDbits.TRISD0
#define DISP_D7_PIN	TRISDbits.TRISD1

//*********************************
//          Funktionsprotoypen
//*********************************

void DisplayInit(void);
void DisplayWrite(char Byte);
void DoWhileDisplayBusy(void);

void DisplayWriteLine(int line, int col, char *str);
void DisplayClearLine(int line);
void DispDelay(int);
void SetDispDatabusDir(int dir);	// Setzt die Datenbusrichtung,
									// 0 = alles Ausgänge
									// 1 = alles Eingänge
void DisplayInit(void);
void DispSetPinsForCommand(void);

void SetCursor(char OnOff);
void SetCursorPos(char X, char Y);

