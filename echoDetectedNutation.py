from matlablike import *
import numpy as np
close('all')
import synthesize as s
p = s.pulsegen()
import gpib_eth as g

try:
    yig
except:
    from yig import _yig as yig
try:
    fc
except:
    fc = g.field_controller()
try:
    a
except:
    a = g.agilent()

averages = 16 # Averages on Scope
a.acquire(averages)


### Define Pulse Parameters ###
dx = 500e-9 # Delay at start
d1 = 1000e-9 # delay between first and second pulse
d2 = 400e-9 # delay between 90-pulse and 180-pulse (2nd and 3rd pulses)
p0 = 1e-9 # varying pulse length, starting delay for this pulse
p1 = 16e-9 # 90-pulse length, 2nd pulse
p2 = 32e-9 # 180-pulse length, 3rd pulse

p30 = 8e-9 # increment in pulse length for first pulse

npts = 32 # number of points in nutation experiment

dataShape = ndshape([npts,1000],['T','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')
TArray = np.arange(p0,p30*npts+p0,p30)

for TIx,TValue in enumerate(TArray):
    print('%i of %i'%(TIx+1,len(TArray)))

    p0 = TValue # set p0

    # Pulse Sequence #
    wave = p.make_highres_waveform([('delay',dx),('rect','x',p0),('delay',d1 - p0),('rect','x',p1),('delay',d2),('rect','x',p2),('delay',9e-6 - dx - d1 - d2 - p0 - p1 - p2)],resolution=1e-9)

    modFreq = -300e6
    modulation = nddata(exp(1j*2*pi*modFreq*wave.getaxis('t'))).rename('value','t').labels('t',wave.getaxis('t'))

    modWave = modulation.copy() * wave.copy()

#    p.synthesize(modWave,longDelay = 1e-3)
    p.synthesize(modWave,autoTWTSwitch = True, longDelay = 1e-3)
    

    d0 = 40e-9 #Offset from agilent scope

    agilentPosition = dx + p0 + (d1 - p0) + 1.5*p1 + 2*d2 + 1.5*p2 + d0

    a.position(agilentPosition)

    dataTemp = a.Waveform_auto()

    dataMatrix['T',TIx] = dataTemp

dataMatrix.labels(['T','t'],[TArray,dataTemp.copy().getaxis('t')])
a.run()

image(dataMatrix)

show()


