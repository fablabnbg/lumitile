// ESCollectDlg.cpp : Implementierungsdatei
//

#include "stdafx.h"
#include "ESCollect.h"
#include "ESCollectDlg.h"
#include "Parameter.h"
#include "PlayerClass.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

HANDLE TimerSemaph;

Parameter Param;

char RxBuff[ANZ_PORTS][ 100000 * 10 ];

COMM *Comm;
CPlayer *Player;

FILE *gfp = NULL; //$$$$

/////////////////////////////////////////////////////////////////////////////
// CAboutDlg-Dialogfeld für Anwendungsbefehl "Info"

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

// Dialogfelddaten
	//{{AFX_DATA(CAboutDlg)
	enum { IDD = IDD_ABOUTBOX };
	//}}AFX_DATA

	// Vom Klassenassistenten generierte Überladungen virtueller Funktionen
	//{{AFX_VIRTUAL(CAboutDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV-Unterstützung
	//}}AFX_VIRTUAL

// Implementierung
	COLORREF crColor;
	COLORREF EditColor;

	CBrush	m_bkBrush;
	CBrush	m_EditBrush;
	

protected:
	//{{AFX_MSG(CAboutDlg)
	afx_msg HBRUSH OnCtlColor(CDC* pDC, CWnd* pWnd, UINT nCtlColor);
	virtual BOOL OnInitDialog();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
	//{{AFX_DATA_INIT(CAboutDlg)
	//}}AFX_DATA_INIT
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CAboutDlg)
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
	//{{AFX_MSG_MAP(CAboutDlg)
	ON_WM_CTLCOLOR()
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CESCollectDlg Dialogfeld

CESCollectDlg::CESCollectDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CESCollectDlg::IDD, pParent)
{
	//{{AFX_DATA_INIT(CESCollectDlg)
	m_Mess1 = _T("");
	m_Anzeige = _T("");
	m_TestEdit = _T("");
	//}}AFX_DATA_INIT
	// Beachten Sie, dass LoadIcon unter Win32 keinen nachfolgenden DestroyIcon-Aufruf benötigt
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CESCollectDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CESCollectDlg)
	DDX_Control(pDX, IDC_DIMMER, m_Dimmer);
	DDX_Control(pDX, IDC_UPLOAD_PROGRESS, m_UploadProgress);
	DDX_Control(pDX, IDC_SPEED, m_Speed);
	DDX_Text(pDX, IDC_MESS1, m_Mess1);
	DDX_Text(pDX, IDC_ANZEIGE, m_Anzeige);
	DDX_Text(pDX, IDC_TESTEDIT, m_TestEdit);
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CESCollectDlg, CDialog)
	//{{AFX_MSG_MAP(CESCollectDlg)
	ON_WM_SYSCOMMAND()
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_WM_TIMER()
	ON_BN_CLICKED(IDC_PARAM, OnParam)
	ON_WM_CLOSE()
	ON_BN_CLICKED(IDC_TEST, OnTest)
	ON_BN_CLICKED(IDC_INFO, OnInfo)
	ON_BN_CLICKED(IDC_LOADFILE, OnLoadfile)
	ON_NOTIFY(NM_RELEASEDCAPTURE, IDC_SPEED, OnReleasedcaptureSpeed)
	ON_BN_CLICKED(IDC_UPLOAD, OnUpload)
	ON_NOTIFY(NM_RELEASEDCAPTURE, IDC_DIMMER, OnReleasedcaptureDimmer)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CESCollectDlg Nachrichten-Handler

BOOL CESCollectDlg::OnInitDialog()
{

char help[STRLEN+1];
//char temp[STRLEN+1];
int i;
int ret;
	
	CDialog::OnInitDialog();

	// Hinzufügen des Menübefehls "Info..." zum Systemmenü.

	// IDM_ABOUTBOX muss sich im Bereich der Systembefehle befinden.
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{	
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// Symbol für dieses Dialogfeld festlegen. Wird automatisch erledigt
	//  wenn das Hauptfenster der Anwendung kein Dialogfeld ist
	SetIcon(m_hIcon, TRUE);			// Großes Symbol verwenden
	SetIcon(m_hIcon, FALSE);		// Kleines Symbol verwenden
	
	// ZU ERLEDIGEN: Hier zusätzliche Initialisierung einfügen



	strcpy(help,"");

	GetCurrentDirectory(STRLEN ,help);
	if ( help[ strlen(help)-1] != '\\')
		strcat(help,"\\");

	cOwnDir = help;
	strcpy(sOwnDir,help);

	strcat(help,INI_FILENAME);
	cIniFileName = help;
	strcpy(sIniFileName,help);

	Param.ReadParam();


	m_Speed.SetPos(Param.Tempo);
	m_Dimmer.SetPos(Param.Brightness);

	m_Status[0] = &m_Mess1;

	m_Labels[0] =  GetDlgItem(IDC_LABEL1);
	for (i = 0; i < ANZ_PORTS; i++)
		m_Labels[i]->SetWindowText(Param.Label[i]);


	BmpBlocked[0] = GetDlgItem(IDC_BMP1);
	BmpConnected[0] = GetDlgItem(IDC_BMP5);

	BmpBlocked[0]->ShowWindow(SW_SHOW);

	for (i = 0; i < ANZ_PORTS; i++)
	{

		RxCnt[i] = 0;

		sock[i].Own = new CMyAsyncSocket ;
		SockSav[i] = sock[i].Own;
		sock[i].Create(atoi(Param.m_Ports[i].GetBuffer(STRLEN)), SOCK_STREAM, FD_READ |FD_ACCEPT | FD_CONNECT | FD_CLOSE);

	int RxBufLen = 10000;
	int Len = sizeof(int);;
		ret = (int)sock[i].GetSockOpt( SO_RCVBUF, &RxBufLen, &Len, SOL_SOCKET );

		RxBufLen = 1000000;

		ret = (int)sock[i].SetSockOpt( TCP_NODELAY, &RxBufLen, sizeof(int), IPPROTO_TCP );
		

		ret = (int)sock[i].SetSockOpt( SO_RCVBUF, &RxBufLen, sizeof(int), SOL_SOCKET );
		ret = (int)sock[i].GetSockOpt( SO_RCVBUF, &RxBufLen, &Len, SOL_SOCKET );
		
		
		sock[i].ConnectionCnt = 0;
		sock[i].Own->ConnectionCnt = 0;
		sock[i].isBlocked = 0;
		sock[i].Blocker = 0;
		sock[i].Listen(0);
		BmpBlocked[i]->ShowWindow(SW_HIDE);
		sock[i].Own->Status =  "Warten auf Verbindung";


	}

	hMutex = CreateSemaphore(NULL,1,1,"EXEC");
	if (hMutex == NULL)
		MessageBox("hMutex kann nicht erzeugt werden","ERROR",MB_OK | MB_ICONEXCLAMATION);


	TimerSemaph = CreateSemaphore(NULL,1,1,"TIMERSEM");
	if (TimerSemaph == NULL)
		MessageBox("TimerSemaph kann nicht erzeugt werden","ERROR",MB_OK | MB_ICONEXCLAMATION);



	SetTimer(1000,10,NULL);


	//********* COM-Schnittstellen-Init *************


	Comm = new COMM;
	Comm->Init(Param.Com,19200);

	m_Speed.SetRange(0,9, TRUE);
	SpeedFaktor = 1.0;

	m_Dimmer.SetRange(0,9, TRUE);
	DimmFaktor = 1.0;
	
//************************************
	UpdateData(FALSE);


	CString CmdLin;
	CmdLin = GetCommandLine();

/*	
	int pos = CmdLin.Find("\" ");
	if (pos > 0)
	{
		CmdLin.Delete(0,pos+2);
		CmdLin.Remove('\"');
		if (FileExists(CmdLin) )
		{
			if (Player != NULL)
				delete Player;
			Player = new CPlayer;
			Player->Init(CmdLin.GetBuffer(STRLEN));
			Player->StartPlayer();
		}
		else
			MessageBox(CmdLin, "Fehler",MB_OK);

	}

*/  
	return TRUE;  // Geben Sie TRUE zurück, außer ein Steuerelement soll den Fokus erhalten
}


int CESCollectDlg::FileExists(CString fname)
{

FILE *fp;

	fp = fopen(fname,"rb");
	if (fp == NULL)
		return 0;
	else
		fclose(fp);
	return 1;


}
void CESCollectDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

// Wollen Sie Ihrem Dialogfeld eine Schaltfläche "Minimieren" hinzufügen, benötigen Sie 
//  den nachstehenden Code, um das Symbol zu zeichnen. Für MFC-Anwendungen, die das 
//  Dokument/Ansicht-Modell verwenden, wird dies automatisch für Sie erledigt.

void CESCollectDlg::OnPaint() 
{
	if (IsIconic())
	{
		CPaintDC dc(this); // Gerätekontext für Zeichnen

		SendMessage(WM_ICONERASEBKGND, (WPARAM) dc.GetSafeHdc(), 0);

		// Symbol in Client-Rechteck zentrieren
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Symbol zeichnen
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// Die Systemaufrufe fragen den Cursorform ab, die angezeigt werden soll, während der Benutzer
//  das zum Symbol verkleinerte Fenster mit der Maus zieht.
HCURSOR CESCollectDlg::OnQueryDragIcon()
{
	return (HCURSOR) m_hIcon;
}
//******************************************************

void CESCollectDlg::OnTimer(UINT nIDEvent) 
{
	// TODO: Code für die Behandlungsroutine für Nachrichten hier einfügen und/oder Standard aufrufen

#define BUFF_LEN 1000

int ret = 0;
static char temp[BUFF_LEN * 10 ];
int i;
static unsigned int KachelIdx;
char ComString[STRLEN];
static int RxStep = 0;

static DWORD takt = 0;
static DWORD tlast = 0;
static DWORD tsumm = 0;
static int count = 0;
DWORD tmittel;
char help[STRLEN];

DWORD WaitRet2, Wait1;
HANDLE hAccess2, hAccess3;
				

	Wait1 = WaitForSingleObject(TimerSemaph,0);
	if (Wait1 == WAIT_OBJECT_0)
	{
		if (nIDEvent == 1000)
		{

// TimerTick-Anzeige in msec
			if (count != 0)
				tmittel = tsumm / count;
			takt = GetTickCount();
			if (count > 0)
			{
				tsumm += (takt-tlast);
			}
			tlast = takt;
			count++;
			sprintf(help,"%d",tmittel);
			m_TestEdit = help;
			UpdateData(FALSE);
			

// UZuerst Player-Funktionen
			if (Player != NULL && Player->PlayStatus == RUN)
			{
				Player->CalcAktValues(SpeedFaktor, DimmFaktor);

				if (KachelIdx >= Player->AnzKacheln)
					KachelIdx = 0;
				int Adr = Player->KachelList[KachelIdx];

				sprintf(ComString,"%c%c%c%c%c%c", STX,
												Adr,
												Player->AktSzeneValues.Kachel[Adr][0],
												Player->AktSzeneValues.Kachel[Adr][1],
												Player->AktSzeneValues.Kachel[Adr][2],
												ETX);
				Comm->TxKachelInfo(ComString,6);
				KachelIdx++;

				if (KachelIdx >= Player->AnzKacheln)
					KachelIdx = 0;
				Adr = Player->KachelList[KachelIdx];

				sprintf(ComString,"%c%c%c%c%c%c", STX,
												Adr,
												Player->AktSzeneValues.Kachel[Adr][0],
												Player->AktSzeneValues.Kachel[Adr][1],
												Player->AktSzeneValues.Kachel[Adr][2],
												ETX);
				Comm->TxKachelInfo(ComString,6);
				KachelIdx++;

/*
if (Player->AktSzeneValues.Kachel[Adr][0] == 0 &&
	Player->AktSzeneValues.Kachel[Adr][1] == 0 &&
	Player->AktSzeneValues.Kachel[Adr][2] == 0)
	int ttt = 1;
*/
if (gfp != NULL)
{
	fprintf(gfp,"%2X %2X %2X %2X\r\n",Adr,
										Player->AktSzeneValues.Kachel[Adr][0],
										Player->AktSzeneValues.Kachel[Adr][1],
										Player->AktSzeneValues.Kachel[Adr][2]);

}


			}

// Dann TCP/IP

			hAccess2 = OpenSemaphore(SEMAPHORE_ALL_ACCESS,FALSE,"EXEC");
			if ( hAccess2  != NULL)
			{
				WaitRet2 = WaitForSingleObject(hAccess2,0);
				
				if (WaitRet2 == WAIT_OBJECT_0)
				{
					hAccess3 = hAccess2;
			
			
					for (i = 0; i < ANZ_PORTS; i++)
					{
						if (sock[i].Own != NULL)
						{
							if (sock[i].Own->ConnectionCnt == 1)
							{
								BmpConnected[i]->ShowWindow(SW_SHOW);
								BmpBlocked[i]->ShowWindow(SW_HIDE);
							}
							else
							{
								BmpConnected[i]->ShowWindow(SW_HIDE);
								BmpBlocked[i]->ShowWindow(SW_SHOW);
							}

							*m_Status[i] = sock[i].Own->Status;
#define TEL_LEN 12					
							while ( (ret = sock[i].Own->Receive(temp,1 ))  >  0)
							{



								switch(RxStep)
								{
								case 0:
									if (temp[0] == '*')
									{
										RxStep = 1;
										RxCnt[i] = 0;
									}
									break;
								case 1:
									if (temp[0] == '#')
									{
										RxBuff[i][RxCnt[i]] = 0; 
										DispatchCmd(RxBuff[i], i);
										RxStep = 2;
									}
									else
										RxBuff[i][RxCnt[i]++] = temp[0];

									break;
								case 2:
									RxStep = 0;
									goto EndWhile;


								}

							}

EndWhile:

							i = i;



						}
					
					}
					ReleaseSemaphore(hAccess3,1,NULL);


				}

			
			}
			CloseHandle(hAccess2);
		}

		
		if (nIDEvent == BLOCK_TIMER_ID)
		{
			for (i = 0; i < ANZ_PORTS; i++)
			{
			}
			KillTimer(BLOCK_TIMER_ID);	
		}	
		
		if (nIDEvent == TC_TIMER_ID)
		{
/*
			SmpteDec.GetDecode(help,0);
			sprintf(temp,"§start§%s %s§end§",help,Vps);
			for (i = 0; i < ANZ_PORTS; i++)
			{
				if (sock[i].Own->ConnectionCnt == 1)
					sock[i].Own->Send(temp,strlen(temp));
			}
			
			
			
			m_TimeCode = help;
*/
		}	


		
	
		ReleaseSemaphore(TimerSemaph,1,NULL);
	}

//	UpdateData(FALSE);
	CDialog::OnTimer(nIDEvent);
}
//******************************************************

void CESCollectDlg::OnParam() 
{
	// TODO: Code für die Behandlungsroutine der Steuerelement-Benachrichtigung hier einfügen
	int i = 0;
	Param.Comm = Comm;
	Param.DoModal();


}

//******************************************************


void CESCollectDlg::OnClose() 
{
	// TODO: Code für die Behandlungsroutine für Nachrichten hier einfügen und/oder Standard aufrufen
//	if (MessageBox("Programm verlassen ?","Warnung",MB_OKCANCEL | MB_ICONEXCLAMATION) == IDOK)
		CDialog::OnClose();
}

void CESCollectDlg::OnCancel() 
{
int i;

	// TODO: Zusätzlichen Bereinigungscode hier einfügen

//	if (MessageBox("Programm verlassen ?","Warnung",MB_OKCANCEL | MB_ICONEXCLAMATION) == IDOK)
//	{
		for (i=0; i < ANZ_PORTS; i++)
			delete SockSav[i];
		CDialog::OnCancel();
//	}
}

int CESCollectDlg::DispatchCmd(char *RecBuff, int SockNr) 
{
	char temp[STRLEN+1];
	int Hex;
	if (!strncmp(strupr(RecBuff),"KACHEL:", strlen("KACHEL:")))
	{	

		if (Player != NULL )
		{
			if (Player->PlayStatus == RUN)
				Sleep(40);
			Player->PlayStatus = STOP;
		}
		sscanf(RecBuff+7,"%x",&Hex);

		sprintf(temp,"%c%c%c%c%c%c", STX,(Hex>>24)&0xFF,(Hex>>16)&0xFF,(Hex>>8)&0xFF,Hex & 0xFF,ETX);
		Comm->TxKachelInfo(temp,6);
		strcat(RecBuff,"\r\n");
		m_Anzeige = RecBuff + m_Anzeige;
		UpdateData(FALSE);
		Sleep(10);
		
	}
#define CMD_PLAYFILE "PLAYFILE:"
	if (!strncmp(strupr(RecBuff),CMD_PLAYFILE, strlen(CMD_PLAYFILE) ) )
	{	
		sscanf(RecBuff+strlen(CMD_PLAYFILE),"%s",temp);

//		sprintf(temp,"%c%c%c%c%c%c", STX,(Hex>>24)&0xFF,(Hex>>16)&0xFF,(Hex>>8)&0xFF,Hex & 0xFF,ETX);
//		Comm->TxKachelInfo(temp,6);

		CString CmdLin;
		CmdLin = temp;
		if (FileExists(CmdLin) )
		{
			if (Player != NULL)
				delete Player;
			Player = new CPlayer;
			Player->Init(temp);
			strcat(temp,"\r\n");
			Player->StartPlayer();
			m_Anzeige = temp + m_Anzeige;
			UpdateData(FALSE);
		}
		else
		{
			CmdLin = "File "+CmdLin;
			CmdLin = CmdLin + " nicht gefunden!";
			MessageBox(CmdLin, "Fehler",MB_OK);
		
		}

	}
	return 0;
}


int CESCollectDlg::FindString(char *str, char * search, int cnt)
{
int i;

	for (i = 0; i < cnt; i++)
	{
		if (str[i] == search[0])
		{
			if (!strncmp(str+i,search,strlen(search) ) )
				return i;
		}
	}

	return -1;
}
//**************************************

void CESCollectDlg::OnTest() 
{
	// TODO: Code für die Behandlungsroutine der Steuerelement-Benachrichtigung hier einfügen

static int toggle = 0;

	toggle = (toggle + 1) & 1;
	
	if (toggle == 1)
	{
		gfp = fopen("test.txt","wb");
	}

	if (toggle == 0)
	{
		fclose(gfp);
		gfp = NULL;
	}

}

//**************************************

int CESCollectDlg::str_FindStrBack(char * str,char *search,int RxIdx)
{
int i;
int len;

	len = strlen(search);
	for (i = RxIdx-len; i >= 0 ; i--)
	{

		if (!strncmp(str+i,search,len) )
			return i;
	}

	return -1;
}



//**************************************


HBRUSH CAboutDlg::OnCtlColor(CDC* pDC, CWnd* pWnd, UINT nCtlColor) 
{
	HBRUSH hbr = CDialog::OnCtlColor(pDC, pWnd, nCtlColor);
	
	// TODO: Attribute des Gerätekontexts hier ändern
	
	// TODO: Anderen Pinsel zurückgeben, falls Standard nicht verwendet werden soll
	pDC->SetBkMode(TRANSPARENT);
//	pDC->SetBkColor(crColor);

	
	
	if (nCtlColor == CTLCOLOR_EDIT )
		return m_EditBrush;
 
	return m_bkBrush;
}


BOOL CAboutDlg::OnInitDialog() 
{
	CDialog::OnInitDialog();

//	crColor = 0x007f7f7f;
//	crColor = 0x008d8d8d;
//	EditColor = 0x00f4ffff;

//	m_brush.CreateStockObject(NULL_BRUSH);
//	m_bkBrush.CreateSolidBrush(crColor);
//	m_EditBrush.CreateSolidBrush(EditColor);

	
	// TODO: Zusätzliche Initialisierung hier einfügen
	
	return TRUE;  // return TRUE unless you set the focus to a control
	              // EXCEPTION: OCX-Eigenschaftenseiten sollten FALSE zurückgeben
}

void CESCollectDlg::OnInfo() 
{
	// TODO: Code für die Behandlungsroutine der Steuerelement-Benachrichtigung hier einfügen
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	
}



void CESCollectDlg::OnLoadfile() 
{

char  	szFilter[256] = "Kachel-PlayFile(*.ledx)|*.ledx";
char chReplace = '|';
int ret;
	for (int i = 0; szFilter[i] != '\0'; i++) {
		if (szFilter[i] == chReplace)
			 szFilter[i] = '\0';
	}

	CFileDialog Open(TRUE);
	Open.m_ofn.lpstrTitle = "Kachelscript-File öffnen";
	Open.m_ofn.lpstrFilter = szFilter;
	Open.m_ofn.Flags |=  OFN_FILEMUSTEXIST;
	if (*sWorkingDir == 0x0)
		strcpy(sWorkingDir, ".\\led");

	Open.m_ofn.lpstrInitialDir = sWorkingDir;

	
	ret = Open.DoModal();
	
	if (ret== IDOK)
	{

		CString cWorkingDir = Open.GetPathName();
		strcpy(sWorkingDir,cWorkingDir.GetBuffer(STRLEN) );

		Param.WriteParam();

		if (Player != NULL)
			delete Player;
		Player = new CPlayer;
		Player->Init(sWorkingDir);
		Player->StartPlayer();
	}	
}


void CESCollectDlg::OnReleasedcaptureSpeed(NMHDR* pNMHDR, LRESULT* pResult) 
{
	// TODO: Code für die Behandlungsroutine der Steuerelement-Benachrichtigung hier einfügen
	SpeedFaktor = (10.0 - (float)m_Speed.GetPos() ) / 10.0;

	Param.Tempo = m_Speed.GetPos();
	Param.WriteParam();

	*pResult = 0;
}

void CESCollectDlg::OnUpload() 
{
int i,k;
char temp[STRLEN+1];
int ret;
int iUploadBuffLength;
DWORD count;

	if (Player != NULL)
	{

		Player->FillUploadBuff();
		Player->PlayStatus = STOP;
		Sleep(50);

		Comm->EmptyRxBuff();
		sprintf(temp,"%cI",STX);
		temp[strlen(temp)] = 0x0;
		AppendPruefsumm(&temp[1]);
		Comm->Tx(temp, strlen(temp) );
		Sleep(20);
		Comm->Rx(temp,&count,0x110);
		if (count == 0)
		{
			MessageBox("Keine Verbindung! Steht der Hex-Schalter in Stellung 4?","Error", MB_OK | MB_ICONEXCLAMATION);
			return;
		}
		if (count >= 12 || temp[0] != 'I')
		{
	// mmhh.. was da schief gegangen ist kann man nicht raten 
			MessageBox("Receive Error!","Error", MB_OK | MB_ICONEXCLAMATION);
			return;
		}
		iUploadBuffLength = (unsigned char) temp[3] * 256 + (unsigned char) temp[4];		
		
		ret = Player->FillUploadBuff();
		if (ret >= iUploadBuffLength)
		{
			MessageBox("Das File ist zu groß für KachelCtrl!","Error", MB_OK | MB_ICONEXCLAMATION);
			return;
		}
	}
	else
	{
		MessageBox("Sie müssen zuerst ein File laden!","Error", MB_OK | MB_ICONEXCLAMATION);
		return;
	}

	m_UploadProgress.SetRange(0,100);
	m_UploadProgress.SetPos(0);
	m_UploadProgress.ShowWindow(SW_SHOW);

	for (i = 0; i < (Player->UploadBuffIdx / 96) +1; i++)
	{
		sprintf(temp,"%cD%02X",STX,i);
		for (k = 0; k < 96; k++)
		{

			AppendHex(temp, Player->UploadBuff[i*96 + k] );
		}
		AppendPruefsumm(&temp[1]);
		Comm->Tx(temp, strlen(temp) );
// $$$ hier Antwort holen
		Sleep(50);
		Comm->Rx(temp,&count,0x110);
		if (count != 1 || temp[0] != ACK)
		{
			MessageBox("Receive Fehler\r\nKeine Antwort!!","Meldung", MB_OK );
			return;
		}

		m_UploadProgress.SetPos((i+1)*96*100/Player->UploadBuffIdx);
		MSG msg;
		while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE))
		{
			if (msg.message == WM_QUIT)
				return  ;

			TranslateMessage(&msg);

			DispatchMessage(&msg);
		}

	}
	sprintf(temp,"%cE",STX);		// Ende-Zeichen
	temp[strlen(temp)] = 0x0;
	AppendPruefsumm(&temp[1]);
	Comm->Tx(temp, strlen(temp) );
	Sleep(20);
	Comm->Rx(temp,&count,0x110);
	m_UploadProgress.ShowWindow(SW_HIDE);
	if (count == 1 && temp[0] == ACK)
	{
		MessageBox("Upload o.k!","Meldung", MB_OK );
	}

}

void CESCollectDlg::AppendHex(char *str, char BinChar) 
{
int idx, len;
char HexTab[] = ("0123456789ABCDEF");

	len = strlen(str);
	idx = (BinChar >> 4) & 0xF;
	str[len] = HexTab[idx];
	idx = BinChar & 0xF;
	str[len+1] = HexTab[idx];
	str[len+2] = 0;
	return;
}


unsigned char CESCollectDlg::AppendPruefsumm(char *str) 
{
int i, idx;
unsigned char Pruefsumm;

	Pruefsumm = 0;
	idx = strlen(str);
	for (i = 0; i < strlen(str); i++)
	{
		Pruefsumm ^= str[i]; 
	}
	AppendHex(str, Pruefsumm);
	str[idx+2] = ETX;
	str[idx+3] = 0x0;
		
	return Pruefsumm;
}


void CESCollectDlg::OnReleasedcaptureDimmer(NMHDR* pNMHDR, LRESULT* pResult) 
{
	// TODO: Code für die Behandlungsroutine der Steuerelement-Benachrichtigung hier einfügen
	DimmFaktor = (10.0 - (float)m_Dimmer.GetPos() ) / 10.0;

	Param.Brightness = m_Dimmer.GetPos();
	Param.WriteParam();
	
	*pResult = 0;
}
