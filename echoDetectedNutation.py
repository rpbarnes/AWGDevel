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

averages = 64 # Averages on Scope
a.acquire(averages)


### Define Pulse Parameters ###
dx = 500e-9 # Delay at start
d1 = 1000e-9 # delay between first and second pulse
d2 = 500e-9 # delay between 90-pulse and 180-pulse (2nd and 3rd pulses)
p0 = 1e-9 # varying pulse length, starting delay for this pulse
p1 = 16e-9 # 90-pulse length, 2nd pulse
p2 = 32e-9 # 180-pulse length, 3rd pulse


p30 = 8e-9 # increment in pulse length for first pulse


### Pulse Amplitudes ###
a0 = 1.0 # amplitude of variable length pulse
a1 = 1.0 # amplitude of 90-pulse
a2 = 1.0 # amplitude of 180-pulse


npts = 32 # number of points in nutation experiment

dataShape = ndshape([npts,1000],['T','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')
TArray = np.arange(p0,p30*npts+p0,p30)

for TIx,TValue in enumerate(TArray):
    print('%i of %i'%(TIx+1,len(TArray)))

    p0 = TValue # set p0

    # Pulse Sequence #
    modFreq = -300e6
    wave = p.make_highres_waveform([('delay',dx),
        ('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
        ('delay',d1-p0),
        ('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x),r_[0,p1]),
        ('delay',d2),
        ('function',lambda x: a2*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p2]),
        ('delay',9.5e-6 - dx - d1 - d2 - p0 - p1 - p2)],
        resolution=1e-9)
    

    p.synthesize(wave,autoSynthSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
    
    d0 = 40e-9 #Offset from agilent scope

    agilentPosition = dx + p0 + (d1 - p0) + 1.5*p1 + 2*d2 + 1.5*p2 + d0

    a.position(agilentPosition)

    dataTemp = a.Waveform_auto()

    dataMatrix['T',TIx] = dataTemp

a.run()

dataMatrix.labels(['T','t'],[TArray,dataTemp.copy().getaxis('t')])
figure()
image(dataMatrix)

dataMatrixFt = dataMatrix.copy().ft('t',shift = True)
figure()
image(dataMatrixFt.runcopy(abs))

centerFrequency = 300e6
bandpassFilter = 100e6
dataMatrixFt['t',lambda x: bandpassFilter/2. < abs(x-centerFrequency)] = 0

nutation = dataMatrixFt.copy().runcopy(abs).sum('t') 

figure()
plot(nutation)



show()


