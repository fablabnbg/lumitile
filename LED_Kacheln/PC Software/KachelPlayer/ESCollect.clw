; CLW-Datei enthält Informationen für den MFC-Klassen-Assistenten

[General Info]
Version=1
LastClass=CESCollectDlg
LastTemplate=CDialog
NewFileInclude1=#include "stdafx.h"
NewFileInclude2=#include "ESCollect.h"

ClassCount=5
Class1=CESCollectApp
Class2=CESCollectDlg
Class3=CAboutDlg

ResourceCount=5
Resource1=IDD_PARAMETER
Resource2=IDR_MAINFRAME
Resource3=IDD_ABOUTBOX
Class4=Parameter
Resource4=IDD_ESCOLLECT_DIALOG
Class5=CFirmwareUpdate
Resource5=IDD_UPLOAD

[CLS:CESCollectApp]
Type=0
HeaderFile=ESCollect.h
ImplementationFile=ESCollect.cpp
Filter=N
LastObject=CESCollectApp

[CLS:CESCollectDlg]
Type=0
HeaderFile=ESCollectDlg.h
ImplementationFile=ESCollectDlg.cpp
Filter=D
BaseClass=CDialog
VirtualFilter=dWC
LastObject=IDC_SPEED

[CLS:CAboutDlg]
Type=0
HeaderFile=ESCollectDlg.h
ImplementationFile=ESCollectDlg.cpp
Filter=D
LastObject=IDOK
BaseClass=CDialog
VirtualFilter=dWC

[DLG:IDD_ABOUTBOX]
Type=1
Class=CAboutDlg
ControlCount=5
Control1=IDC_STATIC,static,1342177294
Control2=IDC_STATIC,static,1342308480
Control3=IDC_STATIC,static,1342308352
Control4=IDOK,button,1342373889
Control5=IDC_STATIC,static,1342308352

[DLG:IDD_ESCOLLECT_DIALOG]
Type=1
Class=CESCollectDlg
ControlCount=22
Control1=IDCANCEL,button,1342242816
Control2=IDC_MESS1,edit,1350631552
Control3=IDC_PARAM,button,1342242816
Control4=IDC_BMP5,static,1073741838
Control5=IDC_TEST,button,1073807360
Control6=IDC_LABEL1,static,1342308352
Control7=IDC_INFO,button,1342242816
Control8=IDC_STATIC,static,1342177294
Control9=IDC_BMP1,static,1342177294
Control10=IDC_ANZEIGE,edit,1352728644
Control11=IDC_LOADFILE,button,1342242816
Control12=IDC_TESTEDIT,edit,1082196096
Control13=IDC_SPEED,msctls_trackbar32,1342242827
Control14=IDC_DIMMER,msctls_trackbar32,1342242827
Control15=IDC_STATIC,static,1342308352
Control16=IDC_STATIC,static,1342308352
Control17=IDC_UPLOAD,button,1342242816
Control18=IDC_UPLOAD_PROGRESS,msctls_progress32,1082130432
Control19=IDC_STATIC,static,1342308352
Control20=IDC_STATIC,static,1342308352
Control21=IDC_STATIC,static,1342308352
Control22=IDC_STATIC,static,1342308352

[DLG:IDD_PARAMETER]
Type=1
Class=Parameter
ControlCount=9
Control1=IDOK,button,1342242817
Control2=IDCANCEL,button,1342242816
Control3=IDC_PORT1,edit,1350631552
Control4=IDC_STATIC,static,1342308352
Control5=IDC_LABEL1,edit,1350631552
Control6=IDC_STATIC,static,1342308352
Control7=IDC_FW_UPDATE,button,1342242816
Control8=IDC_VPSCOM,combobox,1344339970
Control9=IDC_STATIC,static,1342308352

[CLS:Parameter]
Type=0
HeaderFile=Parameter.h
ImplementationFile=Parameter.cpp
BaseClass=CDialog
Filter=D
LastObject=IDC_VPSCOM
VirtualFilter=dWC

[DLG:IDD_UPLOAD]
Type=1
Class=CFirmwareUpdate
ControlCount=8
Control1=IDCANCEL,button,1342242816
Control2=IDC_OPENHEXFILE,button,1342242816
Control3=IDC_VERIFY,button,1342242816
Control4=IDOK,button,1342242816
Control5=IDC_PROGRESS,msctls_progress32,1350565888
Control6=IDC_UPLOAD,button,1342242816
Control7=IDC_ADRESSE,static,1342312448
Control8=IDC_MESSAGE,static,1073872896

[CLS:CFirmwareUpdate]
Type=0
HeaderFile=FirmwareUpdate.h
ImplementationFile=FirmwareUpdate.cpp
BaseClass=CDialog
Filter=D
LastObject=IDC_ADRESSE
VirtualFilter=dWC

