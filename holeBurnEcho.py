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
dx = 500e-9  # Delay at start
d1 = 500e-9 # delay between end of first and start of second pulse
d2 = 500e-9  # delay between 90-pulse and 180-pulse (2nd and 3rd pulses)
p0 = 200e-9  # Pump pulse, 1st pulse
p1 = 6e-9   # 90-pulse length, 2nd pulse
p2 = 12e-9   # 180-pulse length, 3rd pulse

d0 = 60e-9 #Offset from agilent scope

### Pulse Amplitudes ###
a0 = 0.08 # amplitude of pump pulse, 1st pulse
a1 = 1.0 # amplitude of 90-pulse, 2nd pulse
a2 = 1.0 # amplitude of 180-pulse, 3rd pulse


# Pulse Sequence #
modFreq = -308e6
wave = p.make_highres_waveform([('delay',dx),
    ('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
    ('delay',d1),
    ('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x),r_[0,p1]),
    ('delay',d2),
    ('function',lambda x: a2*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p2]),
    ('delay',9.5e-6 - dx - d1 - d2 - p0 - p1 - p2)],
    resolution=1e-9)


p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)



agilentPosition = dx + p0 + d1 + 1.5*p1 + 2*d2 + 1.0*p2 + d0

a.position(agilentPosition)

data = a.Waveform_auto()

paramDict = {
    'dx' : dx, # Delay at start
    'd1' : d1, # delay between end of first and start of second pulse
    'd2' : d2, # delay between 90-pulse and 180-pulse (2nd and 3rd pulses)
    'p0' : p0, # Pump pulse, 1st pulse
    'p1' : p1, # 90-pulse length, 2nd pulse
    'p2' : p2, # 180-pulse length, 3rd pulse
    'd0' : d0, # Offset from agilent scope
    'a0' : a0, # amplitude of pump pulse, 1st pulse
    'a1' : a1, # amplitude of 90-pulse, 2nd pulse
    'a2' : a2, # amplitude of 180-pulse, 3rd pulse
    'modFreq' : modFreq
    }

data.other_info = paramDict

a.run()

### Create New nddata for processing ###
dataFt = data.copy().ft('t') # don't use shift here

bandpassFilter = 500e6

dataFt['t',lambda x: abs(x+modFreq) > bandpassFilter/2.] = 0

dataProcessed = dataFt.copy().ift('t')
dataProcessed.data *= np.exp(1j*2*np.pi*modFreq*dataProcessed.getaxis('t').copy())

dataFt = dataProcessed.copy().ft('t',shift = True)

figure()
plot(dataProcessed.runcopy(real),'b-',label = 'real')
plot(dataProcessed.runcopy(imag),'g-',label = 'imag')

figure()
#plot(dataFt.runcopy(real),'b-',label = 'real')
#plot(dataFt.runcopy(imag),'g-',label = 'imag')
plot(dataFt.runcopy(abs),'g-',label = 'imag')
show()
