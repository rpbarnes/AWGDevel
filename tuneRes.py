import synthesize as s
from matlablike import *
p = s.pulsegen() 

try:
    yig
except:
    from yig import _yig as yig

wave = p.make_highres_waveform([('delay',600e-9),('rect','x',10e-9),('delay',10e-6-610e-9)])

yig.set_mwfreq(9.4e9)
modFreq = 300e6
modulation = nddata(exp(1j*2*pi*modFreq*wave.getaxis('t'))).rename('value','t').labels('t',wave.getaxis('t'))
p.synthesize(wave*modulation,autoSynthSwitch=True,autoTWTSwitch=True,longDelay=10e-4)


