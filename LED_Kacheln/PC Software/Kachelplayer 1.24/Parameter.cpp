// Parameter.cpp: Implementierungsdatei
//

#include "stdafx.h"
#include "ESCollect.h"
#include "ESCollectDlg.h"
#include "Parameter.h"
#include "FirmwareUpdate.h"


#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

extern CESCollectDlg *MainDlg;
/////////////////////////////////////////////////////////////////////////////
// Dialogfeld Parameter 


Parameter::Parameter(CWnd* pParent /*=NULL*/)
	: CDialog(Parameter::IDD, pParent)
{
	//{{AFX_DATA_INIT(Parameter)
	m_Label1 = _T("");
	m_Port1 = _T("");
	//}}AFX_DATA_INIT
}


void Parameter::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(Parameter)
	DDX_Control(pDX, IDC_VPSCOM, m_ComCombo);
	DDX_Text(pDX, IDC_LABEL1, m_Label1);
	DDX_Text(pDX, IDC_PORT1, m_Port1);
	//}}AFX_DATA_MAP
}


BEGIN_MESSAGE_MAP(Parameter, CDialog)
	//{{AFX_MSG_MAP(Parameter)
	ON_BN_CLICKED(IDC_FW_UPDATE, OnFwUpdate)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// Behandlungsroutinen für Nachrichten Parameter 

void Parameter::OnOK() 
{
char temp[STRLEN+1];


	UpdateData(TRUE);
	m_VpsCom = m_ComCombo.GetCurSel();

	WriteParam();
	MessageBox("Die Änderungen werden erst nach dem nächsten Start wirksam","Achtung");



	CDialog::OnOK();
}

BOOL Parameter::OnInitDialog() 
{
	

	CDialog::OnInitDialog();
	
	// TODO: Zusätzliche Initialisierung hier einfügen


	ReadParam();	
	
	m_ComCombo.SetCurSel(Com - 1);

	UpdateData(FALSE);
	return TRUE;  // return TRUE unless you set the focus to a control
	              // EXCEPTION: OCX-Eigenschaftenseiten sollten FALSE zurückgeben


		
}

int Parameter::ReadParam(void)
{
char temp[STRLEN+1];

	GetPrivateProfileString("PORTS","PORT1","1001",temp,STRLEN,MainDlg->sIniFileName);
	m_Port1 = temp;
	m_Ports[0] = temp;
	
	GetPrivateProfileString("LABELS","LABEL1","FREI",temp,STRLEN,MainDlg->sIniFileName);
	m_Label1 = temp;
	strcpy(Label[0], temp);

	GetPrivateProfileString("COM","COMPORT","1",temp,STRLEN,MainDlg->sIniFileName);
	Com = atoi(temp);

	GetPrivateProfileString("FENSTER","TEMPO","100",temp,STRLEN,MainDlg->sIniFileName);
	Tempo = atoi(temp);

	GetPrivateProfileString("FENSTER","HELLIGKEIT","100",temp,STRLEN,MainDlg->sIniFileName);
	Brightness = atoi(temp);

	
	GetPrivateProfileString("PFADE","WORKINGDIR", "",MainDlg->sWorkingDir, STRLEN, MainDlg->sIniFileName);

	return 0;
}

int Parameter::WriteParam(void)
{
char temp[STRLEN+1];


	WritePrivateProfileString("PORTS","PORT1",m_Port1.GetBuffer(STRLEN),MainDlg->sIniFileName);

	sprintf(temp,"%d",m_VpsCom+1);	
	WritePrivateProfileString("COM","COMPORT",temp,MainDlg->sIniFileName);
	
	WritePrivateProfileString("LABELS","LABEL1",m_Label1.GetBuffer(STRLEN),MainDlg->sIniFileName);
	


	sprintf(temp,"%d",Tempo);	
	WritePrivateProfileString("FENSTER","TEMPO", temp,MainDlg->sIniFileName);

	sprintf(temp,"%d",Brightness);	
	WritePrivateProfileString("FENSTER","HELLIGKEIT", temp, MainDlg->sIniFileName);
	
	WritePrivateProfileString("PFADE","WORKINGDIR", MainDlg->sWorkingDir, MainDlg->sIniFileName);


	
	return 0;
}

void Parameter::OnFwUpdate() 
{

	CFirmwareUpdate  *Fwu = new CFirmwareUpdate;
//	strcpy(Fwu.sWorkingDir, sWorkingDir);
	Fwu->Comm = Comm;
	Fwu->DoModal();

	delete Fwu;


}
