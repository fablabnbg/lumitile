	Processor 12F675

; ********************************************************************************************
; **************************  LED-Wall Power  ******************************************
; ********************************************************************************************
;21.06.2007	
;	-Versuch mit diesem PIC eine zentrale Oberspannung zu erzeugen
;
; ********************************************************************************************
	LIST P=12F675
; ********************************************************************************************
#define	W		00
#define	C		00
#define	Z		02
#define	F		01
#define	TMR0		01
#define	PCL		02
#define	STATUS		03
#define	FSR		04
#define	GPIO		05
#define	PCLATH		0A
#define	INTCON		0B
#define	PIR1		0C
#define	PIE1		0C
#define	TMR1L		0E
#define	TMR1H		0F
#define	T1CON		10	; T1Con Register
#define	CMCON		19	
#define	ADRESH		1E
#define	ADCON0		1F

; ab hier Bank 1
#define	OPTION_REG	01
#define	TRIS0		05
#define	OSCCAL		10	; Oszi. 90H
#define	VRCON		19
#define	ADRESL		1E
#define	ANSEL		1F

; ab hier Register 20 .. 5F
#define	Flag_ON		20,0
#define	Stellwert	21
#define	Periode1	22
#define	Periode2	23
#define	Merker		24
#define	Stellwert_S	25
#define	Zaehler		26


#define	W_TEMP		5D
#define	STATUS_TEMP	5E
#define	PCLATH_TEMP	5F

#define	Spannung	b'00000001'
#define	Temperatur	b'10001101'

#define	Wert1		d'255'
#define	Wert2		d'1'

; ********************************************************************************************
; ********************************************************************************************
;12F675-Configs---------------------------------------------------------------------
	__IDLOCS	H'AAAA' ;       User ID
;-----------------------------------------------------------------------------------
;
	__CONFIG  B'01000100000100'
;                   ||||||||||||||
;                   |||||||||||+++---FOSC 111=RC R+C an GP5, GP4=CLKOUT
;                   |||||||||||+++---FOSC 110=RC R+C an GP5
;                   |||||||||||+++---FOSC 101=INTOSC GP4=CLKOUT
;                   |||||||||||+++---FOSC 100=INTOSC
;                   |||||||||||+++---FOSC 011=EC
;                   |||||||||||+++---FOSC 010=HS	***
;                   |||||||||||+++---FOSC 001=XT
;                   |||||||||||+++---FOSC 000=LP
;                   |||||||||||     
;                   ||||||||||+------WDTE 0=disa 1=ena
;                   |||||||||+-------PWRT 0=ena  1=disa
;                   ||||||||+--------MCLR 0=din  1=ena
;                   |||||||+---------BOR  0=disa 1=ena
;                   ||||||+----------CP   0=prod 1=CPF off
;                   |||||+-----------CPD  0=prod 1=CPD off
;                   ||+++------------
;                   |+---------------BG0
;                   +----------------BG1
;
;
;-----------------------------------------------------------------------------------
;=============================================================================================
; PROGRAMM
;=============================================================================================

	NOP
	clrf	STATUS
	goto	start

; ********************************************************************************************
; ********************       ISR     *********************************************************
; ********************************************************************************************
	org	004
; ********************************************************************************************

	RETFIE			; sofort zurück nach INT

; ********************************************************************************************
; ************** Initialisierung beginnt hier *******************
; ********************************************************************************************

start
	clrwdt
	nop

;=============================================================================================
; Register 20H bis 7FH löschen
;=============================================================================================
	movlw	20	; beginne bei Register 20H
	movwf	FSR	; FSR

	clrf	0
	incf	FSR, F

	movlw	0x60
	subwf	FSR, W
	btfss	STATUS, Z
	goto	$-5

;=============================================================================================
; INIT Ports, OPTIN, INTCON
;=============================================================================================

	bsf	STATUS, 5
	movlw	0x80		; Center Frequenz
	movwf	OSCCAL
	movlw	b'00001111'
	movwf	OPTION_REG
	bcf	STATUS, 5

	movlw	b'00000000'
	movwf	INTCON

	movlw	b'00000000'
	movwf	T1CON

	clrf	GPIO
	bsf	STATUS, 5
	movlw	b'00000000'
	movwf	PIE1
	movlw	b'11011011'
	movwf	TRIS0
	bcf	STATUS, 5
	clrf	GPIO

	movlw	b'00000100'	; Comparator GP1=-IN, int. CVref
	movwf	CMCON

	bsf	STATUS, 5
	movlw	0xA3		; 0,6V
	movwf	VRCON

	movlw	b'00101000'
	movwf	ANSEL
	bcf	STATUS, 5

	movlw	b'10011001'
	movwf	ADCON0


	movlw	Wert1
	movwf	Stellwert

;***************************************************************************************************
;***************************************************************************************************

; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
; %%%%%% Hauptprogramm LOOP Begin  %%%%%%%%%
; %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

main
	bsf	GPIO, 2		; Schalttransistor
	clrwdt
	nop
	nop
	nop
	nop
	nop
	bcf	GPIO, 2		; wieder abschalten 
	nop
	nop
	goto	main

;***************************************************************************************************
read_T
	movlw	Temperatur
	movwf	ADCON0
	nop
	nop
	nop
	nop
	nop
	nop
	bsf	ADCON0, 1
	btfsc	ADCON0, 1
	goto	$-1

	return


;***************************************************************************************************
Start_TMR00
	movlw	0xF8
	movwf	TMR0
	bcf	INTCON, 2
	return

Start_TMR01
	movlw	0xFF
	movwf	TMR0
	bcf	INTCON, 2
	return

;***************************************************************************************************
Tab_Wert
	addwf	PCL, F
	retlw 	d'16'	; 0
	retlw 	d'16'	; 1
	retlw 	d'17'	; 2
	retlw 	d'18'	; 3
	retlw 	d'19'	; 4
	retlw 	d'20'	; 5
	retlw 	d'21'	; 6
	retlw 	d'22'	; 7
	retlw 	d'23'	; 8
	retlw 	d'24'	; 9
	retlw 	d'25'	; 10
	retlw 	d'26'	; 11
	retlw 	d'27'	; 12
	retlw 	d'28'	; 13
	retlw 	d'29'	; 14
	retlw 	d'30'	; 15
	retlw 	d'31'	; 16
	retlw 	d'31'	; 17
	retlw 	d'32'	; 18
	retlw 	d'33'	; 19
	retlw 	d'34'	; 20
	retlw 	d'35'	; 21
	retlw 	d'36'	; 22
	retlw 	d'37'	; 23
	retlw 	d'38'	; 24
	retlw 	d'39'	; 25
	retlw 	d'40'	; 26
	retlw 	d'41'	; 27
	retlw 	d'42'	; 28
	retlw 	d'43'	; 29
	retlw 	d'44'	; 30
	retlw 	d'45'	; 31
	retlw 	d'46'	; 32
	retlw 	d'46'	; 33
	retlw 	d'47'	; 34
	retlw 	d'48'	; 35
	retlw 	d'49'	; 36
	retlw 	d'50'	; 37
	retlw 	d'51'	; 38
	retlw 	d'52'	; 39
	retlw 	d'53'	; 40
	retlw 	d'54'	; 41
	retlw 	d'55'	; 42
	retlw 	d'56'	; 43
	retlw 	d'57'	; 44
	retlw 	d'58'	; 45
	retlw 	d'59'	; 46
	retlw 	d'60'	; 47
	retlw 	d'61'	; 48
	retlw 	d'61'	; 49
	retlw 	d'62'	; 50
	retlw 	d'63'	; 51
	retlw 	d'64'	; 52
	retlw 	d'65'	; 53
	retlw 	d'66'	; 54
	retlw 	d'67'	; 55
	retlw 	d'68'	; 56
	retlw 	d'69'	; 57
	retlw 	d'70'	; 58
	retlw 	d'71'	; 59
	retlw 	d'72'	; 60
	retlw 	d'73'	; 61
	retlw 	d'74'	; 62
	retlw 	d'75'	; 63
	retlw 	d'76'	; 64
	retlw 	d'76'	; 65
	retlw 	d'77'	; 66
	retlw 	d'78'	; 67
	retlw 	d'79'	; 68
	retlw 	d'80'	; 69
	retlw 	d'81'	; 70
	retlw 	d'82'	; 71
	retlw 	d'83'	; 72
	retlw 	d'84'	; 73
	retlw 	d'85'	; 74
	retlw 	d'86'	; 75
	retlw 	d'87'	; 76
	retlw 	d'88'	; 77
	retlw 	d'89'	; 78
	retlw 	d'90'	; 79
	retlw 	d'91'	; 80
	retlw 	d'91'	; 81
	retlw 	d'92'	; 82
	retlw 	d'93'	; 83
	retlw 	d'94'	; 84
	retlw 	d'95'	; 85
	retlw 	d'96'	; 86
	retlw 	d'97'	; 87
	retlw 	d'98'	; 88
	retlw 	d'99'	; 89
	retlw 	d'100'	; 90
	retlw 	d'101'	; 91
	retlw 	d'102'	; 92
	retlw 	d'103'	; 93
	retlw 	d'104'	; 94
	retlw 	d'105'	; 95
	retlw 	d'106'	; 96
	retlw 	d'106'	; 97
	retlw 	d'107'	; 98
	retlw 	d'108'	; 99
	retlw 	d'109'	; 100
	retlw 	d'110'	; 101
	retlw 	d'111'	; 102
	retlw 	d'112'	; 103
	retlw 	d'113'	; 104
	retlw 	d'114'	; 105
	retlw 	d'115'	; 106
	retlw 	d'116'	; 107
	retlw 	d'117'	; 108
	retlw 	d'118'	; 109
	retlw 	d'119'	; 110
	retlw 	d'120'	; 111
	retlw 	d'121'	; 112
	retlw 	d'121'	; 113
	retlw 	d'122'	; 114
	retlw 	d'123'	; 115
	retlw 	d'124'	; 116
	retlw 	d'125'	; 117
	retlw 	d'126'	; 118
	retlw 	d'127'	; 119
	retlw 	d'128'	; 120
	retlw 	d'129'	; 121
	retlw 	d'130'	; 122
	retlw 	d'131'	; 123
	retlw 	d'132'	; 124
	retlw 	d'133'	; 125
	retlw 	d'134'	; 126
	retlw 	d'135'	; 127
	retlw 	d'136'	; 128
	retlw 	d'136'	; 129
	retlw 	d'137'	; 130
	retlw 	d'138'	; 131
	retlw 	d'139'	; 132
	retlw 	d'140'	; 133
	retlw 	d'141'	; 134
	retlw 	d'142'	; 135
	retlw 	d'143'	; 136
	retlw 	d'144'	; 137
	retlw 	d'145'	; 138
	retlw 	d'146'	; 139
	retlw 	d'147'	; 140
	retlw 	d'148'	; 141
	retlw 	d'149'	; 142
	retlw 	d'150'	; 143
	retlw 	d'151'	; 144
	retlw 	d'151'	; 145
	retlw 	d'152'	; 146
	retlw 	d'153'	; 147
	retlw 	d'154'	; 148
	retlw 	d'155'	; 149
	retlw 	d'156'	; 150
	retlw 	d'157'	; 151
	retlw 	d'158'	; 152
	retlw 	d'159'	; 153
	retlw 	d'160'	; 154
	retlw 	d'161'	; 155
	retlw 	d'162'	; 156
	retlw 	d'163'	; 157
	retlw 	d'164'	; 158
	retlw 	d'165'	; 159
	retlw 	d'166'	; 160
	retlw 	d'166'	; 161
	retlw 	d'167'	; 162
	retlw 	d'168'	; 163
	retlw 	d'169'	; 164
	retlw 	d'170'	; 165
	retlw 	d'171'	; 166
	retlw 	d'172'	; 167
	retlw 	d'173'	; 168
	retlw 	d'174'	; 169
	retlw 	d'175'	; 170
	retlw 	d'176'	; 171
	retlw 	d'177'	; 172
	retlw 	d'178'	; 173
	retlw 	d'179'	; 174
	retlw 	d'180'	; 175
	retlw 	d'181'	; 176
	retlw 	d'181'	; 177
	retlw 	d'182'	; 178
	retlw 	d'183'	; 179
	retlw 	d'184'	; 180
	retlw 	d'185'	; 181
	retlw 	d'186'	; 182
	retlw 	d'187'	; 183
	retlw 	d'188'	; 184
	retlw 	d'189'	; 185
	retlw 	d'190'	; 186
	retlw 	d'191'	; 187
	retlw 	d'192'	; 188
	retlw 	d'193'	; 189
	retlw 	d'194'	; 190
	retlw 	d'195'	; 191
	retlw 	d'196'	; 192
	retlw 	d'196'	; 193
	retlw 	d'197'	; 194
	retlw 	d'198'	; 195
	retlw 	d'199'	; 196
	retlw 	d'200'	; 197
	retlw 	d'201'	; 198
	retlw 	d'202'	; 199
	retlw 	d'203'	; 200
	retlw 	d'204'	; 201
	retlw 	d'205'	; 202
	retlw 	d'206'	; 203
	retlw 	d'207'	; 204
	retlw 	d'208'	; 205
	retlw 	d'209'	; 206
	retlw 	d'210'	; 207
	retlw 	d'211'	; 208
	retlw 	d'211'	; 209
	retlw 	d'212'	; 210
	retlw 	d'213'	; 211
	retlw 	d'214'	; 212
	retlw 	d'215'	; 213
	retlw 	d'216'	; 214
	retlw 	d'217'	; 215
	retlw 	d'218'	; 216
	retlw 	d'219'	; 217
	retlw 	d'220'	; 218
	retlw 	d'221'	; 219
	retlw 	d'222'	; 220
	retlw 	d'223'	; 221
	retlw 	d'224'	; 222
	retlw 	d'225'	; 223
	retlw 	d'226'	; 224
	retlw 	d'226'	; 225
	retlw 	d'227'	; 226
	retlw 	d'228'	; 227
	retlw 	d'229'	; 228
	retlw 	d'230'	; 229
	retlw 	d'231'	; 230
	retlw 	d'232'	; 231
	retlw 	d'233'	; 232
	retlw 	d'234'	; 233
	retlw 	d'235'	; 234
	retlw 	d'236'	; 235
	retlw 	d'237'	; 236
	retlw 	d'238'	; 237
	retlw 	d'239'	; 238
	retlw 	d'240'	; 239
	retlw 	d'241'	; 240
	retlw 	d'241'	; 241
	retlw 	d'242'	; 242
	retlw 	d'243'	; 243
	retlw 	d'244'	; 244
	retlw 	d'245'	; 245
	retlw 	d'246'	; 246
	retlw 	d'247'	; 247
	retlw 	d'248'	; 248
	retlw 	d'249'	; 249
	retlw 	d'250'	; 250
	retlw 	d'251'	; 251
	retlw 	d'252'	; 252
	retlw 	d'253'	; 253
	retlw 	d'254'	; 254
	retlw 	d'255'	; 255

;***************************************************************************************************
;***************************************************************************************************
	END
