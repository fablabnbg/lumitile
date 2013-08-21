import os,sys,types,re

import wx			#wxPython Fensterbibliothek :-)
import wx.grid			#der Grid ist in einem Untermodul
import wx.lib.colourselect	#da ist der Farbbutton

__pychecker__ = 'no-miximport unusednames=_,_0,_1,_2,_3,_4,_5,_6,_7,_8,_9'

wx.InitAllImageHandlers()	#damit alle bekannten Bildformate von selber gehen

#EIGENE EXCEPTION ...
class LedDataException (Exception):
  pass


#----------------------------------------------------------------------
#AUS MEINER ALTEN BASIS

def ifop(pif,pthen,pelse):
  "Ersatz-Operator pif ? pthen : pelse"
  if pif: return pthen
  else:   return pelse


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

def rgb2hex(rgb):
  return "%02X%02X%02X" % rgb
def col2hex(col):
  return rgb2hex( col.Get() )

def hex2rgb(hex):
  return tuple( map(lambda s: eval("0x" + s), (hex[:2] , hex[2:4] , hex[4:])) )
def hex2col(hex):
  return wx.Colour( *hex2rgb(hex) )

NURSTRICH_RE = re.compile("^-+$")		#Strings die nur aus ----- bestehen
BADHEX_RE    = re.compile("[^0-9a-fA-F]")	#alle non Hexziffern
def HexColorString(hex, meta=None):
  "brutale Anpassung, danach sind es garantiert 6 Hex-Ziffern oder ------"
  
  #besondere Typen zu String...
  if hex is None: hex = "FFFFFF"			#default ist weiss
  elif type(hex)==types.IntType: hex = "%06X" % hex	#Farbe als Zahl, ungenutzt
  elif type(hex)==types.TupleType: hex=rgb2hex(hex)	#RGB Tuple aus Berechnungen
  elif type(hex)==types.InstanceType: hex=col2hex(hex)	#Objekt als wx.Colour versuchen
  elif type(hex)!=types.StringType: hex = "FF0000"	#KEIN BEKANNTER TYP -> rot machen...
  
  #zweierlei Strings anpassen
  else:
    #Striche sauber...
    if NURSTRICH_RE.match(hex): hex = "------"
    else:
      hex = hex.strip().upper()		#Whitespace aussen weg, upper
      hex = hex[:6].zfill(6)		#auf 6 Zeichen kuerzen oder auffuellen
      hex = BADHEX_RE.sub("0",hex)	#alles was nicht 0-F ist durch 0 ersetzen
  
  #NEU: mit meta ist auch gleich die Anpassung darauf inklusive
  if meta:
    if meta==-1: return "------"	#'verboten', egal was in den Daten war
    if hex=="------": return "FF0000"	#irrtuemlich verboten, rot machen...
  
  return hex

def RgbMix(rgb0,rgb1, zaehler,nenner):
  "Lineare Mischung von 2 RGB-Vektoren anhand des Bruchs zaehler/nenner"
  return tuple( map(lambda x0,x1: ((x1-x0) * zaehler) / nenner + x0, rgb0, rgb1) )


#----------------------------------------------------------------------
#kleine GUI Helper...

#DIE SUPER-FENSTER !
MainWin = None			#DAS HAUPTFENSTER
SzeneList = None		#  DIE SZENENFOLGE als eigenes ListCtrl
TheGrid = None			#  DER GROSSE GRID als Zeichenfenster
ColourButton = None		#  1 FARBBUTTON dient als Mini-Palette
  ###LATER: ganzer Stack von bisherigen Farben
  ###  - eigene class von Panel oder so ableiten, Sizer wie bisher oben in main
  ###  - Right Click auf Zelle macht Push hierher
  ###  - Right Click auf Register holt aus aktueller Zelle
  ###  =>Problem: Register- und Stack-denke zu sehr vermischt :-|

#Fehler-Optik aus basis.LogMessage herausgeloest
MSG_INFO  = 0
MSG_WARNG = 1
MSG_ERROR = 2
MSG_FATAL = 3

MSG_Levelnames  = [ "OKAY", "WARNING", "ERROR", "FATAL" ]		#die Textform
MSG_Levelcolors = [ "#FFFFFF", "#FFFF00", "#FF0000", "#FF00FF" ]		#Farbe der HTML-Tabellenzeile :-)
MSG_Levelicons  = [ wx.ICON_INFORMATION, wx.ICON_EXCLAMATION, wx.ICON_ERROR, wx.ICON_ERROR ]	#das Icon fuer wx.MessageDialog

def LogMessageDialog(level, message):
  dlg = wx.MessageDialog(MainWin, message,
                         MSG_Levelnames[level],
                         wx.OK | MSG_Levelicons[level])
  dlg.ShowModal()
  dlg.Destroy()

def QuestionDialog(level, message, yesdefault):
  dlg = wx.MessageDialog(MainWin, message,
                         MSG_Levelnames[level],
                         wx.YES_NO
                         | ifop(yesdefault,wx.YES_DEFAULT,wx.NO_DEFAULT)
                         | MSG_Levelicons[level])
  ret = (dlg.ShowModal() == wx.ID_YES)
  dlg.Destroy()
  return ret

def EventVeto(event):
  "allgemeine Callbackroutine zum Veto von Events"
  event.Veto()

def EventPrint(event):
  "allgemeines Print als Feedback fuer Event"
  print event.GetEventType()

def EventIgnore(event):
  "leere Callback fuer Events"
  pass


#----------------------------------------------------------------------
#SZENEN SIND EIGENSTAENDIGE OBJEKTE

class LedSzene:
  "eine Szene ist ein BMP-basierter Schritt eines LED Programms"
  
  #member ledprog	Referenz nach oben auf das LED Programm zu dem ich gehoere
  #member name		mein Name fuer Anzeige in der GUI
  #member dauer		meine Dauer in 1/10 sec
  #
  #member farben	2D Liste [width][height] => Farbstring "1188FF" oder "------" fehlt in meta
  
  #-------------------------------------------------
  #INIT aus dict, STR nach String
  
  def __init__(self, ledprog, name,dauer,farben=None,copy=None,fill=None):
    "Konstruktion einer Szene mit farben-Liste oder mit fill gefuellt"
    
    self.ledprog = ledprog
    self.name    = name
    self.dauer   = dauer
    
    #die eigentlichen Farben: A) aus Vorgabe pruefen
    if farben:
      self.SetFarben( farben, frominit=True )
    
    #                         B) Copy aus anderer Szene
    elif copy:
      self.name    = copy.name			#die genannten 2 Werte waren ein Fake
      self.dauer   = copy.dauer			#auch von dort holen
      
      self.farben  = map(list, copy.farben)	#2D tiefe copy der farben
    
    #                         C) oder leer fuellen (weiss wenn alles fehlt)
    else:
      if fill: fill = HexColorString(fill,1)	#genannte Fuellfarbe pruefen (##TRICK: mit meta!=-1 wird ------ vermieden)
      else:    fill = "FFFFFF"			#sonst Weiss
      
      #eine Kopie von meta: -1 wird ------, Rest wird fill
      self.farben = map(
        lambda line: map(
          lambda kachel: ifop(kachel==-1,'------',fill),
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
    ret.append( "      'farben': [" )
    
    for line in self.farben:
      ret.append( "        " + str(line) + "," )
    
    ret.append( "      ]," )
    ret.append( "    }" )
    
    return '\n'.join( ret )
  
  #-------------------------------------------------
  #Schnittstelle zum GRID u.a.: 2D Liste von Farbstrings
  
  def GetFarben(self):
    "einfach, nur der Symmetrie halber..."
    ##ACHTUNG: nur Referenz, aussen nicht einfach aendern !
    return self.farben
  
  def SetFarben(self,farben, frominit=False):
    "fertige 2D Liste von Farbstrings oder ------ genau geprueft nach self.farben uebernehmen"
    
    #von farben -nach-> newfarben -nach-> self.farben mit Metapruefung uebertragen
    newfarben = []
    for l in range(self.ledprog.size[1]):
      try: line = farben[l]
      except IndexError: line = []		#fuellt map selber mit None auf
      metaline = self.ledprog.meta[l]
      
      newfarben.append( map(
        lambda color,meta: HexColorString(color,meta),
        line[:self.ledprog.size[0]],		#auf Laenge von metaline kuerzen, None auffuellen passiert automatisch
        metaline
      ) )
    
    if not frominit:
      if newfarben==self.farben: return		#der Rest passiert nur bei Aenderung !
      self.ledprog.needsave = True
    
    self.farben = newfarben
    
    #needsave nur wenn was existierendes geaendert wurde
    
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
        if hex=="------": rgb = (0,0,0)
        else:             rgb = hex2rgb(hex)
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

MAXSIZE = 20		#20 * 20 ist absolute Schmerzgrenze
MAXKACHEL = MAXSIZE**2	#maximale Kachelnummer, koennte auch 9999 sein

class LedProgramm:
  "eigenes Objekt kapselt das aktuell bearbeitete LED-Programm mit Layout als Basis + allen Szenen"
  
  #member filename	das File, aus dem die Daten gelesen wurden
  #
  #member size		Tuple (width,height) fuer die 'aeussere' Feldgroesse
  #member meta		2D Liste [width][height] => Kachelnummer oder -1=fehlt
  #member ketten	DICT von Kachelnummer -> alle Positionen (nur doppelte, selber aus meta gesammelt)
  #member prop		DICT von User defined Properties
  #
  #member ablauf	die eigentlichen PROGRAMMSCHRITTE (derzeit nur LEDSzene's, spaeter mehr)
  #member needsave	FLAG: ob ich gesichert werden muesste
  
  #-------------------------------------------------
  #INIT, FILEARBEIT
  
  def __init__(self, filename):
    self.Load(filename)
  
  def Load(self, filename=None):
    if filename: self.filename = filename
    if not self.filename: raise LedDataException,"kein Filename fuer LedProgramm.Load angegeben"
    
    try:
      progdict = eval( open(self.filename,"rt").read() )
      
      #===== SIZE laden =====
      try: self.size = progdict.pop("size",(5,5))
      except KeyError: raise SyntaxError,"Fehlende 'size' Angabe"
      
      if type(self.size) != types.TupleType or \
         len(self.size) != 2 or \
         not (0 < self.size[0] < MAXSIZE) or \
         not (0 < self.size[1] < MAXSIZE):
        raise SyntaxError,"Illegale 'size' " + str(self.size)
      
      #===== META aufwendig gegen size pruefen und ergaenzen, gleich fuer KETTEN sammeln =====
      try: meta = progdict.pop("meta")
      except KeyError: raise SyntaxError,"Fehlende 'meta' Szene"
      
      if not meta or \
         type(meta) != types.ListType:
        raise SyntaxError,"Illegales 'meta' " + str(meta)
      
      self.meta = []
      ketten = {}
      
      width = self.size[0]
      for l in range( self.size[1] ):	#fuer alle *geplanten* Zeilen
        try: line = meta[l]		  #aktuelle Zeile holen
        except IndexError: line = []	  #nicht genug Zeilen da ?
        
        #auf width beschneiden oder mit -1 auffuellen
        line = line[:width] + (width - len(line)) * [ -1 ]
        
        #Kachelnummern duerfen nur -1 bis MAXSIZE Quadrat sein
        line = map( lambda kachel: ifop(-1<=kachel<=MAXKACHEL, kachel, -1), line )
        self.meta.append( line )
        
        #gleich fuer Ketten sammeln
        for c,kachel in enumerate(line):
          poslist = ketten.setdefault(kachel,[])	#Positionsliste zu dieser Kachelnummer holen/anlegen
          poslist.append( (l,c) )
      
      #===== KETTEN sollen nur die wirklich doppelten uebrigbleiben =====
      self.ketten = dict(filter( lambda (kachel,poslist): len(poslist)>1, ketten.items() ))
      self.ketten.pop(-1,None)				#fehlende Kacheln -1 bilden keine Ketten
      
      #===== Die grosse Szenen-Folge =====
      ###LEDSCHRITT: nicht nur LedSzene darin, ich muss erstmal anhand der Daten
      ###       die richtige Unterklasse von LedSchritt (LedBlende...) finden
      
      try: ablauf = progdict.pop("ablauf")
      except KeyError: raise SyntaxError,"Fehlende 'ablauf' Szenenfolge"
      
      if not ablauf or \
         type(ablauf) != types.ListType:
        raise SyntaxError,"Illegaler 'ablauf' " + str(ablauf)
      
      self.ablauf = []
      
      for szenedict in ablauf:
        #den Rest erledigt der Konstruktor...
        szene = LedSzene(self, **szenedict)
        self.ablauf.append( szene )
      
      #===== restliche Inhalte sind freie [UDP] Properties =====
      self.prop = progdict
      
      #fertig, ich bin frisch geladen
      self.needsave = False
    
    except (NameError,SyntaxError,IOError),ex:
      raise LedDataException,"Kann LED Programm nicht laden: " + str(ex)
  
  def Save(self, filename=None):
    if filename: self.filename = filename
    if not self.filename: raise LedDataException,"kein Filename fuer LedProgramm.Save angegeben"
    
    try:
      try:
        f = None
        f = open(self.filename,"wt")
        print >>f, "#LED-Programm direkt als Pythondaten, vorsichtig editieren !"
        print >>f, "{"
        
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
        print >>f, "'ablauf': ["
        
        for step in self.ablauf:
          #__str__ von einer Szene macht das fertig eingerueckte {...} nur , fehlt noch
          print >>f, step, ","
        
        print >>f, "  ],"
        print >>f, "}"
      
        self.needsave = False
      
      finally:
        if f: f.close()
    
    except IOError,ex:
      raise LedDataException,"Kann LED Programm nicht sichern: " + str(ex)
  
  
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
    
    if not poslist: return []
    poslist.remove( (row,col) )				#Zelle selber aus Kopie rausnehmen (ist immer drin !)
    return poslist
  
  #AKTUELLE SZENE: nicht hier, sondern im Szenen-Listen-Widget
  
  #BITMAP Import & Export: nicht hier, direkt ueber die Szene
  ##LATER hier das ganze Programm als Bildfolge ? Animation ?
  
  #-------------------------------------------------
  #Arbeit mit der SZENENFOLGE
  
  def SzeneNew(self, index):
    "Neue, leere Szene einfuegen"
    
    szene = LedSzene(self, "new",10)	#Name 'new',1sec,weiss
    self.ablauf.insert( index+1, szene )
    self.needsave = True
    return szene
  
  def SzeneDupl(self, index):
    "statt Kopie mit Zielort einfach Duplicate an Ort und Stelle"
    
    szene = LedSzene(self, "",0, copy=self.ablauf[index])	#Copy Konstruktor
    self.ablauf.insert( index+1, szene )
    self.needsave = True
    return szene
  
  def SzeneMove(self, index, diff):
    "statt Move mit Zielort nur Einzelschritte +/- 1"
    
    if not (0 <= index+diff < len(self.ablauf)): return None
    szene = self.ablauf.pop(index)
    self.ablauf.insert(index+diff, szene)
    self.needsave = True
    return szene
  
  def SzeneDel(self, index):
    "Szene loeschen, ausser der letzten"
    
    if len(self.ablauf)<2: return False
    del self.ablauf[index]
    self.needsave = True
    return True
  
  
  #-------------------------------------------------
  ##KUNDE -> Arbeit auf Metaebene
  ##         wenn es GUI zum Editieren von size + meta gibt


#Singleton, es gibt nur 1 globales Programm	##LATER: spaeter mehrere moeglich
MainProg = None					#wird erst in main initialisiert

#das ist der Defaultname
LedProgName = "main.led"


#----------------------------------------------------------------------
#SZENEN-LISTE ist der Chef "ueber" dem Grid

#braucht SzeneListCtrl fuer die Einsprungpunkte,
#zum Glueck braucht der mich nicht zur Konstruktion
SZENEMOVES = []

###SVEN: SzeneDialog zum allgemeinem Properties Dialog ausbauen ?
###  - fuer int die Typcallbacks mitgeben (int,str)
###  - nicht davon ableiten, einfach Werte einsetzen...

#Dialog zum Editieren der Zusatz-Werte einer Szene
class SzeneDialog(wx.Dialog):
  #member nameitem	das TextCtrl fuer name
  #member daueritem	 "      "      "  dauer
  
  def __init__(self, parent, id, name,dauer):
    wx.Dialog.__init__(self, parent, id, "Edit Szene")
    
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    #Zeile 1 Name
    grid = wx.FlexGridSizer(0,2, 0,0)
    grid.AddGrowableCol(1,1)
    
    label = wx.StaticText(self, -1, "Name:")
    grid.Add(label, 0, wx.ALL, 3)
    self.nameitem = wx.TextCtrl(self, -1, name, size=(80,-1))
    grid.Add(self.nameitem, 1, wx.EXPAND|wx.ALL, 3)
    
    #Zeile 2 1/10 sec
    label = wx.StaticText(self, -1, "1/10sec:")
    grid.Add(label, 0, wx.ALL, 3)
    self.daueritem = wx.TextCtrl(self, -1, str(dauer), size=(80,-1))
    grid.Add(self.daueritem, 1, wx.EXPAND|wx.ALL, 3)
    
    sizer.Add(grid, 0, wx.EXPAND|wx.ALL, 3)
    
    #Zeile 3 OK/Cancel
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
    try: dauer = int(self.daueritem.GetValue())
    except ValueError: dauer = 0
    return self.nameitem.GetValue(),dauer

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
    self.InsertColumn(0, "sec/10", format=wx.LIST_FORMAT_RIGHT, width=50)
    self.InsertColumn(1, "Szene", width=70)
    self.SetMinSize((50+70+5,-1))
    
    #SZENEN: abgetrennt, weil es mit jedem Programmwechsel neu kommt
    self.LoadProg()
    
    #-------------------------------------------------
    #LISTEN EVENTS...
    
      #Wechsel der Selektion fuehrt zu Grid-Update
      ##NOT: nur ueber select, deselect kommt zu spaet, suspekt
    self.Bind(wx.EVT_LIST_ITEM_SELECTED,    self.OnItemSelected)
    ##self.Bind(wx.EVT_LIST_ITEM_DESELECTED,  self.OnItemDeselected)
    
      #Begin Edit ist egal, aber am Ende Programm updaten oder veto
    self.Bind(wx.EVT_LIST_END_LABEL_EDIT,   self.OnEndEdit)
    
      #Doppelklick (extra EVT_LEFT_DCLICK unnoetig) oder Enter fuehrt zu groesserem Editdialog
    self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,   self.OnItemActivated)
    
      #Rechtsklick gleiches Menue wie &Step
      #for wxMSW
    self.Bind(wx.EVT_COMMAND_RIGHT_CLICK,   self.OnRightClick)
      #for wxGTK
    self.Bind(wx.EVT_RIGHT_UP,              self.OnRightClick)
    
    ##LATER Veto des Spaltenresize ueberlegen
    ##self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag)
  
  def LoadProg(self):
    "ein Listenitem fuer jeden Programmschritt"
    
    #Zielgroesse fuer BildResize auf etwa 16x16 (ratio,ganzzahliger...)
    faktor = min( map(lambda x: 16/x, MainProg.size) )
    if faktor>1: self.resize = map(lambda x: faktor * x, MainProg.size)
    else:        self.resize = None
    
    #Fuer jeden step im Programm ein Item in der Liste
    for i,szene in enumerate(MainProg.ablauf):
      index = self.InsertSzene(sys.maxint, szene)
      assert i==index,"Verstoss gegen die Annahme Itemnummer==Programmschrittnummer"
    
    #erste Zeile komplett selekten
    self.SelectSzene(0,nosave=True)
  
  ##DOKU: es gibt kein SaveProg, Aenderungen die ich in dieser Liste
  ##  am Gesamtprogramm vornehme, geschehen sofort, damit das Grid damit arbeiten kann
  
  def MakeSzeneBitmap(self, index, szene=None):
    "fuer Listenelement index aus der Szene das aktuelle Bild holen"
    if not szene: szene = MainProg.ablauf[index]
    
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
    
    #neues Item einfuegen
    index = self.InsertImageStringItem(pos, str(szene.dauer), imgidx)
    #Text fuer 2.Spalte nachtragen
    self.SetStringItem(index, 1, szene.name)
    
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
    return MainProg.ablauf[ self.currstep ]
  
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
    
    try: dauer = int( self.GetItemText(self.currstep) )
    except ValueError: dauer = 0
    name = self.GetItem(self.currstep,1).GetText()
    return name,dauer
  
  def SetItemTexte(self, name,dauer):
    "alle [2] Werte zur aktuellen Zeile setzen"
    
    self.SetItemText(self.currstep, str(dauer))	#nicht setitem, das bild soll bleiben
    self.SetStringItem(self.currstep, 1, name)	#andere Methode wegen Spaltennummer
  
  
  #-----------------------------------------------------------
  #EVENT-HANDLER
  
  ##TIP: Auskunft ueber item in events:
  ##  item = event.GetItem() - darin sind jede menge m_xxx Infos, siehe SetItem
  
  def OnItemSelected(self, event):
    "alte Szene SICHERN, neue Szene LADEN"
    
    self.selectevent = True		#ja, das Event kam...
    
    #ALT SICHERN...
    if self.currstep is not None:	#Sonderfall nosave: anfangs & mitten in Step-Operationen
      self.SaveGrid()			#TheGrid.SaveFarben + Zusatzdaten
    
    #NEU LADEN...
      #Sonderfall Direktaufruf mit int beachten
    if type(event)==types.IntType:
      self.currstep = event
      event = None
    else:
      self.currstep = event.GetIndex()
    
      #Grid neu laden
    if TheGrid: TheGrid.LoadFarben()	##CLEAN: Ausnahme nur fuers 1.mal ist etwas unschoen
    if event: event.Skip()
  
  def SaveGrid(self):
    "wichtig: alle verlassenen Szenen darueber den Grid sichern"
    
    TheGrid.SaveFarben()		#vom Grid ins Programm/Szene
    					#achtet selber auf Aenderungen und setzt needsave
    
    szene = self.CurrSzene()		#auch meine 2 Daten ins Programm
    name,dauer = self.GetItemTexte()	#aber auf Aenderung achten
    if (name,dauer) != (szene.name,szene.dauer):
      szene.name,szene.dauer = name,dauer
      MainProg.needsave = True
    
    self.MakeSzeneBitmap(self.currstep, szene)	#aus Szene in meine Liste
  
  ##NICHT MEHR...
  ##def OnItemDeselected(self, event):
  ##  "bei Verlassen der alten Szene SICHERN"
  ##  pass
  
  def OnEndEdit(self, event):
    "das Label sind die ms-Zahlen damit sie leicht zu editieren sind"
    
    if event.GetColumn()==0:	#nur fuer die 1.Spalte (die Zahl)
      #die Zeile event.GetIndex() ist egal...
      
      try: int( event.GetText() )
      except ValueError: event.Veto()
      else: event.Skip()
  
  def OnItemActivated(self, event):
    "Doppelklick oder Enter fuehrt zu groesserem Editdialog"
    dlg = SzeneDialog(self, -1, *self.GetItemTexte())
    
    if dlg.ShowModal() == wx.ID_OK:
      self.SetItemTexte( *dlg.GetValues() )
    
    dlg.Destroy()
    event.Skip()
  
  def OnRightClick(self, event):
    "rechter Mausklick: gleiches Menue wie oben &Step"
    
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
    
    self.SaveGrid()			#TheGrid.SaveFarben + Zusatzdaten
    szene = MainProg.SzeneNew(self.currstep)
    
    #dahinter einfuegen & dahin wechseln
    self.InsertSzene(self.currstep+1, szene, makecurr=True)
  
  def SzeneDupl(self,_event):
    "statt Kopie mit Zielort einfach Duplicate an Ort und Stelle"
    
    self.SaveGrid()			#TheGrid.SaveFarben + Zusatzdaten
    szene = MainProg.SzeneDupl(self.currstep)
    
    #dahinter einfuegen & dahin wechseln
    self.InsertSzene(self.currstep+1, szene, makecurr=True)
  
  def SzeneMove(self, diff):
    "statt Move mit Zielort nur Einzelschritte +/- 1"
    
    self.SaveGrid()			#TheGrid.SaveFarben + Zusatzdaten
    szene = MainProg.SzeneMove(self.currstep, diff)
    
    if szene:
      self.DeleteItem(self.currstep)
      #verschoben wieder einfuegen & dahin wechseln
      self.InsertSzene(self.currstep + diff, szene, makecurr=True)

  def SzeneMoveUp(self,_event): self.SzeneMove(-1)
  def SzeneMoveDn(self,_event): self.SzeneMove(+1)
  
  def SzeneDel(self,_event):
    "Szene loeschen, ausser der letzten"
    
    self.SaveGrid()			#TheGrid.SaveFarben + Zusatzdaten
    
    if MainProg.SzeneDel(self.currstep):
      self.DeleteItem(self.currstep)
      
      #aktuelle Szene wird das danach, nur ganz hinten rueckt es 1 rein
      newidx = ifop( self.currstep >= self.GetItemCount(), self.currstep-1, self.currstep )
      self.SelectSzene( newidx, nosave=True )


#----------------------------------------------------------------------
#THE GRID !!!

class LedGrid (wx.grid.Grid):
  "die grosse Zeichenflaeche ist ein wx.Grid, da die 'Pixel' riesig sind"
  
  #classvari showhex	ob der hexwert mit angezeigt wird
  showhex = True
  
  #member firstselect	TUPLE: Zellenposition, wo ich mit selekten angefangen habe
  
  def __init__(self, parent,id):
    #===== Basis die so eingestellt bleibt =====
      #Grid erzeugen
    wx.grid.Grid.__init__(self, parent,id)
    self.firstselect = None
    
      #verhindert nur resize-Cursor "mittendrin"; Resize-Events per Header siehe Quadratisch unten
    self.DisableDragGridSize()
      #Font monospaced
    self.SetDefaultCellFont(wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL))
      #alles mittig
    self.SetDefaultCellAlignment(wx.ALIGN_CENTRE,wx.ALIGN_CENTRE)
    
    #===== GRID-EVENTS =====
      #Doppelklick oeffnet Farbdialog, Rechtsklick fuer Austausch mit HexColourButton
    self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
    self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
    
      #Quadratisches resize
    self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.OnRowSize)
    self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColSize)
    
      #erstes Element eines eventuellen Blocks fuer Zeichenops merken
    self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
    ##NOT beobachten, ich kann anfragen
    ##self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
    
      #Farbe dem hex anpassen
    self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnCellChange)
    
    ##OPTIONAL: Veto kann editieren live verbieten oder auf falschem Wert stehenbleiben
    ##self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN,  self.OnEditorShown)
    ##self.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnEditorHidden)
    
    #===== Meta-Infos Farb-Daten aus dem LED-Programm uebertragen =====
    self.RefreshMeta()
    self.LoadFarben()
  
  def RefreshMeta(self):
    "grundlegendes Layout, wenn sich Meta-Programm aendert"
      #width,height ---umdrehen--> rows,cols
    self.CreateGrid( MainProg.size[1], MainProg.size[0] )
      #wird mit gespeichert, 50 ist nur der default
    self.Quadratisch( MainProg.GetProperty("QuadratSize",50) )
      #auch Spalten nicht a,b,c sondern 1,2,3
    for i in range( MainProg.size[0] ): self.SetColLabelValue(i, str(i+1))
  
  def LoadFarben(self):
    self.SetLEDAll( SzeneList.CurrSzene().GetFarben() )
  
  def SaveFarben(self):
    SzeneList.CurrSzene().SetFarben( self.GetLEDAll() )
  
  #-------------------------------------------------
  #schlaues Setzen einer Zelle
  
  ##DOKU: grosses GetLEDCell ist unnoetig
  ##  - fuer den eigentlichen hex-string genuegt GetCellValue vom wx.Grid selber
  ##  - GetCellRGB ist zur Bequemlichkeit schon nach RGB konvertiert
  def GetCellRGB(self, row,col):
    return hex2rgb( self.GetCellValue(row,col) )
  
  def SetLEDCell(self, row,col, hex=None, inkette=False):
    "Hex-Farbwert einstellen [falls genannt] und entsprechend faerben"
    
    #0.fuer reines Update erstmal den hexstring holen (weiss falls da auch nix)
    if not hex: hex = self.GetCellValue(row,col)
    if not hex: hex = "FFFFFF"
    
    #1.Wert anpassen, simpel und ohne Fehlermeldungen
    ##LATER koennte man statt brutaler Anpassung in boesen Zellen drinbleiben
    ##      die simplegrid Demo hat 2 doofe Moeglichkeiten, besser waere Veto fuer EditorHidden ?
    ##      ! aber Vorsicht, das wird nicht nur in GUI genutzt
    hex = HexColorString( hex, MainProg.meta[row][col] )
    #danach sind es garantiert 6 Hex-Ziffern und passt auch zu meinem meta
    
    #2.den eigentlichen Wert setzen
    self.SetCellValue(row,col, hex)
    
    if hex == "------":			#gesperrte Zellen, da ist keine Kachel
      self.SetCellBackgroundColour(row,col, wx.BLACK)
      self.SetCellTextColour(row,col, wx.RED)
      self.SetReadOnly(row,col, True)	#was nicht da ist, kann man nicht einschalten
    
    else:
      #RRGGBB korrekt in Farbewerte (Liste von 3 Zahlen) zerschneiden
      rgb = hex2rgb( hex )
      farbe = wx.Colour( *rgb )
      
      #hier wird die Zelle eingefaerbt !!!
      self.SetCellBackgroundColour(row,col, farbe)
      
      if self.showhex:
        #normalerweise gut sichtbare Farbe
        ##ALT invers war zu bunt: farbe = wx.Colour(* map(lambda c: (256-c), rgb) )
        farbe = ifop( sum(rgb)<384, wx.WHITE, wx.BLACK )
        self.SetCellTextColour(row,col, farbe)
      else:
        #wenn hex nicht angezeigt wird, ist es einfach in der gleichen Farbe + readonly
        self.SetCellTextColour(row,col, farbe)
        self.SetReadOnly(row,col, True)	#was ich nicht sehen kann, kann ich so nicht editieren
    
    #+ AUSSERDEM: wenn ich Teil einer Kette bin, dann die anderen mitziehen
    if inkette: return		#nicht noetig, ich bin schon auf dem Wege gerufen worden
    kette = MainProg.GetKette(row,col)
    for r,c in kette:
      self.SetLEDCell(r,c, hex, inkette=True)
    
    ##NICHT MEHR: nicht einfach Text-Hintergrund setzen,
    ##  sondern eigenen Renderer schreiben ?
  
  #-------------------------------------------------
  #Austausch: GRID <--> LEDPROGRAMM.aktuelle Szene
  #           die gemeinsame Sprache hierfuer ist die 2D Liste von Farbstrings
  
  ##NICHT MEHR: vielleicht statt Strings eigene Werte-Typen ? 
  ##  dafuer die LedSzene von wxGridTableBase ableiten
  ##  die Werte waeren None und Zahlen als Hex
  
  def GetLEDAll(self):
    "die 2D Liste von Farbstrings aus meinen Zellen holen"
    ##DOKU: hier geht's nach Grid-size und nicht nach MainProg.size,
    ##      geht theoretisch auch mit groesserem Grid
    
    ret = []
    for row in range( self.GetNumberRows() ):	#0..height
      farbline = []
      ret.append( farbline )
      
      for col in range( self.GetNumberCols() ):	#0..width
        farbline.append( self.GetCellValue(row,col) )
    
    return ret
  
  def SetLEDAll(self,farben):
    "die 2D Liste von Farbstrings auf meine Zellen verteilen"
    ##DOKU: hier geht's nach farben und nicht nach MainProg.size,
    ##      geht theoretisch auch mit kleineren Feldern
    
    for row,farbline in enumerate(farben):	#0..height + farbline gleich fertig
      for col,farbe in enumerate(farbline):	#0..width  + farbstring gleich fertig
        self.SetLEDCell(row,col, farbe)
    
    self.ClearSelection()
  
  
  #-------------------------------------------------
  #EVENTS...
  
  def EventCelldata(self, event):
    row = event.GetRow()
    col = event.GetCol()
    hex = self.GetCellValue(row,col)
    bad = hex=="------"
    return (row,col,hex,bad)
  
  def OnCellLeftDClick(self, event):
    "Doppelklick oeffnet Farbdialog fuer die Zelle"
    
    #die aktuelle Zelle
    row,col,hex,bad = self.EventCelldata(event)
    if bad:
      event.Skip()
      return
    
    #nicht self (Grid) als Parent sondern weiter oben
    dlg = wx.ColourDialog(wx.GetTopLevelParent(self))
    
    data = dlg.GetColourData()
    data.SetChooseFull(True)		#voller Dialog, wie bei HexColourButton implizit auch
    data.SetColour(hex2col( hex ))	#Init mit Farbe aus der Zelle
    
    if dlg.ShowModal() == wx.ID_OK:	#OK gedrueckt, neue Farbe in die Zelle
      self.SetLEDCell(row,col, col2hex( data.GetColour() ))
    
    dlg.Destroy()
    event.Skip()
  
  def OnCellRightClick(self, event):
    "Rechter Klick fuer Austausch <- => mit Farbbutton rechts"
    
    #die aktuelle Zelle
    row,col,hex,bad = self.EventCelldata(event)
    if bad:
      event.Skip()
      return
    
    if event.ControlDown():		#mit Ctrl: "PICK" in den Button rueber
      ColourButton.SetHex( hex )
    else:				#ohne: "FILL" die Zelle faerben
      self.SetLEDCell(row,col, ColourButton.GetHex())
    
    event.Skip()
  
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
    
    #NEU: Minsize, damit Layout klappt
    #     n Zeilen dieser Breite + Kopfzeile + Reserve falls Editor eingeblendet wird
    self.SetMinSize(( (size+1)*(self.GetNumberCols()+1)+12, (size+1)*(self.GetNumberRows()+1)+12 ))
    ###LATER: Size-Handling eingreifen, so dass er Scrollbars die gar nicht da sind
    ###  fuer das Erscheinen der Scrollbars nicht immer mit einrechnet
  
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
    self.SetLEDCell( event.GetRow(),event.GetCol() )
  
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
  
  def FillCheck(self):
    "Box Selektion -> sortierte Zeilen & Spaltenlisten fuer Fill-Operationen; leer wenn ungeeignet"
    
    if not self.firstselect: return [],[]		#der Anfangspunkt (Pivot-Zelle) fehlt
    row,col = self.firstselect
    
    ###DOKU: in wxPython 2.6.1.0 fur PY 2.4 
    ###  waren mehrere linke obere/rechte untere Ecken fuer disjunkte (Ctrl-Drag) Bereiche moeglich
    ###  aber Einzelzellen waren nur in GetSelectedCells und nicht hier
    ###  =>das ist egal, ich verlange eh' reine Box
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
    if not rows: LogMessageDialog(MSG_ERROR, "Fuell-Operationen brauchen genau eine einzelne Box-Selektion")
    return rows,cols

  ###DOKU: FARBEN fuer die Ops nicht erfragen (doof) und nicht aus HexButton (vorher machen)
  ###  sondern direkt aus den Tabellenzellen
  ###  ! dazu wird die erste Zelle (PIVOT-Zelle) einer Blockselektion vermerkt
  
  ###ACHTUNG: die 6 Buttons/Menuepunkte bleiben immer aktiv,
  ###  ich muss am Anfang der jeweiligen Operation pruefen
  
  def FillHori (self,event):
    "Horizontal fuellen nach links oder rechts, zeilenweise unabhaengig"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    for r in rows:			#aeussere Schleife ueber Zeilen
      hex = "------"			#erstmal definiert ungueltig
      for c in cols:
        #solange ich noch suche, merke ich mir nur die Farben
        if hex == "------": hex = self.GetCellValue(r,c)
        #wenn ich eine Farbe habe, fuelle ich die von jetzt an (------ wird nicht ueberschrieben)
        else:		    self.SetLEDCell(r,c,hex)
  
  def FillVerti(self,event):
    "Vertikal fuellen --> wie FillHori transponiert"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    for c in cols:			#--> wie FillHori transponiert
      hex = "------"
      for r in rows:
        if hex == "------": hex = self.GetCellValue(r,c)
        else:		    self.SetLEDCell(r,c,hex)
  
  def FillDiag (self,event):
    "Ganze Box fuellen, alle aus erster Zelle"
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    hex = "------"			#--> wie FillHori "GEOEFFNET"
    for r in rows:			#    Suche nach 1.Farbe und dann Weitertragen fuer alle
      for c in cols:
        if hex == "------": hex = self.GetCellValue(r,c)
        else:		    self.SetLEDCell(r,c,hex)
  
  def GradHori (self,event):
    "Horizontaler Gradient von links nach rechts, zeilenweise unabhaengig"
    ##HINT: wenn ich zeilenweise mal nicht will, muss ich vorher vertikal fuellen...
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    for r in rows:			#aeussere Schleife ueber Zeilen
      colscut = list(cols)		#Kopie der Spaltenliste zum Beschneiden
      try:				#vorne und hinten ------ abschneiden
        while self.GetCellValue(r,colscut[ 0])=="------": del colscut[ 0]
        while self.GetCellValue(r,colscut[-1])=="------": del colscut[-1]
      except IndexError:		#wenn es nur ------ war, dann naechste Zeile
        continue
      
      if len(colscut)<=2: continue	#len=0 war IndexError, aber 1 oder 2 geht auch kein Gradient
      
      #von jetzt an gilt colscut, dazwischen soll der Gradient entstehen
      c0 = colscut[ 0] ; rgb0 = self.GetCellRGB(r,c0)	#erste und letzte Nummer
      c1 = colscut[-1] ; rgb1 = self.GetCellRGB(r,c1)	#und Farbe dort
      
      for c in colscut[1:-1]:		#nur die inneren Zellen mit Mischfarbe fuellen
        #direkt die RGB Mischfarbe einfuellen
        self.SetLEDCell(r,c, RgbMix(rgb0,rgb1,c-c0,c1-c0) )
  
  def GradVerti(self,event):
    "Vertikaler Gradient --> wie GradHori transponiert"
    ##HINT: wenn ich zeilenweise mal nicht will, muss ich vorher vertikal fuellen...
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    for c in cols:			#--> wie GradHori transponiert
      rowscut = list(rows)
      try:
        while self.GetCellValue(rowscut[ 0],c)=="------": del rowscut[ 0]
        while self.GetCellValue(rowscut[-1],c)=="------": del rowscut[-1]
      except IndexError:
        continue
      
      if len(rowscut)<=2: continue
      
      r0 = rowscut[ 0] ; rgb0 = self.GetCellRGB(r0,c)
      r1 = rowscut[-1] ; rgb1 = self.GetCellRGB(r1,c)
      
      for r in rowscut[1:-1]:
        self.SetLEDCell(r,c, RgbMix(rgb0,rgb1,r-r0,r1-r0) )
  
  def GradDiag (self,event):
    "Schraeger Gradient 45 Grad, ganze Flaeche"
    ##DOKU: 45 Grad ist nicht nur einfacher als Koordinatentransformation
    ##  in beliebigem Winkel, das ist Absicht
    ##  sonst waere schon fuer eine Box von 6*7 praktisch jede Farbe anders
    
    rows,cols = self.FillCheckMsg()	#fertige Zeilen & Spaltenlisten
    if not rows: return			#leer falls keine richtige Box
    
    ##TRICK: flache Liste aller relevanten Punkte
    points = map(
      lambda r: map( lambda c: (r,c), cols ),
      rows
    )
    points = sum(points,[])
    if len(points)<=2: return		#die meisten kleinen Boxen machen Sinn, nur 2 Zellen nicht
    
    ##ACHTUNG: erste und letzte gueltige Farbe suchen, 
    ##  und einfach so tun, als wenn sie in der Ecke waere
    rgb0 = None ; rgb1 = None
    for r,c in points:
      if self.GetCellValue(r,c)!="------":
        rgb0 = self.GetCellRGB(r,c)
        break
    
    points.reverse()			#und jetzt von hinten/unten...
    for r,c in points:
      if self.GetCellValue(r,c)!="------":
        rgb1 = self.GetCellRGB(r,c)
        break
    
    if not rgb0 or not rgb1: return	#nur ------ im Block
    
    ##DOKU: fuer die 45 Grad Diagonalen genuegt die Summe der Koordinaten r+c
    ##      allerdings eventuell gekippt, also r-c
    kipp = (rows[0]<=rows[-1]) != (cols[0]<=cols[-1])	#verschiedene Sortierung, gekippt !
    if kipp:
      diag0 = rows[ 0]-cols[ 0]
      diag1 = rows[-1]-cols[-1]
    else:
      diag0 = rows[ 0]+cols[ 0]
      diag1 = rows[-1]+cols[-1]
    
    for r in rows:			#Schleife ueber beide Achsen
      for c in cols:			#(alle Zellen, auch die 2 aeusseren)
        diag = ifop( kipp, (r-c), (r+c) )
        self.SetLEDCell(r,c, RgbMix(rgb0,rgb1, diag-diag0,diag1-diag0) )
  
  def MoveHori (self,event):
    #@@@MOVE
    pass
  
  def MoveVerti(self,event):
    #@@@MOVE
    pass
  
  def MoveDiag (self,event):
    #@@@MOVE
    pass

  
#----------------------------------------------------------------------
#FARBBUTTONS fuer den rechten Rand

class HexColourButton (wx.lib.colourselect.ColourSelect):
  "kleine Variante von ColourSelect, die hex spricht und auch hex als Label zeigt"
  
  def __init__(self, parent,id, hex,size):
    wx.lib.colourselect.ColourSelect.__init__(self, parent,id, hex, hex2rgb(hex), size = size)
    self.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.OnSelectColour)
  
  def OnSelectColour(self, event):
    colour = event.GetValue()
    self.SetLabel( col2hex( colour ) )	#das macht kein Refresh :-(
    self.SetColour( colour )		#deshalb muss ich die gleiche Farbe nochmal reingeben
  
  #-------------------------------------------------
  #auch hier gilt hexstring als Esperanto
  def GetHex(self):
    return col2hex( self.GetColour() )
  def SetHex(self,hex):
    self.SetLabel( hex )		#Label und Farbe...
    self.SetColour( hex2col(hex) )	#deshalb muss ich die gleiche Farbe nochmal reingeben


#----------------------------------------------------------------------
#HAUPTFENSTER: GRID + Menues + Bars ...

def MyToolAdd(win,target, text,help, pic, action, oldid=None):
  "kleiner Helper: ein Tool in 1 oder mehrere Menues und Toolbars einfuegen"
  
  #MULTI-TARGET: in alle gleich einfuegen
  if type(target)==types.ListType:
    #NEU: dann auch mehrere ID's returnen (oldid macht nur fuer einen Sinn...)
    return map(lambda t: MyToolAdd(win,t, text,help, pic, action, oldid), target)
  
  if oldid is None: newid = wx.NewId()
  else:             newid = oldid
  
  #MENU: Zeile mit Icon
  if isinstance(target,wx.Menu):
    item = wx.MenuItem(target, newid, text, help)
    if pic: item.SetBitmap(wx.Bitmap( pic, wx.BITMAP_TYPE_ANY ))
    target.AppendItem(item)	##WXBUG: Bitmap muss man vor Append einstellen
    
    if oldid is None: wx.EVT_MENU(win, newid, action)	#sonst bestehende Bindung annehmen
    return newid
  
  #TOOLBAR: nur ein Icon
  if isinstance(target,wx.ToolBar):
    target.AddSimpleTool(newid, wx.Bitmap( pic, wx.BITMAP_TYPE_ANY ), text,help)
    
    if oldid is None: win.Bind(wx.EVT_TOOL,action,id=newid)	#sonst bestehende Bindung annehmen
    return newid
  
  raise AssertionError,"Target fuer MyToolAdd muss Menu,Toolbar oder Liste davon sein"

class MyFrame (wx.Frame):
  def __init__(self, parent, id, title):
    wx.Frame.__init__(self, parent, id, title, size=(800,600))
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    self.CreateStatusBar()		#nicht aktiv schreiben (SetStatusText), aber fuer rollover-Hilfe
    					##LATER: Warnings und Infos hierher ?
    
    icon = wx.Icon("icons/ledp.ico",wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)
    
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
    ##  colourbutton2 = HexColourButton(self,-1, "FF8080", (60, 60))
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
    
    MyToolAdd(self,[menu,toolBar], "&Save\tCtrl-S", "Save LED program", "icons/file-save.gif", self.OnSave)
    
    menu.AppendSeparator()
    MyToolAdd(self,menu, "&Import Image", "Read Szene from Image file","icons/file-bmpin.gif", self.ImageImport)
    MyToolAdd(self,menu, "&Export Image", "Save Szene to BMP file",    "icons/file-bmpex.gif", self.ImageExport)
    menu.AppendSeparator()
    MyToolAdd(self,menu, "e&Xit\tCtrl-Q", "Terminate the program",     "icons/file-exit.gif",  self.OnQuit)
    menuBar.Append(menu, "&File");
    ##ICONS WARTEN: file-load.gif, file-new.gif, file-saveas.gif
    
    #===== 2.Menue: Operationen auf der Szeneliste =====
    menu = wx.Menu()
    
    #verspaetetes Init, braucht die SzeneList
    global SZENEMOVES
    SZENEMOVES = [
      [ "&New",  "New Szene",       "icons/scene-new.gif", SzeneList.SzeneNew ],
      [ "&Dupl", "Duplicate Szene", "icons/scene-dup.gif", SzeneList.SzeneDupl ],
      [ "&Up",   "Move Up",         "icons/scene-up.gif",  SzeneList.SzeneMoveUp ],
      [ "d&Own", "Move Down",       "icons/scene-dn.gif",  SzeneList.SzeneMoveDn ],
      [ "de&L",  "Delete Szene",    "icons/scene-del.gif", SzeneList.SzeneDel ],
    ]
    
    #5 Szene-Moves genau wie im Popupmenu
    for move in SZENEMOVES:
      MyToolAdd(self,menu, *move)
    
    menuBar.Append(menu, "&Step");
    
    #===== 3.Menue: 3*3 Fill++-Operationen =====
    menu = wx.Menu()
    toolBar.AddSeparator()
    
    MyToolAdd(self,[menu,toolBar], "Fill &Hori", "Fill Horizontal", "icons/fill-hori.bmp",  TheGrid.FillHori)
    MyToolAdd(self,[menu,toolBar], "Fill &Verti","Fill Vertical",   "icons/fill-verti.bmp", TheGrid.FillVerti)
    MyToolAdd(self,[menu,toolBar], "Fill &Diag", "Fill Diagonal",   "icons/fill-diag.bmp",  TheGrid.FillDiag)
    
    MyToolAdd(self,[menu,toolBar], "Grad Hori",  "Grad Horizontal", "icons/grad-hori.bmp",  TheGrid.GradHori)
    MyToolAdd(self,[menu,toolBar], "Grad Verti", "Grad Vertical",   "icons/grad-verti.bmp", TheGrid.GradVerti)
    MyToolAdd(self,[menu,toolBar], "Grad Diag",  "Grad Diagonal",   "icons/grad-diag.bmp",  TheGrid.GradDiag)
    
    MyToolAdd(self,[menu,toolBar], "Move Hori",  "Move Horizontal", "icons/move-hori.bmp",  TheGrid.MoveHori)
    MyToolAdd(self,[menu,toolBar], "Move Verti", "Move Vertical",   "icons/move-verti.bmp", TheGrid.MoveVerti)
    MyToolAdd(self,[menu,toolBar], "Move Diag",  "Move Diagonal",   "icons/move-diag.bmp",  TheGrid.MoveDiag)
    
    menuBar.Append(menu, "&Area");
    
    self.SetMenuBar(menuBar)
    toolBar.Realize()
    
    
    #--------------------------------------------------
    #ALLES DRIN, ABSCHLUSS
    
    self.Fit()			#self.Layout + self.SetClientSize(minsize...)
    self.Show(True)
  
  
  #------------------------------------------------------------
  #ENDE + Save...
  
  def OnQuit(self, _): #event)
    "das ist die aktive Quit-Aktion 'bitte mache Quit', Rest passiert in OnCloseWindow"
    self.Close()
  
  def OnSave(self, event=None):
    #event=None heisst aus OnCloseWindow indirekt gerufen (ist mir hier egal...)
    
    #1.zuerst aktuelles Bild sauber mit dazu...
    ##ACHTUNG: die Farbwerte sind zeitweilig nur im Grid selber, jetzt abholen
    ##         (ausser wenn mit event=None selber aus Quit gerufen)
    if event: SzeneList.SaveGrid()
    
    #2.das MainProg sichern
    try:
      MainProg.Save()
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
  
  def OnCloseWindow(self,event):
    "[x] Button gedrueckt oder Quit selber gerufen -> ich kann entscheiden"
    
    #erstmal aus der GUI zurueck ins Programm, sonst stimmt needsave nicht !
    SzeneList.SaveGrid()
    
    #Editor-Metapher, Rueckfrage falls nicht gespeichert
    if MainProg.needsave:
      #wenn Veto verboten ist, dann gar kein Cancel erst anzeigen :-)
      cancel = ifop(event.CanVeto(), wx.CANCEL, 0)
      
      #Dialog anzeigen: JA-Sichern, NEIN-Ende, CANCEL-Ende abbrechen
      dlg = wx.MessageDialog(MainWin, "Vor dem Beenden Aenderungen speichern ?","Check",
                             wx.YES_NO|cancel|wx.ICON_QUESTION)
      ret = dlg.ShowModal()
      dlg.Destroy()
      
      #Cancel heisst Veto, das ist hier sicher erlaubt
      if ret == wx.ID_CANCEL:
        event.Veto()
        return
      
      #Sichern (ID_YES) oder nicht (ID_NO), aber auf jeden Fall ins Ende weiterlaufen
      if ret == wx.ID_YES:
        self.OnSave()
    
    #das normale Ende (not dirty, nach Save, ohne Save)
    self.Destroy()
  
  #------------------------------------------------------------
  #Image Import und Export in aktuelle Szene
  
  def ImageImport(self,event):
    "Read Szene from Image file"
    
      #vorher Grid in die Szene, falls das Bild nicht alles ueberschreibt
    SzeneList.SaveGrid()
      #File laden
    wximage = wx.Image( "test.bmp", wx.BITMAP_TYPE_ANY )
      #Szene liest das Image aus
    SzeneList.CurrSzene().SetImage(wximage)
      #von der Szene in den Grid
    TheGrid.LoadFarben()
  
  def ImageExport(self,event):
    "Save Szene to BMP file"
    
      #vom Grid in die Szene
    SzeneList.SaveGrid()
      #aus der Szene ein Image erzeugen
    wximage = SzeneList.CurrSzene().GetImage()
      #File schreiben (nur BMP)
    wximage.SaveFile("test.bmp", wx.BITMAP_TYPE_BMP)


#----------------------------------------------------------------------
#HAUPTPROGRAMM: 1.Objektstrukturen -> 2.GUI

class MyApp(wx.App):
  def OnInit(self):
    #--------------------------------------------------
    #1.SCHRITT "DATEN" - alle internen Strukturen aufbauen
    
    #wie ueblich zur EXE wechseln
    mydir = os.path.dirname( os.path.abspath(sys.argv[0]) )
    os.chdir( mydir )
    
    try:
      #die interne Struktur zum LED Programm aus dem Standardfile aufbauen
      global MainProg
      MainProg = LedProgramm(LedProgName)
    
    except LedDataException,ex:
      LogMessageDialog(MSG_ERROR, str(ex))
      return False	#in diesem Falle kein Fenster erzeugen...
    
    #--------------------------------------------------
    #2.SCHRITT "GUI" - die Fenster zur Anzeige aufbauen
    global MainWin
    MainWin = MyFrame(None, -1, "LED-Wall-Editor (Prototyp)")
    self.SetTopWindow(MainWin)
    return True		#return False oder Exception ist schon oben passiert

#main nicht aufrufen, wenn ich importiert sein sollte
if __name__ == "__main__":
  app = MyApp(redirect=False)
  app.MainLoop()
else:
  raise NotImplementedError, "Der LED-EDITOR ist nicht als Modul gedacht"
