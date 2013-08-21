# -*- coding: cp1252 -*-
import os,sys,types,re,time

import wx			#wxPython Fensterbibliothek :-)
import wx.grid			#der Grid ist in einem Untermodul
import wx.lib.colourselect	#da ist der Farbbutton
import socket                   #für TCP/IP-Verbindung zum Player

__pychecker__ = 'no-miximport unusednames=_,_0,_1,_2,_3,_4,_5,_6,_7,_8,_9'

wx.InitAllImageHandlers()	#damit alle bekannten Bildformate von selber gehen

#EIGENE EXCEPTION ...
class LedDataException (Exception):
  pass

#DIE BASIS DATEN !
  #Singleton, es gibt nur 1 globales Programm, was gerade editiert wird kein MDI
  # ! das Objekt dahinter wird allerdings bei New und Reload komplett getauscht
MainProg = None
  #DER GROSSE MODUS: M=META oder P=PAINT (normales edit)
MainMode = 'P'


#DIE SUPER-FENSTER !
MainWin = None			#DAS HAUPTFENSTER
SzeneList = None		#  DIE SZENENFOLGE als eigenes ListCtrl
TheGrid = None			#  DER GROSSE GRID als Zeichenfenster
ColourButton = None		#  1 FARBBUTTON dient als Mini-Palette, offizieller Name "Clipboard-Button"
  ##LATER: ganzer Stack von bisherigen Farben
  ##  - eigene class von Panel oder so ableiten, Sizer wie bisher oben in main
  ##  - Right Click auf Zelle macht Push hierher
  ##  - Right Click auf Register holt aus aktueller Zelle
  ##  =>Problem: Register- und Stack-denke zu sehr vermischt :-|


#GLOBALE KONSTANTEN: Version der ledp/ledx Files
LedOutputVersion = 1.00		#diese Version erzeuge ich
LedInputVersions = (0.6, 1.0)	#dieses Intervall akzeptiere ich ohne Gemecker

#NEU ECHTES INI-FILE: mit ConfigParser
import ConfigParser		#maechtig und nicht WIN-spezifisch

ini = None			#wird im main initialisiert

inidefaults = {			##ACHTUNG: diese Varis kenne ich, mit diesen defaults
  "PlayerName":"KachelPlayer.exe",	#meine Verbindung zur Player-EXE
  "PlayerIP":  "127.0.0.1",
  "PlayerPort":"4444",

  "TempLedxName":"testplay.ledx",	#Filename fuers temporaere LEDX-File

  #3 boolsche Variable zur Feineinstellung des Verhaltens
  "ShowHexNumbers":"1",			#ob der Grid die Hexzahlen der Farben zeigt
  "BlockMouseEdit":"1",			#NEU: Zell-Edit per Maus verhindern (trotz hex-Anzeige)
  "FillKillSelection":"0",		#ob Fill-Operationen die Selektion entfernen, damit man das Ergebnis besser sieht
}

lastledpath = ""		#letzter Pfad von Load/Save aus kleinem INI-File daneben


#----------------------------------------------------------------------
#AUS MEINER ALTEN BASIS

def ifop(pif,pthen,pelse):
  "Ersatz-Operator pif ? pthen : pelse"
  if pif: return pthen
  else:   return pelse

def int0(input,defvalue=0):
  "vereinfachtes 'int' wird 0 bei Fehler"
  try: return int(input)
  except (ValueError,TypeError): return 0

def iconCheck(iconfile):
  "empfaengt einen Filenamen icon/... und returnt ihn *GEPRUEFT* wieder"
  try:
    if os.path.getsize(iconfile): return iconfile
    else: raise LedDataException,"Empty Iconfile %s" % iconfile
  except OSError,ex:
    raise LedDataException,"Missing Iconfile: %s" % str(ex)


#----------------------------------------------------------------------
#LOWEST LEVEL: Verbindung zu Player.exe (und Export von LEDX Files)

#EIGENE EXCEPTION nur fuer die Verbindung, just in Case
class LedConnException (LedDataException):
  pass

  #so mache ich normale Kommentare (in Scite GRUEN),
  #die nach dem Ausfuellen von Pseudocode noch drin sein duerften

class CPlayerConnection:
  "die Schnittstelle von der GUI oben zum TCP/IP Kanal zum Player"
  
  #member ledprog	Referenz nach oben auf das LED Programm zu dem ich gehoere
  #member running	FLAG, ob zur Zeit ein ganzes Programm laeuft
  #			(was fuer Einzelops abgebrochen werden muss)
      
      ##  Ich gehe davon aus dass sich auch das Verbindungsobjekt hier merkt, 
      ##  ob er zuletzt das Spielen eines ganzen Programms angewiesen hat.
      ##  Ob die EXE unten wirklich noch spielt oder auf der letzten Szene steht
      ##  (falls loop ausgeschaltet), ist sekundaer:
      ##  - fuer das Abbruchsignal (falls es das extra gibt) nach unten ist es egal,
      ##    der Player wird sicher auch Abbruch verkraften wenn er schon steht
      ##  - damit die GUI gezwungen wird statt SendKachel das ganze SendSzene zu machen,
      ##    *MUSS* es sogar hier passieren, egal ob er laeuft oder steht
  
  #member lasterror	TEXT des letzten gemeldeten Fehlers
  
  def __init__(self):
    "KONSTRUKTOR: Verbindung herstellen"
    
    self.running = False	#anfangs laeuft noch kein Programm
    self.lasterror = ""		#es gab keinen vorherigen Fehler
    
    self.Connect()		#evtl Starten, dann Verbinden, LedConnException schlaegt nach oben durch
  
  def Connect(self):
    "nicht nur auf Socket verbinden, sondern Player eventuell erst starten"
    
    #0.Schliessen versuchen, wird auch als re-Connect verwendet...
    try: self.sock.close()
    except: pass
    self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    
    #1.Verbinden zu bereits laufendem Player
    try: self.sock.connect((ini.get("KachelEditor","PlayerIP"), ini.getint("KachelEditor","PlayerPort")))
    except socket.error,ex: pass
    else:
      self.lasterror = ""
      return
    
    #2.sonst Player starten
    try: os.startfile( ini.get("KachelEditor","PlayerName") )	#wie Doppelklick auf die EXE, os.system ist leider mit Shell-Fenster
    except Exception,ex: pass
    else:
    
      #3.drei Versuche im Sekundentakt jetzt zu verbinden
      for i in range(3):
        try: self.sock.connect((ini.get("KachelEditor","PlayerIP"), ini.getint("KachelEditor","PlayerPort")))
        except socket.error,ex: time.sleep(1)
        else: 
          self.lasterror = ""
          return
    
    #wenn nix geht, als meine eigene Exception nach oben geben
    self.TryRaise("Problem in PlayerConnection: ",str(ex))
  
  def TryRaise(self, head,msg):
    "bedingtes 'raise', nur wenn das gleiche Problem noch nicht gemeldet wurde"
    
    if self.lasterror != msg:
      self.lasterror = msg
      raise LedConnException, head + msg
  
  def TrySend(self, data):
    "Wrapper um self.sock.send inklusive Fehlerbehandlung"
    
    try:
      self.sock.send(data[:1])			##SOCKET-BUG: aus irgendeinem Grund geht das erste Schreiben in toten Socket noch gut,
      self.sock.send(data[1:])			##  erst das zweite liefert die Exception
    
    except socket.error: 
      self.Connect()				#bei Problemen Re-Connect versuchen, neue LedConnException-Meldungen schlagen durch
      
      try:
        self.sock.send(data[:1])		#wenns geklappt hat nochmal versuchen
        self.sock.send(data[1:])		##SOCKET-BUG: siehe oben...
      except socket.error,ex:			#[unwahrscheinlich] connect geht, aber send nicht...
        self.TryRaise("Problem beim Senden: ",str(ex))
  
  def Disconnect(self):
    "[manueller] DESTRUKTOR: nur Verbindung trennen, Player *SOLL* weiterlaufen"
    
    try: self.sock.close()
    except socket.error: pass
    self.running = False
  
  def SendKachel(self, kachel,rgb):
    "KLEINE SCHNITTSTELLE: nur R,G,B Werte fuer eine einzelne Kachel"
    
    #wenn ein Programm laeuft, stoppe ich das und returne False, damit ich die ganze Szene bekomme
    if self.running:
      self.running = False
      return False
    
    ##DOKU: die Werte sind 1..127 fuer Kachel, und jeweils 0..255 fuer r,g,b
    r,g,b = rgb
    self.TrySend( "*Kachel:%02X%02X%02X%02X#\r\n" % (kachel,r,g,b) )
    return True			#WICHTIG ! Erfolg melden
  
  def SendSzene(self, pixelliste):
    "ZWISCHEN-SCHICHT: mehrere/alle Kacheln aus dem Grid neu zuweisen"
    ##ACHTUNG: im Zuge der Optimierung kann die pixelliste
    ##  auch nur einen Teil aller Kacheln der Szene enthalten
    
    #wenn ein Programm laeuft, stoppe ich das (aber kein return False, ich habe ja schon ganze Szene)
    if self.running:
      self.running = False
    
    ##OPTIMIERUNG: wie im TXT argumentiert sollte eine ganze Szene
    ##   auch als 1 Paket ueber den Kanal gehen,
    ##   wenn das nicht gewuenscht ist, kann alles so bleiben !
    for pixel in pixelliste:
      ##DOKU: pixel ist jeweils (kachel, (r,g,b)), zB. (127, (255,255,255))
      ##   das wird durch '*' zerlegt und als kachel,rgb reingegeben...
      self.SendKachel( *pixel )		#evtl Fehler schlaegt weiter durch
  
  def SendProgramm(self, program,file, play=False, loop=False):
    "GROSSE SCHNITTSTELLE: ganzes Program Exportieren und/oder Abspielen lassen"
    #NEU: Abspielen geht immer ueber LEDX File, file wird immer genannt
    
    #--------------------------------------------------
    #1.EINPACKEN
    
    ##PSEUDOCODE: das verwendete LEDX Format war eigentlich nur als Beispiel gedacht,
    ##  der Player verwendet es aber seitdem auch
    
    ledx = []			#das entstehende LEDX als Liste von Zeilen sammeln, ist effektiver !
    
    #einzige Headerinformation ist die Version, z.B. V=0.51
    ##TODO: Player sollte auch warnen bei zu neuen ledx-Files
    ##      wie ich bei ledp Files unten (nach LedInputVersions suchen...)
    ledx.append( "V=" + program['version'] )
    
    #ansonsten folgt eine Liste von Szenen
    for szene in program['szenen']:
      #Szenenanfang, die Einzelszene enthaelt dauer und trans als Zahl
      ledx.append( "S(%d,%d) {" % (szene['dauer'],szene['trans']) )
      
      #Schleife ueber Pixel (Kacheln + Farbwerte)
      for (kachel,(r,g,b)) in szene['pixel']:
        ledx.append( "  %03d=%02x,%02x,%02x" % (kachel,r,g,b) )
      
      #Szenenende + Leerzeile
      ledx.append( "}" )
      ledx.append( "" )
    
    ledx = '\n'.join(ledx)	#so wird aus der Zeilenliste ein einziger langer String
    
    
    #--------------------------------------------------
    #2.LEDX SCHREIBEN
    
    try:
      ledxfile = open(file,"wt")
      ledxfile.write(ledx)
      ledxfile.close()
    except IOError,ex:
      raise LedDataException,"Kann Programm zum Abspielen nicht schreiben: " + str(ex) + "\nBitte nicht direkt von CD starten."
    
    
    #--------------------------------------------------
    #3.DEN PLAYER ZUM SPIELEN ANWEISEN
    
    if play:
      self.TrySend( "*PlayFile:" + file + "#\r\n" )
      
      ##@@SIGI: das Flag 'loop' sollte mit runtergegeben werden
      ##   Programme die nicht loopen bleiben auf letzter Szene stehen,
      ##   sie springen nicht etwa selber auf gui-anzeige zurueck
      self.running = True

PlayerConn = None		#in dieser globale Vari legt main das Verbindungsobjekt an


#----------------------------------------------------------------------
#THEMA FARBEN & HEX-STRINGS

def PrintImage(wximage):
  "Debugroutine zum Ausgeben von Bildfarben"
  for ry in range(wximage.GetHeight()):		#row bzw. y
    for cx in range(wximage.GetWidth()):		#col bzw. x
      rgb = (wximage.GetRed(cx,ry), wximage.GetGreen(cx,ry), wximage.GetBlue(cx,ry))
      #wximage.IsTransparent(cx,ry) fuer interne Bilder erstmal ignoriert
      print HexColorString( rgb ),
    print

def hexonly(hex):
  return ifop(hex[0]=='(', hex[1:-1], hex)

def rgb2hex(rgb):
  return "%02X%02X%02X" % rgb
def col2hex(col):
  return rgb2hex( col.Get() )

def hex2rgb(hex):
  hex = hexonly(hex)
  return tuple( map(lambda s: eval("0x" + s), (hex[:2] , hex[2:4] , hex[4:])) )
def hex2col(hex):
  return wx.Colour( *hex2rgb(hex) )

def RgbMix(rgb0,rgb1, zaehler,nenner):
  "Lineare Mischung von 2 RGB-Vektoren anhand des Bruchs zaehler/nenner"
  return tuple( map(lambda x0,x1: ((x1-x0) * zaehler) / nenner + x0, rgb0, rgb1) )

def autopastell(kachelnum):
  if kachelnum==-1: return (0,0,0)

  ##DOKU: PASTELLFORMEL
  ##  die 7 bits der Kachelnummer sind -rgbRGB
  ##  die hinteren Stellen werden die hoeherwertigen, damit sich Nachbarn gut unterscheiden  
  lo,hi = map(int, oct(kachelnum)[-2:])		#die 2 Oktalziffern fuer rgb und RGB
  r = ((hi & 4) << 4) + ((lo & 4) << 3)		#3 Farbwerte r,g,b jeweils im Bit-Bereich -xx-----
  g = ((hi & 2) << 5) + ((lo & 2) << 4)
  b = ((hi & 1) << 6) + ((lo & 1) << 5)
  return map(lambda c: (0x9F+c), [r,g,b])	#+ 1--11111 Grau = Pastell

BADHEX_RE    = re.compile("[^0-9a-fA-F]")	#alle non Hexziffern
def HexColorString(hex, meta=None):
  "brutale Anpassung, danach sind es garantiert 6 Hex-Ziffern mit oder ohne (boese klammer)"
  
  #besondere Typen zu String...
  boese = False
  if hex is None: hex = "FFFFFF"			#default ist weiss
  elif type(hex)==types.IntType: hex = "%06X" % hex	#Farbe als Zahl, ungenutzt
  elif type(hex)==types.TupleType: hex=rgb2hex(hex)	#RGB Tuple aus Berechnungen
  elif type(hex)==types.InstanceType: hex=col2hex(hex)	#Objekt als wx.Colour versuchen
  elif type(hex)!=types.StringType: hex = "FF0000"	#KEIN BEKANNTER TYP -> rot machen...
  
  #zweierlei Strings anpassen
  else:
    hex = hex.strip().upper()		#Whitespace aussen weg, upper
    if hex[ 0]=='(': boese = True; hex = hex[1:]	#boese sind nicht ------
    if hex[-1]==')': boese = True; hex = hex[:-1]	#sondern virtuelle Farbe
    
    hex = hex[:6].zfill(6)		#auf 6 Zeichen kuerzen oder auffuellen
    hex = BADHEX_RE.sub("0",hex)	#alles was nicht 0-F ist durch 0 ersetzen
  
  #genanntes meta hat Prio darueber ob es schon 'boese' war
  if meta is not None: boese = (meta==-1)
  
  #je nach boese mit oder ohne Klammer (virtuell)
  if boese: return "(%s)" % hex
  else:     return hex

def KachelCheck(kachel):
  "der Bruder von HexColorString fuer Kachelnummern"
  try: kachel = int(kachel)
  except: return -1
  
  if kachel < 1: return -1		##TRICK: auch -1 wird zu -1
  if kachel > MAXKACHEL: return MAXKACHEL
  return kachel


#----------------------------------------------------------------------
#GENERISCHE, WIEDERVERWENDBARE DIALOGE

#Fehler-Optik aus basis.LogMessage herausgeloest
MSG_INFO  = 0
MSG_WARNG = 1
MSG_ERROR = 2
MSG_FATAL = 3

MSG_Levelnames  = [ "OKAY", "WARNING", "ERROR", "FATAL" ]		#die Textform
MSG_Levelcolors = [ "#FFFFFF", "#FFFF00", "#FF0000", "#FF00FF" ]		#Farbe der HTML-Tabellenzeile :-)
MSG_Levelicons  = [ wx.ICON_INFORMATION, wx.ICON_EXCLAMATION, wx.ICON_ERROR, wx.ICON_ERROR ]	#das Icon fuer wx.MessageDialog

def LogMessageDialog(level, message):
  "simple OK-MESSAGE mit Fehlerleveln"
  dlg = wx.MessageDialog(MainWin, message,
                         MSG_Levelnames[level],
                         wx.OK | MSG_Levelicons[level])
  dlg.ShowModal()
  dlg.Destroy()

def QuestionDialog(level, message, yesdefault):
  "JA/NEIN-FRAGE mit Fehlerleveln"
  dlg = wx.MessageDialog(MainWin, message,
                         MSG_Levelnames[level],
                         wx.YES_NO
                         | ifop(yesdefault,wx.YES_DEFAULT,wx.NO_DEFAULT)
                         | MSG_Levelicons[level])
  ret = (dlg.ShowModal() == wx.ID_YES)
  dlg.Destroy()
  return ret

def UseFileDialog(win,title, path,wildcard, save, isled=True):
  "Vereinfachender Wrapper fuer meine typischen Open & Save Dialoge"
  
  if path: dir,file = os.path.split(path)
  else:
    global lastledpath
    while not os.path.exists(lastledpath):					#lastledpath PRUEFEN und sonst:
      if len(lastledpath)<=3:	lastledpath = os.getcwd() + "/led"			#  wenn ganzes Drive x:\ fehlt, dann current dir
      else:			lastledpath = os.path.dirname(lastledpath)	#  wenn einfaches x:\yyy\zzz fehlt, dann 1 Stufe hoch
    dir,file = lastledpath,""
  
  modeflags = ifop(save, wx.SAVE|wx.OVERWRITE_PROMPT, wx.OPEN|wx.FILE_MUST_EXIST)
  
  try:
    dlg = wx.FileDialog(win,title, dir,file,wildcard, modeflags)
    if dlg.ShowModal() == wx.ID_OK:
      path = dlg.GetPath()
      if isled:
        lastledpath = os.path.dirname(path)
        
        try:		#einfach sofort ins INI schreiben
          lastini = open("LastPath.ini","wt")
          lastini.write("[LastPath]\nlastledpath=%s\n" % lastledpath)
          lastini.close()
        except IOError,ex:
          pass		#Probleme mit LastPath.ini werden ignoriert
      
      return path
    else: return None
  finally: dlg.Destroy()

class MyTableDialog(wx.Dialog):
  "Generischer WERTE-LISTEN DIALOG, zeilenweise Name: [Value]"
  
  ##DOKU: values & labels werden nur zum Init der Elemente gebraucht
  #member items		Liste aller TextCtrl zum Auslesen
  #member typen		 "      "   Konversionen (str,int0) dafuer
  
  def __init__(self,parent,id, values, labels,typen):
    wx.Dialog.__init__(self, parent, id, "Edit Szene")
    
    self.items = [ None ] * len(values)
    self.typen = typen
    
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    #eine Grid Zeile fuer jeden einzustellenden Wert
    grid = wx.FlexGridSizer(0,2, 0,0)
    grid.AddGrowableCol(1,1)
    
    for i in range(len(values)):
      label = wx.StaticText(self,-1, labels[i])
      grid.Add(label, 0, wx.ALL, 3)
      if type(typen[i])==types.ListType:	#Listendarstellung als Dropdown
        self.items[i] = wx.ComboBox(self,-1, str(values[i]), choices=typen[i], size=(80,-1), style=wx.CB_READONLY)
      else:
        self.items[i] = wx.TextCtrl(self,-1, str(values[i]), size=(80,-1))
      grid.Add(self.items[i], 1, wx.EXPAND|wx.ALL, 3)
    
    sizer.Add(grid, 0, wx.EXPAND|wx.ALL, 3)
    
    #letzte Zeile Ok/Cancel
    btnsizer = wx.StdDialogButtonSizer()
    btn = wx.Button(self, wx.ID_OK)
    btn.SetDefault()
    btnsizer.AddButton(btn)
    btn = wx.Button(self, wx.ID_CANCEL)
    btnsizer.AddButton(btn)
    btnsizer.Realize()
    sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
    
    self.SetSizer(sizer)
    sizer.Fit(self)
  
  def GetValues(self):
    ret = []
    for typ,item in zip( self.typen, self.items ):
      #Listen-Typen werden oben zur Combobox, ich muss hier nicht pruefen
      if type(typ)==types.ListType: value =      item.GetValue()
      else:                         value = typ( item.GetValue() )
      ret.append( value )
    return ret

def UseTableDialog(parent, values, labels,typen):
  "die komplette Benutzung von MyTableDialog bequem gekapselt"
  
  #die 3 Listen muessen gleich lang sein...
  assert len(values)==len(labels)==len(typen),"Widerspruechliche Beschreibung fuer MyTableDialog"
  
  dlg = MyTableDialog(parent,-1, values, labels,typen)
  if dlg.ShowModal() == wx.ID_OK: values = dlg.GetValues()
  else:                           values = []
  dlg.Destroy()
  return values


#----------------------------------------------------------------------
#SZENEN SIND EIGENSTAENDIGE OBJEKTE

class LedSzene:
  "eine Szene ist ein BMP-basierter Schritt eines LED Programms"
  
  #member ledprog	Referenz nach oben auf das LED Programm zu dem ich gehoere
  #member name		mein Name fuer Anzeige in der GUI
  #member dauer		stillstehende Dauer		in 1/10 sec
  #member trans		Uebergang zur naechsten Szene	in 1/10 sec
  #
  #member farben	2D Liste [width][height] => Farbstring "1188FF" normal oder "(2277CC)" virtuell
  
  #-------------------------------------------------
  #INIT aus dict, STR nach String
  
  def __init__(self, ledprog, name,dauer,trans,farben=None,copy=None,fill=None):
    "Konstruktion einer Szene mit farben-Liste oder mit fill gefuellt"
    
    self.ledprog = ledprog
    self.name    = name
    self.dauer   = dauer
    self.trans   = trans
    
    #die eigentlichen Farben: A) aus Vorgabe pruefen
    if farben:
      self.SetFarben( farben, frominit=True )
    
    #                         B) Copy aus anderer Szene
    elif copy:
      self.name    = copy.name + "."		#die genannten 2 Werte waren ein Fake, copy kopieren (nur Name anders)
      self.dauer   = copy.dauer			#auch von dort holen
      self.trans   = copy.trans			#auch von dort holen
      
      self.farben  = map(list, copy.farben)	#2D tiefe copy der farben
    
    #                         C) oder leer fuellen (weiss wenn alles fehlt)
    else:
      if fill: fill = HexColorString(fill,1)	#genannte Fuellfarbe pruefen (##TRICK: mit meta!=-1 wird (virtuell...) vermieden)
      else:    fill = "FFFFFF"			#sonst Weiss
      
      #eine Kopie von meta: -1 wird (fill), Rest wird fill
      self.farben = map(
        lambda line: map(
          lambda kachel: ifop(kachel==-1,'(%s)'%fill,fill),
          line
        ),
        ledprog.meta
      )
  
  def __str__(self):
    "meine Stringform ist ein sauber umgebrochenes dict wie es im *.LED in Pythonformat steht"
    ##ACHTUNG: inklusive fester Einrueckung, es steht immer in gleicher Tiefe im File
    
    ret = [ "    { " ]		#return wird als Liste von Zeilen gesammelt
    
    ret.append( "      'name': '%s'," % self.name )
    ret.append( "      'dauer': %d," % self.dauer )
    ret.append( "      'trans': %d," % self.trans )
    ret.append( "      'farben': [" )
    
    for line in self.farben:
      ret.append( "        " + str(line) + "," )
    
    ret.append( "      ]," )
    ret.append( "    }" )
    
    return '\n'.join( ret )
  
  def GetExport(self):
    "Export-Helper: ganze Szene fertig als Dict fuer PlayerConn aufbereiten"
    
    #Hauptsache: alle Pixel (kachel, rgb) unique in dict sammeln
    pixeldict = {}
    
    for line,metaline in zip(self.farben, self.ledprog.meta):
      for hex,meta in zip(line,metaline):
        if meta!=-1:
          pixeldict[meta] = hex2rgb(hex)
    
    return { "dauer": self.dauer, 
             "trans": self.trans,
             "pixel": pixeldict.items() }
  
  
  #-------------------------------------------------
  #Schnittstelle zum GRID u.a.: 2D Liste von Farbstrings + Export-Schnittstelle
  
  def GetFarben(self):
    "einfach, nur der Symmetrie halber..."
    ##ACHTUNG: nur Referenz, aussen nicht einfach aendern !
    return self.farben
  
  def SetFarben(self,farben, frominit=False):
    "fertige 2D Liste von Farbstrings normal oder (virtuell) genau geprueft nach self.farben uebernehmen"
    
    #von farben -nach-> newfarben -nach-> self.farben mit Metapruefung uebertragen
    newfarben = []
    for l in range(self.ledprog.size[1]):
      try: line = farben[l]
      except IndexError: line = []		#fuellt map selber mit None auf
      metaline = self.ledprog.meta[l]
      
      newfarben.append( map(
        HexColorString,
        line[:self.ledprog.size[0]],		#auf Laenge von metaline kuerzen, None auffuellen passiert automatisch
        metaline
      ) )
    
    if not frominit:
      if newfarben==self.farben: return		#der Rest passiert nur bei Aenderung !
      self.ledprog.needsave = True
      #needsave nur wenn was existierendes geaendert wurde
    
    self.farben = newfarben
    
    #Zusatz: Ketten beruecksichtigen
    for _,poslist in self.ledprog.ketten.items():
      pos = poslist[0]
      first = self.farben[pos[0]][pos[1]]	#der Farbwert von der ersten pos
      for pos in poslist[1:]:			#... gilt auch fuer alle folgenden
        self.farben[pos[0]][pos[1]] = first
  
  
  #-------------------------------------------------
  #Bild-Schnittstelle ist wx.Image
  #  (Filearbeit, Resize, Convert 2 wx.Bitmap ... passiert aussen)
  
  def GetImage(self):
    "mein exaktes Abbild als wx.Image erstellen"
    
    rows = self.ledprog.size[1]
    cols = self.ledprog.size[0]
    
    wximage = wx.EmptyImage(cols,rows)
    for ry in range(rows):
      for cx in range(cols):
        hex = self.farben[ry][cx]
        ##LATER auf Wunsch transparent if hex[0]=="(": rgb = (-1,-1,-1) geht nicht, Aufwand... else:
        rgb = hex2rgb(hex)
        wximage.SetRGB(cx,ry, *rgb)
    
    return wximage
  
  def SetImage(self, wximage):
    "Image (aus Bildfile) als Hexfarben einlesen"
    
    rows = min(self.ledprog.size[1], wximage.GetHeight())
    cols = min(self.ledprog.size[0], wximage.GetWidth())
    
    for ry in range(rows):		#row bzw. y
      for cx in range(cols):		#col bzw. x
        rgb = (wximage.GetRed(cx,ry), wximage.GetGreen(cx,ry), wximage.GetBlue(cx,ry))
        if not wximage.IsTransparent(cx,ry):	#transparente Pixel aendern nix :-)
          self.farben[ry][cx] = HexColorString( rgb, self.ledprog.meta[ry][cx] )


#----------------------------------------------------------------------
#LED-PROGRAMM-OBJEKT

MAXSIZE = 30		#30 in einer Richtung ist absolute Schmerzgrenze
MAXKACHEL = 127		#maximale Kachelnummer ist nicht 30*30=900, sondern nur 7 bit
DEFAULTSIZE = 5		#default bei Problemen ist 5*5

class LedProgramm:
  "eigenes Objekt kapselt das aktuell bearbeitete LED-Programm mit Layout als Basis + allen Szenen"
  
  #member filename	das File, aus dem die Daten gelesen wurden
  #
  #member size		Tuple (width,height) fuer die 'aeussere' Feldgroesse
  #member meta		2D Liste [width][height] => Kachelnummer oder -1=fehlt
  #member ketten	DICT von Kachelnummer -> alle Positionen (nur doppelte, selber aus meta gesammelt)
  #member prop		DICT von User defined Properties
  #
  #member szenen	die eigentlichen PROGRAMMSCHRITTE (derzeit nur LEDSzene's, spaeter mehr)
  #member needsave	FLAG: ob ich gesichert werden muesste
  
  #-------------------------------------------------
  #INIT, FILEARBEIT
  
  def __init__(self, filename=None, size=None):
    assert not (filename and size), "LedProgramm kann nur aus file /ODER/ size konstruiert werden"
    
    self.meta   = []
    self.szenen = []
    
    if filename:	#KONSTRUKTOR aus File
      self.Load(filename)
    
    else:		#LEERER KONSTRUKTOR
      if size: w,h=size
      else:    w,h=DEFAULTSIZE,DEFAULTSIZE
      
      self.filename = ""
      self.SetSize(w,h, fillmeta=True)	#defaults, meta gleich aufzaehlen
      self.SetMeta()			#meta pruefen, NOCH KEINE weisse Startszene
      self.prop = { "QuadratSize":50 }	#derzeit nur 1 Property, mit defaults
      self.needsave = False
  
  def Load(self, filename=""):
    #LEDX Reimport geht nicht, verweigern und gar nicht erst hier festhalten
    if filename.lower().endswith(".ledx"): raise LedDataException,"Exportierte LEDX Programme koennen nicht mehr editiert werden"
    
    if filename: self.filename = os.path.abspath(filename)
    if not self.filename: raise LedDataException,"kein Filename fuer LedProgramm.Load angegeben"
    
    try:
      progdict = eval( open(self.filename,"rt").read() )
      
      #===== VERSION pruefen =====
      version = progdict.pop("version", 0.6)
        #default 0.6, das war die Urversion wo es noch Files ohne Versionsnummer gab
        #das wird nicht gespeichert, ich schreibe immer nur File der jetzigen Version
      
      #NEU: als Input akzeptiere ich laut LedInputVersions ein ganzes Intervall
      #     weiterhin nur als Warnung, es koennte ja trotzdem gehen...
      if version+0.001 < LedInputVersions[0]:
        LogMessageDialog(MSG_WARNG, "LEDP-Programmversion %0.2f\nist zu alt\nFolgefehler sind moeglich" % (version))
      if version-0.001 > LedInputVersions[1]:
        LogMessageDialog(MSG_WARNG, "LEDP-Programmversion %0.2f\nist zu neu\nFolgefehler sind moeglich" % (version))
      ##ACHTUNG: +- 0.001 Toleranz wegen Float-Gefahren
      
      #===== SIZE laden =====
      try: self.SetSize( *progdict.pop("size") )
      except KeyError: raise LedDataException,"Fehlende 'size' Angabe"			#beim pop
      except TypeError,ex: raise LedDataException,"Falsche 'size' Angabe: "+str(ex)	#beim Zerlegen, von unten kommt nix
      
      #===== META aufwendig gegen size pruefen und ergaenzen, gleich fuer KETTEN sammeln =====
      try: self.SetMeta( progdict.pop("meta") )
      except KeyError: raise LedDataException,"Fehlende 'meta' Szene"			#beim pop
      except ValueError: raise LedDataException,"Falsche 'meta' Angabe: "+str(ex)	#unten in der Funktion
      
      #===== Die grosse Szenen-Folge =====
      try: szenen = progdict.pop("szenen")
      except KeyError: raise LedDataException,"Fehlende 'szenen' Szenenfolge"
      
      if not szenen or \
         type(szenen) != types.ListType:
        raise LedDataException,"Illegaler 'szenen' " + str(szenen)
      
      self.szenen = []
      
      for szenedict in szenen:
        #den Rest erledigt der Konstruktor...
        szene = LedSzene(self, **szenedict)
        self.szenen.append( szene )
      
      #===== restliche Inhalte sind freie [UDP] Properties =====
      self.prop = progdict
      
      #fertig, ich bin frisch geladen
      self.needsave = False
    
    except Exception,ex:
      #alle Fehler auf meinen abbilden
      raise LedDataException,"Kann LED Programm nicht laden: " + str(ex)
  
  def SetSize(self, w,h, fillmeta=False):
    "Size w * h mit guter Kontrolle setzen, optional meta dabei durchzaehlen"
    
    ##TRICK: mit der getrennten Nennung w,h wollte ich nur sichergehen dass es genau 2 sind
    ##       jetzt aber als Schleife
    size = []
    for x in [w,h]:
      try: x = int(x)
      except (ValueError,TypeError): x = DEFAULTSIZE
      ##ACHTUNG: wie ueblich keinen Error, brutal auf default anpassen
      
      if   x < 1: x = 1
      elif x > MAXSIZE: x = MAXSIZE
      size.append(x)
    
    self.size = tuple(size)
    
    #optional Meta mit 1 ... w*h fuellen
    if fillmeta:
      self.meta = []
      self.ketten = {}
      start = 1
      for l in range( self.size[1] ):				#fuer alle Zeilen
        self.meta.append( range(start, start+self.size[0]) )	#fertige Nummernliste ab start...
        start += self.size[0]
    
    self.needsave = True
  
  def SetMeta(self, meta=None, makefirst=False, checkszenen=True):
    if not meta: meta = self.meta			#wenn nicht genannt, dann jetziges meta pruefen
    if not meta: raise ValueError,"Leerer meta-Wert"	#wenn es immer noch nix ist...
    if type(meta) != types.ListType: raise ValueError,"meta ist keine Liste"
    ##ACHTUNG: ValueError ist legitim - aus File fange ich ihn ab, aus grid waere es Fehler von mir
    
    #Pruefung gegen die size wie bisher beim Programm einlesen...
    newmeta = []
    ketten = {}
    
    width = self.size[0]
    for l in range( self.size[1] ):	#fuer alle *geplanten* Zeilen
      try: line = meta[l]		  #aktuelle Zeile holen
      except IndexError: line = []	  #nicht genug Zeilen da ?
      
      #auf width beschneiden oder mit -1 auffuellen
      line = line[:width] + (width - len(line)) * [ -1 ]
      
      #Kachelnummern duerfen nur 1..127 sein, sonst sind sie -1
      line = map( KachelCheck, line )
      newmeta.append( line )
      
      #gleich fuer Ketten sammeln
      for c,kachel in enumerate(line):
        poslist = ketten.setdefault(kachel,[])	#Positionsliste zu dieser Kachelnummer holen/anlegen
        poslist.append( (l,c) )
    
    #diese Folgen entstehen nur bei Ungleichheit
    if newmeta != self.meta:
      self.needsave = True
      self.meta = newmeta
      
      #KETTEN sollen nur die wirklich doppelten uebrigbleiben und auch nicht -1
      self.ketten = dict(filter( lambda (kachel,poslist): len(poslist)>1, ketten.items() ))
      self.ketten.pop(-1,None)
    
    #KONSEQUENZEN FUER DIE SZENEN-LISTE (auch bei Gleichheit wegen Wechsel zu Metaview und Zurueck)
    if checkszenen:
      for szene in self.szenen:
        #der Szene die eigenen Farben nochmal geben, dabei wird gegen meta geprueft
        ##TRICK: das ist wie frominit am Anfang, auch bei Gleichheit neu durchgehen
        szene.SetFarben( szene.GetFarben(), frominit=True )
    
    #optional die allererste Szene anlegen
    if not self.szenen and makefirst:
      self.szenen = [ LedSzene(self, "Szene 1",10,10) ]	#leerer Konstruktor: 2*1sec,komplett weiss
  
  def Save(self, filename=None):
    if filename: self.filename = os.path.abspath(filename)
    if not self.filename: raise LedDataException,"kein Filename fuer LedProgramm.Save angegeben"
    
    #eventuell erst ein .bak File anlegen...
    if os.path.exists(self.filename):
      try: os.remove(self.filename+".bak")
      except OSError: pass
      try: os.rename(self.filename, self.filename+".bak")
      except OSError: pass
    
    #und jetzt zeilenweise raus-printen
    try:
      try:
        f = None
        f = open(self.filename,"wt")
        print >>f, "#LED-Programm in lesbarer Form, nur VORSICHTIG editieren !"
        print >>f, "{"
        print >>f, "'version': %0.2f," % LedOutputVersion
        
        print >>f, "#DIE METASZENE..."
        print >>f, "'size':", self.size, ","
        print >>f, "'meta': ["
        
        for metaline in self.meta:
          #nicht einfach str(...), Wunschformatierung kann man besser lesen & editieren
          print >>f, "    [" + ("%3d," * self.size[0]) % tuple(metaline) + " ],"
        
        print >>f, "  ],"
        print >>f
        print >>f, "#USER DEFINED PROPERTIES"
        
        ##LATER (wenn es mehr werden...) dictsort nach Wunschsortierung
        for n,v in self.prop.items():
          print >>f, "'%s': %s," % (n, str(v))
        
        print >>f
        print >>f, "#LISTE VON SZENEN"
        print >>f, "'szenen': ["
        
        for szene in self.szenen:
          #__str__ von einer Szene macht das fertig eingerueckte {...} nur , fehlt noch
          print >>f, szene, ","
        
        print >>f, "  ],"
        print >>f, "}"
      
        self.needsave = False
      
      finally:
        if f: f.close()
    
    except IOError,ex:
      raise LedDataException,"Kann LED Programm nicht sichern: " + str(ex)
  
  def GetExport(self):
    "Export-Helper: mein Programm fertig als Dict fuer PlayerConn aufbereiten"
    ##ACHTUNG: die "fertige" Form hier ist nur ein gefiltertes Dict
    ##  die eigentliche Formatierung als kompaktes Ascii macht PlayerConn selber
    
    szenenex = []		#Kern: Liste von Szenen in Pixelform
    progex = { "version": "%0.2f" % LedOutputVersion, "szenen":szenenex }
    
    for szene in self.szenen:
      szenenex.append( szene.GetExport() )
    
    return progex
  
  
  #-------------------------------------------------
  #DIVERSE DATEN...
  
  def SetProperty(self, name,value):
    "beliebige UDP im header ablegen"
    
    #diese Props muessen gross anfangen, damit sind sie im File nicht mit festen Sachen zu verwechseln
    if not name[0].isupper():
      raise LedDataException,"UDP fuer SetProperty faengt nicht mit Grossbuchstaben an:" + name
    
    #eintragen [und vor allem needsave setzen] nur wenn es nicht schon so war
    if self.prop.get(name,not value) != value:
      self.needsave = True
      self.prop[name] = value
  
  def GetProperty(self, name,default):
    return self.prop.get(name,default)
  
  def GetKette(self, row,col):
    "moegliche Ketten-Brueder zu genannter Position auflisten, sonst []"
    kachel = self.meta[row][col]			#kachelnummer dort
    poslist = list( self.ketten.get(kachel, []) )	#Kopie der posliste dazu
    
    if len(poslist)<2: return []
    poslist.remove( (row,col) )				#Zelle selber aus Kopie rausnehmen (ist immer drin !)
    return poslist
  
  #AKTUELLE SZENE: nicht hier, sondern im Szenen-Listen-Widget
  
  #BITMAP Import & Export: nicht hier, direkt ueber die Szene
  ##LATER hier das ganze Programm als Bildfolge ? Animation ?
  
  #-------------------------------------------------
  #Arbeit mit der SZENENFOLGE
  
  def SzeneNew(self, index):
    "Neue, leere Szene einfuegen"
    
    szene = LedSzene(self, "Szene %d" % (len(self.szenen)+1) ,10,10)	#Name 'new',2*1sec,komplett weiss
    self.szenen.insert( index+1, szene )
    self.needsave = True
    return szene
  
  def SzeneDupl(self, index):
    "statt Kopie mit Zielort einfach Duplicate an Ort und Stelle"
    
    szene = LedSzene(self, "",0,0, copy=self.szenen[index])	#Copy Konstruktor
    self.szenen.insert( index+1, szene )
    self.needsave = True
    return szene
  
  def SzeneMove(self, index, diff):
    "statt Move mit Zielort nur Einzelschritte +/- 1"
    
    if not (0 <= index+diff < len(self.szenen)): return None
    szene = self.szenen.pop(index)
    self.szenen.insert(index+diff, szene)
    self.needsave = True
    return szene
  
  def SzeneDel(self, index):
    "Szene loeschen, ausser der letzten"
    
    if len(self.szenen)<2: return False
    del self.szenen[index]
    self.needsave = True
    return True


#----------------------------------------------------------------------
#SZENEN-LISTE ist der Chef "ueber" dem Grid

#braucht SzeneListCtrl fuer die Einsprungpunkte,
#zum Glueck braucht der mich nicht zur Konstruktion
SZENEMOVES = []

class SzeneListCtrl (wx.ListCtrl):
  #member currstep	aktuell selektierter Schritt aus Event gemerkt
  #			(aktuellen Step muss ich mir jeweils merken, weil ich ihn nur umstaendlich erfragen kann)
  
  ##DOKU: technische Details
  #member resize	Zielgroesse fuer Bildresize (etwa 16x16, aber sauber)
  #member selectevent	beobachtet, ob gerade ein Select-Event kam
  #member popupids	IDs von Popupmenu-Items, wo Bindungen erhalten bleiben
  
  def __init__(self, parent,id):
    #2 spaltig mit Zeilenlinien, editierbar, single selektion
    wx.ListCtrl.__init__(self, parent,id, 
                         style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_EDIT_LABELS|wx.LC_SINGLE_SEL)
    self.selectevent = False
    self.popupids = [None] * 5		#fuers Popupmenue spaeter
    
    self.imglist = wx.ImageList(16, 16)
    self.SetImageList(self.imglist, wx.IMAGE_LIST_SMALL)
    
    #COLUMNS: nicht nur einfach InsertColumn, ich will Bilder
    self.InsertColumn(0, "Szene", format=wx.LIST_FORMAT_RIGHT, width=70)
    self.InsertColumn(1, "Dauer", width=50)
    self.InsertColumn(2, "Trans", width=50)
    self.SetMinSize((70+50+50+5,-1))
    
    #-------------------------------------------------
    #LISTEN EVENTS...
    
      #Wechsel der Selektion fuehrt zu Grid-Update
      ##NOT: nur ueber select, deselect kommt zu spaet, suspekt
    self.Bind(wx.EVT_LIST_ITEM_SELECTED,    self.OnItemSelected)
    ##self.Bind(wx.EVT_LIST_ITEM_DESELECTED,  self.OnItemDeselected)
    
      #Begin Edit verbieten falls Meta
    self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT,   self.OnBeginEdit)
      ##NO: das Label ist doch der Name, denn es sind ja 2 Zahlen
    ##self.Bind(wx.EVT_LIST_END_LABEL_EDIT,   self.OnEndEdit)
    
      #Doppelklick (extra EVT_LEFT_DCLICK unnoetig) oder Enter fuehrt zu groesserem Editdialog
    self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,   self.OnItemActivated)
    
      #Rechtsklick gleiches Menue wie &Step
      #for wxMSW
    self.Bind(wx.EVT_COMMAND_RIGHT_CLICK,   self.OnRightClick)
      #for wxGTK
    self.Bind(wx.EVT_RIGHT_UP,              self.OnRightClick)
    
    ##LATER Veto des Spaltenresize ueberlegen
    ##self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag)
    
    #-------------------------------------------------
    #am Ende des Konstruktors aktuelles Programm laden
    self.LoadProgram()
  
  def LoadProgram(self):
    "GROSSES UPDATE: das LedProgramm laden und je nach Modus in der Liste darstellen"
    
    #RELOAD: wird nicht mehr nur am Anfang gerufen !
    self.DeleteAllItems()	#items in beiden Faellen raus, spalten bleiben leben !
    self.imglist.RemoveAll()	#die sterben nicht mit den Items !
    
    if MainMode=='M':		#META: NUR EIN KLEINER ROTER HINWEIS
      ##KEINE Progdaten, keine Berechnungen, kein Verhalten (das ist in Handlern)
      self.SetBackgroundColour(wx.RED)
      img = self.imglist.Add( wx.Bitmap(iconCheck("icons/meta.bmp")) )
      self.InsertImageStringItem(0, "META !", img)	#nur 1 Item einfuegen, nur 1 Spalte
      
      #in diesem Modus gibt es kein Selektevent, Grid einmalig von Hand anstossen
      if TheGrid: TheGrid.LoadSzene()
    
    else:			#PAINT: FUER JEDE SZENE EIN LISTENITEM HIER
      self.SetBackgroundColour(wx.WHITE)
      
      #Zielgroesse fuer BildResize auf etwa 16x16 (ratio,ganzzahliger...)
      faktor = min( map(lambda x: 16/x, MainProg.size) )
      if faktor>1: self.resize = map(lambda x: faktor * x, MainProg.size)
      else:        self.resize = None
      
      #Fuer jeden step im Programm ein Item in der Liste
      for i,szene in enumerate(MainProg.szenen):
        index = self.InsertSzene(sys.maxint, szene)
        assert i==index,"Verstoss gegen die Annahme Itemnummer==Programmschrittnummer"
      
      #erste Zeile komplett selekten
      self.SelectSzene(0,nosave=True)
      ##=>GEHT WEITER AN GRID.LoadSzene
  
  def SaveProgram(self):
    "GROSSES SAVE: meine Aenderungen und vor allem die vom Grid ins Programm"
    
    TheGrid.SaveSzene()		#vom Grid ins Programm/Szene
      				#achtet selber auf Aenderungen und setzt needsave
      				#achtet auch auf den Modus !
    
    if MainMode=='M':		#META: GRID genuegt.
      pass
    
    else:			#PAINT: GRID + Restdaten von mir sichern
      szene = self.CurrSzene()			#auch meine 2 Daten ins Programm
      self.MakeSzeneBitmap(self.currstep,szene)	#aus Szene in meine Liste
      
      name,dauer,trans = self.GetItemTexte()	#aber auf Aenderung achten
      if (name,dauer,trans) != (szene.name, szene.dauer, szene.trans):
        szene.name,szene.dauer,szene.trans = name,dauer,trans
        MainProg.needsave = True
  
  def MakeSzeneBitmap(self, index, szene=None):
    "fuer Listenelement index aus der Szene das aktuelle Bild holen"
    if not szene: szene = MainProg.szenen[index]
    
    wximage = szene.GetImage()
    if self.resize: wximage.Rescale(* self.resize )	#sauber skalieren 16x16
    wximage.Resize((16,16),(0,0), -1,-1,-1)
    bmp = wx.BitmapFromImage(wximage)
    
    imgidx = self.GetItem(index).m_image
    self.imglist.Replace(imgidx,bmp)
    ##UNIX: Replace gibt es nur unter Windows
    ##  sonst: imglist.Remove, imglist.Add, neue Nummer von Add nach self.SetItemImage
    ##         kann leicht alles hier passieren...
  
  def InsertSzene(self, pos, szene, makecurr=False):
    #erstmal nur Dummybild einfuegen
    imgidx = self.imglist.Add(wx.EmptyBitmap(16,16))
    
    index = self.InsertImageStringItem(pos, szene.name, imgidx)	#neues Item einfuegen 1.Spalte Name
    self.SetStringItem(index, 1, str(szene.dauer))		#2.Spalte Dauer nachtragen
    self.SetStringItem(index, 2, str(szene.trans))		#3.Spalte Transition nachtragen
    
    #den Rest macht die Bildroutine passend zur Szene
    self.MakeSzeneBitmap(index, szene)
    
    ##LATER: evtl Textfarbe
    ##  item = self.GetItem(index)
    ##  item.SetTextColour(wx.BLUE)
    ##  self.SetItem(item)
    
    #wenn makecurr, dann wird die neu angelegte Szene auch gleich die neue
    #  (ohne sichern der alten, das ist in GUI Ops schon passiert)
    if makecurr:
      self.SelectSzene(pos, nosave=True)
    
    return index
  
  def CurrSzene(self):
    "einfacher Zugang zur aktuellen Szene, von hier ins Programm"
    return MainProg.szenen[ self.currstep ]
  
  def SelectSzene(self,idx, nosave=False):
    "vollwertiges Selectevent simulieren: optisch + logisch"
    
    if nosave:			#Sonderfall nosave: in Eventroutine uebereifriges Speichern
      self.currstep = None	#  am Anfang und mitten in Ops verhindern
    
    self.selectevent = False	#Testrahmen ob das Event kam...
    self.Select(idx)		#optisch: die blaue Zeile
    
    if not self.selectevent:	#das Event kommt nicht immer, ich beobachte es...
      self.OnItemSelected(idx)	#logisch: mein Eventhandler
  
  def GetItemTexte(self):
    "alle [2] Werte zur aktuellen Zeile holen"
    
    name = self.GetItemText(self.currstep)
    try: dauer = int( self.GetItem(self.currstep,1).GetText() )
    except ValueError: dauer = 0
    try: trans = int( self.GetItem(self.currstep,2).GetText() )
    except ValueError: trans = 0
    
    return name,dauer,trans
  
  def SetItemTexte(self, name,dauer,trans):
    "alle [2] Werte zur aktuellen Zeile setzen"
    
    self.SetItemText(self.currstep, name)		#nicht setitem, das bild soll bleiben
    self.SetStringItem(self.currstep, 1, str(dauer))	#andere Methode wegen Spaltennummer
    self.SetStringItem(self.currstep, 2, str(trans))
  
  
  #-----------------------------------------------------------
  #EVENT-HANDLER
  
  ##TIP: Auskunft ueber item in events:
  ##  item = event.GetItem() - darin sind jede menge m_xxx Infos, siehe SetItem
  
  def OnItemSelected(self, event):
    "alte Szene SICHERN, neue Szene LADEN"
    
    if MainMode=='M': 			#META: Event verbieten
      if event: event.Skip()
      return
      ##LATER: die Demo hat Beispielcode um Selekt dieser Zeile zu verhindern...
    
    self.selectevent = True		#ja, das Event kam...
    
    #ALT SICHERN...
    if self.currstep is not None:	#Sonderfall nosave: anfangs & mitten in Step-Operationen
      self.SaveProgram()		#TheGrid.SaveSzene + Zusatzdaten
    
    #NEU LADEN...
      #Sonderfall Direktaufruf mit int beachten
    if type(event)==types.IntType:
      self.currstep = event
      event = None
    else:
      self.currstep = event.GetIndex()
    
      #Grid neu laden
    if TheGrid: TheGrid.LoadSzene()	##CLEAN: Ausnahme nur fuers 1.mal ist etwas unschoen
    if event: event.Skip()
  
  ##NICHT MEHR...
  ##def OnItemDeselected(self, event):
  ##  "bei Verlassen der alten Szene SICHERN"
  ##  pass
  
  
  #Begin Edit verbieten falls Meta
  def OnBeginEdit(self, event):
    "im Modus Meta editing verbiegen"
    
    if MainMode=='M': 			#META: Event GANZ verbieten !
      event.Veto()
  
  ##NO: das Label ist doch der Name, denn es sind ja 2 Zahlen
  ##def OnEndEdit(self, event):
  ##  "das Label sind die ms-Zahlen damit sie leicht zu editieren sind"
  ##  
  ##  if event.GetColumn()==0:	#nur fuer die 1.Spalte (die Zahl)
  ##    #die Zeile event.GetIndex() ist egal...
  ##    
  ##    try: int( event.GetText() )
  ##    except ValueError: event.Veto()
  ##    else: event.Skip()
  
  def OnItemActivated(self, event):
    "Doppelklick oder Enter fuehrt zu groesserem Editdialog"
    if MainMode=='M': 			#META: Event verbieten
      if event: event.Skip()
      return
    
    values = UseTableDialog(self,self.GetItemTexte(),
                                 [ "Name:", "Dauer 1/10sec:", "Trans 1/10sec:" ],
                                 [ str,     int0,             int0 ])
    
    if values: self.SetItemTexte( *values )
    event.Skip()
  
  def OnRightClick(self, event):
    "rechter Mausklick: gleiches Menue wie oben &Step"
    
    if MainMode=='M': 			#META: Event verbieten
      if event: event.Skip()
      return
    
    menu = wx.Menu()
    
    #5 Szene-Moves genau wie in &Step
    for i,move in enumerate(SZENEMOVES):
      ##TRICK: das Anhaengen von oldid=... ist umstaendlich aber nach *move Aufloesung
      ##  darf sonst nix mehr kommen
      move = move + [self.popupids[i]]
      
      #die oldid ist so beim ersten Mal None und spaeter bekannt, Bindungen bleiben
      self.popupids[i] = MyToolAdd(self,menu, *move)
    
    #ich habe im Event kein Maus-xy, aber das ist sogar besser
    itemrect = self.GetItemRect(self.currstep)
    self.PopupMenu(menu, (itemrect.GetLeft(), itemrect.GetBottom()))
    menu.Destroy()
    event.Skip()
  
  ##LATER Veto des Spaltenresize ueberlegen
  ##def OnColBeginDrag(self, event):
  ##  event.Veto()
  
  
  #-------------------------------------------------
  #Arbeit mit der SZENENFOLGE
  #  basiert auf gleichnamigen Methoden oben beim Programm,
  #  diese aendern die Datenstruktur, ich ziehe die Folgen hier
  
  def SzeneNew(self,_event):
    "Neue, leere Szene einfuegen"
    if MainMode=='M': return		#META: Liste hat nur 1 Dummy-Item, ignorieren
    
    self.SaveProgram()			#TheGrid.SaveSzene + Zusatzdaten
    szene = MainProg.SzeneNew(self.currstep)
    
    #dahinter einfuegen & dahin wechseln
    self.InsertSzene(self.currstep+1, szene, makecurr=True)
  
  def SzeneDupl(self,_event):
    "statt Kopie mit Zielort einfach Duplicate an Ort und Stelle"
    if MainMode=='M': return		#META: Liste hat nur 1 Dummy-Item, ignorieren
    
    self.SaveProgram()			#TheGrid.SaveSzene + Zusatzdaten
    szene = MainProg.SzeneDupl(self.currstep)
    
    #dahinter einfuegen & dahin wechseln
    self.InsertSzene(self.currstep+1, szene, makecurr=True)
  
  def SzeneMove(self, diff):
    "statt Move mit Zielort nur Einzelschritte +/- 1"
    if MainMode=='M': return		#META: Liste hat nur 1 Dummy-Item, ignorieren
    
    self.SaveProgram()			#TheGrid.SaveSzene + Zusatzdaten
    szene = MainProg.SzeneMove(self.currstep, diff)
    
    if szene:
      self.DeleteItem(self.currstep)
      #verschoben wieder einfuegen & dahin wechseln
      self.InsertSzene(self.currstep + diff, szene, makecurr=True)

  def SzeneMoveUp(self,_event): self.SzeneMove(-1)
  def SzeneMoveDn(self,_event): self.SzeneMove(+1)
  
  def SzeneDel(self,_event):
    "Szene loeschen, ausser der letzten"
    if MainMode=='M': return		#META: Liste hat nur 1 Dummy-Item, ignorieren
    
    self.SaveProgram()			#TheGrid.SaveSzene + Zusatzdaten
    
    if MainProg.SzeneDel(self.currstep):
      self.DeleteItem(self.currstep)
      
      #aktuelle Szene wird das danach, nur ganz hinten rueckt es 1 rein
      newidx = ifop( self.currstep >= self.GetItemCount(), self.currstep-1, self.currstep )
      self.SelectSzene( newidx, nosave=True )
  
  
  #-------------------------------------------------
  #Export und Play des Gesamtprogramms
    ##DOKU: Einzelkacheln und ganze Szenen ans CONN-Objekt siehe Grid
  
  ledpwildcard=	"LED Programs (*.ledp)|*.ledp|" \
  		"All files (*.*)|*.*"
  ledxwildcard=	"LED eXecutables (*.ledx)|*.ledx"
  
  def ProgExPlay(self, event, play=True):
    "Export [und evtl Play] LEDX: nur Filedialog und Aufruf von PlayerConn"
    
    #erstmal aus der GUI zurueck ins Programm, alles aktuell
    self.SaveProgram()
    
    #LEDX Name: fuer play nur temporaer
    if play:
      ledxname = ini.get("KachelEditor","TempLedxName")
    
    #der reine Export ist parallel zum LEDP
    else:
      ledxname = MainProg.filename
      if not ledxname: return		#Save war vorher, das sollte gesetzt sein
      
      if ledxname.lower().endswith(".ledp"): ledxname = ledxname[:-5]
      ledxname += ".ledx"
    
      #Gesamtprogramm in die Form fuer Conn-Objekt bringen
    progex = MainProg.GetExport()
      #alles ans Conn-Objekt geben
    try:
      PlayerConn.SendProgramm(progex,ledxname, play=play, loop=True)
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
  
  def ProgTest(self, event):
    "Special export for test playing"
    
    #erstmal aus der GUI zurueck ins Programm, alles aktuell
    self.SaveProgram()
    
    #Dialog fuer Sondereinstellungen beim Test-Play
    values = UseTableDialog(self,[ "False",		"10" ],
                                 [ "Loop:",		"Steplimit 1/10sec:" ],
                                 [ ["False","True"],	int0 ])
    if not values: return
    
      #Gesamtprogramm in die Form fuer Conn-Objekt bringen
    progex = MainProg.GetExport()
    
      #Werte aus dem Dialog beruecksichtigen
    try:    loop = eval(values[0])
    except: loop = False
    
      #NEU: "Play from Here"
    progex['szenen'] = progex['szenen'][self.currstep:]
    
    steplimit = values[1]
    if steplimit:		#0 oder leer "" (wird zu 0) heisst kein limit
      for szene in progex['szenen']:
        szene['dauer'] = min(szene['dauer'], steplimit)
        szene['trans'] = min(szene['trans'], steplimit)
    
      #alles ans Conn-Objekt geben
    try:
      PlayerConn.SendProgramm(progex,ini.get("KachelEditor","TempLedxName"), play=True, loop=loop)
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
    
    ##LATER: steplimit weiter ausbauen: "so schnell wie moeglich"
    ##  das muss der Player wieder als Zusatzflag erhalten, er schiebt so schnell er kann ?
    
    ##LATER: genauer als "from here" ?
    ##  aber nicht einfach Multiline in der Liste (disjunkt ? events ?)
    ##  sondern SetBegin,SetEnd -> gelbe Hintergrundfarbe


#----------------------------------------------------------------------
#THE GRID !!!

class LedGrid (wx.grid.Grid):
  "die grosse Zeichenflaeche ist ein wx.Grid, da die 'Pixel' riesig sind"
  
  #member firstselect	TUPLE: Zellenposition, wo ich mit selekten angefangen habe
  #member sendbatch	None (direkt senden) oder Dict wo Batch-Send gesammelt wird
  #member undolast	Daten fuer Undo von 1 Step: * None wenn kein Undo
  #			* 2D WERTELISTE fuer vollen Grid
  #			* TUPLE (row,col,value) fuer eine Zelle
  			##LATER: Liste von solchen Teilen fuer mehrfaches Undo
  			##LATER: mit staendigem Update vom Grid in die direkt verbundene Szene
  			##  koennte man deep kopierte Szene aufheben statt den Grid zu lesen
  #member undoedit	kleiner Zusatz um alten Wert vor dem Edit zu merken, OnCellChange ist es zu spaet
  #member clicktime	Zeitpunkt des letzten linken Mausklicks,
  #			falls Start des Editing ueber Maus laut INI verboten ist
  
  def __init__(self, parent,id):
    #===== Basis die so eingestellt bleibt =====
      #Grid erzeugen
    wx.grid.Grid.__init__(self, parent,id)
    self.sendbatch = None
    self.undoedit  = None
    self.clicktime = 0
    
      #verhindert nur resize-Cursor "mittendrin"; Resize-Events per Header siehe Quadratisch unten
    self.DisableDragGridSize()
      #Font monospaced
    self.SetDefaultCellFont(wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL))
      #alles mittig
    self.SetDefaultCellAlignment(wx.ALIGN_CENTRE,wx.ALIGN_CENTRE)
    
    #===== GRID-EVENTS =====
      #Doppelklick oeffnet Farbdialog, Rechtsklick fuer Austausch mit HexColourButton
    self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnColorPicker)
    self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
    
      #einfacher Klick fuer clicktime Stempel wegen Edit ueber Maus
    self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
    
      #Quadratisches resize
    self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.OnRowSize)
    self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColSize)
    
      #erstes Element eines eventuellen Blocks fuer Zeichenops merken
    self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
    ##NOT beobachten, ich kann anfragen
    ##self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
    
      #Farbe dem hex anpassen
    self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnCellChange)
      #fuer Undo muss ich den Anfangswert wissen, in CellChange ist schon der neue
    self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,self.OnEditorShown)
    
    ##OPTIONAL: Veto kann editieren live verbieten oder falschem Wert fallenlassen
    ##self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,  self.OnEditorShown)
    ##self.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnEditorHidden)
    
    #-------------------------------------------------
    #am Ende des Konstruktors aktuelles Programm laden
    
    self.CreateGrid( MainProg.size[1], MainProg.size[0] )	#das geht nur beim 1.Mal !
    self.NewSize()		#volle Aenderung, inklusive Size...
    self.LoadSzene()  		#macht noch einige Resets die nicht ins init muessen...
  
  def NewSize(self):
    "grundlegendes Layout, wenn sich Meta-Programm aendert"
    ##ACHTUNG: so muss der Grid von neuer Size erfahren, 
    ##  das kann er nicht aus Zusammenspiel mit Liste oder Modus erraten
    
      #CreateGrid geht leider kein 2.Mal, ich muss zu Fuss ran
    progcols,progrows = MainProg.size
    gridcols,gridrows = self.GetNumberCols(),self.GetNumberRows()
    
    if   gridcols>progcols: self.DeleteCols(progcols, gridcols-progcols)
    elif gridcols<progcols: self.AppendCols(progcols-gridcols)
    if   gridrows>progrows: self.DeleteRows(progrows, gridrows-progrows)
    elif gridrows<progrows: self.AppendRows(progrows-gridrows)
    
      #die Groesse in der GUI wird mit gespeichert
    self.Quadratisch( MainProg.GetProperty("QuadratSize",50) )
      #auch Spalten nicht a,b,c sondern 1,2,3
    for i in range( MainProg.size[0] ): self.SetColLabelValue(i, str(i+1))
  
  
  #-------------------------------------------------
  #meine Wrapper um die Send-Operationen in der Connection,
  #plus Optimierung und Ausweichen auf ganze Szene
    ##DOKU: ganzes Programm ans CONN-Objekt siehe Liste
  
  def SendKachel(self, kachel,rgb):
    "Einzelne Kachel, Opti und Ausweichen zwischenschalten"
    
    if self.sendbatch is None:
      try:
        return PlayerConn.SendKachel(kachel,rgb)	#normalerweise Einzelkachel, eventuell return False
      except LedDataException,ex:
        LogMessageDialog(MSG_ERROR, str(ex))
        return False
    
    else:
      self.sendbatch[kachel] = rgb			#batch in dict sammeln, keine Duplikate
      return True
    
    ##KUNDE: falls gar keine Optimierung gewuenscht, dann hier if-frage und else-zweig auskommentieren
  
  def SendBatch(self):
    "Gesammelte Batch auf einmal an SendSzene geben"
    
    try:
      #die im dict gesammelten items (kachel,rgb) einfach auf einmal runter
      if self.sendbatch:
        try:
          PlayerConn.SendSzene(self.sendbatch.items())
        except LedDataException,ex:
          LogMessageDialog(MSG_ERROR, str(ex))
    finally:
      self.sendbatch = None
  
  #-------------------------------------------------
  #schlaues Setzen einer Zelle
  
  def GetCellHEX(self, row,col):
    #kein meta-test: der Zahlen-String in der Zelle faengt nie mit ( an, hexonly laesst ihn also
    return hexonly( self.GetCellValue(row,col) )
  def GetCellRGB(self, row,col):
    return hex2rgb( self.GetCellValue(row,col) )
  
  def SetLEDCell(self, row,col, value=None, inkette=False):
    "Hex-Farbwert einstellen [falls genannt] und entsprechend faerben"
    
    #0.fuer reines Update erstmal den hexstring holen (weiss falls da auch nix)
    if not value: value = self.GetCellValue(row,col)
    fullupdate = False
    
    if MainMode=='M':		#META:  garantiert int -1 oder 1..127
      #1.Wert anpassen, simpel und ohne Fehlermeldungen
      value = KachelCheck( value )
      
      #2.den eigentlichen Wert setzen
      self.SetCellValue(row,col, str(value))
      self.SetReadOnly(row,col, False)		#es sind alle editierbar, auch die in Paint tot waren
      
      if value == -1:				#tote Zellen -1 wieder in Schwarz
        self.SetCellBackgroundColour(row,col, wx.BLACK)
        self.SetCellTextColour(row,col, wx.WHITE)
      
      else:					#echte Kacheln 1..127 in Falschfarben :-)
        rgb = autopastell(value)		#Pastellformel von oben...
        farbe = wx.Colour(*rgb)
        
        self.SetCellBackgroundColour(row,col, farbe)
        self.SetCellTextColour(row,col,wx.BLACK)#Text immer schwarz, die Falschfarben sind pastell
        if not self.SendKachel(value, rgb):	#Pastellton auch an den echten Grid !
          fullupdate = True			#Player lief, volles Update
    
    else:			#PAINT: garantiert 6 Hex-Ziffern und eventuell () passend zu meinem meta
      #1.Wert anpassen, simpel und ohne Fehlermeldungen
      meta  = MainProg.meta[row][col]
      value = HexColorString( value, meta )
      
      #2.den eigentlichen Wert setzen und korrekt als rgb + farbe vorbereiten
      self.SetCellValue(row,col, value)
      rgb = hex2rgb( value )
      farbe = wx.Colour( *rgb )
      
      if value[0] == '(':			#gesperrte Zellen mit virtueller Farbe
        self.SetCellBackgroundColour(row,col, wx.BLACK)
        self.SetCellTextColour(row,col, farbe)	#die virtuelle Farbe wird im Text dargestellt
        self.SetReadOnly(row,col, True)		#ABER: direktes Editieren fuer virtuelle Farben verwirrend
      
      else:
        self.SetCellBackgroundColour(row,col, farbe)
        
        if ini.getboolean("KachelEditor","ShowHexNumbers"):
          #normalerweise gut sichtbare Farbe
          ##ALT invers war zu bunt: farbe = wx.Colour(* map(lambda c: (256-c), rgb) )
          farbe = ifop( sum(rgb)<384, wx.WHITE, wx.BLACK )
          self.SetCellTextColour(row,col, farbe)
        else:
          #wenn value nicht angezeigt wird, ist es einfach in der gleichen Farbe + readonly
          self.SetCellTextColour(row,col, farbe)
          self.SetReadOnly(row,col, True)	#was ich nicht sehen kann, kann ich so nicht editieren
        
        if not inkette:
          if not self.SendKachel(meta,rgb):	#FARBE AN DEN ECHTEN GRID !
            fullupdate = True			#Player lief, volles Update
      
      #AUSSERDEM: wenn ich Teil einer Kette bin, dann die anderen mitziehen
      if not inkette and not fullupdate:	#nicht noetig, wenn full folgt oder ich schon als Kette gerufen
        kette = MainProg.GetKette(row,col)
        for r,c in kette:
          self.SetLEDCell(r,c, value, inkette=True)
    
    if fullupdate:				#Player lief, volles Update
      ##TRICK: einfach aktuelle Szene aktualisieren, das gibt sie auch an den Player
      ##  allerdings muss ich Undo retten, weil es trotz LoadSzene bleiben soll
      undosave = self.undolast			#was immer es vor dem Trick war
      self.LoadSzene() 				#wenn Wall nach Stop ungueltig, dann ganze Szene
      self.undolast = undosave			#was immer es vor dem Trick war
      
      ##  danach muss ich allerdings dieses Pixel nochmal setzen
      self.SetLEDCell(row,col, value, inkette)
    
    ##NICHT MEHR: nicht einfach Text-Hintergrund setzen,
    ##  sondern eigenen Renderer schreiben ?
  
  #-------------------------------------------------
  #Austausch: GRID <--> LEDPROGRAMM.aktuelle Szene
  #           die gemeinsame Sprache hierfuer ist die 2D Liste von Farbstrings
  
  ##NICHT MEHR: vielleicht statt Strings eigene Werte-Typen ? 
  ##  dafuer die LedSzene von wxGridTableBase ableiten
  ##  die Werte waeren None und Zahlen als Hex
  
  ##DOKU: KLEINES UPDATE & SAVE werden aus der linken Liste
  ##      beim GROSSEN UPDATE & SAVE gerufen !
  
  def SetAllCells(self,farben2d):
    "Basis fuer UPDATE: alle Werte ans Grid geben, inklusive opti. Player Update..."
    
    try:
      self.sendbatch = {}
      
      ##DOKU: hier geht's nach farben2d und nicht nach MainProg.size,
      ##      geht theoretisch auch mit kleineren Feldern
      for row,farbline in enumerate(farben2d):	#0..height + farbline gleich fertig
        for col,farbe in enumerate(farbline):	#0..width  + farbstring gleich fertig
          self.SetLEDCell(row,col, farbe)
    
    finally:
      self.SendBatch()
  
  def GetAllCells(self):
    "Basis fuer SAVE: alle Werte aus dem Grid holen"
    
    ##DOKU: hier geht's nach Grid-size und nicht nach MainProg.size,
    ##      geht theoretisch auch mit groesserem Grid
    farben2d = []
    for row in range( self.GetNumberRows() ):	#0..height
      farbline = []
      farben2d.append( farbline )
      
      for col in range( self.GetNumberCols() ):	#0..width
        value = self.GetCellValue(row,col)
        farbline.append( value )
    return farben2d
  
  def LoadSzene(self):
    "KLEINES UPDATE: die 2D Liste von Farbstrings aus aktueller Szene auf meine Zellen verteilen"
    
    ##SUPER: nur die Quelle der 2D Liste unterscheidet sich fuer die Modi
    
    if MainMode=='M':		#META:  META IST FERTIGES 2D (von Kachelnummern)
      farben2d = MainProg.meta
    else:			#PAINT: AUS DER AKTUELLEN SZENE HOLEN
      farben2d = SzeneList.CurrSzene().GetFarben()
    
    self.SetAllCells(farben2d)	#ALLE ZELLEN SETZEN, inklusive Player
    
    self.firstselect = (0,0)	#volles Update, also aktuelle Zelle links oben
    self.ClearSelection()	#  keine Selektion
    self.undolast = None	#  und kein "im-Grid-Undo" mehr
  
  def SaveSzene(self):
    "KLEINES SAVE: die 2D Liste von Farbstrings aus meinen Zellen holen fuer die aktuelle Szene"
    
    farben2d=self.GetAllCells()	#ALLE ZELLWERTE AUS DEM GRID HOLEN
    
    if MainMode=='M':		#META:  META-SET MIT NEBENWIRKUNGEN !
      MainProg.SetMeta( farben2d, makefirst=True )
    else:			#PAINT: AN AKTUELLE SZENE GEBEN
      SzeneList.CurrSzene().SetFarben(farben2d)
  
  def Undo(self, event):
    "UNDO existiert z.Zt. nur low level im Grid"
    if not self.undolast: return
    
    if   type(self.undolast)==types.TupleType:	#EINZELSCHRITT
      row,col,value = self.undolast
      redo = (row,col, self.GetCellValue(row,col))
      self.SetLEDCell(row,col, value)
    
    elif type(self.undolast)==types.ListType:	#FULL GRID
      redo = self.GetAllCells()
      self.SetAllCells(self.undolast)
    
    self.undolast = redo	#es gibt nur 1 Schritt Undo, also ist Undo of Undo wie Redo
  
  
  #-------------------------------------------------
  #EVENTS...
  
  def EventCelldata(self, event):
    row = event.GetRow()
    col = event.GetCol()
    hex = self.GetCellValue(row,col)
    
    return (row, col, hexonly(hex), hex[0]=='(')
  
  def OnColorPicker(self, event):
    "Farbdialog fuer die aktuelle Zelle bei Doppelklick oder Hotkey"
    
    if MainMode=='M': 			#META: Event verbieten
      if event: event.Skip()
      return
      ##LATER vielleicht Liste aller freien/belegten Nummern aufpoppen ?
    
    #nur fuer eine Zelle !
    self.ClearSelection()
    
    #die aktuelle Zelle: Doppelklick ist ein Grid-Event, die Zelldaten sind einfach
    if isinstance(event, wx.grid.GridEvent):
      row,col,hex,bad = self.EventCelldata(event)
    
    #                    fuer Hotkey/Menu muss ich aktuelle selber suchen
    else:
      #SICHERHEITSHALBER: bad, falls mehr als die eine Zelle selected oder gar keine (?)
      #  :-) das trat nie ein, weil der Hotkey es automatisch auf 1 Zelle reduziert
      bad = self.GetSelectedCells() or self.GetSelectionBlockTopLeft() or not self.firstselect
      
      if not bad:
        row,col = self.firstselect
        hex = self.GetCellValue(row,col)	#2.Teil von EventCelldata kopiert...
        hex,bad = hexonly(hex), hex[0]=='('
    
    if bad:
      event.Skip()	#BLEIBT: direktes Editieren fuer virtuelle Farben verwirrend
      return
    
    #nicht self (Grid) als Parent sondern weiter oben
    dlg = wx.ColourDialog(wx.GetTopLevelParent(self))
    
    data = dlg.GetColourData()
    data.SetChooseFull(True)		#voller Dialog, wie bei HexColourButton implizit auch
    data.SetColour(hex2col( hex ))	#Init mit Farbe aus der Zelle
    
    if dlg.ShowModal() == wx.ID_OK:	#OK gedrueckt, neue Farbe in die Zelle
      self.undolast = (row,col,hex)	#1 step undo !
      self.SetLEDCell(row,col, col2hex( data.GetColour() ))
    
    dlg.Destroy()
    event.Skip()
  
  def OnCellRightClick(self, event):
    "Rechter Klick fuer Austausch <- => mit Farbbutton rechts"
    ##RECYCLING: META VOELLIG GLEICH :-)
    
    #nur fuer eine Zelle !
    self.ClearSelection()
    
    #die aktuelle Zelle
    row,col,hex,bad = self.EventCelldata(event)
    #bad ist egal, virtuelle Farbe
    
    if event.ControlDown():		#mit Ctrl: "PICK" in den Button rueber
      ColourButton.SetHex( hex )
    else:				#ohne: "FILL" die Zelle faerben
      self.undolast = (row,col,hex)	#1 step undo !
      self.SetLEDCell(row,col, ColourButton.GetHex())
    
    event.Skip()
  
  def OnCellLeftClick(self, evt):
    self.clicktime = time.time()
    evt.Skip()
  
  #-------------------------------------------------
  #RESIZE: immer fuer alle gemeinsam
  
  def Quadratisch(self,size):
    "mache komplett quadratisches Layout Zeilen,Spalten und auch Titelfelder"
    try:
      MainProg.SetProperty("QuadratSize",size)
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
    
    self.SetDefaultColSize(size, True)
    self.SetDefaultRowSize(size, True)
    self.SetRowLabelSize(size)
    self.SetColLabelSize(size)
    
    #Minsize, damit Layout klappt
    #n Zeilen dieser Breite + Kopfzeile + Reserve falls Editor eingeblendet wird
    self.SetMinSize(( size*(self.GetNumberCols()+1)+20, size*(self.GetNumberRows()+1)+20 ))
    ##LATER: Size-Handling eingreifen, so dass er Scrollbars die gar nicht da sind
    ##  fuer das Erscheinen der Scrollbars nicht immer mit einrechnet
  
  def OnRowSize(self, event):
    self.Quadratisch( self.GetRowSize( event.GetRowOrCol() ) )
    event.Skip()
  def OnColSize(self, event):
    self.Quadratisch( self.GetColSize( event.GetRowOrCol() ) )
    event.Skip()
  
  #Selektion fuer Zeichenops...
  def OnSelectCell(self, event):
    "erstes Element eines eventuellen Blocks fuer Zeichenops merken"
    self.firstselect = (event.GetRow(), event.GetCol())
    event.Skip()
  
  ##NOT beobachten, ich kann anfragen
  ##def OnRangeSelect(self, event):
  ##  if event.Selecting():
  ##    print("OnRangeSelect: top-left %s, bottom-right %s" % (event.GetTopLeftCoords(), event.GetBottomRightCoords()))
  ##  event.Skip()
  
  def OnCellChange(self, event):
    "nach jedem Edit: Wert nicht kaputtmachen, nur Farbe updaten"
    ##RECYCLING: META VOELLIG GLEICH :-)
    
    row,col,_,_ = self.EventCelldata(event)	#der Wert ist hier schon der neue :-(
    
    if self.undoedit:			#ohne das geht hier kein Undo
      rowx,colx,hex = self.undoedit	#da ist der alte Wert
      if rowx==row and colx==col:
        self.undolast = (row,col,hex)	#1 step undo !
    
    self.SetLEDCell(row,col)
  
  def OnEditorShown(self, event):
    "NEU fuer Undo: gerade editierten Wert aufheben, OnCellChange kriegt new :-|"
    
    #Mausedit verboten ? natuerlich nur Paint ! Editor per Maus gestartet ?
    if ini.getboolean("KachelEditor","BlockMouseEdit") and MainMode=='P' and (time.time()-self.clicktime)<0.5:
      ##print "OnEditorShown VETO!!! time=%f" % (time.time()-self.clicktime)
      event.Veto()
      return
    ##else:
    ##  print "OnEditorShown time=%f" % (time.time()-self.clicktime)
    
    row,col,hex,_ = self.EventCelldata(event)
    self.undoedit = (row,col,hex)
  
  ##OPTIONAL: Veto kann editieren vorher/nachher live verbieten
  ##def OnEditorShown(self, event):
  ##  #event.Veto() + return um es gezielt zu verbieten
  ##  print("OnEditorShown: (%d,%d) %s" % (event.GetRow(), event.GetCol(), event.GetPosition()))
  ##  event.Skip()
  ##def OnEditorHidden(self, event):
  ##  #event.Veto() + return um es zu verbieten
  ##  print("OnEditorHidden: (%d,%d) %s" % (event.GetRow(), event.GetCol(), event.GetPosition()))
  ##  event.Skip()
  
  #-------------------------------------------------
  #ZEICHENOPS: von self.firstselect den ganzen Block fuellen
  ##RECYCLING: META MEIST VOELLIG GLEICH :-)
  ##  ! ausser Gradient, was nur als Trick zum Fuellen mit verschiedenen
  ##    Zahlen recycled wird...
  
  def FillCheck(self):
    "Box Selektion -> sortierte Zeilen & Spaltenlisten fuer Fill-Operationen; leer wenn ungeeignet"
    
    if not self.firstselect: return [],[]		#der Anfangspunkt (Pivot-Zelle) fehlt
    row,col = self.firstselect
    
    ##LATER: fuer weitere Op-Typen relevant
    ##DOKU: in wxPython 2.6.1.0 fur PY 2.4 
    ##  waren mehrere linke obere/rechte untere Ecken fuer disjunkte (Ctrl-Drag) Bereiche moeglich
    ##  aber Einzelzellen waren nur in GetSelectedCells und nicht hier
    ##  =>das ist egal, ich verlange eh' reine Box
    if self.GetSelectedCells(): return [],[]		#es gibt zusaetzliche Einzelzellen
    
    topleft = self.GetSelectionBlockTopLeft()
    botrite = self.GetSelectionBlockBottomRight()
    if len(topleft)!=1 or len(botrite)!=1: return [],[]	#mehr als ein richtiger Block
    
    row0,col0 = topleft[0] 
    row1,col1 = botrite[0]
    if row not in [row0,row1] or \
       col not in [col0,col1]: return [],[]		#firstselect ist keine der 4 Ecken
    
    #DIE BOX PASST => fertig sortierte Zeilen und Spaltennummern returnen
    rows = range(row0,row1+1)		#Zeilenliste
    if row==row1: rows.reverse()	#firstselect war unten, also umgekehrt
    
    cols = range(col0,col1+1)		#Spaltenliste
    if col==col1: cols.reverse()	#firstselect war rechts, also umgekehrt
    
    return rows,cols
  
  def FillCheckMsg(self):
    "kleiner Wrapper um FillCheck, gleich mit Fehlermeldung"
    rows,cols = self.FillCheck()
    if rows:		#Full Grid Undo merken wenn es passt :-)
      ##EINSCHRAENKUNG: normalerweise ist hier klar, ob die Op stattfinden wird,
      ##  Gradient-Ops haben aber noch eine kleine zusaetzliche Einschraenkung;
      ##  die wird hier ignoriert, wenn eine Op passieren sollte, ist klar, dass Undo ueberschrieben ist
      self.undolast = self.GetAllCells()
    else:		#oder Fehlermeldung falls nicht
      LogMessageDialog(MSG_ERROR, "Fuell-Operationen brauchen genau eine einzelne Box-Selektion")
    return rows,cols

  ##DOKU: FARBEN fuer die Ops nicht erfragen (doof) und nicht aus HexButton (vorher machen)
  ##  sondern direkt aus den Tabellenzellen
  ##  ! dazu wird die erste Zelle (PIVOT-Zelle) einer Blockselektion vermerkt
  
  ##ACHTUNG: die 6 Buttons/Menuepunkte bleiben immer aktiv,
  ##  ich muss am Anfang der jeweiligen Operation pruefen
  
  #========== FILL: Farbe aus Anfangszelle[n] durch ganze Flaeche ziehen ==========
  def FillHori (self,event):
    "Horizontal fuellen nach links oder rechts, zeilenweise unabhaengig"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#aeussere Schleife ueber Zeilen
        hex = ""				#erstmal suchen
        for c in cols:
          if not hex: hex=self.GetCellHEX(r,c)	#solange ich noch suche, merke ich mir nur die Farben
          else:       self.SetLEDCell(r,c,hex)	#wenn ich eine Farbe habe, fuelle ich die von jetzt an
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def FillVerti(self,event):
    "Vertikal fuellen --> wie FillHori transponiert"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for c in cols:			#--> wie FillHori transponiert
        hex = ""
        for r in rows:
          if not hex: hex = self.GetCellHEX(r,c)
          else:       self.SetLEDCell(r,c,hex)
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def FillDiag (self,event):
    "Ganze Box fuellen, alle aus erster Zelle"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      hex = ""				#--> wie FillHori "GEOEFFNET"
      for r in rows:			#    Suche nach 1.Farbe und dann Weitertragen fuer alle
        for c in cols:
          if not hex: hex = self.GetCellHEX(r,c)
          else:       self.SetLEDCell(r,c,hex)
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  #========== GRADIENT: Farbuebergang zwischen aus Anfangszelle[n] und Endzelle[n] ==========
  def GradHori (self,event):
    "Horizontaler Gradient von links nach rechts, zeilenweise unabhaengig"
    ##HINT: wenn ich zeilenweise mal nicht will, muss ich vorher vertikal fuellen...
    
    if MainMode=='M':			#META: nicht GradXxxx sondern NumberXxxx
      self.NumberHori(event)
      return
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    if len(cols)<=2: return		#nicht nur len=0, 1 oder 2 geht auch kein Gradient
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#aeussere Schleife ueber Zeilen
        c0 = cols[ 0] ; rgb0 = self.GetCellRGB(r,c0)	#erste und letzte Nummer
        c1 = cols[-1] ; rgb1 = self.GetCellRGB(r,c1)	#und Farbe dort
        
        for c in cols[1:-1]:		#nur die inneren Zellen mit Mischfarbe fuellen
          #direkt die RGB Mischfarbe einfuellen
          self.SetLEDCell(r,c, RgbMix(rgb0,rgb1,c-c0,c1-c0) )
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def GradVerti(self,event):
    "Vertikaler Gradient --> wie GradHori transponiert"
    ##HINT: wenn ich zeilenweise mal nicht will, muss ich vorher vertikal fuellen...
    
    if MainMode=='M':			#META: nicht GradXxxx sondern NumberXxxx
      self.NumberVerti(event)
      return
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not cols: return			#--> wie GradHori transponiert
    if len(rows)<=2: return
    
    try:
      self.sendbatch = {}
      
      for c in cols:
        r0 = rows[ 0] ; rgb0 = self.GetCellRGB(r0,c)
        r1 = rows[-1] ; rgb1 = self.GetCellRGB(r1,c)
        
        for r in rows[1:-1]:
          self.SetLEDCell(r,c, RgbMix(rgb0,rgb1,r-r0,r1-r0) )
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def GradDiag (self,event):
    "Schraeger Gradient 45 Grad, ganze Flaeche"
    ##DOKU: 45 Grad ist nicht nur einfacher als Koordinatentransformation
    ##  in beliebigem Winkel, das ist Absicht
    ##  sonst waere schon fuer eine Box von 6*7 praktisch jede Farbe anders
    
    if MainMode=='M':			#META: nicht GradXxxx sondern NumberXxxx
      self.NumberDiag(event)
      return
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    if (len(rows)*len(cols))<=2: return	#die meisten kleinen Boxen machen Sinn, nur 2 Zellen nicht
    
    #wirklich die allererste und allerletzte Zelle, virtuelle Farben helfen
    rgb0 = self.GetCellRGB(rows[ 0],cols[ 0])
    rgb1 = self.GetCellRGB(rows[-1],cols[-1])
    
    ##DOKU: fuer die 45 Grad Diagonalen genuegt die Summe der Koordinaten r+c
    ##      allerdings eventuell gekippt, also r-c
    kipp = (rows[0]<=rows[-1]) != (cols[0]<=cols[-1])	#verschiedene Sortierung, gekippt !
    if kipp:
      diag0 = rows[ 0]-cols[ 0]
      diag1 = rows[-1]-cols[-1]
    else:
      diag0 = rows[ 0]+cols[ 0]
      diag1 = rows[-1]+cols[-1]
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#Schleife ueber beide Achsen
        for c in cols:			#(alle Zellen, auch die 2 aeusseren)
          diag = ifop( kipp, (r-c), (r+c) )
          self.SetLEDCell(r,c, RgbMix(rgb0,rgb1, diag-diag0,diag1-diag0) )
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  #========== MOVE: Farben eine Zelle weit bewegen, von aussen kommt Masterfarbe rein ==========
  def MoveHori (self,event):
    "Horizontal bewegen nach links oder rechts, Masterfarbe von aussen"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#aeussere Schleife ueber Zeilen
        hex = ColourButton.GetHex()	#von aussen kommt Masterfarbe
        
        for c in cols:
          tmp = self.GetCellHEX(r,c)	#auslesen, das kommt in die naechste Zelle
          self.SetLEDCell(r,c,hex)	#neuen Wert druebersetzen
          hex = tmp			#fuer die naechste Zelle
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def MoveVerti(self,event):
    "Vertikal bewegen --> wie MoveHori transponiert"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for c in cols:			#--> wie MoveHori transponiert
        hex = ColourButton.GetHex()
        
        for r in rows:
          tmp = self.GetCellHEX(r,c)
          self.SetLEDCell(r,c,hex)
          hex = tmp
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def MoveDiag (self,event):
    "Schraeg uebers Eck bewegen - besondere Quellkoordinaten"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    #von links und oben kommt die Masterfarbe
    master = ColourButton.GetHex()
    #1 hex-Wert weitertragen reicht nicht, ich brauche ganze Liste fuer diese Zeile
    hexlist = [master] * len(cols)
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#aeussere Schleife ueber Zeilen
        hexlist = [master] + hexlist[:-1]	#von links master rein
        
        for i,c in enumerate(cols):
          tmp = self.GetCellHEX(r,c)	#auslesen, das kommt in die Liste
          self.SetLEDCell(r,c,hexlist[i])	#neuen Wert druebersetzen
          hexlist[i] = tmp		#fuer die Zelle +1,+1
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  #========== NUMBER: mit Folge von Kachelnummern fuellen (statt Gradient fuer Meta) ==========
  ##ACHTUNG: kein Test auf Duplikate ausserhalb; ich beachte schon den Anfangswert,
  ##         Duplikate ausserhalb koennen ja Absicht sein
  
  def NumberHori (self,event):
    "Horizontal numerieren nach links oder rechts, zeilenweise unabhaengig"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for r in rows:			#aeussere Schleife ueber Zeilen
        kachel = 0			#erstmal suchen
        for c in cols:
          if not kachel: kachel = KachelCheck( self.GetCellValue(r,c) )	#Anfangswert
          else:          self.SetLEDCell(r,c,kachel)	#wenn ich eine Farbe habe, fuelle ich die von jetzt an
          kachel += 1
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def NumberVerti(self,event):
    "Vertikal numerieren --> wie NumberHori transponiert"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      for c in cols:			#--> wie NumberHori transponiert
        kachel = 0
        for r in rows:
          if not kachel: kachel = KachelCheck( self.GetCellValue(r,c) )	#Anfangswert
          else:          self.SetLEDCell(r,c,kachel)
          kachel += 1
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  def NumberDiag (self,event):
    "Ganze Box numerieren, alle von erster Zelle an"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    try:
      self.sendbatch = {}
      
      kachel = 0				#--> wie NumberHori "GEOEFFNET"
      for r in rows:			#    Suche nach 1.Farbe und dann Weitertragen fuer alle
        for c in cols:
          if not kachel: kachel = KachelCheck( self.GetCellValue(r,c) )	#Anfangswert
          else:          self.SetLEDCell(r,c,kachel)
          kachel += 1
    
    finally:
      self.SendBatch()
      if ini.getboolean("KachelEditor","FillKillSelection"): self.ClearSelection()
  
  ##CLEAN,LATER: diese Funktionen sind sehr regelmaessig,
  ##  eine Vereinheitlichung wuerde aber intensive Nutzung von lambda-Funktionen bedeuten...


#----------------------------------------------------------------------
#FARBBUTTONS fuer den rechten Rand

##CLEAN: ist eigentlich allgemein praktisch :-)
def labelundrgb(value):
  "aus einem Value (value oder kachel) ein Stringlabel und das RGB Farbtuple"
  
  if MainMode=='M':		#META:  Hex ist eigentlich Kachelnummer, Pastellton wie im Grid
    value = KachelCheck(value)
    return str(value), wx.Colour(* autopastell(value) )
  else:				#PAINT: Farbstring und Farbe direkt
    value = HexColorString(value,1)
    return value, hex2col(value)

class HexColourButton (wx.lib.colourselect.ColourSelect):
  "kleine Variante von ColourSelect, die hex spricht und auch hex als Label zeigt"
  
  def __init__(self, parent,id, hex, size):
    hex,col = labelundrgb(hex)
    wx.lib.colourselect.ColourSelect.__init__(self, parent,id, hex, col, size = size)
    self.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.OnSelectColour)
  
  def OnClick(self, event):
    if MainMode=='M': return		#META: kein Farbdialog
    wx.lib.colourselect.ColourSelect.OnClick(self, event)
    ##LATER: wie in Gridzelle die Liste der benutzten/unbenutzten ?
  
  def OnSelectColour(self, event):
    if MainMode=='M': return		#META: just in case, darf eigentlich fuer Meta nicht kommen
    
    colour = event.GetValue()
    self.SetLabel(col2hex(colour))	#das macht kein Refresh :-(
    self.SetColour( colour )		#deshalb muss ich die gleiche Farbe nochmal reingeben
  
  #-------------------------------------------------
  #auch hier gilt hexstring als Esperanto
  
  def GetHex(self):
    if MainMode=='M':			#META:  Kachelnummer aus dem Label
      return KachelCheck( self.GetLabel() )
    else:				#PAINT: die gewaehlte Farbe
      return col2hex( self.GetColour() )
  
  def SetHex(self,hex):
    hex,col = labelundrgb(hex)
    self.SetLabel( hex )		#Label und Farbe...
    self.SetColour( col )


#----------------------------------------------------------------------
#HAUPTFENSTER: GRID + Menues + Bars ...

def MyToolAdd(win,target, text,help, pic, action, oldid=None):
  "kleiner Helper: ein Tool in 1 oder mehrere Menues und Toolbars einfuegen"
  
  #MULTI-TARGET: in alle gleich einfuegen
  if type(target)==types.ListType:
    #dann auch mehrere ID's returnen (oldid macht nur fuer einen Sinn...)
    return map(lambda t: MyToolAdd(win,t, text,help, pic, action, oldid), target)
  
  if oldid is None: newid = wx.NewId()
  else:             newid = oldid
  
  if pic: pic = wx.Bitmap( iconCheck(pic), wx.BITMAP_TYPE_ANY )
  
  #MENU: Zeile mit Icon
  if isinstance(target,wx.Menu):
    item = wx.MenuItem(target, newid, text, help)
    if pic: item.SetBitmap(pic)
    target.AppendItem(item)	##WXBUG: Bitmap muss man vor Append einstellen
    
    if oldid is None: wx.EVT_MENU(win, newid, action)	#sonst bestehende Bindung annehmen
    return newid
  
  #TOOLBAR: nur ein Icon
  if isinstance(target,wx.ToolBar):
    target.AddSimpleTool(newid, pic, text,help)
    
    if oldid is None: win.Bind(wx.EVT_TOOL,action,id=newid)	#sonst bestehende Bindung annehmen
    return newid
  
  raise AssertionError,"Target fuer MyToolAdd muss Menu,Toolbar oder Liste davon sein"

class MyFrame (wx.Frame):
  #member modemenu	wx.Menu + IDs darin zum Umschalten nach
  #member modemeta	  id -> Meta
  #member modepaint	  id -> Paint
  
  #member rahmenmode	\ letzter Stand in RahmenUpdate
  #member rahmenfile	/

  def __init__(self, parent, id, title):
    wx.Frame.__init__(self, parent, id, title, size=(800,600))
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    self.CreateStatusBar()		#nicht aktiv schreiben (SetStatusText), aber fuer rollover-Hilfe
    					##LATER: Warnings und Infos hierher ?
    
    icon = wx.Icon(iconCheck("icons/ledp.ico"),wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)
    
    self.rahmenmode = 'X'
    self.rahmenfile = ""
    
    
    #--------------------------------------------------
    #WIDGETS: SIZER + FENSTER DARIN...
    
    self.SetAutoLayout(True)
    mainsizer = wx.BoxSizer(wx.HORIZONTAL)
    self.SetSizer(mainsizer)
    
    global SzeneList,TheGrid,ColourButton
    
    #LINKS: UMSCHALTUNG DER SZENEN
    SzeneList = SzeneListCtrl(self, -1)
    mainsizer.Add(SzeneList, 0, wx.ALL|wx.EXPAND, 0)	#no resize, aber fill the space
    
    #KERN: DER GROSSE GRID
    TheGrid = LedGrid(self, -1)
    mainsizer.Add(TheGrid, 1, wx.ALL|wx.EXPAND, 0)	#EXPAND, das ist der Kern !
    
    #erstmal nur 1 Farbbutton
    colbuttsizer = wx.BoxSizer(wx.VERTICAL)
    
    ColourButton = HexColourButton(self,-1, "FFFFFF", (60, 60))
    colbuttsizer.Add(ColourButton, 0, wx.ALL, 3)
    #EVT_COLOURSELECT ist unten gebunden, aendert nur das Label
    
    ##LATER: falls mehrere Buttons
    ##  colourbutton2 = HexColourButton(self,-1, "FF00FF", (60, 60))
    ##  colbuttsizer.Add(colourbutton2, 0, wx.ALL, 3)
    
    mainsizer.Add(colbuttsizer, 0, wx.ALL, 0)
    
    #--------------------------------------------------
    #MENUBALKEN + TOOLBAR auf einmal !
    #  die MyToolAdd Methode kann in beide auf einmal einfuegen...
    
    menuBar = wx.MenuBar()
    toolBar = self.CreateToolBar( wx.TB_HORIZONTAL|wx.TB_FLAT )
    
    #===== 1.Menu: File-Operationen =====
    ##DOKU hinter Tab (\t) koennen Hotkeys im Menuetext stehen
    menu = wx.Menu()
    
    MyToolAdd(self,[menu,toolBar], "&New\tCtrl-N",  "Empty program",       "icons/file-new.gif",   self.OnNew)
    MyToolAdd(self,[menu,toolBar], "&Open\tCtrl-O", "Open LED program",    "icons/file-load.gif",  self.OnOpen)
    MyToolAdd(self,[menu,toolBar], "&Save\tCtrl-S", "Save LED program",    "icons/file-save.gif",  self.OnSave)
    MyToolAdd(self, menu         , "save &As",      "Save with new name",  "icons/file-saveas.gif",self.OnSaveAs)
    MyToolAdd(self, menu         , "&Resize",       "Resize existing Grid","icons/file-resize.gif",self.OnResize)
    
    menu.AppendSeparator()
    MyToolAdd(self,menu, "&Import Image", "Read Szene from Image file","icons/file-bmpin.gif", self.ImageImport)
    MyToolAdd(self,menu, "&Export Image", "Save Szene to BMP file",    "icons/file-bmpex.gif", self.ImageExport)
    menu.AppendSeparator()
    MyToolAdd(self,menu, "e&Xit\tCtrl-Q", "Terminate the program",     "icons/file-exit.gif",  self.OnQuit)
    menuBar.Append(menu, "&File");
    
    #===== 2.Menue: Modi Paint/Meta und grosses Play =====
    toolBar.AddSeparator()
    menu = wx.Menu()
    self.modemenu = menu
    
    MyToolAdd(self,[menu,toolBar], "&Undo\tCtrl-Z", "Undo last Grid-Step", "icons/undo.gif", TheGrid.Undo)
    
    menu.AppendSeparator()
    
    newid = wx.NewId()
    menu.AppendRadioItem(newid, "&Meta",  "Tile layout in Meta-Scene")
    wx.EVT_MENU(self, newid, self.OnViewMeta)
    self.modemeta = newid
    newid = wx.NewId()
    menu.AppendRadioItem(newid, "&Paint", "Paint normal Scenes")
    wx.EVT_MENU(self, newid, self.OnViewPaint)
    self.modepaint = newid
    
    menu.AppendSeparator()
    
    menuBar.Append(menu, "&Mode");
    
    MyToolAdd(self,menu, "&Play",           "Play full program",  "icons/mode-play.gif",   SzeneList.ProgExPlay)
    MyToolAdd(self,menu, "play from &Here", "Play in test mode",  "icons/mode-test.gif",   SzeneList.ProgTest)
    
    #===== 3.Menue: Operationen auf der Szeneliste =====
    menu = wx.Menu()
    
    #verspaetetes Init, braucht die SzeneList
    global SZENEMOVES
    SZENEMOVES = [
      [ "&New",		"New Szene",	"icons/scene-new.gif",	SzeneList.SzeneNew ],
      [ "&Dupl\tCtrl-C","Duplicate Szene","icons/scene-dup.gif",SzeneList.SzeneDupl ],
      [ "&Up",		"Move Up",	"icons/scene-up.gif",	SzeneList.SzeneMoveUp ],
      [ "d&Own",	"Move Down",	"icons/scene-dn.gif",	SzeneList.SzeneMoveDn ],
      [ "de&L\tCtrl-X",	"Delete Szene",	"icons/scene-del.gif",	SzeneList.SzeneDel ],
    ]
    
    #5 Szene-Moves genau wie im Popupmenu
    for move in SZENEMOVES:
      MyToolAdd(self,menu, *move)
    
    menuBar.Append(menu, "&Step");
    
    #===== 4.Menue: 3*3 Fill++-Operationen =====
    toolBar.AddSeparator()
    menu = wx.Menu()
    
    MyToolAdd(self,[menu,toolBar], "Fill &Hori", "Fill Horizontal", "icons/fill-hori.bmp",  TheGrid.FillHori)
    MyToolAdd(self,[menu,toolBar], "Fill &Verti","Fill Vertical",   "icons/fill-verti.bmp", TheGrid.FillVerti)
    MyToolAdd(self,[menu,toolBar], "Fill &Diag", "Fill Diagonal",   "icons/fill-diag.bmp",  TheGrid.FillDiag)
    
    MyToolAdd(self,[menu,toolBar], "Grad Hori\tCtrl-H",  "Grad Horizontal", "icons/grad-hori.bmp",  TheGrid.GradHori)
    MyToolAdd(self,[menu,toolBar], "Grad Verti\tCtrl-V", "Grad Vertical",   "icons/grad-verti.bmp", TheGrid.GradVerti)
    MyToolAdd(self,[menu,toolBar], "Grad Diag\tCtrl-D",  "Grad Diagonal",   "icons/grad-diag.bmp",  TheGrid.GradDiag)
    
    MyToolAdd(self,[menu,toolBar], "Move Hori",  "Move Horizontal", "icons/move-hori.bmp",  TheGrid.MoveHori)
    MyToolAdd(self,[menu,toolBar], "Move Verti", "Move Vertical",   "icons/move-verti.bmp", TheGrid.MoveVerti)
    MyToolAdd(self,[menu,toolBar], "Move Diag",  "Move Diagonal",   "icons/move-diag.bmp",  TheGrid.MoveDiag)
    
    menu.AppendSeparator()
    toolBar.AddSeparator()
    
    #NEU: damit Color Dialog einen Hotkey haben kann, muss er Menupunkt haben
    MyToolAdd(self,[menu,toolBar], "Color Picker\tCtrl-F",  "Pick Color Dialog",   "icons/picker.bmp",  TheGrid.OnColorPicker)
    
    menuBar.Append(menu, "&Area");
    
    #===== 5.Menue: Help =====
    menu = wx.Menu()
    
    MyToolAdd(self,menu, "&Help", "Open html help", None, self.OnHelp)
    MyToolAdd(self,menu, "&About","About LED edit", None, self.OnAbout)
    
    menuBar.Append(menu, "&Help");
    
    self.SetMenuBar(menuBar)
    toolBar.Realize()
    
    
    #--------------------------------------------------
    #ALLES DRIN, ABSCHLUSS
    
    self.RahmenUpdate()		#Fenstertitel, Hexbutton, Viewmenu
    self.Fit()			#self.Layout + self.SetClientSize(minsize...)
    self.Show(True)
  
  def RahmenUpdate(self):
    "Update fuer kleine GUI-Elemente, die kein Load/Save haben"
    ##<=INPUT: MainMode			(gespeichert in self.rahmenmode)
    ##<=INPUT: MainProg.filename	(     "       " self.rahmenfile)
    
    ##LATER: MainProg.needsave ist noch nicht mit dabei, wird noch nicht im Titel angezeigt
    ##  das waere aufwendiger weil es von viel mehr Orten angestossen wird und weil 
    ##  MainProg.needsave noch nichtmal reicht (auch geaenderter Grid, der noch nicht im Prog ist)
    
    if MainMode	!= self.rahmenmode:
      #Hexbutton := default je nach Modus
      ColourButton.SetHex(None)
      
      #Radiobuttons fuer Modus im View-Menu
      self.modemenu.Check( ifop(MainMode=='M',self.modemeta,self.modepaint), True )
    
    if MainMode	!= self.rahmenmode or MainProg.filename != self.rahmenfile:
      #Fenstertitel mit Filename und Meta
      self.SetTitle("'%s' - LED-Wall-Editor %s" % (os.path.basename(MainProg.filename), ifop(MainMode=='M',"(META)","")))
    
    #neuen letzten Stand merken...
    self.rahmenmode = MainMode
    self.rahmenfile = MainProg.filename
  
  
  #------------------------------------------------------------
  #FILEMENUE, GRUNDLAGEN
  
  def AskSave(self,event=None):
    "VOR AKTION: mit Rueckfrage sichern, inklusive eventuelles Veto und no-thanks return"
    ##MIT EVENT von OnCloseWindow (Veto moeglich)
    ##OHNE EVENT mein New oder Load (Veto gar nicht noetig)
    
    #erstmal aus der GUI zurueck ins Programm, sonst stimmt needsave nicht !
    SzeneList.SaveProgram()
    
    if MainProg.needsave:
      #wenn Veto verboten ist, dann gar kein Cancel erst anzeigen :-)
      cancel = ifop(not event or event.CanVeto(), wx.CANCEL, 0)
      
      #Dialog anzeigen: JA-Sichern, NEIN-Ende, CANCEL-Ende abbrechen
      ##CLEAN: 3 wertig auch oben verallgemeinern ?
      dlg = wx.MessageDialog(MainWin, "Vor dem Beenden Aenderungen speichern ?","Check",
                             wx.YES_NO|cancel|wx.ICON_QUESTION)
      ret = dlg.ShowModal()
      dlg.Destroy()
      
      #Cancel heisst Veto, das ist hier sicher erlaubt
      if ret == wx.ID_CANCEL:
        if event: event.Veto()
        return False		#das aufrufende Command nicht ausfuehren
      
      #Sichern (ID_YES) oder nicht (ID_NO), aber auf jeden Fall ins Ende weiterlaufen
      if ret == wx.ID_YES:
        self.OnSave()
    
    return True
  
  def RiesenUpdate(self):
    "NACH GROSSER AKTION: GANZ GROSSES UPDATE"
    
    TheGrid.NewSize()			#Layoutanpassung bevor die Werte kommen
    SzeneList.LoadProgram()		#links rot, Grid mit Kachelnummern
    self.RahmenUpdate()			#Fenstertitel, Hexbutton, Viewmenu
  
  def OnNew(self, event):
    "NEW: leeres LedProgramm laut Dialog, dann nach META springen"
    global MainProg,MainMode
    
    #Rueckfrage wegen Speichern, return falls Cancel
    if not self.AskSave(): return
    #Sizedialog fuer 2 Werte
    size = UseTableDialog(self, MainProg.size, ["Width","* Height"], [int0,int0])
    
    if not size: return
    MainProg = LedProgramm(size=size)
    MainMode = 'M'
    
    #Gridsize, Liste+Grid Daten, Rahmenupdate
    self.RiesenUpdate()
  
  def OnOpen(self, event):
    "OPEN: LedProgramm laden..."
    global MainProg,MainMode
    
    #Rueckfrage wegen Speichern, return falls Cancel
    if not self.AskSave(): return
    
    #Open File Dialog neben dem aktuellen Programm
    progname = UseFileDialog(self,"Open program", MainProg.filename, SzeneList.ledpwildcard, save=False)
    
    if not progname: return
    
    try:
      OldMainProg = MainProg		#das komplette alte Programm, fuer Fehlerfall...
      MainProg = LedProgramm(filename=progname)
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
      MainProg = OldMainProg		#...das ist der Fehlerfall
    else:
      if MainProg.szenen: MainMode = 'P'
      else:               MainMode = 'M'	#nach META, wenn es noch gar keine Szenen gab, ist offenbar ganz frisch !
    
    #Gridsize, Liste+Grid Daten, Rahmenupdate
    self.RiesenUpdate()
  
  def OnResize(self, event):
    "RESIZE ist wie kleines NEW: per Dialog die Groesse anpassen und nach META gehen, aber diesmal bleibt alles leben"
    
    #Sizedialog fuer 2 Werte, aktuelles als Vorgabe
    size = UseTableDialog(self, MainProg.size, ["Width","* Height"], [int0,int0])
    
    if not size: return
    if tuple(size)==MainProg.size: return
    
    MainProg.SetSize(*size)		#w,h eintragen
    MainProg.SetMeta(checkszenen=False)	#harte Metaanpassung, aber die Szenen noch nicht (erst bei Umschaltung)
    
    global MainMode
    MainMode = 'M'
    
    #Gridsize, Liste+Grid Daten, Rahmenupdate
    self.RiesenUpdate()
    
    ##TRICK: Resize geht auch mehrmals aus Meta heraus, wenn was nicht passt,
    ##  das ist gut, weil erst beim Verlassen von Meta die Szenen angepasst werden...
  
  def OnSave(self, event=None, progname=""):
    "SAVE: LedProgramm sichern unter altem oder genannten (via SaveAs) Namen..."
    
    #eventuell erstmal Save As Dialog
    if not MainProg.filename and not progname:
      return self.OnSaveAs(event)
    
    #1.zuerst aus der GUI ins Programm
    ##event=None heisst aus OnCloseWindow indirekt gerufen
    if event: SzeneList.SaveProgram()
    
    #2.das MainProg sichern
    try:
      MainProg.Save(progname)			#LEDP
      SzeneList.ProgExPlay(event, play=False)	#LEDX, nur export, nicht play
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
  
  def OnSaveAs(self, event):
    "SAVE: LedProgramm sichern unter gewuenschtem Namen, das bleibt der aktuelle Name"
    
    #Save File Dialog neben dem aktuellen Programm
    progname = UseFileDialog(self,"Save Program", MainProg.filename, SzeneList.ledpwildcard, save=True)
    
    if not progname: return
    self.OnSave(event, progname)	#Save mit extra Parameter
    self.RahmenUpdate()			#Fenstertitel wegen Filename !
  
  def OnQuit(self, _): #event)
    "das ist die aktive Quit-Aktion 'bitte mache Quit', Rest passiert in OnCloseWindow"
    self.Close()
  
  def OnCloseWindow(self,event):
    "[x] Button gedrueckt oder Quit selber gerufen -> ich kann entscheiden"
    
    #Rueckfrage wegen Speichern, return falls Cancel
    if not self.AskSave(event): return
    
    #das normale Ende (not dirty, nach Save, ohne Save)
    self.Destroy()
  
  #------------------------------------------------------------
  #Image Import und Export in aktuelle Szene
  
  bmpwildcard=	"BMP files (*.bmp)|*.bmp"
  
  ###UNIX: Listen von mehreren *.xxx gehen nur unter Windows
  imagewildcard="Image files|*.bmp;*.jpg;*.jpeg;*.gif;*.png;*.tif;*.tiff|" \
  		"All files (*.*)|*.*"
  
  def ImageImport(self,event):
    "Read Szene from Image file"
    ##NO: wx.lib.imagebrowser.ImageDialog ist ein gewaltiger Overkill
    
    if MainMode=='M': 			#META: Action mit Message verbieten
      LogMessageDialog(MSG_WARNG, "Bitmapimport & -export geht nicht mit Meta-Szene")
      return
      ##LATER: Arbeit mit Transparenz oder Schwellwert :-)
    
    #Open File Dialog im current dir
    imagepath = UseFileDialog(self,"Import image", "", self.imagewildcard, save=False, isled=False)
    
    if not imagepath: return
      #vorher Grid in die Szene, falls das Bild nicht alles ueberschreibt
    SzeneList.SaveProgram()
      #File laden
    wximage = wx.Image( imagepath, wx.BITMAP_TYPE_ANY )
      #Szene liest das Image aus
    SzeneList.CurrSzene().SetImage(wximage)
      #von der Szene in den Grid
    TheGrid.LoadSzene()
  
  def ImageExport(self,event):
    "Save Szene to BMP file"
    
    if MainMode=='M': 			#META: Action mit Message verbieten
      LogMessageDialog(MSG_WARNG, "Bitmapimport & -export geht nicht mit Meta-Szene")
      return
      ##LATER: Arbeit mit Transparenz oder Schwellwert :-)
    
    #Save File Dialog im current dir
    imagepath = UseFileDialog(self,"Export image", "", self.bmpwildcard, save=True, isled=False)
    
    if not imagepath: return
      #vom Grid in die Szene
    SzeneList.SaveProgram()
      #aus der Szene ein Image erzeugen
    wximage = SzeneList.CurrSzene().GetImage()
      #File schreiben (nur BMP)
    wximage.SaveFile(imagepath, wx.BITMAP_TYPE_BMP)
  
  
  #------------------------------------------------------------
  #GROSSE MODUS-UMSCHALTUNG Meta <=> Paint
  
  def OnViewMeta(self,event):
    "Wechsel nach Meta ist harmlos"
    SzeneList.SaveProgram()		#SAVE ALT: Farben aus Grid in aktuelle Szene
    
    global MainMode
    MainMode = 'M'
    
    SzeneList.LoadProgram()		#LOAD NEW: Grid mit Kacheln fuellen...
    self.RahmenUpdate()			#Fenstertitel, Hexbutton, Viewmenu
  
  def OnViewPaint(self,event):
    "Wechsel von Meta nach Paint ist spannender: Metaaenderungen wirken sich auf Szenen aus"
    SzeneList.SaveProgram()		#SAVE ALT: Grid speichert sich nach => PROG.SetMeta()
    					#  dabei die Szenen pruefen und eventuell "makefirst"
    global MainMode
    MainMode = 'P'
    
    #kein GRID.NewSize, denn die size ist nicht mehr neu
    SzeneList.LoadProgram()		#LOAD NEW: Grid wieder mit echten Farben...
    self.RahmenUpdate()			#Fenstertitel, Hexbutton, Viewmenu
  
  def OnHelp(self,event):
    try:
      os.startfile("help\\index.html")	#wie Doppelklick aufs HTML
    except Exception,ex:
      LogMessageDialog(MSG_ERROR, "Problem mit der Hilfe: " + str(ex))
  
  def OnAbout(self,event):
    dlg = wx.MessageDialog(self, '\ngrafischer Editor fuer\nLED Kachelwaende\n(c) Leber Systemtechnik 2006',
    			   "LED Edit %.2f" % LedOutputVersion, wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


#----------------------------------------------------------------------
#HAUPTPROGRAMM: 1.Objektstrukturen -> 2.GUI

class MyApp(wx.App):
  def OnInit(self):
    #--------------------------------------------------
    #1.SCHRITT "CONNECTION" zu Player.exe und "DATEN" interne Strukturen aufbauen
    
    #wie ueblich zum Hauptprogramm (PY oder EXE) wechseln
    pyexe = os.path.abspath(sys.argv[0])
    os.chdir( os.path.dirname(pyexe) )
    #wenn ich direkt in PY laufe, dann findet sich der ganze Rest in Nachbar-Directory
    if pyexe.lower().endswith(".py"):
      os.chdir( "../DELIVERY" )
    
    #NEU: als allererstes INI laden, die Werte werden ueberall gebraucht
    try:
      #INI Parser inklusive Defaults fuer meine Varis
      global ini
      ini = None
      ini = ConfigParser.SafeConfigParser( inidefaults )
      
      #per Default ist meine Section leer, ich verlange gar nix von INIs
      ini.add_section("KachelEditor")
      
      #gemeinsam mit Player moeglich, meine eigene 'KachelEditor.ini' hat Prio
      ini.read(["Parameter.ini","KachelEditor.ini"])
    
    except ConfigParser.Error,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
      if not ini or not ini.defaults():
        return False	#da hoert die Toleranz auf, meine defaults muessen ankommen
    
    #GANZ NEU: kleine INI nur fuer letzten Pfad...
    global lastledpath
    try:
      #kleine extra INI
      lastini = ConfigParser.SafeConfigParser()
      lastini.read("LastPath.ini")
      
      #einzigen Wert sofort auslesen
      lastledpath = lastini.get("LastPath","lastledpath")
    
    except ConfigParser.Error,ex:
      #Fehler sind ohne default ganz normal, echte Probleme mit LastPath.ini werden ignoriert
      lastledpath = os.getcwd() + "/led"
    
    try:
      #1a.Connection zum Player als allererstes, sonst brauche ich gar nicht weiter
      global PlayerConn
      PlayerConn = None
      PlayerConn = CPlayerConnection()
      ##raises LedConnException, das wird hier gefangen und fuehrt zu Start-Abbruch
      
      #1b.interne Struktur zum LED Programm entsprechend Kommandozeile aufbauen
      global MainProg,MainMode
      if len(sys.argv)>1 and sys.argv[1]:	#LOAD genanntes Programm
        progname = sys.argv[1]
        MainProg = LedProgramm(filename=progname)
        MainMode = 'P'
      
      if not MainProg:				#NEW, leeres Programm
        MainProg = LedProgramm()
        MainMode = 'M'
    
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
      return False	#in diesem Falle kein Fenster erzeugen...
    
    #--------------------------------------------------
    #2.SCHRITT "GUI" - die Fenster zur Anzeige aufbauen
    global MainWin
    MainWin = MyFrame(None, -1, "LED-Wall-Editor")
    self.SetTopWindow(MainWin)
    return True		#return False oder Exception ist schon oben passiert

#main nicht aufrufen, wenn ich importiert sein sollte
if __name__ == "__main__":
  try:
    try:
      app = MyApp(redirect=False)
      app.MainLoop()
    except Exception,ex:
      msg = str(ex)
      if msg != "OnInit returned false, exiting...":
        LogMessageDialog(MSG_ERROR, msg)
  finally:
    if PlayerConn: PlayerConn.Disconnect()
