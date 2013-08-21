#define PLAYERCLASS 1

#define STRLEN 512

#define MAX_SZENEN	200
#define MAX_KACHELN 128
#define	MAX_FELDER 20

#define MAX_BUFF_KACHELCTRL	10000	// Bytes Rohdaten
#define STOP	0
#define RUN		1
#define PAUSE	2



typedef struct tagSzene {	DWORD Dauer;
							DWORD Uebergang;
							char SzeneName[STRLEN+1];
							int Kachel[MAX_KACHELN][3];
						} Szene;



class CPlayer
{
 
private: 


public:

	CPlayer();
	~CPlayer();
	int Init(char *FileName);
	void SplitLine(char *zeile1);
	int CalcNextSzene(void);
	void IncSzeneIndex(void);
	void StartPlayer(void);
	void CalcAktValues(float SpeedFaktor, float DimmerFaktor);
	unsigned char SetFarbe(unsigned char last, unsigned char next, float proz, float DimmerFaktor) ;
	int FillUploadBuff(void);


//*********** MemberVariablen ************	
	char Felder[MAX_FELDER][STRLEN+1];
	int AnzSzenen;
	int AnzKacheln;
	int Loop;
	int PlayStatus;

	Szene SzeneList[MAX_SZENEN];

	Szene AktSzeneValues;
	Szene LastSzeneValues;

	int KachelList[MAX_KACHELN];

	int AktSzene;
	int NextSzene;
	DWORD TimeSzeneStart;
	int StatusSzene;
	unsigned char UploadBuff[10000];
	int UploadBuffIdx;
	char ProgName[STRLEN+1];
};