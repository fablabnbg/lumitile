#include "stdafx.h"
#include "str_.h"
#include <windows.h>
#include <stdio.h>
//#include "KachelCtrlDlg.h"

#include "PlayerClass.h"




CPlayer::CPlayer()	// Konstruktor
{
int i, k;



	AnzSzenen = 0;
	AnzKacheln = 0;
	Loop = 1;
	PlayStatus = STOP;

	for (i = 0; i < MAX_SZENEN; i++)
	{
		SzeneList[i].Dauer = -1;
		SzeneList[i].Uebergang = -1;
		for (k = 0; k < MAX_KACHELN; k++)
		{
			SzeneList[i].Kachel[k][0] = -1;
			SzeneList[i].Kachel[k][1] = -1;
			SzeneList[i].Kachel[k][2] = -1;
		}
	}
	for (i = 0; i < MAX_KACHELN; i++)
	{
		KachelList[i] = -0;
	}

	UploadBuffIdx = 0;
}

CPlayer::~CPlayer()	// Destruktor
{
int i;

	for (i = 0; i < AnzSzenen; i++)
	{

	}

}

int CPlayer::Init(char *FileName)
{
FILE *fp;
char temp[STRLEN+1];
int state;
int i, idx;


	idx = strlen(FileName);
	while(idx != 0)
	{
		if (FileName[idx] == '\\')
			break;
		idx--;
	}
	if (idx != 0)
		idx++;
	strcpy(ProgName,&FileName[idx]);
	ProgName[8] = 0x0;


	fp = fopen(FileName,"rb");
	if (fp != NULL)
	{
		state = 0;
		while (! feof(fp) )
		{
			fgets(temp,STRLEN,fp);
			str_remblanks(temp);		// Cr+LF am Ende entfernen
			strupr(temp);
			if (temp[0] == 0)
				continue;
			switch (state)
			{
			case 0:
				if (!strncmp(temp, "S(",2) )
				{
					SzeneList[AnzSzenen].Dauer = atoi(&temp[2]) * 100;
					SplitLine(temp);
					SzeneList[AnzSzenen].Uebergang = atoi(Felder[1]) * 100;
					state++;
					AnzKacheln = 0;
				}
				break;
			case 1:
				if (temp[0] != '}')
				{
					int KachelNr = atoi(temp);
					KachelList[AnzKacheln] = KachelNr;
					AnzKacheln++;
					int idx = str_search(temp,'=');
					if (idx != 0)
					{
						SplitLine(&temp[idx+1]);
						int HexWert;
						sscanf(Felder[0],"%X",&HexWert);
						SzeneList[AnzSzenen].Kachel[KachelNr][0] = HexWert;

						sscanf(Felder[1],"%X",&HexWert);
						SzeneList[AnzSzenen].Kachel[KachelNr][1] = HexWert;

						sscanf(Felder[2],"%X",&HexWert);
						SzeneList[AnzSzenen].Kachel[KachelNr][2] = HexWert;

					}
				}
				else
				{
					state = 0;
					AnzSzenen++;
				}
				break;
			}
		
		}
		fclose(fp);
		AktSzene = 0;
		NextSzene = CalcNextSzene();
	}
	else
	{
		AfxMessageBox("Kann File nicht öffnen",MB_OK);
	}

	return 0;
}
/*********************************************************************
CalcNextSzene() rechnet den Index auf die nächste Szene aus, i.d.R. 
AktSzene+1, nur wenn AktSzene == AnzSzenen dann NextSzene = 0  
 **********************************************************************/


int CPlayer::FillUploadBuff(void)
{
int idx;
int i, k;

	idx = 2;			// 0 (Länge) wird später ergänzt

	UploadBuff[idx++] = AnzSzenen;
	UploadBuff[idx++] = AnzKacheln;
	strcpy((char *)&UploadBuff[idx], ProgName);
	idx += 8;
	
	for (i = 0; i < AnzKacheln; i++)
	{
		UploadBuff[idx++] = KachelList[i];	// Adressen der Kacheln
	}

	for (i = 0; i < AnzSzenen; i++)
	{

		UploadBuff[idx++] = (unsigned char) ( (int)(SzeneList[i].Dauer/100) & 0xff);
		UploadBuff[idx++] = (unsigned char) ( ((int)(SzeneList[i].Dauer/100) & 0xff00) >> 8);
		UploadBuff[idx++] = (unsigned char) ( (int)(SzeneList[i].Uebergang/100) & 0xff);
		UploadBuff[idx++] = (unsigned char) ( ((int)(SzeneList[i].Uebergang/100) & 0xff00) >> 8);

		for (k = 0; k < AnzKacheln; k++)
		{
			UploadBuff[idx++] = (unsigned char) SzeneList[i].Kachel[k+1][0];
			UploadBuff[idx++] = (unsigned char) SzeneList[i].Kachel[k+1][1];
			UploadBuff[idx++] = (unsigned char) SzeneList[i].Kachel[k+1][2];

		}
	}
	UploadBuffIdx = idx;

	UploadBuff[0] = idx & 0xFF;						// Low Byte
	UploadBuff[1] = ((idx & 0xFF00) >> 8) & 0xFF;	// High Byte

	UploadBuffIdx = idx;
	return idx;

}
/*********************************************************************
CalcNextSzene() rechnet den Index auf die nächste Szene aus, i.d.R. 
AktSzene+1, nur wenn AktSzene == AnzSzenen dann NextSzene = 0  
 **********************************************************************/


int CPlayer::CalcNextSzene(void)
{
int ret;

	ret = AktSzene+1;
	if (ret >= AnzSzenen)
		ret = 0;

	return ret;
}
/*********************************************************************
 **********************************************************************/


void CPlayer::IncSzeneIndex(void)
{


	AktSzene++;
	if (AktSzene >= AnzSzenen)
		AktSzene = 0;
	
	NextSzene = CalcNextSzene();

	return;
}

/*********************************************************************
StartPlayer() 
 **********************************************************************/


void CPlayer::StartPlayer(void)
{


	TimeSzeneStart = GetTickCount();
	StatusSzene	= 0;	// 0 = Dauer, 1= Übergang zu nächsten Szene
	PlayStatus = RUN;
	return;
}

/*********************************************************************
StartPlayer() 
 **********************************************************************/


void CPlayer::CalcAktValues(float SpeedFaktor, float DimmerFaktor)
{
DWORD TimeAkt;
int i;

Repeat:

	TimeAkt = GetTickCount();
	if (StatusSzene == 0)		// Stehenbleiben der Anzeige
	{

		if (TimeAkt-TimeSzeneStart > SzeneList[AktSzene].Dauer * SpeedFaktor)
		{
			StatusSzene = 1;
		}
		else
		{
			for (i = 0; i < AnzKacheln; i++)
			{
				AktSzeneValues.Kachel[ KachelList[i] ][0] = SzeneList[AktSzene].Kachel[ KachelList[i] ][0] * DimmerFaktor;
				AktSzeneValues.Kachel[ KachelList[i] ][1] = SzeneList[AktSzene].Kachel[ KachelList[i] ][1] * DimmerFaktor;
				AktSzeneValues.Kachel[ KachelList[i] ][2] = SzeneList[AktSzene].Kachel[ KachelList[i] ][2] * DimmerFaktor;
			}
		}
	}

	if (StatusSzene == 1)		// Ändern auf nächste Szene
	{
		if (TimeAkt-TimeSzeneStart > ( SzeneList[AktSzene].Dauer + SzeneList[AktSzene].Uebergang)  * SpeedFaktor)
		{
			TimeSzeneStart = GetTickCount();
			StatusSzene = 0;
			IncSzeneIndex();
			goto Repeat;
		}
		else
		{
			for (i = 0; i < AnzKacheln; i++)
			{

				float Proz = float(TimeAkt-TimeSzeneStart -  SzeneList[AktSzene].Dauer * SpeedFaktor) / (float(SzeneList[AktSzene].Uebergang) * SpeedFaktor) ;
				if (Proz > 1.0)
					Proz = 1.0;
				if (Proz < 0.0)
					Proz = 0.0;
				
		AktSzeneValues.Kachel[ KachelList[i] ][0] = SetFarbe (SzeneList[AktSzene ].Kachel[ KachelList[i] ][0], 
															  SzeneList[NextSzene].Kachel[ KachelList[i] ][0], Proz, DimmerFaktor) ;

		AktSzeneValues.Kachel[ KachelList[i] ][1] = SetFarbe (SzeneList[AktSzene ].Kachel[ KachelList[i] ][1], 
															  SzeneList[NextSzene].Kachel[ KachelList[i] ][1], Proz, DimmerFaktor);


		AktSzeneValues.Kachel[ KachelList[i] ][2] = SetFarbe (SzeneList[AktSzene ].Kachel[ KachelList[i] ][2], 
															  SzeneList[NextSzene].Kachel[ KachelList[i] ][2], Proz, DimmerFaktor);




			}
		}
	}


	return;
}

//--------------------------------------

unsigned char CPlayer::SetFarbe(unsigned char last, unsigned char next, float proz, float DimmerFaktor) 
{
unsigned char ret;

	if (last < next)
		ret = (last + (float)(next-last) * proz) * DimmerFaktor;
	else
		ret = (last - (float)(last-next) * proz) * DimmerFaktor;


	return ret;
}


//-----------------------------

/*********************************************************************
 SplitLine(char *str) zerteilt str in einzelne Felder, die durch#
 Komma getrennt sein müssen und speichert sie im Array Felder[][] ab.
 Der übergebene String bleibt unverändert.
  
 **********************************************************************/


void CPlayer::SplitLine(char *zeile1)
{
int i;
char *ptr;
char zeile[STRLEN];

	str_cpy(zeile,zeile1);
	for (i = 0; i < MAX_FELDER; i++)
   	Felder[i][0] = 0x0;
	if (*zeile1 == 0x0)
   	return;
	if (zeile1 == NULL)
		return;
	str_tok(zeile,";");		// Kommentar entfernen
	for (i = 0; i < MAX_FELDER; i++)
   {
		if (i == 0)
      	ptr = str_tok(zeile,",");
		else
      	ptr = str_tok(NULL,",");
		str_remblanks(ptr);
		if (ptr != NULL)
	      str_cpy(Felder[i],ptr);
		else
		{
      	break;
      }
   }

}
