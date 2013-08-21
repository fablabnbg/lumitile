

class  CMyAsyncSocket: public CAsyncSocket
{

public:

virtual void CMyAsyncSocket::OnAccept(int nErrorCode);
virtual void CMyAsyncSocket::OnClose(int nErrorCode);
virtual void CMyAsyncSocket::OnConnect(int nErrorCode);
virtual void CMyAsyncSocket::OnReceive(int nErrorCode);


CString Status;
CMyAsyncSocket *Own;
int ConnectionCnt;
int isBlocked;
int Blocker;
};