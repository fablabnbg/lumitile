// ESCollect.h : Haupt-Header-Datei f�r die Anwendung ESCOLLECT
//

#if !defined(AFX_ESCOLLECT_H__EAD7C4F1_D700_11D7_8897_00D05C0074E1__INCLUDED_)
#define AFX_ESCOLLECT_H__EAD7C4F1_D700_11D7_8897_00D05C0074E1__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

#ifndef __AFXWIN_H__
	#error include 'stdafx.h' before including this file for PCH
#endif

#include "resource.h"		// Hauptsymbole

/////////////////////////////////////////////////////////////////////////////
// CESCollectApp:
// Siehe ESCollect.cpp f�r die Implementierung dieser Klasse
//

class CESCollectApp : public CWinApp
{
public:
	CESCollectApp();

// �berladungen
	// Vom Klassenassistenten generierte �berladungen virtueller Funktionen
	//{{AFX_VIRTUAL(CESCollectApp)
	public:
	virtual BOOL InitInstance();
	//}}AFX_VIRTUAL

// Implementierung

	//{{AFX_MSG(CESCollectApp)
		// HINWEIS - An dieser Stelle werden Member-Funktionen vom Klassen-Assistenten eingef�gt und entfernt.
		//    Innerhalb dieser generierten Quelltextabschnitte NICHTS VER�NDERN!
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};


/////////////////////////////////////////////////////////////////////////////

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ f�gt unmittelbar vor der vorhergehenden Zeile zus�tzliche Deklarationen ein.

#endif // !defined(AFX_ESCOLLECT_H__EAD7C4F1_D700_11D7_8897_00D05C0074E1__INCLUDED_)
