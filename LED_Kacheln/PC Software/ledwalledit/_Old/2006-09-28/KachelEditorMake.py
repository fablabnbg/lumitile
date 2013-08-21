#PYTHON 2 EXE: dieses Script macht aus KachelEditor.py im Arbeits-Verzeichnis
#  die KachelEditor.exe im Delivery-Verzeichnis
from distutils.core import setup
import py2exe
import sys

#mein Haupt-Script wird eigentlich von py2exe analysiert
#  hier hole ich mir nur die Versionsnummer
import KachelEditor

#if run without args, do 'py2exe'
if len(sys.argv) == 1:
  sys.argv.append("py2exe")

#DAS GEWUENSCHTE SETUP PY -> EXE
setup(
  options = {"py2exe": {
      "compressed": 1,
      "optimize": 2,
      "ascii": 1,
      "bundle_files": 1,		##WIN98 BUG: "bundle_files": 3,
      "dist_dir": "../DELIVERY",	##WIN98 BUG: "dist_dir": "../DELIVERY98",
    } },				##  LoadLibrary von Win9x kann nicht alle Tricks,
    					##  statt 3 Files muesste man hier 13 ausliefern :-(
  zipfile = None,
  
  windows = [{
      "script":		"KachelEditor.py",
      
      #icon resource
      "icon_resources":	[(1, "../DELIVERY/icons/ledp.ico")],
      
      #versioninfo resource
      "name":		"KachelEditor",
      "description":	"GUI for Editing Leber LED Tiles",
      "version":	"%.2f" % KachelEditor.LedOutputVersion,
      "company_name":	"Leber Systemtechnik",
      "copyright":	"(c) Leber Systemtechnik 2006",
    }]
  )

##NEU: 2 Zwischenfiles und 1 sinnlosen Output loeschen...
import os
print "\nMuellfiles werden geloescht ..."

try: os.remove("../DELIVERY/LastPath.ini")
except OSError: pass
try: os.remove("../DELIVERY/testplay.ledx")
except OSError: pass
try: os.remove("../DELIVERY/w9xpopen.exe")
except OSError: pass
