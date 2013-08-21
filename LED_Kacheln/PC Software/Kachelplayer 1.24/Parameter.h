#if !defined(AFX_PARAMETER_H__EAD7C500_D700_11D7_8897_00D05C0074E1__INCLUDED_)
#define AFX_PARAMETER_H__EAD7C500_D700_11D7_8897_00D05C0074E1__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// Parameter.h : Header-Datei
//
#include "CommClass.h"

/////////////////////////////////////////////////////////////////////////////
// Dialogfeld Parameter 

class Parameter : public CDialog
{
// Konstruktion
public:
	Parameter(CWnd* pParent = NULL);   // Standardkonstruktor

// Dialogfelddaten
	//{{AFX_DATA(Parameter)
	enum { IDD = IDD_PARAMETER };
	CComboBox	m_ComCombo;
	CString	m_Label1;
	CString	m_Port1;
	//}}AFX_DATA


// Überschreibungen
	// Vom Klassen-Assistenten generierte virtuelle Funktionsüberschreibungen
	//{{AFX_VIRTUAL(Parameter)
	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV-Unterstützung
	//}}AFX_VIRTUAL

// Implementierung

public:
	char Port[ANZ_PORTS][STRLEN+1];
	char Label[ANZ_PORTS][STRLEN+1];
//	char KD_Nr[STRLEN+1];
//	char SendeZeilen[STRLEN+1];
	int Com;
	COMM *Comm;
	int m_VpsCom;

	int Tempo;
	int Brightness;
	//	CString m_IpGateway;
//	CString m_IpMask;

	CString m_Ports[ANZ_PORTS];
	int ReadParam(void);
	int WriteParam(void);

protected:

	// Generierte Nachrichtenzuordnungsfunktionen
	//{{AFX_MSG(Parameter)
	virtual void OnOK();
	virtual BOOL OnInitDialog();
	afx_msg void OnFwUpdate();
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ fügt unmittelbar vor der vorhergehenden Zeile zusätzliche Deklarationen ein.

#endif // AFX_PARAMETER_H__EAD7C500_D700_11D7_8897_00D05C0074E1__INCLUDED_
