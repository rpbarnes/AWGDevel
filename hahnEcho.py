from matlablike import *
import numpy as np
close('all')
import synthesize as s
import gpib_eth as g
import time

import paramsClient
from paramsClient import recvParams,recvDate,recvTime

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
try:
    p
except:
    p = s.pulsegen()


### Import Pulse Parameters from GUI ###
fromGui = True
if fromGui:
    data = recvParams()

    try:
        exec('paramsDict = ' + data)
        print('paramsDict:')
        for key in paramsDict:
            print key, ' : ', paramsDict[key]
    except:
        pass
    
    averages = paramsDict['averages'] # averages on scope
    p0 = paramsDict['p0']             # 90-pulse Length
    p1 = paramsDict['p1']             # 180-pulse Length

    a0 = paramsDict['a0']             # amplitude of 90-pulse
    a1 = paramsDict['a1']             # amplitude of 180-pulse

    dx =  paramsDict['dx']            # delay at start
    d1 =  paramsDict['d1']            # delay between 90- and 180- pulses
    d0 = paramsDict['d0']             # Offset from Agilent scope
    modFreq =  paramsDict['modFreq']  # Pulse frequency offset from carrier
    bandpassFilter = paramsDict['bandpassFilter'] # bandpass filter for data
    phaseCycle = paramsDict['phaseCycle'] # type of phase cycle
    scans = paramsDict['scans'] # number of repeats

else:
    # If Gui is turned off #
    dx = 500e-9 # Delay at start
    d1 = 500e-9 # delay between 90- and 180-pulses
    p0 = 32e-9 # 90-pulse length
    p1 = 32e-9 # 180-pulse length

    d0 = 60e-9 #Offset from agilent scope

    ### Pulse Amplitudes ###
    a0 = 0.5 # amplitude of 90-pulse
    a1 = 1.0  # amplitude of 180-pulse

    modFreq = -308e6
    bandpassFilter = 500e6
    phaseCycle = '2-step'

    averages = 64 # Averages on Scope
    scans = 1 # experiment repeats

    ### Define Pulse Parameters ###
    paramsDict = {}
    paramsDict['averages'] = averages # averages on scope
    paramsDict['p0'] = p0             # 90-pulse Length
    paramsDict['p1'] = p1             # 180-pulse Length

    paramsDict['a0'] = a0             # amplitude of 90-pulse
    paramsDict['a1'] = a1             # amplitude of 180-pulse

    paramsDict['dx'] = dx             # delay at start
    paramsDict['d1'] = d1             # delay between 90- and 180- pulses
    paramsDict['d0'] = d0             # Offset from Agilent scope
    paramsDict['modFreq'] = modFreq   # Pulse frequency offset from carrier
    paramsDict['bandpassFilter'] = bandpassFilter


# Determine Phase Cycle #
if phaseCycle == '2-step':
    # 2-step on 90-pulse
    ph0 = np.r_[0,np.pi]
    ph1 = np.r_[0]

    rph0 = np.r_[0,np.pi]
    rph1 = np.r_[0]
elif phaseCycle == '4-step':
    # 4-step on 90-pulse
    ph0 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
    ph1 = np.r_[0]

    rph0 = np.r_[0,-np.pi/2.,-np.pi,-3.*np.pi/2.]
    rph1 = np.r_[0]
elif phaseCycle == '16-step':
    ph0 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
    ph1 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]

    rph0 = np.r_[0,-np.pi/2.,-np.pi,-3.*np.pi/2.]
    rph1 = np.r_[0,np.pi,0,np.pi]

else: # if something else, assume 'none'
    ph0 = np.r_[0]
    ph1 = np.r_[0]

    rph0 = np.r_[0]
    rph1 = np.r_[0]

    phaseCycle = 'none'
    phaseCycle = paramsDict['phaseCycle']


# Add Experiment Specific tags to paramsDict #
paramsDict['exp'] = ['HahnEcho']
paramsDict['epochTime'] = time.time()
paramsDict['time'] = recvTime()
paramsDict['date'] = recvDate()


# Pre-allocate data array and add parameters #
dataShape = ndshape([1000],['t'])
data = dataShape.alloc(dtype = 'complex')
data.other_info = paramsDict

# set scope averages
a.acquire(averages)

for scan in np.arange(scans):
    agilentPosition = dx + 2*d1 + 1.5*p0 + p1 + d0
    a.position(agilentPosition)
    for ph0Ix,ph0Value in enumerate(ph0):
        for ph1Ix, ph1Value in enumerate(ph1):

            # Pulse Sequence #
            wave = p.make_highres_waveform([('delay',dx),
            ('function',lambda x: a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
            ('delay',d1),
            ('function',lambda x: a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),
            ('delay',9.5e-6 - dx - d1 - p0 - p1)],
            resolution=1e-9)

            # Send pulse to DAC board
            p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)


            # Pull data from scope
            dataTemp = a.Waveform_auto()

            # Process data: Shift to on-resonance and apply bandpass filter
            dataTemp.ft('t')
            dataTemp['t',lambda x: abs(x+modFreq) > bandpassFilter/2.] = 0 
            dataTemp.ift('t')
            dataTemp.data *= np.exp(1j*2*np.pi*modFreq*dataTemp.getaxis('t').copy())

            # Compute Receiver phase and apply
            receiverPhase = rph0[ph0Ix]+rph1[ph1Ix]
            dataTemp.data *= np.exp(1j*receiverPhase)

            # Add to data array
            data += dataTemp

a.run()

dataProcessed = data.copy()
phase = np.arctan(np.sum(np.imag(dataProcessed.copy().data))/np.sum(np.real(dataProcessed.copy().data)))

dataProcessed = data.copy()*np.exp(-1j*phase)
if np.sum(dataProcessed.runcopy(real).data) < 0:
    dataProcessed.data *= -1.

dataFt = dataProcessed.copy().ft('t',shift = True)
# NOTE: The following corrects the linear phase roll in frequency domain, but I'm not sure why
dataFt.data *= np.exp(-1j*np.pi*np.arange(len(dataFt.getaxis('t').copy())))
figure('Frequency domain Hahn Echo')
plot(dataFt.runcopy(real),'b-',label = 'real')
plot(dataFt.runcopy(imag),'g-',label = 'imag')



figure('Phase Corrected Hahn Echo')
plot(dataProcessed.runcopy(real),'b-',label = 'real')
plot(dataProcessed.runcopy(imag),'g-',label = 'imag')
show()

