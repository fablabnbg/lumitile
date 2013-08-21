#if !defined(AFX_FIRMWAREUPDATE_H__E7A5F3F4_AC9F_492D_AD31_D2418D7F6E1D__INCLUDED_)
#define AFX_FIRMWAREUPDATE_H__E7A5F3F4_AC9F_492D_AD31_D2418D7F6E1D__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// FirmwareUpdate.h : Header-Datei
//

#ifndef COMMCLASS
	#include "CommClass.h"
#endif
#include "ESCollectDlg.h"

#define HEXBUFF_LEN 0xf000
#define RX_TIMEOUT	100	// *50MS


/////////////////////////////////////////////////////////////////////////////
// Dialogfeld CFirmwareUpdate 

class CFirmwareUpdate : public CDialog
{
// Konstruktion
public:
	CFirmwareUpdate(CWnd* pParent = NULL);   // Standardkonstruktor
	
	int CFirmwareUpdate::ConvertRecord(char *RecBuff, unsigned char *BinBuff);
	unsigned char CFirmwareUpdate::HexToBin(char *RecBuff);
	void CFirmwareUpdate::AppendPruefsumme(char *str) ;
	void CFirmwareUpdate::sPrintRow(int Adr, char* str);


// Dialogfelddaten
	//{{AFX_DATA(CFirmwareUpdate)
	enum { IDD = IDD_UPLOAD };
	CProgressCtrl	m_Progress;
	CString	m_Adresse;
	//}}AFX_DATA


// Überschreibungen
	// Vom Klassen-Assistenten generierte virtuelle Funktionsüberschreibungen
	//{{AFX_VIRTUAL(CFirmwareUpdate)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV-Unterstützung
	//}}AFX_VIRTUAL

// Implementierung

	public:
	COMM *Comm;

	char sWorkingDir[STRLEN];
	CString cWorkingDir;
	struct tagHexData
	{
		unsigned char data[2];
	} _HexData;


	tagHexData HexData[HEXBUFF_LEN];

	int UpdateStatus;
	int WatchdogFlag;


protected:

	// Generierte Nachrichtenzuordnungsfunktionen
	//{{AFX_MSG(CFirmwareUpdate)
	afx_msg void OnOpenhexfile();
	afx_msg void OnVerify();
	virtual BOOL OnInitDialog();
	afx_msg void OnUpload();
	afx_msg void OnTimer(UINT nIDEvent);
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ fügt unmittelbar vor der vorhergehenden Zeile zusätzliche Deklarationen ein.

#endif // AFX_FIRMWAREUPDATE_H__E7A5F3F4_AC9F_492D_AD31_D2418D7F6E1D__INCLUDED_
