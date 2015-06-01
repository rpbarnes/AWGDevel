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

### NOTE: Add options for setup and nutation type experients ###

averages = 1024 # Averages on Scope
a.acquire(averages)

### Define Observe Pulse Parameters ###
dx = 500e-9  # Delay at start
d1 = 1000e-9 # delay between 90-pulse and 180-pulse
p0 = 32e-9   # (observe) 90-pulse length, 1st pulse
p1 = 32e-9   # (observe) 180-pulse length, 3rd pulse

d0 = 60e-9 #Offset from agilent scope

### Pulse Amplitudes ###
a0 = 0.375    # amplitude of 90-pulse, 1st pulse
a1 = 0.375    # amplitude of 180-pulse, 3rd pulse

### ELDOR pulse parameters ###
pELDOR = 12e-9   # ELDOR pulse length, 2nd pulse
aELDOR = 1.0     # amplitude of ELDOR pulse, 2nd pulse
dELDOR = 10e-9   # Starting delay for ELDOR pulse after 90-pulse, changes during loop
d30 = 6e-9      # time increment in ELDOR pulse position
freqOffsetELDOR = 65e6 # frequency offset of ELDOR pulse, in Hz

nptsELDOR = 100 # number of points in ELDOR trace

delayELDOR = np.r_[dELDOR:(nptsELDOR-1)*d30+dELDOR:1j*nptsELDOR]

scans = 1 # number of DEER traces summed together

### Verify ELDOR delay will not exceed d1 ###
if (d1 - np.max(delayELDOR) - pELDOR) < 1.0:
    print '*'*50
    print('\tWARNING!!!\n\tdELDOR + pELDOR > d1\n\tautomatically correcting length of ELDOR trace')
    nptsELDOR = int(np.floor((d1 - pELDOR - dELDOR) / d30))
    delayELDOR = np.r_[dELDOR:(nptsELDOR-1)*d30+dELDOR:1j*nptsELDOR]
    print('\tnptsELDOR = %i'%(nptsELDOR))
    print '*'*50
    
dataShape = ndshape([nptsELDOR,1000],['tELDOR','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')



for scan in range(scans):

    for delayIx, delay in enumerate(delayELDOR): 
        print('%i of %i'%(scan+1,scans))
        print('\t%i of %i'%(delayIx+1,len(delayELDOR)))
        dELDOR = delay

        # Pulse Sequence #
        modFreq = -308e6
        wave = p.make_highres_waveform([('delay',dx),
            ('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
            ('delay',dELDOR),
            ('function',lambda x: aELDOR*np.exp(1j*2*np.pi*(freqOffsetELDOR+modFreq)*x),r_[0,pELDOR]),
            ('delay',d1 - dELDOR - pELDOR),
            ('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),
            ('delay',9.5e-6 - dx - d1 - p0 - p1)],
            resolution=1e-9)


        p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
        


        agilentPosition = dx + 2*d1 + 1.5*p0 + p1 + d0

        a.position(agilentPosition)

        dataTemp = a.Waveform_auto()

        if scan == 0:
            dataMatrix['tELDOR',delayIx] = dataTemp
        else:
            dataMatrix['tELDOR',delayIx] += dataTemp

dataMatrix.labels(['tELDOR','t'],[delayELDOR,dataTemp.copy().getaxis('t')])


a.run()


dELDOR = delayELDOR[0]
paramDict = {
    'averages' : 1024, # Averages on Scope
    'dx' : dx,  # Delay at start
    'd1' : d1, # delay between 90-pulse and 180-pulse
    'p0' : p0,   # (observe) 90-pulse length, 1st pulse
    'p1' : p1,   # (observe) 180-pulse length, 3rd pulse
    'd0' : d0, #Offset from agilent scope
    'a0' : a0,    # amplitude of 90-pulse, 1st pulse
    'a1' : a1,    # amplitude of 180-pulse, 3rd pulse
    'pELDOR' : pELDOR,   # ELDOR pulse length, 2nd pulse
    'aELDOR' : aELDOR,     # amplitude of ELDOR pulse, 2nd pulse
    'dELDOR' : dELDOR,   # Starting delay for ELDOR pulse after 90-pulse, changes during loop
    'd30' : d30,      # time increment in ELDOR pulse position
    'freqOffsetELDOR' : freqOffsetELDOR, # frequency offset of ELDOR pulse, in Hz
    'nptsELDOR' : nptsELDOR, # number of points in ELDOR trace
    'modFreq' : modFreq
    }


dataMatrix.other_info = paramDict


figure('raw data')
image(dataMatrix)



# Fourier Transform
dataMatrixFt = dataMatrix.copy().ft('t')
# Digital Bandpass Filter
bandpassFilter = 500e6
dataMatrixFt['t',lambda x: abs(x+modFreq) > bandpassFilter/2.] = 0

dataMatrixProcessed = dataMatrixFt.copy().ift('t')
dataMatrixProcessed.data *= np.exp(1j*2*np.pi*modFreq*dataMatrixProcessed.getaxis('t').copy())


# Integration window for echo
integrationWindow = 100e-9
dataMatrixProcessed['t',lambda x: abs(x-np.mean(dataMatrixProcessed.getaxis('t'))) > integrationWindow/2.] = 0

figure()
image(dataMatrixProcessed)


eldorTrace = dataMatrixProcessed.copy().sum('t')
figure()
plot(eldorTrace.runcopy(real),label = 'real')
plot(eldorTrace.runcopy(imag),label = 'imag')
plot(eldorTrace.runcopy(abs),label = 'abs')

show()


