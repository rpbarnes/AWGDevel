from matlablike import *
import time
import numpy as np
close('all')
import gpib_eth as g

#{{{ Import necessary modules if do not exist alreay
try:
    s
except:
    import synthesize as s
try:
    p
except:
    p = s.pulsegen()
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
    a = g.agilent()#}}}


### Query for fileName ### #{{{
#save = raw_input("Do you wish to save your data set?\n (y or n) --> ") 
#if str(save) == 'y': 
#    fileName = '190415Experiments.h5' 
#    print "Saving to file ",fileName 
#    dataName = raw_input("Name your data set \n -->")
#    save = True
#elif str(save) == 'n':
#    print "Not saving your file"
#    save = False
#else:
#    "Didn't understand your answer, continuing..."#}}}

##############################################

### Import Pulse Parameters from GUI ###
fromGui = True
if fromGui:
    # start client
    import os
    import sys
    from socket import *
    serverHost = 'localhost'
    serverPort = 50007
    message = [b'handshake']

    print 'starting socket'
    sockobj = socket(AF_INET, SOCK_STREAM)
    sockobj.connect((serverHost, serverPort))
    print 'sending handshake'
    for line in message:
        sockobj.send(line)
        print 'receiving data'
        data = sockobj.recv(1024)
    print 'closing socket'
    sockobj.close()

    try:
        exec('paramsDict = ' + data)
        print 'Received Parameters:'
        for key in paramsDict:
            print key, ' : ', paramsDict[key]
    except:
        pass
        
    
    p0 = paramsDict['p0']             # 90-pulse Length
    p1 = paramsDict['p1']             # 180-pulse Length

    a0 = paramsDict['a0']             # amplitude of 90-pulse
    a1 = paramsDict['a1']             # amplitude of 180-pulse

    dx =  paramsDict['dx']            # delay at start
    d1 =  paramsDict['d1']            # delay between 90- and 180- pulses
    d0 = paramsDict['d0']             # Offset from Agilent scope
    d30 = paramsDict['d30']           # increment in tau

    modFreq =  paramsDict['modFreq']  # Pulse frequency offset from carrier
    bandpassFilter = paramsDict['bandpassFilter'] # bandpass filter for data
    integrationWindow = paramsDict['integrationWindow'] # integration range in time over echo
    tauPoints = paramsDict['tauPoints']
    phaseCycle = paramsDict['phaseCycle']

    averages = paramsDict['averages'] # averages on scope
    scans = paramsDict['scans']       # number of repeats

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

    paramsDict['d30'] = d30           # increment in tau
    parameters['tauPoints'] = tauPoints # number of points in tau axis

    paramsDict['modFreq'] = modFreq   # Pulse frequency offset from carrier
    paramsDict['bandpassFilter'] = bandpassFilter
    paramsDict['integrationWindow'] = integrationWindow


# define tau axis
tauArray = np.r_[d1:(tauPoints-1)*d30+d1:1j*tauPoints]

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

# Test for maximum delay for safety
maxDelay = 6e-6
if (maxDelay - np.max(tauArray) - p0 - p1) < 0:
    print '*'*50
    print('\tWARNING!!!\n\ttauArray exceeds limit\n\tautomatically correcting length of tauArray')
    
    tauPoints = int(np.floor((maxDelay - np.max(tauArray) - p0 - p1)/d30))
    tauArray = np.r_[d1:(tauPoints-1)*d30+d1:1j*tauPoints]
    print('\ttauPoints = %i'%tauPoints)
    print '*'*50

### Data Storage ###
dataShape = ndshape([tauPoints,1000],['tau','t'])
dataMatrix = dataShape.alloc(dtype = 'complex')
dataMatrix.other_info = paramsDict

a.acquire(averages)

startTime = time.time()



for scan in np.arange(scans):
    for tauIx, tauValue in enumerate(tauArray):
        percentDone = 100*float((scan*scans+tauIx))/float((scans*len(tauArray)))
        print('%0.1f%%'%percentDone)
        d1 = tauValue # increment tau value

        # calculate new Agilent scope position and set new position
        agilentPosition = dx + 2*d1 + 1.5*p0 + 1.*p1 + d0
        a.position(agilentPosition)

        for ph0Ix, ph0Value in enumerate(ph0):
            for ph1Ix, ph1Value in enumerate(ph1):
                # Pulse Sequence #
                wave = p.make_highres_waveform([('delay',dx),
                    ('function',lambda x: a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*modFreq*x),r_[0,p0]),
                    ('delay',d1),
                    ('function',lambda x: a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*modFreq*x),np.r_[0,p1]),
                    ('delay',9.5e-6 - dx - d1 - p0 - p1)],
                    resolution=1e-9)
                

                p.synthesize(wave,autoSynthSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)

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
                dataMatrix['tau',tauIx] += dataTemp



endTime = time.time()
print 'Experiment Time: ', endTime - startTime

dataMatrix.labels(['tau','t'],[tauArray,dataTemp.copy().getaxis('t')])

a.run()


dataMatrixProcessed = dataMatrix.copy()
dataMatrixProcessed['t',lambda x: abs(x - np.mean(dataMatrixProcessed.getaxis('t'))) > integrationWindow/2.]


decay = dataMatrix.copy().sum('t') 

figure('Raw data matrix')
image(dataMatrix)
figure('processed data matrix')
image(dataMatrixProcessed)
figure('decay')
plot(decay)
xlabel('Time (ns)') 

show()




