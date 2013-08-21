// ESCollectDlg.h : Header-Datei
//
#include "CMyAsyncSocket.h"

#if !defined(AFX_ESCOLLECTDLG_H__EAD7C4F3_D700_11D7_8897_00D05C0074E1__INCLUDED_)
#define AFX_ESCOLLECTDLG_H__EAD7C4F3_D700_11D7_8897_00D05C0074E1__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

/////////////////////////////////////////////////////////////////////////////
// CESCollectDlg Dialogfeld

#define STRLEN 512
#define INI_FILENAME "Parameter.ini"
#define ANZ_PORTS 1
#define CMD_LENGTH	16
#define CMD_SENDPAGE "§§Comm:SendPag§§"
#define CMD_BLOCK_CH "§§Comm:BlockCh§§"
#define CMD_FREE_CH "§§Comm:FreeChn§§"


#define BLOCK_TIMER_ID 2000
#define BLOCK_TIMEOUT	3600000

#define TC_TIMER_ID 3000
#define TC_TIMEOUT	40

#define VPS_TIMER_ID 4000
#define VPS_TIMEOUT	500

#define VPS_UEBERWACH_TIMER_ID 5000
#define VPS_UEBERWACH_TIMEOUT	5000

#define VPS_TIMERMESSAGE_ID 6000
#define VPS_TIMEOUT_MESSAGE 5000

#define STX 0x2
#define ETX 0x3
#define ACK 0x6		//ctrl-F
#define NAK 0x15	//ctrl-U


class CESCollectDlg : public CDialog
{
// Konstruktion
public:
	CESCollectDlg(CWnd* pParent = NULL);	// Standard-Konstruktor

// Dialogfelddaten
	//{{AFX_DATA(CESCollectDlg)
	enum { IDD = IDD_ESCOLLECT_DIALOG };
	CSliderCtrl	m_Dimmer;
	CProgressCtrl	m_UploadProgress;
	CSliderCtrl	m_Speed;
	CString	m_Mess1;
	CString	m_Anzeige;
	CString	m_TestEdit;
	//}}AFX_DATA

	// Vom Klassenassistenten generierte Überladungen virtueller Funktionen
	//{{AFX_VIRTUAL(CESCollectDlg)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV-Unterstützung
	//}}AFX_VIRTUAL

public:
// Implementierung


	COLORREF crColor;
	COLORREF EditColor;

	CBrush	m_bkBrush;
	CBrush	m_EditBrush;



	CMyAsyncSocket sock[ANZ_PORTS];
	CMyAsyncSocket *SockSav[ANZ_PORTS];
	CString *m_Status[ANZ_PORTS];
	CString *m_Pages[ANZ_PORTS];
	CWnd *BmpBlocked[ANZ_PORTS];
	CWnd *BmpConnected[ANZ_PORTS];
	CWnd *m_Labels[ANZ_PORTS];
	CWnd *VpsBmp;
	CWnd *InserterBmp;

	int RxCnt[ANZ_PORTS];

	char sWorkingDir[STRLEN];
	CString cWorkingDir;


	CString cOwnDir;
	char sOwnDir[STRLEN+1];

	
	CString cIniFileName;
	char	sIniFileName[STRLEN+1];
	
	int ES_initialized;
	HINSTANCE  hLibrary;


	int CESCollectDlg::InitES(void);
	int CESCollectDlg::DispatchCmd(char *, int SockNr) ;
	int CESCollectDlg::FindString(char *str, char * search, int cnt);
	int CESCollectDlg::str_FindStrBack(char * str,char *search,int RxIdx);
	int CESCollectDlg::InitVps() ;
	unsigned char CESCollectDlg::AppendPruefsumm(char *str); 
	void CESCollectDlg::AppendHex(char *str, char HexChar) ;
	int CESCollectDlg::FileExists(CString fname);


	HANDLE hMutex;

	int SmpteKanal;		// für TimeCode
	HANDLE        i_HandleCom;      // Für VPS-Com-Schnittstelle

	char RecBuff[STRLEN*10];
	unsigned long ByteCount;
	float SpeedFaktor;
	float DimmFaktor;


protected:
	HICON m_hIcon;

	// Generierte Message-Map-Funktionen
	//{{AFX_MSG(CESCollectDlg)
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	afx_msg void OnTimer(UINT nIDEvent);
	afx_msg void OnParam();
	afx_msg void OnClose();
	virtual void OnCancel();
	afx_msg void OnTest();
	afx_msg void OnInfo();
	afx_msg void OnLoadfile();
	afx_msg void OnReleasedcaptureSpeed(NMHDR* pNMHDR, LRESULT* pResult);
	afx_msg void OnUpload();
	afx_msg void OnReleasedcaptureDimmer(NMHDR* pNMHDR, LRESULT* pResult);
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ fügt unmittelbar vor der vorhergehenden Zeile zusätzliche Deklarationen ein.

#endif // !defined(AFX_ESCOLLECTDLG_H__EAD7C4F3_D700_11D7_8897_00D05C0074E1__INCLUDED_)
