#include "stdafx.h"

#include<stdio.h>
#include<string.h>
#include<ctype.h>
#include<stdlib.h>

char * str_tok(char *string, char *such);
void str_cpy(char *dest,char *src);
int str_isdigit(char *string);
void str_remblanks(char *ptr);
void str_nfill(char *help,int zeichen,int anzahl);
void str_filln(char *help,int zeichen,int anzahl);
void str_cpyback(char *dest, char *src);
int str_ncmp(char *str1, char *str2, int anz);
int str_search(char *zeichenkette,char zeichen);
void str_RemTrailBlanks(char *ptr);
int str_cmp(char *str1, char *str2);
int str_GetLine(char *ret, char *buff);


/************************************************************************
	fügt den string ins an den ANfang von String str ein
*************************************************************************/
void str_ins(char *str, char *ins)
{
char temp[1000];
	str_cpy(temp,ins);
   strcat(temp,str);
   str_cpy(str,temp);
   return;
}
/************************************************************************
	str_tok(char*, char*) arbeitet wie strtok(..) von C++, mit folgender
	Žnderung:
1.	Der zu suchende String ist nur ein Character lang!
	str_tok("AC,BC,Cc","Cc") sucht also nur nach "C" als Delimiter, liefert
	als Ergebnis also "A"
2.	strtok(";Kommentar",";") liefert ";Kommentar" als Ergebnis! Von der
	Logik her máte es einen Nullstring zurckliefern.
	str_tok(..) korrigiert diesen Fehler!
*************************************************************************/
char * str_tok(char *string, char *such)
{
static char *start;
static char *end;
static char *string_end;


	if (string != NULL)
	{
		start = string;
		end = string;
		string_end = start + strlen(string);
	}
	else
	{
		if ( start == NULL)
			return(start);
		if (end == string_end)
		{
			start = NULL;
			return(start);
		}
		start = end+1;
		end = start;
	}
	while( 1 )
	{
		if (*start == 0x0)
		{
			start = NULL;
			break;
		}
		if ( (*end == *such) || ( *end == 0x0) )
		{
			*end = 0x0;
			break;
		}

		end++;
	}
	return(start);
}
/************************************************************************
	str_cpy(char *dest,char *src) arbeitet wie strcpy mit dem Unterschied:
	wenn src NULL ist, dann ist auch dest NULL
*************************************************************************/
void str_cpy(char *dest,char *src)
{
	if (src == NULL)
	{
		*dest = 0x0;
		return;
	}
	strcpy(dest,src);
}
/************************************************************************
   str_upr(char *string) arbeitet wie strurp mit dem Unterschied:
	wenn string NULL ist, dann wird keine Operation ausgeführt
*************************************************************************/
void str_upr(char *string)
{
	if (string == NULL)
   	return;
   else
   	strupr(string);
	return;
}
/************************************************************************
	str_isdigit(char *) prft einen String, ob er nur Ziffern (einschl. +-)
	enth„lt. Rckgabe = 1 wenn nur digits
*************************************************************************/
int str_isdigit(char *string)
{
char *ptr;
	ptr = string;
	while (*ptr != 0x0)
	{
		if ( !(isdigit(*ptr)) )
			return(-1);
	}
	return(1);
}
/*********************************************************************
 Diese Funktion entfernt fhrende und anh„ngende Blanks in einem eber-
 gebenen String. Ebenso TAB, CR,LF

**********************************************************************/

void str_remblanks(char *ptr)
{
char *help;

	if (ptr == NULL)			// Null-String
		return;
	if (*ptr == 0x0)			// Null-String
		return;
	help = ptr;
// fhrende Blanks
	while( isspace(*help) )
	{
		if (*help >= 0)		// ISSPACE betrachtet alle Zeichen > 7f als Space
			help++;
		else
			break;
	}
// ANHŽNGENDE Blanks
	while ( isspace( (int) *(help+strlen(help) -1) )  )
	{
		if ( strlen(help) == 0 )
			break;
		if ( *(help+strlen(help)-1) < 0x7f)
			*(help+strlen(help) -1) = 0x0;
		else
			break;
	}
	strcpy(ptr,help);
}


/*********************************************************************
 Diese Funktion entfernt fhrende und anh„ngende Blanks in einem eber-
 gebenen String. Ebenso TAB, CR,LF
nur characters zwischen 0x1 und 0x20 werden entfernt, keine VTX-Sonderzeichen
**********************************************************************/

void str_remblanks_spez(char *ptr)
{
char *help;

	if (ptr == NULL)			// Null-String
		return;
	if (*ptr == 0x0)			// Null-String
		return;
	help = ptr;
// fhrende Blanks
	while( isspace(*help) )
	{
		if (*help >= 0)		// ISSPACE betrachtet alle Zeichen > 7f als Space
			help++;
		else
			break;
	}
// ANHŽNGENDE Blanks
	while ( isspace( (int) *(help+strlen(help) -1) )  )
	{
		if ( strlen(help) == 0 )
			break;

		
		if (*(help+strlen(help) -1)  < 0)		// ISSPACE betrachtet alle Zeichen > 7f als Space
			break;
		
		
		if ( *(help+strlen(help)-1) < 0x7f)
			*(help+strlen(help) -1) = 0x0;
		else
			break;
	}
	strcpy(ptr,help);
}


/*********************************************************************
 Diese Funktion entfernt nur führende „ngende Blanks in einem eber-
 gebenen String. Ebenso TAB, CR,LF

**********************************************************************/

void str_remleadblanks(char *ptr)
{
char *help;

	if (ptr == NULL)			// Null-String
		return;
	if (*ptr == 0x0)			// Null-String
		return;
	help = ptr;
// führende Blanks
	while( isspace(*help) )
	{
		if (*help >= 0)		// ISSPACE betrachtet alle Zeichen > 7f als Space
			help++;
		else
			break;
	}
	strcpy(ptr,help);
}

/*********************************************************************
 Diese Funktion entfernt anhängende Blanks in einem Über-
 gebenen String. Ebenso TAB, CR,LF

**********************************************************************/

void str_RemTrailBlanks(char *ptr)
{
char *help;

	if (ptr == NULL)			// Null-String
		return;
	if (*ptr == 0x0)			// Null-String
		return;
	help = ptr;
// ANHÄNGENDE Blanks
	while ( isspace( (int) *(help+strlen(help) -1) )  )
	{
		if ( strlen(help) == 0 )
			break;
		if ( (unsigned)*(help+strlen(help)-1) <= 0x20)
			*(help+strlen(help) -1) = 0x0;
		else
			break;
	}
	strcpy(ptr,help);
}
/**************************************************************
	str_nfill(*char, int zeichen,int Anzahl) fllt einen String
	von ANfang an mit "Anzahl" "zeichen" und schlieát mit 0 ab.
**************************************************************/
void str_nfill(char *help,int zeichen,int anzahl)
{
int count;

	for (count = 0; count < anzahl; count++)
	{
		*help++ = (char) zeichen;
	}
	*help = 0x0;
}
/**************************************************************
	str_filln() verl„ngert einen String auf "anzahl" character mit
	dem  Zeichen "zeichen" und schlieát auf anzahl mit 0 ab
	d.h. der String wird ggf, gekrzt
**************************************************************/

void str_filln(char *help,int zeichen,int anzahl)
{
int count;
int count1 ;

	count = anzahl - strlen(help);
	if (count <= 0)
	{
		*(help+anzahl) = 0x0;
		return;
	}
	while( *help != 0x0)
	{
		help++;
	}
	for (count1 = 0; count1 <count ; count1++)
	{
		*help++ = (char) zeichen;
	}
	*help = 0x0;
}
/**************************************************************
	str_cpyback(char *dest, char *src) kopiert den String source
	in den String dest, aber vom Ende des Strings dest her
**************************************************************/
void str_cpyback(char *dest, char *src)
{
int count;
int i;

	count = strlen(src);
	if (  count == 0  )
		return;
	if (  count > (int)strlen(dest) )
		count = strlen(dest);
	src += (strlen(src) - 1);
	dest += (strlen(dest) - 1);
	for (i = 0; i < count  ; i++)
	{
		*dest-- = *src--;
	}

}

/*********************************************************************
  str_searchchar(char *, char)
	sucht char in *char

  Übergabeparameter: Pointer auf string, suchcharacter

  RÜckgabe:  0 wenn kein Zeichen gefunden, 1 wenn gefunden
**********************************************************************/
int str_searchchar(char *zeichenkette,char zeichen)
{
int i;

	if (zeichenkette == NULL)
		return 0;
	for (i = 0; i < (int)strlen(zeichenkette); i++)
	{
		if ( *(zeichenkette+i) == zeichen )
			return(1);

	}

	return(0);
}
/*********************************************************************
  str_search(char *, char)
	sucht char in *char

  Übergabeparameter: Pointer auf string, suchcharacter

  RÜckgabe:  -1 wenn Zeichen nicht gefunden, sons Position des Zeichens
**********************************************************************/
int str_search(char *zeichenkette,char zeichen)
{
int i;

	for (i = 0; i < (int)strlen(zeichenkette); i++)
	{
		if ( *(zeichenkette+i) == zeichen )
			return i;

	}

	return -1;
}
/*********************************************************************
	int str_ncmp(char *str1, char *str2, int anz);

  Übergabeparameter: Pointer auf string1,string2 Anzahl

  RÜckgabe:  wie strncmp, jedoch NULL-Check
**********************************************************************/
int str_ncmp(char *str1, char *str2, int anz)
{
int ret;

	if ( str1 == NULL && str2 == NULL)
   	return 0;
	if (str1 == NULL )
   	return -1;
	if (str2 == NULL )
   	return 1;
	if (*str1 == 0x0 && *str2 == 0x0)
   	return 0;
	if (*str2 == 0x0)
   	return 1;
	if (*str1 == 0x0)
   	return -1;
	ret = strncmp(str1,str2,anz);
   return ret;

}

/*********************************************************************
	int str_cmp(char *str1, char *str2);

  Übergabeparameter: Pointer auf string1,string2

  RÜckgabe:  wie strcmp, jedoch NULL-Check
**********************************************************************/
int str_cmp(char *str1, char *str2)
{
int ret;


	if ( str1 == NULL && str2 == NULL)
   	return 0;
	if (strlen(str1) != strlen(str2) )
		return -1;
	if (str1 == NULL )
   	return -1;
	if (str2 == NULL )
   	return 1;
	if (*str1 == 0x0 && *str2 == 0x0)
   	return 0;
	if (*str2 == 0x0)
   	return 1;
	if (*str1 == 0x0)
   	return -1;
	ret = strcmp(str1,str2);
   return ret;

}

/*********************************************************************
  str_delchar(char *str, int pos) loescht im String den character
  str[i] raus.
  CR definiert NICHT das Strin-Ende

**********************************************************************/
int str_delchar(char *str, int pos)
{

	while(str[pos] != 0x0)
	{
   	str[pos] = str[pos+1];
		pos++;
	}
	return 0;
}
/*********************************************************************
  str_len(char *str) liefert die Laenge eine Strings zurueck
  CR definiert NICHT das String-Ende

**********************************************************************/
int str_len(char *str)
{
int i=0;

	while(str[i] != 0x0)
	{
		i++;
	}
	return i;
}

/*********************************************************************
  str_len(char *str) liefert die Laenge eine Strings zurueck
  CR definiert NICHT das String-Ende

**********************************************************************/
int str_cat(char *str, char *str1)
{
int i, k, m;

	i = str_len(str);
	k = str_len(str1);
	for( m = 0; m < k; m++)
   	*(str + i + m) = *(str1 + m);
	*(str + i + k) = 0x0;

	return 0;
}
/*********************************************************************
  str_getline(char* ret, char *buff)
  1. AUfruf: buff != 0
  nächste Aufrufe Buff = NULL,

**********************************************************************/
int str_GetLine(char *ret, char *buff)
{
static char *ptr;
static char *buff1;
static char *zstart;
char zeichen;
int loop = 1;
int count = 0;
static int bufflen;

	if (buff == NULL && ret == NULL)
   {
		ptr--;
		return -1;
	}
	if (buff != NULL)
   {
		ptr = buff;
		buff1 = buff;
		bufflen = strlen(buff);
   }
	zstart = ptr;
   if (  ptr-buff1 >= bufflen)
   {
     	*ret = 0x0;
		return 0;
   }
	while (loop)
   {
	   zeichen = *(ptr++);
      *(ret++) = zeichen;
	  count++;
      if (zeichen == 0xa ||   ptr-buff1 >= bufflen || count == 512-1 )
      {
      	*ret = 0x0;
			return (zstart - buff1);
		}
   }
	return 0;
}


/*********************************************************************
  str_RemoveEmptyLines(char *buff)
  entfernt aus einem String leere Zeilen

**********************************************************************/
void str_RemoveEmptyLines(char *buff)
{
char *tmp;
char help[512];
int ret;

	tmp = buff;
	str_GetLine(help,buff);
	do
   {
		if (help[0] == 0x0)
   		return;
   	if ( help[0] == 0xd)
      {
      	str_delchar(buff,ret);
         str_GetLine(NULL,NULL);
      	str_delchar(buff,ret);
         str_GetLine(NULL,NULL);
      }
   }
	while ( (ret = str_GetLine(help,NULL)) >= 0);

	return;
}
/*********************************************************************
  str_ishexdigit(char ) prüft, ob ein character ein Hexdigit ist
  Rückgabe = 1 wenn ja, sonst 0
**********************************************************************/
int str_isHexDigit(char zeichen)
{

	zeichen = toupper(zeichen);
	if( isdigit(zeichen) )
   	return 1;
	if (zeichen >= 0x41 && zeichen <= 0x46)
   	return 1;

	return 0;
}

/*********************************************************************
  str_ishexdigit(char ) prüft, ob ein character ein Hexdigit ist
  Rückgabe = 1 wenn ja, sonst 0
**********************************************************************/
int str_IsHexString(char *buff)
{
unsigned int i;

	strupr(buff);

	for (i = 0; i < strlen(buff); i++)
	{
		if (!isdigit(*(buff+i)) && (*(buff+i) < 0x41 || *(buff+i) > 0x46))
   			return 0;
	}
	return 1;
}

/*********************************************************************
str_DelLine(char *str) löschte eine Zeile aus einem buffer
**********************************************************************/

void str_DelLine(char *buff)
{
char temp[513];
int anz;

	
	str_GetLine(temp,buff);
	anz = strlen(buff) - strlen(temp);
	memmove(buff,buff+strlen(temp),anz);
	memset(buff+anz  ,0x0,strlen(temp) );
	return;
}

/*********************************************************************
str_HasStringAlpha(char *str) gibt 1 zurück, wenn in einem String ein
Buchstabe autaucht.
**********************************************************************/
int str_HasStringAlpha( char *str)
{
int i;
	if ( str ==NULL)
		return 0;
	for (i = 0; i < (int)strlen(str); i++)
	{
		if ( isalpha(str[i] ) )
			return 1;
	}
	return 0;
}

/*********************************************************************
 Diese Funktion zentriert einen String ohne die L„nge zu ver„ndern
**********************************************************************/

void str_center(char *ptr)
{
char temp[512];
int len, len1;
int i = 0;
int test,test1
;
	len = strlen(ptr);
	len1 = len;
	str_remblanks_spez(ptr);
	str_cpy(temp,ptr);
	test = strlen(temp);

	while (*(ptr+i) < 0x0  && len1 > 0)
	{
		if (*(ptr+i) < 0x0 )
			len1--;
		i++;
	}
	  
	
	*ptr = 0x0;
	str_filln(ptr,0x20,len);
	test1 = len1 - strlen(temp);

	if (  test1 < 0)
		len1 = len;

	str_cpy(ptr+(len1-strlen(temp))/2,temp);
	str_filln(ptr,0x20,len);
	return;

}


/*********************************************************************
 Diese Funktion wandelt DOS-Umlaute in VTX-Umlaute um
**********************************************************************/
char umlaute_bereinigen(char zeichen)
{

	switch(zeichen)
	{
		case '„':
			zeichen = 0x7b;
			break;
		case '':
			zeichen = 0x7d;
			break;
		case '”':
			zeichen = 0x7c;
			break;
		case 'á':
			zeichen = 0x7e;
			break;
		case 'Ž':
			zeichen = 0x5b;
			break;
		case '™':
			zeichen = 0x5c;
			break;
		case 'š':
			zeichen = 0x5d;
	}
	if ( (unsigned char) zeichen == 0xc0)			// ALT 192 = Wolfgangs Spezial Paragraph aus Alcatel-Zeiten (?)
		zeichen = 0x40;


	return(zeichen);
}
/*********************************************************************
 Diese Funktion wandelt VTX-Umlaute in WIN-Umlaute um
**********************************************************************/
char str_umlaute_VtxToWin(char zeichen)
{

		switch(zeichen)
		{
		case 0x7b:
			zeichen = 'ä';
			break;
		case 0x7d:
			zeichen = 'ü';
			break;
		case 0x7c:
			zeichen = 'ö';
			break;
		case 0x7e:
			zeichen = 'ß';
			break;
		case 0x5b:
			zeichen = 'Ä';
			break;
		case 0x5c:
			zeichen = 'Ö';
			break;
		case 0x5d:
			zeichen = 'Ü';
			break;
	}
	return(zeichen);
}

/*********************************************************************
 Diese Funktion wandelt WIN-Umlaute in VTX-Umlaute um
**********************************************************************/
char str_umlaute_WinToVtx(char zeichen)
{

		switch(zeichen)
		{
		case 'ä':
			zeichen = 0x7b;
			break;
		case 'ü':
			zeichen = 0x7d;
			break;
		case 'ö':
			zeichen = 0x7c;
			break;
		case 'ß':
			zeichen = 0x7e;
			break;
		case 'Ä':
			zeichen = 0x5b;
			break;
		case 'Ö':
			zeichen = 0x5c;
			break;
		case 'Ü':
			zeichen = 0x5d;
			break;
	}
	return(zeichen);
}

void str_WinToVtx(char *str)
{
	
unsigned int i;

	if (str == NULL)
		return;

	for (i = 0; i < strlen(str); i++)
	{
		str[i] = str_umlaute_WinToVtx(str[i]);

	}
	return;

}

/**********************Characters Wordstar-kompatibel machen ***********/

unsigned char ws_convert( unsigned char zeichen)
{
#define  TFBs   0xc0-0xc0
#define 	TFBrt  0xc1-0xc0
#define  TFBgr  0xc2-0xc0
#define  TFBgb  0xc3-0xc0
#define  TFBbl  0xc4-0xc0
#define  TFBma  0xc5-0xc0
#define  TFBcy  0xc6-0xc0
#define  TFBws  0xc7-0xc0

#define  GFBs   0xd0-0xc0
#define 	GFBrt  0xd1-0xc0
#define  GFBgr  0xd2-0xc0
#define  GFBgb  0xd3-0xc0
#define  GFBbl  0xd4-0xc0
#define  GFBma  0xd5-0xc0
#define  GFBcy  0xd6-0xc0
#define  GFBws  0xd7-0xc0

#define	BstH	 0xd
#define  HGan	 0x1d
#define	HGaus	 0x1c
#define 	FLASHan	0x8
#define FLASHaus	0x9
#define GRF2		0x1a
#define BOXan		0xb
#define BOXaus		0xa
#define HOLDgrf	0x1e

		switch (zeichen)
		{
		case 180:
			zeichen = TFBs;
			break;
		case 181:
			zeichen = TFBrt;
			break;
		case 182:
			zeichen = TFBgr;
			break;
		case 183:
			zeichen = TFBgb;
			break;
		case 184:
			zeichen = TFBbl;
			break;
		case 185:
			zeichen = TFBma;
			break;
		case 186:
			zeichen = TFBcy;
			break;
		case 187:
			zeichen = TFBws;
			break;
		case 240:
			zeichen = GFBs;
			break;
		case 241:
			zeichen = GFBrt;
			break;
		case 242:
			zeichen = GFBgr;
			break;
		case 243:
			zeichen = GFBgb;
			break;
		case 244:
			zeichen = GFBbl;
			break;
		case 245:
			zeichen = GFBma;
			break;
		case 246:
			zeichen = GFBcy;
			break;
		case 247:
			zeichen = GFBws;
			break;
		case 189:
			zeichen = HGan;
			break;
		case 190:
			zeichen = HGaus;
			break;
		case 191:
			zeichen = BstH;
			break;
		case 193:
			zeichen = FLASHan;
			break;
		case 194:
			zeichen = FLASHaus;
			break;
		case 209:
			zeichen = GRF2;
			break;
		case 211:
			zeichen = BOXan;
			break;
		case 212:
			zeichen = BOXaus;
			break;
		case 215:
			zeichen = HOLDgrf;
			break;
		default:
			break;
		};
	return(zeichen);
}

/*********************************************************************
 Diese Funktion wandelt in einem String DOS-Umlaute in VTX-Umlaute
 um sowie Steuerzeichen (Farbe, H”he, Hintergrund usww.) aus Wordstar-
 bearbeiteten Dateien (VIDCON) in die entsprechenden VTX-Steuerzeichen
**********************************************************************/
void str_vtx_convert(unsigned char *ptr)
{

	while (*ptr != 0x0)
	{
		*ptr = ws_convert( *ptr ) ;
		*ptr = umlaute_bereinigen( *ptr) ;
		ptr++;
	}


}

//******************************************************************
// str_isTime(char *time) prüft, ob time eine gültige Zeit enthält.
// erlaubte Formate:   hh:mm   hh:mm:ss
// Die Funktion überprüft auch die Zahlen (Stunde >= 0; <=23 usw.)
// RETURN: -1 wenn ungültig, sonst Anzahl Sekunden
//******************************************************************
long str_isTime(char *time)
{
int ZiffCnt = 0;
long Ziff1;
long Ziff2;
long Ziff3;
int i = 0;
char temp[512+1];
int tempidx = 0;

	*temp = 0x0; tempidx = 0;	
	while(time[i] != 0)
	{
		if ( !isdigit(time[i]) )
		{
			if (i == 0)
				return -1;
			else
			{
				i++;
				break;
			}
		}
		else
		{
			temp[tempidx++] = time[i++];
			temp[tempidx] = 0x0;
		}	
	}
	Ziff1 = atol(temp);
	if (i == (int)strlen(time) )
		return -1;



	*temp = 0x0; tempidx = 0;	
	while(time[i] != 0)
	{
		if ( !isdigit(time[i]) )
		{
				i++;
				break;
		}
		else
		{
			temp[tempidx++] = time[i++];
			temp[tempidx] = 0x0;
		}	
	}
	Ziff2 = atol(temp);
	if (i == (int)strlen(time) )			// hh:mm
	{
		if (Ziff1 > 23 || Ziff1 < 0)
			return -1;
		if (Ziff2 > 59 || Ziff2 < 0)
			return -1;
	
		return Ziff1*3600L + Ziff2 * 60L;
	}

	*temp = 0x0; tempidx = 0;	
	while(time[i] != 0)
	{
		if ( !isdigit(time[i]) )
		{
				i++;
				break;
		}
		else
		{
			temp[tempidx++] = time[i++];
			temp[tempidx] = 0x0;
		}	
	}
	Ziff3 = atol(temp);

	if (Ziff1 > 23 || Ziff1 < 0)
		return -1;
	if (Ziff2 > 59 || Ziff2 < 0)
		return -1;

	if (Ziff3 > 59 || Ziff2 < 0)
		return -1;

	return Ziff1*3600L + Ziff2 * 60L +Ziff3;




}

//**************************************

int str_FindStrBack(char * str,char *search,int RxIdx)
{
int i;
int len;

	len = strlen(search);
	for (i = RxIdx-len; i >= 0 ; i--)
	{

		if (!strncmp(str+i,search,len) )
			return i;
	}

	return -1;
}



//**************************************

void str_GetUhrzeit(char *str)
{
	time_t tim; struct tm  *LocT;
	time(&tim); LocT = localtime(&tim); 
	sprintf(str,"%02d:%02d:%02d", LocT->tm_hour,LocT->tm_min,LocT->tm_sec);

	return;
}

