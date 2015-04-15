from matlablike import *
import time
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
d1 = 20e-9 # delay between 90- and 180-pulses
p0 = 100e-9 # 90-pulse length
p1 = 100e-9 # 180-pulse length

### Pulse Amplitudes ###
a0 = .16 # amplitude of 90-pulse
a1 = .32 # amplitude of 180-pulse

### Delays ###
d30 = 24e-9 # sampling of interpulse delays 
tauPoints = 200 # total number of interpulse delays
tauArray = np.r_[d1:(tauPoints-1)*d30+d1:1j*tauPoints]

### phase cycle ###
doPhaseCycle = True
if doPhaseCycle:
    phcyc90 = np.r_[0.,np.pi/2.,np.pi,3.*np.pi/2.]
    phcyc180 = np.r_[0.,np.pi/2.,np.pi,3.*np.pi/2.]
#    phcyc180 = np.r_[0.]
    receiver90 = np.r_[0.,np.pi/2.,np.pi,3.*np.pi/2.]
#    receiver180 = np.r_[0.,-1*np.pi,0.,-1*np.pi]
    receiver180 = np.r_[0.,np.pi,0.,np.pi]
#    receiver180 = np.r_[0.]
else:
    phcyc90 = np.r_[0.]
    phcyc180 = np.r_[0.]
    receiver90 = np.r_[0.]
    receiver180 = np.r_[0.]


### Data Storage ###
dataShape = ndshape([tauPoints,len(phcyc90),len(phcyc180),1000],['tau','phcyc90','phcyc180','t'])
#dataShape = ndshape([tauPoints,1000],['tau','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')

startTime = time.time()

for tauIx, tauValue in enumerate(tauArray):
    print('%i of %i' %(tauIx+1,len(tauArray)))
    d1 = tauValue
    d0 = 40e-9#Offset from agilent scope
    # 942 ns = last pulse position
    agilentPosition = dx + 2*d1 + 1.5*p0 + 1.5*p1 + d0
    a.position(agilentPosition)
#    wave = p.make_highres_waveform([('delay',dx),('rect','x',p0),('delay',d1),('rect','x',p1),('delay',9e-6 - dx - d1 - p0 - p1)],resolution=1e-9)
    #NOTE: Phase must be sent to 'rect' in degrees, so I convert from radians
    for ph90Ix, ph90 in enumerate(phcyc90):
        print('\t%i of %i' %(ph90Ix+1,len(phcyc90)))
        print 'ph90: ',ph90, np.exp(1j*ph90)

        for ph180Ix, ph180 in enumerate(phcyc180):
            print 'ph180: ',ph180, np.exp(1j*ph180)

            # Pulse Sequence #
            modFreq = -300e6
            wave = p.make_highres_waveform([('delay',dx),('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x)*np.exp(1j*ph90),r_[0,p0]),('delay',d1),('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x)*np.exp(1j*ph180),np.r_[0,p1]),('delay',9.5e-6 - dx - d1 - p0 - p1)],resolution=1e-9)

            p.synthesize(wave,autoSynthSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)

            dataTemp = a.Waveform_auto()
#            if ph90Ix == 0: # if first step, create new array, 
#                dataTemp = a.Waveform_auto()*np.exp(1j*(receiver90[ph90Ix]+receiver180[ph180Ix]))
#            else:
#                dataTemp += a.Waveform_auto()*np.exp(1j*(receiver90[ph90Ix]+receiver180[ph180Ix]))

#            dataMatrix['tau',tauIx] = dataTemp
            dataMatrix['tau',tauIx,'phcyc90',ph90Ix,'phcyc180',ph180Ix] = dataTemp

endTime = time.time()
print 'Experiment Time: ', endTime - startTime

#dataMatrix.labels(['tau','t'],[tauArray,dataTemp.copy().getaxis('t')])
dataMatrix.labels(['tau','t','phcyc90','phcyc180'],[tauArray,dataTemp.copy().getaxis('t'),phcyc90,phcyc180])
dataMatrix.getaxis('t')[:] -= dataMatrix.getaxis('t').copy().mean()

a.run()
# NOTE Remove later
#dataMatrix.sum('tau')
#
#figure('Time domain')
#image(dataMatrix)

dataMatrixFt = dataMatrix.copy().ft('phcyc90').ft('phcyc180')
#figure('Time domain phcyc')
#image(dataMatrixFt)

dataMatrixFt = dataMatrixFt.ft('t',shift = True)
#figure('Frequency domain')
#image(dataMatrixFt)


centerFrequency = 300e6
bandpassFilter = 100e6

figure('slice')
#image(dataMatrixFt.runcopy(real)['phcyc90',1,'phcyc180',2],label = 'real')
#image(dataMatrixFt.runcopy(imag)['phcyc90',1,'phcyc180',2],label = 'imag')
image(dataMatrixFt.runcopy(abs)['phcyc90',1,'phcyc180',2],label = 'abs')

dataMatrixFt['t',lambda x: bandpassFilter/2. < abs(x-centerFrequency)] = 0

figure('slice bandpass')
#image(dataMatrixFt.runcopy(real)['phcyc90',1,'phcyc180',2],label = 'real')
#image(dataMatrixFt.runcopy(imag)['phcyc90',1,'phcyc180',2],label = 'imag')
image(dataMatrixFt.runcopy(abs)['phcyc90',1,'phcyc180',2],label = 'abs')
#dataMatrixFt.sum('t')

decay = dataMatrixFt.copy()['phcyc90',1,'phcyc180',2].runcopy(abs).sum('t') 

figure('decay')
plot(decay)
xlabel('Time (ns)') 

show()

