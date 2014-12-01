# 
# Make the recorder show the fft.
sudo zypper in python-PyAudio python-matplotlib python-scipy 
sudo zypper in python-numpy-1.9.1 python-qt4 python-qwt5
python SWHRecorder/realTimeAudio.py
# CTRL-C


# vi SWHRecorder/realTimeAudio.py
#    # trimBy=20: max=1200Hz
#    # trimBy=10: max=2500Hz
#    # trimBy=8:  max=3000Hz
#    # trimBy=7:  max=3500Hz
#    # trimBy=5:  max=5000Hz
#    xs,ys=SR.fft(logScale=False, trimBy=7, divBy=2000)

