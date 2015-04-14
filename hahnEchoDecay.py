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

averages = 256 # Averages on Scope
a.acquire(averages)


### Define Pulse Parameters ###
dx = 500e-9 # Delay at start
d1 = 200e-9 # delay between 90- and 180-pulses
p0 = 16e-9 # 90-pulse length
p1 = 32e-9 # 180-pulse length

d30 = 8e-9
tauPoints = 11
tauArray = np.arange(d1,tauPoints*d30+d1,tauPoints)

doPhaseCycle = True
# define phase cycle

if doPhaseCycle:
    phcyc1 = np.arange(0,2*pi,4)
    phcyc2 = np.arange(0,2*pi,4)
else:
    phcyc1 = np.array([0])
    phcyc2 = np.array([0])



dataShape = ndshape([tauPoints,1000],['tau','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')

for 
# Pulse Sequence #
wave = p.make_highres_waveform([('delay',dx),('rect','x',p0),('delay',d1),('rect','x',p1),('delay',9e-6 - dx - d1 - p0 - p1)],resolution=1e-9)

modFreq = -300e6
modulation = nddata(exp(1j*2*pi*modFreq*wave.getaxis('t'))).rename('value','t').labels('t',wave.getaxis('t'))

modWave = modulation.copy() * wave.copy()

p.synthesize(modWave)#,longDelay = 1e-3)

d0 = 0e-9#Offset from agilent scope

# 942 ns = last pulse position
agilentPosition = dx + 2*d1 + 1.5*p0 + 1.5*p1 + d0

a.position(agilentPosition)


for fieldIx, fieldValue in enumerate(fieldArray):
    print('%i of %i'%(fieldIx+1,len(fieldArray)))
    fc.set_field(np.round(fieldValue,1))
    if fieldIx == 0:
        print('Waiting for field to stabilize')
        time.sleep(10)
    else:
        time.sleep(1)

    dataTemp = a.Waveform_auto()

    dataMatrix['field',fieldIx] = dataTemp

dataMatrix.labels(['field','t'],[fieldArray,dataTemp.copy().getaxis('t')])

a.run()

figure()
image(dataMatrix)

show()

