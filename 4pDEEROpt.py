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

averages = 64 # Averages on Scope
a.acquire(averages)

### Define Observe Pulse Parameters ###
dx = 500e-9  # Delay at start
d1 = 200e-9 # delay between 90-pulse and 180-pulse
d2 = 1000e-9 # delay between 2 observe 180-pulses
p0 = 32e-9   # (observe) 90-pulse length, 1st pulse
p1 = 32e-9   # (observe) 180-pulse length, 2nd and 4th pulse

d0 = 90e-9   # Offset from agilent scope

### Pulse Amplitudes ###
a0 = 0.05    # amplitude of 90-pulse, 1st pulse
a1 = 0.1    # amplitude of 180-pulse, 2nd and 4th pulse

# Modulation frequency for observe pulses
modFreq = -308e6

### ELDOR pulse parameters ###
pELDOR = 12e-9   # ELDOR pulse length, 3nd pulse
aELDOR = 1.0     # amplitude of ELDOR pulse, 3nd pulse
dELDOR = 500e-9   # Starting delay for ELDOR pulse after 90-pulse, changes during loop
d30 = 12e-9      # time increment in ELDOR pulse position
freqOffsetELDOR = -60e6 # frequency offset of ELDOR pulse from modFreq, in Hz

nptsELDOR = 10 # number of points in ELDOR trace

#delayELDOR = np.r_[dELDOR:(nptsELDOR-1)*d30+dELDOR:1j*nptsELDOR]
ampELDOR = np.r_[0.:aELDOR:1j*nptsELDOR]

scans = 1 # number of DEER traces summed together

bandpassFilter = 500e6 # filter for data
    

dataShape = ndshape([len(ampELDOR),1000],['aELDOR','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')

doPhaseCycle = True
phaseCycle = '16-step'
if doPhaseCycle:
    if phaseCycle == '16-step':

        # Phase for each Pulse
        ph1 = np.r_[0,np.pi]
        ph2 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
        ph3 = np.r_[0,np.pi]
        ph4 = np.r_[0]

        # Receiver Phase for each pulse
        rph1 = np.r_[0,np.pi]
        rph2 = np.r_[0,np.pi,0,np.pi]
        rph3 = np.r_[0,0]
        rph4 = np.r_[0]
        

else:
        ph1 = np.r_[0]
        ph2 = np.r_[0]
        ph3 = np.r_[0]
        ph4 = np.r_[0]

        rph1 = np.r_[0]
        rph2 = np.r_[0]
        rph3 = np.r_[0]
        rph4 = np.r_[0]


# set agilent position (does not depend on sequence)
agilentPosition = dx + 0.5*p0 + p1 + 2*d2 + d0
a.position(agilentPosition)

for scan in range(scans):

    for ampIx, amp in enumerate(ampELDOR): 
        print('%i of %i'%(scan+1,scans))
        print('\t%i of %i'%(ampIx+1,len(ampELDOR)))
        aELDOR = amp

        # Phase Cycle #
        
        receiverPhaseIx = 0
        for ph1Ix,ph1Value in enumerate(ph1):
            print('\t%i of %i'%(ph1Ix+1,len(ph1)))
            for ph2Ix,ph2Value in enumerate(ph2):
                print('\t\t%i of %i'%(ph2Ix+1,len(ph2)))
                for ph3Ix,ph3Value in enumerate(ph3):
                    print('\t\t\t%i of %i'%(ph3Ix+1,len(ph3)))
                    for ph4Ix,ph4Value in enumerate(ph4):
                        print('\t\t\t\t%i of %i'%(ph4Ix+1,len(ph4)))
#                        print('Phase Cycle: %i of %i'%(receiverPhaseIx+1,len(ph1)*len(ph2)*len(ph3)*len(ph4)))

                        # Pulse Sequence #
                        wave = p.make_highres_waveform([
                            ('delay',dx),
                            ('function',lambda x: a0*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p0]),
                            ('delay',d1),
                            ('function',lambda x: a1*np.exp(1j*ph2Value)*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),
                            ('delay',dELDOR),
                            ('function',lambda x: aELDOR*np.exp(1j*ph3Value)*np.exp(1j*2*np.pi*(freqOffsetELDOR+modFreq)*x),r_[0,pELDOR]),
                            ('delay',d2 - dELDOR - pELDOR),
                            ('function',lambda x: a1*np.exp(1j*ph4Value)*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),
                            ('delay',9.5e-6 - dx - d1 - d2 - p0 - 2*p1)],
                            resolution=1e-9)


                        p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
                        

                        dataTemp = a.Waveform_auto()
                        dataTemp.ft('t')
                        dataTemp['t',lambda x: abs(x+modFreq) > bandpassFilter/2.] = 0
                        dataTemp.ift('t')
                        dataTemp.data *= np.exp(1j*2*np.pi*modFreq*dataTemp.getaxis('t').copy())

                        receiverPhase = rph1[ph1Ix]+rph2[ph2Ix]+rph3[ph3Ix]+rph4[ph4Ix]
#                        dataTemp.data = np.real(dataTemp.data)*asg1[receiverPhase] + 1j*np.imag(dataTemp.data)*bsg1[receiverPhase]
                        dataTemp.data = dataTemp.data*np.exp(1j*receiverPhase)


                        dataMatrix['aELDOR',ampIx] += dataTemp

                        receiverPhaseIx += 1 #step the receiver phase

dataMatrix.labels(['aELDOR','t'],[ampELDOR,dataTemp.copy().getaxis('t')])


a.run()


aELDOR = ampELDOR[0]
paramDict = {
    'averages' : averages, # Averages on Scope
    'dx' : dx,  # Delay at start
    'd1' : d1, # delay between 90-pulse and 180-pulse
    'd2' : d2,  # delay between 2 observe 180-pulses
    'p0' : p0,   # (observe) 90-pulse length, 1st pulse
    'p1' : p1,   # (observe) 180-pulse length, 3rd pulse
    'd0' : d0, #Offset from agilent scope
    'a0' : a0,    # amplitude of 90-pulse, 1st pulse
    'a1' : a1,    # amplitude of 180-pulse, 3rd pulse
    'pELDOR' : pELDOR,   # ELDOR pulse length, 2nd pulse
    'aELDOR' : pELDOR,     # amplitude of ELDOR pulse, 2nd pulse
    'dELDOR' : dELDOR,   # Starting delay for ELDOR pulse after 90-pulse, changes during loop
    'd30' : d30,      # time increment in ELDOR pulse position
    'freqOffsetELDOR' : freqOffsetELDOR, # frequency offset of ELDOR pulse, in Hz
    'nptsELDOR' : nptsELDOR, # number of points in ELDOR trace
    'modFreq' : modFreq,
    'scans' : scans, # number of summed DEER traces
    'bandpassFilter' : bandpassFilter
    }


dataMatrix.other_info = paramDict


figure('raw data')
image(dataMatrix)

dataMatrixProcessed = dataMatrix.copy()

# Integration window for echo
integrationWindow = 100e-9
dataMatrixProcessed['t',lambda x: abs(x-np.mean(dataMatrixProcessed.getaxis('t'))) > integrationWindow/2.] = 0


figure('Integration Window')
image(dataMatrixProcessed)


eldorTrace = dataMatrixProcessed.copy().sum('t')
figure('ELDOR Trace')
plot(eldorTrace.runcopy(real),label = 'real')
plot(eldorTrace.runcopy(imag),label = 'imag')
plot(eldorTrace.runcopy(abs),label = 'abs')

show()


