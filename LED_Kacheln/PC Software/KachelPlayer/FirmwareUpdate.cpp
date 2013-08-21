// FirmwareUpdate.cpp: Implementierungsdatei
//

#include "stdafx.h"
#include "ESCollect.h"
#include "FirmwareUpdate.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

/////////////////////////////////////////////////////////////////////////////
// Dialogfeld CFirmwareUpdate 


CFirmwareUpdate::CFirmwareUpdate(CWnd* pParent /*=NULL*/)
	: CDialog(CFirmwareUpdate::IDD, pParent)
{
	//{{AFX_DATA_INIT(CFirmwareUpdate)
	m_Adresse = _T("");
	//}}AFX_DATA_INIT
}


void CFirmwareUpdate::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CFirmwareUpdate)
	DDX_Control(pDX, IDC_PROGRESS, m_Progress);
	DDX_Text(pDX, IDC_ADRESSE, m_Adresse);
	//}}AFX_DATA_MAP
}


BEGIN_MESSAGE_MAP(CFirmwareUpdate, CDialog)
	//{{AFX_MSG_MAP(CFirmwareUpdate)
	ON_BN_CLICKED(IDC_OPENHEXFILE, OnOpenhexfile)
	ON_BN_CLICKED(IDC_VERIFY, OnVerify)
	ON_BN_CLICKED(IDC_UPLOAD, OnUpload)
	ON_WM_TIMER()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// Behandlungsroutinen für Nachrichten CFirmwareUpdate 

void CFirmwareUpdate::OnOpenhexfile() 
{
char temp[STRLEN];
char  	szFilter[256] = "Intel Hex-File (*.HEX)|*.HEX";
char chReplace = '|';
int ret;
char RecBuff[STRLEN+1];				// enthält die HEX_bytes einer Zeile
unsigned char BinBuff[STRLEN+1];	// enthält die Binärbytes einer Zeile
FILE *fp;
int i;
int Ignore;	
int Adress;
int FileError;

	for ( i = 0; szFilter[i] != '\0'; i++) {
		if (szFilter[i] == chReplace)
			 szFilter[i] = '\0';
	}

	CFileDialog Open(TRUE);
	Open.m_ofn.lpstrTitle = "HEX-File öffnen";
	Open.m_ofn.lpstrFilter = szFilter;
	Open.m_ofn.Flags |=  OFN_FILEMUSTEXIST;
	Open.m_ofn.lpstrInitialDir = sWorkingDir;
	
	ret = Open.DoModal();
	
	if (ret== IDOK)
	{
		cWorkingDir = Open.GetPathName();
		strcpy(sWorkingDir,cWorkingDir.GetBuffer(STRLEN) );
		
		SetWindowText( "Firmware Update --> "+Open.GetFileName());
		fp = fopen(sWorkingDir, "rb");
		if (fp != NULL)
		{
			m_Adresse = sWorkingDir;

			for (i = 0; i < HEXBUFF_LEN; i++)
			{
				HexData[i].data[0] = 0xff;
				HexData[i].data[1] = 0xff;
			}

			FileError = 0;
			Ignore = 1;
			while(fgets(RecBuff,STRLEN,fp) != NULL)
			{
				strupr(RecBuff);
				if (ConvertRecord(RecBuff, BinBuff) == 0)
				{
					if (BinBuff[3] == 0x4 && BinBuff[4] == 0 && BinBuff[5] == 0)
						Ignore = 0;
					if (BinBuff[3] == 0x4 && (BinBuff[4] != 0 ||BinBuff[5] != 0) )
						Ignore = 1;
					if ( !Ignore && BinBuff[3] == 0x0)
					{
						Adress = (BinBuff[1] * 256 + BinBuff[2]) / 2;
						if (Adress == 0x4)
							int test=1;
						for (i = 0; i < BinBuff[0] / 4; i++)	// 4 Bytes pro Adresse für dsPic, das 4. als Füller (immer 0)
						{
							HexData[Adress+i*2].data[0] = BinBuff[4 + i*4 + 0];
							HexData[Adress+i*2].data[1] = BinBuff[4 + i*4 + 1];
							HexData[Adress+i*2+1].data[0] = BinBuff[4 + i*4 + 2];
						}
					}
				}
				else
					FileError = 1;
			}	
			fclose(fp);
			if (!FileError)
			{
//				GetDlgItem(IDC_VERIFY)->ShowWindow(SW_SHOW);
//				GetDlgItem(IDC_RESTART)->ShowWindow(SW_SHOW);
				GetDlgItem(IDC_UPLOAD)->ShowWindow(SW_SHOW);

			}

		}
		else
		{
			sprintf(temp,"File %s kann nicht geschrieben werden",sWorkingDir);
			AfxMessageBox(temp ,MB_OK |MB_ICONEXCLAMATION);	
		}

		UpdateData(FALSE);
	}
	

	
}

void CFirmwareUpdate::OnVerify() 
{
char temp[STRLEN+1];
DWORD RxCount;
int VerifyError;
int i;
char StatusMeldung[STRLEN+1];


	UpdateStatus = 2;

	sprintf(temp,"%cFWUP:",STX);
	AppendPruefsumme(temp);
	strcat(temp,"\x3");
	Comm->Tx(temp,strlen(temp) );
	Sleep(RX_TIMEOUT);
	Comm->Rx(temp,&RxCount,STRLEN);

	temp[RxCount] = 0;
	if (RxCount == 1 && temp[0] == ACK)
		int test =1;

	VerifyError = 0;

	m_Progress.ShowWindow(SW_SHOW);
	m_Progress.SetRange(0,0x3C00/0x40);
	GetDlgItem(IDCANCEL)->ShowWindow(SW_HIDE);
	GetDlgItem(IDOK)->ShowWindow(SW_HIDE);
			


	for (i = 0; i < 0x3c00/0x40 ; i++)
	{

		sprintf(temp,"%cV",STX);
		sPrintRow( i * 0x40, &temp[strlen(temp)] );

		sprintf(StatusMeldung,"Verify Adresse %d",i * 0x20 + 0x20);
		m_Adresse = StatusMeldung;
		UpdateData(FALSE);

		AppendPruefsumme(temp);
		strcat(temp,"\x3");
		Comm->Tx(temp,strlen(temp) );
		Sleep(30);
		Comm->Rx(temp,&RxCount,STRLEN);
		if (RxCount != 1 || temp[0] != ACK)
		{
			VerifyError = 1;
			break;
		}
		m_Progress.SetPos((unsigned int)(i) );
		MSG msg;
		while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE))
		{
			if (msg.message == WM_QUIT)
				return  ;

			TranslateMessage(&msg);
			DispatchMessage(&msg);
		}
		if (WatchdogFlag)
		{
			WatchdogFlag = 0;
						
			sprintf(temp,"%cW",STX);		// Watchdog triggern
			AppendPruefsumme(temp);
			strcat(temp,"\x3");
			Comm->Tx(temp,strlen(temp) );
			Comm->Rx(temp,&RxCount,STRLEN);

		}

	}
	if (VerifyError)
	{
		strcat(StatusMeldung," --> Fehler!");
		m_Adresse = StatusMeldung;
	}
	else
	{
		m_Adresse = "Verify ok!";
		
	}
	m_Progress.ShowWindow(SW_HIDE);
	GetDlgItem(IDCANCEL)->ShowWindow(SW_SHOW);
	GetDlgItem(IDOK)->ShowWindow(SW_SHOW);

	UpdateData(FALSE);
	UpdateStatus = 0;
	
}

BOOL CFirmwareUpdate::OnInitDialog() 
{
	CDialog::OnInitDialog();
	
	UpdateStatus = 0;
	WatchdogFlag = 0;

	SetTimer(1000,500,NULL);	// In diesem Handler wird zyklisch ein Flag gesetzt,
								// das das Aussenden 
	
	return TRUE;  // return TRUE unless you set the focus to a control
	              // EXCEPTION: OCX-Eigenschaftenseiten sollten FALSE zurückgeben
}

//**************************************

int CFirmwareUpdate::ConvertRecord(char *RecBuff, unsigned char *BinBuff) 
{
int idx = 0;
unsigned char length;
int i;

	if ( *(RecBuff++) != ':')
	{
		AfxMessageBox("Das File ist kein gültiges HEX-File!",MB_OK |MB_ICONEXCLAMATION);	
		return -1;
	}
	
	length = HexToBin(RecBuff);
	*(BinBuff++) = length;
	RecBuff += 2;						// auf nächstes Zeichenpaar stellen
	for (i = 0; i < length + 3; i++)	// + 3 wg. Adr High, Adr Low und RecordType
	{
		*(BinBuff++) = HexToBin(RecBuff);
		RecBuff += 2;					// auf nächstes Zeichenpaar stellen
	}

	return 0;

}


//**************************************
unsigned char CFirmwareUpdate::HexToBin(char *RecBuff) 
{
unsigned char  ReturnValue;
	
	if (*RecBuff >= '0' && *RecBuff <= '9')
		ReturnValue = (*RecBuff - 0x30) * 16;
	else
		ReturnValue = (*RecBuff - 55) * 16;


	if ( *(RecBuff+1) >= '0' && *(RecBuff+1) <= '9')
		ReturnValue += *(RecBuff+1) - 0x30;
	else
		ReturnValue += *(RecBuff+1) - 55;


	return ReturnValue;

	

}

//**************************************

void CFirmwareUpdate::AppendPruefsumme(char *str) 
{

int i;
int Pruefsumme = 0;

char HexTab[] = {'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F',};

	for (i = 1; i < (signed)strlen(str); i++)
	{
		Pruefsumme ^= str[i];
	}
	str[i++] = HexTab[ Pruefsumme>>4 ];
	str[i++] = HexTab[ Pruefsumme & 0xf];
	str[i++] = 0;
}

//**************************************

void CFirmwareUpdate::sPrintRow(int Adr, char* str) 
{
int k, m;
char HexTab[] = {'0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F',};
unsigned char byte;


// zuerst Adresse schreiben:

		byte = Adr >> 8;
		*(str++) = HexTab[ byte >>4 ];
		*(str++) = HexTab[ byte & 0xf];

		byte = Adr & 0xff;
		*(str++) = HexTab[ byte >>4 ];
		*(str++) = HexTab[ byte & 0xf];

		for (k = 0; k < 32; k++)
		{
			for (m = 0; m < 2; m++)
			{
				byte = HexData[Adr].data[m];
				*(str++) = HexTab[ byte >>4 ];
				*(str++) = HexTab[ byte & 0xf];
			}
			Adr++;
			byte = HexData[Adr].data[0];
			*(str++) = HexTab[ byte >>4 ];
			*(str++) = HexTab[ byte & 0xf];
			*(str) = 0;
			Adr++;
		}



}


//********************************************


void CFirmwareUpdate::OnUpload() 
{
char temp[STRLEN+1];
DWORD RxCount;
int VerifyError;
int i;
char StatusMeldung[STRLEN+1];


	UpdateStatus = 1;


	sprintf(temp,"%cFWUP:",STX);
	AppendPruefsumme(temp);
	strcat(temp,"\x3");
	Comm->Tx(temp,strlen(temp) );
	Sleep(RX_TIMEOUT);
	Comm->Rx(temp,&RxCount,STRLEN);

	temp[RxCount] = 0;
	if (RxCount == 1 && temp[0] == ACK)
		int test =1;

	VerifyError = 0;

	m_Progress.ShowWindow(SW_SHOW);
	m_Progress.SetRange(0,0x3C00/0x40);
	GetDlgItem(IDCANCEL)->ShowWindow(SW_HIDE);
	GetDlgItem(IDOK)->ShowWindow(SW_HIDE);

	GetDlgItem(IDC_UPLOAD)->ShowWindow(SW_HIDE);
	GetDlgItem(IDC_OPENHEXFILE)->ShowWindow(SW_HIDE);
	GetDlgItem(IDC_VERIFY)->ShowWindow(SW_HIDE);
	GetDlgItem(IDC_MESSAGE)->ShowWindow(SW_SHOW);
			


	for (i = 0; i < 0x3c00/0x40 ; i++)
	{

		sprintf(temp,"%cP",STX);
		sPrintRow( i * 0x40, &temp[strlen(temp)] );

		sprintf(StatusMeldung,"Programmiere Adresse %d",i * 0x20 + 0x20);
		m_Adresse = StatusMeldung;
		UpdateData(FALSE);

		AppendPruefsumme(temp);
		strcat(temp,"\x3");
		Comm->Tx(temp,strlen(temp) );
		Sleep(30);
		Comm->Rx(temp,&RxCount,STRLEN);
		if (RxCount != 1 || temp[0] != ACK)
		{
			VerifyError = 1;
//$$$$			break;
		}
		m_Progress.SetPos((unsigned int)(i) );
		MSG msg;
		while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE))
		{
			if (msg.message == WM_QUIT)
				return  ;

			TranslateMessage(&msg);
			DispatchMessage(&msg);
		}
		if (WatchdogFlag)
		{
			WatchdogFlag = 0;
						
			sprintf(temp,"%cW",STX);		// Watchdog triggern
			AppendPruefsumme(temp);
			strcat(temp,"\x3");
			Comm->Tx(temp,strlen(temp) );
			Comm->Rx(temp,&RxCount,STRLEN);

		}
		

	}
	if (VerifyError)
	{
		strcat(StatusMeldung," --> Fehler!");
		m_Adresse = StatusMeldung;
	}
	else
		m_Adresse = "Programmierung ok!";
	Sleep(1000);
	OnVerify();

	sprintf(temp,"%cG",STX);		// Watchdog triggern
	AppendPruefsumme(temp);
	strcat(temp,"\x3");
	Comm->Tx(temp,strlen(temp) );
	Comm->Rx(temp,&RxCount,STRLEN);
	
	m_Progress.ShowWindow(SW_HIDE);
//	GetDlgItem(IDCANCEL)->ShowWindow(SW_SHOW);
	GetDlgItem(IDOK)->ShowWindow(SW_SHOW);
//	GetDlgItem(IDC_RESTART)->ShowWindow(SW_SHOW);
	GetDlgItem(IDC_UPLOAD)->ShowWindow(SW_SHOW);
	GetDlgItem(IDC_OPENHEXFILE)->ShowWindow(SW_SHOW);
	GetDlgItem(IDC_MESSAGE)->ShowWindow(SW_HIDE);

	UpdateData(FALSE);
	UpdateStatus = 0;
	
}

void CFirmwareUpdate::OnTimer(UINT nIDEvent) 
{
char temp[STRLEN+1];
DWORD RxCount;


	if (nIDEvent == 1000)
	{
		KillTimer(1000);	
		OnOpenhexfile();
	}
/*		
	if (UpdateStatus != 0)
	{
		WatchdogFlag = 1;
	}

	sprintf(temp,"%cW",STX);		// Watchdog triggern
	AppendPruefsumme(temp);
	strcat(temp,"\x3");
	Comm->Tx(temp,strlen(temp) );
	Comm->Rx(temp,&RxCount,STRLEN);
*/
	
	CDialog::OnTimer(nIDEvent);
}
