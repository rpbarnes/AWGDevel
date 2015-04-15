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
d1 = 400e-9 # delay between 90- and 180-pulses
p0 = 16e-9 # 90-pulse length
p1 = 100e-9 # 180-pulse length

### Pulse Amplitudes ###
a0 = 1.0 # amplitude of 90-pulse
a1 = .32 # amplitude of 180-pulse


# Pulse Sequence #
modFreq = -300e6
wave = p.make_highres_waveform([('delay',dx),('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),('delay',d1),('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),('delay',9.5e-6 - dx - d1 - p0 - p1)],resolution=1e-9)

p.synthesize(wave,autoSynthSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
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

