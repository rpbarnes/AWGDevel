from matlablike import *
import numpy as np
close('all')
import synthesize as s
p = s.pulsegen()
import gpib_eth as g

###NOTE: Code not finished###

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

fieldPoints = 11
fieldArray = np.arange(d1,tauPoints*d30+d1,tauPoints)

dataShape = ndshape([fieldPoints,1000],['field','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')



### Define Pulse Parameters ###
dx = 500e-9 # Delay at start
d1 = 400e-9 # delay between 90- and 180-pulses
p0 = 16e-9 # 90-pulse length
p1 = 32e-9 # 180-pulse length


# Pulse Sequence #
wave = p.make_highres_waveform([('delay',dx),('rect','x',p0),('delay',d1),('rect','x',p1),('delay',9e-6 - dx - d1 - p0 - p1)],resolution=1e-9)

modFreq = -300e6
#modFreq = 0e6
modulation = nddata(exp(1j*2*pi*modFreq*wave.getaxis('t'))).rename('value','t').labels('t',wave.getaxis('t'))

modWave = modulation.copy() * wave.copy()

p.synthesize(modWave,autoTWTSwitch = True, longDelay = 1e-3)
#p.synthesize(modWave,autoTWTSwitch = False, longDelay = 1e-3)

d0 = 40e-9#Offset from agilent scope

# 942 ns = last pulse position
agilentPosition = dx + 2*d1 + 1.5*p0 + 1.5*p1 + d0

a.position(agilentPosition)

data = a.Waveform_auto()

a.run()

figure()
plot(data.runcopy(real),'b-',label = 'real')
plot(data.runcopy(imag),'g-',label = 'imag')

show()


