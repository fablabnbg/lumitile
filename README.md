lumitile
========

"Revival of LumiTile hardware with new software."

Das LumiTile USB-Kabel verbindet eine oder mehrere LED Kacheln mit einem PC.
Das USB-Kabel enthält zwei aktive Komponenten: Einen USB-RS232-Wandler und
einen ATtiny2313, welcher als 200mA Leitungstreiber und Protokollwandler for
RS458 arbeitet.

Das Kabel meldet sich als USART Gerät am Rechner. Unter Linux ist das z.B.
/dev/tty/USB0 

Die Übertragungsgeschwindigkeit ist 19200 Baud (in der Software vom 21.8.2013).  
Das Protokoll besteht aus Kommandos, die mit ENTER (oder Carriage Return) 
abgeschlossen werden.
Ein typisches Kommando besteht aus 4 Dezimalzahlen im Bereich von 0 bis 255, 
jeweils durch Leerzeichen abgetrennt.

Die Werte bedeuten der Reihe nach: Kachel-Adresse, Rot, Grün, Blau.
Die Kachel-Adresse 255 spricht immer alle Kacheln an. Rot/Grün/Blau Werte von 0
schalten den jeweiligen Farbkanal auf Minimum (ganz aus geht leider nicht).
Werte von 255 sind Maximum.

Beispiel: Kachel 3 soll orange leuchten:
	3 255 122 0

Die Kachel-Addresse mus auf der Rückseite einer jeden Kachel eingestellt werden.
Dazu dienen die DIP-Schalter SCH1 und SCH2.
Achtung: Laut einstellanweisung werden alle Kacheln mit Adresse 254 ausgeliefert.
D.h. vor Inbetriebnahme sind unbedingt die DIP-Schalter zu korrigieren.

Die niedrigste mögliche Adresse ist 1. 

<pre>
Addr	SCH1		  SCH2
----    ----              ----
1	OFF ON  ON  ON    ON  ON  ON  ON
2	ON  OFF ON  ON    ON  ON  ON  ON
3	OFF OFF ON  ON    ON  ON  ON  ON
4	ON  ON  OFF ON    ON  ON  ON  ON

16	ON  ON  ON  ON    OFF ON  ON  ON
17	OFF ON  ON  ON    OFF ON  ON  ON

32	ON  ON  ON  ON    ON  OFF ON  ON
33	OFF ON  ON  ON    ON  OFF ON  ON

64	ON  ON  ON  ON    ON  ON  OFF ON
65	OFF ON  ON  ON    ON  ON  OFF ON

128	ON  ON  ON  ON    ON  ON  ON  OFF
129	OFF ON  ON  ON    ON  ON  ON  OFF

254	ON  OFF OFF OFF   OFF OFF OFF OFF
</pre>
