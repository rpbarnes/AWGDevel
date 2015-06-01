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

averages = 1024 # Averages on Scope
a.acquire(averages)


### Define Pulse Parameters ###
dx = 500e-9  # Delay at start
d1 = 500e-9  # delay between 90- and 180-pulses
p0 = 100e-9   # 90-pulse length
p1 = 100e-9   # 180-pulse length

d0 = 40e-9   #Offset from agilent scope

### Pulse Amplitudes ###
a0 = 0.25 # amplitude of 90-pulse, A-spin
a1 = 0.5  # amplitude of 180-pulse, A-spin
a2 = 0.0  # amplitude of 180-pulse, B-spin

### Excitation Frequency Offset for B-spins ###
pulseFreqOffset = 50e6 # excitation frequency of B-spins offset from A-spins


### Check to make sure pulse amplitude will not exceed 1 ###
if (a1 + a2) > 1.0:
    print '*'*50
    print('\tWARNING!!!\n\ta1 + a2 > 1.0\n\tautomatically normalizing a1 and a2')
    totalAmplitude = a1 + a2
    a1 /= totalAmplitude
    a2 /= totalAmplitude
    print('\ta1 = %0.2f; a2 = %0.2f'%(a1,a2))
    print '*'*50



# Pulse Sequence #
modFreq = -308e6
wave = p.make_highres_waveform([('delay',dx),
    ('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
    ('delay',d1),
    ('function', lambda x: a1*np.exp(1j*2*np.pi*modFreq*x) + a2*np.exp(1j*2*np.pi*(modFreq+pulseFreqOffset)*x),np.r_[0,p1]),
    ('delay',9.5e-6 - dx - d1 - p0 - p1)],
    resolution=1e-9)

p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)


agilentPosition = dx + 2*d1 + 1.5*p0 + p1 + d0

a.position(agilentPosition)

data = a.Waveform_auto()

paramDict = {
    'dx' : dx, # Delay at start
    'd1' : d1, # delay between end of first and start of second pulse
    'p0' : p0, # Pump pulse, 1st pulse
    'p1' : p1, # 90-pulse length, 2nd pulse
    'd0' : d0, # Offset from agilent scope
    'a0' : a0, # amplitude of pump pulse, 1st pulse
    'a1' : a1, # amplitude of 90-pulse, 2nd pulse
    'a2' : a2, # amplitude of 180-pulse, 3rd pulse
    'modFreq' : modFreq,
    'pulseFreqOffset' : pulseFreqOffset,
    'averages' : averages
    }


data.other_info = paramDict

a.run()

### Create New nddata for processing ###
dataFt = data.copy().ft('t') # don't use shift here

bandpassFilter = 500e6

dataFt['t',lambda x: abs(x+modFreq) > bandpassFilter/2.] = 0

dataProcessed = dataFt.copy().ift('t')
dataProcessed.data *= np.exp(1j*2*np.pi*modFreq*dataProcessed.getaxis('t').copy())

phase = np.arctan(np.sum(np.imag(dataProcessed.copy().data))/np.sum(np.real(dataProcessed.copy().data)))
dataProcessed.data *= np.exp(-1j*phase) # doesn't work???
if np.sum(dataProcessed.runcopy(real).data) < 0:
    dataProcessed.data *= -1.

dataFt2 = dataFt.copy()
dataFt2.data *= np.exp(-1j*np.pi*np.arange(len(dataFt2.getaxis('t').copy())))
plot(dataFt2.runcopy(real),'b-',label = 'real')
plot(dataFt2.runcopy(imag),'g-',label = 'imag')


dataFt = dataProcessed.copy().ft('t',shift = True)

figure()
plot(dataProcessed.runcopy(real),'b-',label = 'real')
plot(dataProcessed.runcopy(imag),'g-',label = 'imag')
show()
