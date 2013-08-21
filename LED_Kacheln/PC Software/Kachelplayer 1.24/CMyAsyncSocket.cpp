#include "stdafx.h"
#include "CMyAsyncSocket.h"

#define STRLEN 512



void CMyAsyncSocket::OnAccept(int nErrorCode)
{

	if (nErrorCode == 0)
	{
		int i = 0;
		Accept(*Own);

int ret;	
int RxBufLen = 1000000;
	
		ret = (int)Own->SetSockOpt( TCP_NODELAY, &RxBufLen, sizeof(int), IPPROTO_TCP );
		ret = (int)Own->SetSockOpt( SO_RCVBUF, &RxBufLen, sizeof(int), SOL_SOCKET );
		Own->Status = "Connected";
		Own->isBlocked = 0;
		Own->Blocker = 0;

		ConnectionCnt = 1;
		Own->ConnectionCnt = 1;


	}
}

void CMyAsyncSocket::OnClose(int nErrorCode)
{
char temp[STRLEN];
int ret = 0;

//	Own->ConnectionCnt = 0;
	ConnectionCnt = 0;
	while( (ret = Receive(temp,STRLEN) ) > 0);
	ShutDown(2);
	Close();
	int i = 0;
	Status = "Warten auf Verbindung";


}
void CMyAsyncSocket::OnReceive(int nErrorCode)
{

	if (nErrorCode == 0)
	{
//		Receive(temp,1132);
int i = 0;	
	
	}
}

void CMyAsyncSocket::OnConnect(int nErrorCode)
{


	if (nErrorCode == 0)
	{
		int i = 0;
		MessageBeep(-1);
		Status = "Connected";
	}
}