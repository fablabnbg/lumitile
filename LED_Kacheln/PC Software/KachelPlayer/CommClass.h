#define COMMCLASS 1

#define STRLEN 512

class COMM
{
 
private: 

	HANDLE hComm;
	OVERLAPPED ovr,ovw;
	DCB dcb;
	COMMTIMEOUTS ctmo;
	char KompBuff[1000];

public:

	COMM();
	~COMM();
	int Init(int com, int baud);
	int Tx(char *buff, int count);
	int TxKachelInfo(char *buff, int count);
	int Rx(char *buff, DWORD *count, int MaxCount);
	void Komprimieren(char *KompBuff,int *KompCount,char *buff,int count);
	void EmptyRxBuff(void);



};