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

averages = 128 # Averages on Scope
a.acquire(averages)

### Query for fileName ###
save = raw_input("Do you wish to save your data set?\n (y or n) --> ") 
if str(save) == 'y': 
    fileName = '190415Experiments.h5' 
    print "Saving to file ",fileName 
    dataName = raw_input("Name your data set \n -->")
    save = True
elif str(save) == 'n':
    print "Not saving your file"
    save = False
else:
    "Didn't understand your answer, continuing..."



### Define Pulse Parameters ###
dx = 500e-9 # Delay at start
d1 = 500e-9 # delay between 90- and 180-pulses
p0 = 32e-9 # 90-pulse length
p1 = 32e-9 # 180-pulse length

### Pulse Amplitudes ###
a0 = 0.05 # amplitude of 90-pulse
a1 = 0.1 # amplitude of 180-pulse


fieldPoints = 101
centerField = 3290.
sweepWidth = 100
fieldArray = np.r_[-1*sweepWidth/2.:sweepWidth/2.:1j*fieldPoints] + centerField

### phase cycle ###
doPhaseCycle = False
if doPhaseCycle:
    phcyc90 = np.r_[0.,np.pi/2.,np.pi,3.*np.pi/2.]
#    phcyc90 = np.r_[0]
    phcyc180 = np.r_[0.,np.pi/2.,np.pi,3.*np.pi/2.]
#    phcyc180 = np.r_[0.,np.pi]
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


dataShape = ndshape([fieldPoints,len(phcyc90),len(phcyc180),1000],['field','phcyc90','phcyc180','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')



d0 = 60e-9#Offset from agilent scope

# 942 ns = last pulse position
agilentPosition = dx + 2*d1 + 1.5*p0 + p1 + d0

a.position(agilentPosition)


for fieldIx, fieldValue in enumerate(fieldArray):
    print('%i of %i'%(fieldIx+1,len(fieldArray)))
    fc.set_field(np.round(fieldValue,2))
    if fieldIx == 0:
        print('Waiting for field to stabilize...')
        time.sleep(2)
    else:
        time.sleep(.01)

    for ph90Ix, ph90 in enumerate(phcyc90):
        print('\t\t%i of %i' %(ph90Ix+1,len(phcyc90)))
        print 'ph90: ',ph90, np.exp(1j*ph90)

        for ph180Ix, ph180 in enumerate(phcyc180):
            print('\t%i of %i' %(ph180Ix+1,len(phcyc180)))
            print 'ph180: ',ph180, np.exp(1j*ph180)

            # Pulse Sequence #

            modFreq = -300e6
            wave = p.make_highres_waveform([('delay',dx),
            ('function',lambda x: a0*np.exp(1j*2*np.pi*modFreq*x)*np.exp(1j*ph90),r_[0,p0]),
            ('delay',d1),
            ('function',lambda x: a1*np.exp(1j*2*np.pi*modFreq*x)*np.exp(1j*ph180),np.r_[0,p1]),
            ('delay',9.5e-6 - dx - d1 - p0 - p1)],
            resolution=1e-9)

            p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
    

            dataTemp = a.Waveform_auto()

            dataMatrix['field',fieldIx,'phcyc90',ph90Ix,'phcyc180',ph180Ix] = dataTemp

dataMatrix.labels(['field','phcyc90','phcyc180','t'],[fieldArray,phcyc90,phcyc180,dataTemp.copy().getaxis('t')])

fc.set_field(np.round(centerField,1))
a.run()

figure()
image(dataMatrix)


dataMatrixFt = dataMatrix.copy().ft('t',shift = True)
if doPhaseCycle:
    dataMatrixFt = dataMatrixFt['phcyc90',1,'phcyc180',2]
    singlePoint = dataMatrix['phcyc90',1,'phcyc180',2,'t',500]
#    dataMatrixFt = dataMatrixFt['phcyc90',0,'phcyc180',1]
#    singlePoint = dataMatrix['phcyc90',0,'phcyc180',1,'t',500]
else:
    dataMatrixFt = dataMatrixFt.sum('phcyc90').sum('phcyc180')
    singlePoint = dataMatrix['phcyc90',0,'phcyc180',0,'t',500]

figure()
image(dataMatrixFt)

centerFrequency = 300e6
bandpassFilter = 100e6
dataMatrixFt['t',lambda x: bandpassFilter/2. < abs(x-centerFrequency)] = 0
fse = dataMatrixFt.copy().runcopy(abs).sum('t') 

figure()
plot(fse)
xlabel('Field (G)')

signalPhase = np.arctan(np.sum(np.imag(singlePoint.data))/np.sum(np.real(singlePoint.data)))
singlePoint *= np.exp(-1j*signalPhase)

figure()
plot(singlePoint.runcopy(real),label = 'real')
plot(singlePoint.runcopy(imag),label = 'imag')
xlabel('Field (G)')
ylabel('Echo Amplitude')

show()

### Add all parameters to saveDict and add to dataMatrix ###
saveDict = {'dx':dx,                 # Delay at start
        'd1':d1,                     # delay between 90- and 180-pulses
        'p0':p0,                     # 90-pulse length
        'p1':p1,                     # 180-pulse length
        'a0':a0,                     # amplitude of 90-pulse
        'a1':a1,                     # amplitude of 180-pulse
        'd30':d30,                   # sampling of interpulse delays 
        'd0':d0,                     # Agilent Scope offset
        'fieldPoints':fieldPoints,       # total number of interpulse delays
        'centerField':centerField,   # center field value
        'sweepWidth':sweepWidth
        }
    
dataMatrix.other_info = saveDict


if save:
    print "saving data ",dataName," to file ",fileName,"\n"
    dataMatrix.name(str(dataName))
    dataMatrix.hdf5_write(fileName)



