from matlablike import *
import numpy as np

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





class DEER():

    def __init__(self):
        '''Initialize data arrays for DEER setup and measurements'''
        self.setupParams()
        # Array for 1d data
        dataShape = ndshape([1000],['t'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict

        # Array for 2d data, 
        dataMatrixShape = ndshape([2,1000],['x','t'])
        self.dataMatrix = dataMatrixShape.alloc(dtype = 'complex')
        self.dataMatrix.other_info = self.paramsDict

    def determinePhaseCycleHahnEcho(self,phaseCycle):
        ### Phase Cycles ###
        if phaseCycle == '2-step':
            # 2-step on 90-pulse
            self.ph0 = np.r_[0,np.pi]
            self.ph1 = np.r_[0]

            self.rph0 = np.r_[0,np.pi]
            self.rph1 = np.r_[0]
        elif phaseCycle == '4-step':
            # 4-step on 90-pulse
            self.ph0 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph1 = np.r_[0]

            self.rph0 = np.r_[0,-np.pi/2.,-np.pi,-3.*np.pi/2.]
            self.rph1 = np.r_[0]
        elif phaseCycle == '16-step':
            self.ph0 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph1 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]

            self.rph0 = np.r_[0,-np.pi/2.,-np.pi,-3.*np.pi/2.]
            self.rph1 = np.r_[0,np.pi,0,np.pi]

        else: # if something else, assume 'none'
            self.ph0 = np.r_[0]
            self.ph1 = np.r_[0]

            self.rph0 = np.r_[0]
            self.rph1 = np.r_[0]

            phaseCycle = 'none'
            phaseCycle = paramsDict['phaseCycle']
    def determinePhaseCycle(self,phaseCycle):
        ### Phase Cycles ###
        if phaseCycle == '2-step':
            # 2-step on 90-pulse
            self.ph0 = np.r_[0,np.pi]
            self.ph1 = np.r_[0]
            self.ph2 = np.r_[0]
            self.ph3 = np.r_[0]

            self.rph0 = np.r_[0,np.pi]
            self.rph1 = np.r_[0]
            self.rph2 = np.r_[0]
            self.rph3 = np.r_[0]

        if phaseCycle == '8-step':

            # Phase for each Pulse
            self.ph0 = np.r_[0,np.pi]
            self.ph1 = np.r_[0]
            self.ph2 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph3 = np.r_[0]

            # Receiver Phase for each pulse
            self.rph0 = np.r_[0,np.pi]
            self.rph1 = np.r_[0]
            self.rph2 = np.r_[0,0,0,0]
            self.rph3 = np.r_[0]

        if phaseCycle == '16-step': # NOTE -> 16-step doesn't work yet

            # Phase for each Pulse
            self.ph0 = np.r_[0,np.pi]
            self.ph1 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph2 = np.r_[0,np.pi]
            self.ph3 = np.r_[0]

            # Receiver Phase for each pulse
            self.rph0 = np.r_[0,np.pi]
            self.rph1 = np.r_[0,np.pi,0,np.pi]
            self.rph2 = np.r_[0,0]
            self.rph3 = np.r_[0]
            
        if phaseCycle == '32-step':

            # Phase for each Pulse
            self.ph0 = np.r_[0,np.pi]
            self.ph1 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph2 = np.r_[0,np.pi/2.,np.pi,3.*np.pi/2.]
            self.ph3 = np.r_[0]

            # Receiver Phase for each pulse
            self.rph0 = np.r_[0,np.pi]
            self.rph1 = np.r_[0,np.pi,0,np.pi]
            self.rph2 = np.r_[0,0,0,0]
            self.rph3 = np.r_[0]

        else:
            # Phase for each Pulse
            self.ph0 = np.r_[0]
            self.ph1 = np.r_[0]
            self.ph2 = np.r_[0]
            self.ph3 = np.r_[0]
            # Receiver Phase for each pulse
            self.rph0 = np.r_[0]
            self.rph1 = np.r_[0]
            self.rph2 = np.r_[0]
            self.rph3 = np.r_[0]

            phaseCycle = 'none'

    def setupParams(self):
        paramsData = recvParams()

        try:
            exec('self.paramsDict = ' + paramsData) #NOTE: self.paramsDict?
            print('paramsDict:')
            for key in self.paramsDict:
                print key, ' : ', self.paramsDict[key]
        except:
            pass
        
        self.averages = self.paramsDict['averages'] # averages on scope

        ### Pulse Length Parameters ###
        self.p0 = self.paramsDict['p0']             # observe 90-pulse Length
        self.p1 = self.paramsDict['p1']             # observe 180-pulse Length

        self.p2 = self.paramsDict['p2']             # Pulse length for nutation experiments

        self.p3 = self.paramsDict['p3']             # 4p-DEER pump pulse
        self.p5 = self.paramsDict['p5']             # 5p-DEER pump pulse

        self.p30 = self.paramsDict['p30']           # pulse length increment for nutation experiments


        ### Pulse Amplitude Parameters ###
        self.a0 = self.paramsDict['a0']             # amplitude of 90-pulse
        self.a1 = self.paramsDict['a1']             # amplitude of 180-pulse

        self.a2 = self.paramsDict['a2']             # amplitude of nutation pulse

        self.a3 = self.paramsDict['a3']             # amplitude of 4p-DEER pump pulse
        self.a5 = self.paramsDict['a5']             # amplitude of 5p-DEER pump pulse

        ### Pulse Delay Parameters ###
        self.dx =  self.paramsDict['dx']            # delay at start
        self.d1 =  self.paramsDict['d1']            # delay between 90- and 180- pulses

        self.d2 = self.paramsDict['d2']             # delay between 180-pulses for 4-pulse DEER
        self.d3 = self.paramsDict['d3']             # ELDOR pulse offset 4-pulse DEER
        self.d5 = self.paramsDict['d5']             # ELDOR pulse offset 5-pulse DEER

        self.d0 = self.paramsDict['d0']             # Offset from Agilent scope

        self.d30 = self.paramsDict['d30']           # delay increment


        ### Frequency parameters ###
        self.modFreq =  self.paramsDict['modFreq']  # Pulse frequency offset from carrier
        self.freqOffsetELDOR = self.paramsDict['freqOffsetELDOR']   # frequence offset for ELDOR pulses

        self.nptsELDOR = self.paramsDict['nptsELDOR']   # number of points in ELDOR trace

        self.nptsOpt = self.paramsDict['nptsOpt']   # number of points for nutation experiment


        self.bandpassFilter = self.paramsDict['bandpassFilter'] # bandpass filter for data
        self.integrationWindow = self.paramsDict['integrationWindow'] # integation window for echo
        self.phaseCycle = self.paramsDict['phaseCycle'] # type of phase cycle
        self.scans = self.paramsDict['scans'] # number of repeats

        ### Field parameters ###
        self.fieldPoints = self.paramsDict['fieldPoints']  # number of points in field axis
        self.centerField = self.paramsDict['centerField']  # center field for field sweep
        self.sweepWidth = self.paramsDict['sweepWidth']    # sweep width for field swept echo


    def hahnEcho(self):
        self.setupParams() # pull parameters from server
        self.determinePhaseCycle(self.phaseCycle)

        paramsDict = self.paramsDict
        # Add Experiment Specific tags to paramsDict #
        paramsDict['exp'] = ['HahnEcho']
        paramsDict['epochTime'] = time.time()
        paramsDict['time'] = recvTime()
        paramsDict['date'] = recvDate()
        
        a.acquire(self.averages)

        dataShape = ndshape([1000],['t'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict

        # Set agilent scope position
        agilentPosition = self.dx + 2*self.d1 + 1.5*self.p0 + self.p1 + self.d0
        a.position(agilentPosition)

        for scan in np.arange(self.scans):
            for ph0Ix,ph0Value in enumerate(self.ph0):
                for ph1Ix, ph1Value in enumerate(self.ph1):

                    # Pulse Sequence #
                    wave = p.make_highres_waveform([('delay',self.dx),
                    ('function',lambda x: self.a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*self.modFreq*x),r_[0,self.p0]),
                    ('delay',self.d1),
                    ('function',lambda x: self.a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                    ('delay',9.5e-6 - self.dx - self.d1 - self.p0 - self.p1)],
                    resolution=1e-9)

                    # Send pulse to DAC board
                    p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)


                    # Pull data from scope
                    dataTemp = a.Waveform_auto()

                    # Process data: Shift to on-resonance and apply bandpass filter
                    dataTemp.ft('t')
                    dataTemp['t',lambda x: abs(x+self.modFreq) > self.bandpassFilter/2.] = 0 
                    dataTemp.ift('t')
                    dataTemp.data *= np.exp(1j*2*np.pi*self.modFreq*dataTemp.getaxis('t').copy())

                    # Compute Receiver phase and apply
                    receiverPhase = self.rph0[ph0Ix]+self.rph1[ph1Ix]
                    dataTemp.data *= np.exp(1j*receiverPhase)

                    # Add to data array
                    self.data += dataTemp

        a.run()
        data.labels(['t'],[dataTemp.getaxis('t')])


        # apply phase shift
        phaseShift = np.arctan(np.sum(np.imag(data.copy().data))/np.sum(np.real(data.copy().data)))
        data.data *= np.exp(-1j*phaseShift)
        if np.sum(np.real(data.copy().data)) < 0:
            data.data *= -1.

        # plot result
        close('all')
        figure('Hahn Echo')
        plot(self.data.runcopy(real),label = 'real',linewidth = 2.,alpha = 0.7)
        plot(self.data.runcopy(imag),label = 'imag',linewidth = 2.,alpha = 0.7)
        legend()
        show()

    def fse(self):
        '''Perform field swept echo experiment'''
        self.setupParams() # pull parameters from server
        self.determinePhaseCycle(self.phaseCycle)

        paramsDict = self.paramsDict
        # Add Experiment Specific tags to paramsDict #
        paramsDict['exp'] = ['HahnEcho']
        paramsDict['epochTime'] = time.time()
        paramsDict['time'] = recvTime()
        paramsDict['date'] = recvDate()
        
        a.acquire(self.averages)

        fieldArray = np.r_[-1*self.sweepWidth/2.:self.sweepWidth/2.:1j*self.fieldPoints] + self.centerField

        dataShape = ndshape([len(fieldArray)],['field'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict

        # Set agilent scope position
        agilentPosition = self.dx + 2*self.d1 + 1.5*self.p0 + self.p1 + self.d0
        a.position(agilentPosition)

        for scan in np.arange(self.scans):
            for fieldIx,fieldValue in enumerate(fieldArray):
                fc.set_field(fieldValue)
                # wait for field to settle
                if fieldIx == 0:
                    time.sleep(1)
                else:
                    time.sleep(0.1)

                for ph0Ix,ph0Value in enumerate(self.ph0):
                    for ph1Ix, ph1Value in enumerate(self.ph1):

                        # Pulse Sequence #
                        wave = p.make_highres_waveform([('delay',self.dx),
                        ('function',lambda x: self.a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*self.modFreq*x),r_[0,self.p0]),
                        ('delay',self.d1),
                        ('function',lambda x: self.a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                        ('delay',9.5e-6 - self.dx - self.d1 - self.p0 - self.p1)],
                        resolution=1e-9)

                        # Send pulse to DAC board
                        p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)


                        # Pull data from scope
                        dataTemp = a.Waveform_auto()

                        # Process data: Shift to on-resonance and apply bandpass filter
                        dataTemp.ft('t')
                        dataTemp['t',lambda x: abs(x+self.modFreq) > self.bandpassFilter/2.] = 0 
                        dataTemp.ift('t')
                        dataTemp.data *= np.exp(1j*2*np.pi*self.modFreq*dataTemp.getaxis('t').copy())

                        # Compute Receiver phase and apply
                        receiverPhase = self.rph0[ph0Ix]+self.rph1[ph1Ix]
                        dataTemp.data *= np.exp(1j*receiverPhase)

                        # Set data to zero outside integration region of echo
                        dataTemp['t',lambda x: abs(x - np.mean(dataTemp.getaxis('t'))) > self.integrationWindow/2.] = 0

                        # Add to data array
                        self.data.data[lengthIx] += np.sum(dataTemp.data)

        a.run()
        data.labels(['field'],[fieldArray])


        # apply phase shift
        phaseShift = np.arctan(np.sum(np.imag(data.copy().data))/np.sum(np.real(data.copy().data)))
        data.data *= np.exp(-1j*phaseShift)
        if np.sum(np.real(data.copy().data)) < 0:
            data.data *= -1.

        # plot result
        close('all')
        figure('Pump Pulse Optimization')
        plot(self.data.runcopy(real),label = 'real',linewidth = 2.,alpha = 0.7)
        plot(self.data.runcopy(imag),label = 'imag',linewidth = 2.,alpha = 0.7)
        legend()
        show()

    def optPump(self):
        ''' Experiment for optimizing length and amplitude of pump pulse 
            The frequency of the nutation experiment is at the frequency of the pump pulses'''
        self.setupParams() # pull parameters from server
        self.determinePhaseCycle(self.phaseCycle)

        paramsDict = self.paramsDict
        # Add Experiment Specific tags to paramsDict #
        paramsDict['exp'] = ['HahnEcho']
        paramsDict['epochTime'] = time.time()
        paramsDict['time'] = recvTime()
        paramsDict['date'] = recvDate()

        lengthArray = np.arange(self.p2,self.p30*self.nptsOpt+self.p2,self.p30)

        dataShape = ndshape([len(lengthArray)],['length'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict
        
        a.acquire(self.averages)

        freq = self.modFreq + self.freqOffsetELDOR

        for scan in np.arange(self.scans):
            for lengthIx,lengthValue in enumerate(lengthArray):
                p2 = lengthValue
                for ph0Ix,ph0Value in enumerate(self.ph0):
                    for ph1Ix, ph1Value in enumerate(self.ph1):

                        # Pulse Sequence #
                        wave = p.make_highres_waveform([('delay',self.dx),
                            ('function',lambda x: self.a0*np.exp(1j*0)*np.exp(1j*2*np.pi*(freq)*x),r_[0,p2]), # variable length pulse
                            ('delay',self.d1 - p2),
                            ('function',lambda x: self.a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*freq*x),r_[0,self.p0]),
                            ('delay',self.d2),
                            ('function',lambda x: self.a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*freq*x),np.r_[0,self.p1]),
                            ('delay',9.5e-6 - self.dx - self.d1 - self.d2 - self.p0 - self.p1 - p2)],
                            resolution=1e-9)

                        # Send pulse to DAC board
                        p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)

                        # set agilent position
                        agilentPosition = self.dx + self.p2 + (self.d1 - self.p2) + 1.5*self.p0 + 2.*self.d2 + 1.5*self.p1 + self.d0
                        a.position(agilentPosition)

                        # Pull data from scope
                        dataTemp = a.Waveform_auto()

                        # Process data: Shift to on-resonance and apply bandpass filter
                        dataTemp.ft('t')
                        dataTemp['t',lambda x: abs(x+self.modFreq) > self.bandpassFilter/2.] = 0 
                        dataTemp.ift('t')
                        dataTemp.data *= np.exp(1j*2*np.pi*self.modFreq*dataTemp.getaxis('t').copy())

                        # Compute Receiver phase and apply
                        receiverPhase = self.rph0[ph0Ix]+self.rph1[ph1Ix]
                        dataTemp.data *= np.exp(1j*receiverPhase)

                        # Set data to zero outside integration region of echo
                        dataTemp['t',lambda x: abs(x - np.mean(dataTemp.getaxis('t'))) > self.integrationWindow/2.] = 0

                        # Add to data array
                        self.data.data[lengthIx] += np.sum(dataTemp.data)

        a.run()
        self.data.labels(['length'],[lengthArray])


        # apply phase shift
        phaseShift = np.arctan(np.sum(np.imag(data.copy().data))/np.sum(np.real(data.copy().data)))
        data.data *= np.exp(-1j*phaseShift)
        if np.sum(np.real(data.copy().data)) < 0:
            data.data *= -1.

        # plot result
        close('all')
        figure('Pump Pulse Optimization')
        plot(self.data.runcopy(real),label = 'real',linewidth = 2.,alpha = 0.7)
        plot(self.data.runcopy(imag),label = 'imag',linewidth = 2.,alpha = 0.7)
        legend()
        show()

    def setupELDOR(self):
        ''' Experiment to determine timings for ELDOR experiment'''
        self.setupParams() # pull parameters from server
        self.determinePhaseCycle(self.phaseCycle)

        paramsDict = self.paramsDict
        # Add Experiment Specific tags to paramsDict #
        paramsDict['exp'] = ['HahnEcho']
        paramsDict['epochTime'] = time.time()
        paramsDict['time'] = recvTime()
        paramsDict['date'] = recvDate()

        dataShape = ndshape([1000],['t'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict
        
        a.acquire(self.averages)

        agilentPosition = self.dx + 0.5*self.p0 + self.p1 + 2*self.d2 + self.d0
        a.position(agilentPosition)
        
        for scan in range(self.scans):

#            for delayIx, delay in enumerate(delayELDOR): 
#                print('%i of %i'%(scan+1,scans))
#                print('\t%i of %i'%(delayIx+1,len(delayELDOR)))
#                dELDOR = delay

            # Phase Cycle #
            dELDOR = self.d3
            
            for ph0Ix,ph0Value in enumerate(self.ph0):
                print('\t%i of %i'%(ph0Ix+1,len(self.ph0)))
                for ph1Ix,ph1Value in enumerate(self.ph1):
                    print('\t\t%i of %i'%(ph1Ix+1,len(self.ph1)))
                    for ph2Ix,ph2Value in enumerate(self.ph2):
                        print('\t\t\t%i of %i'%(ph2Ix+1,len(self.ph2)))
                        for ph3Ix,ph3Value in enumerate(self.ph3):
                            print('\t\t\t\t%i of %i'%(ph3Ix+1,len(self.ph3)))

                            # Pulse Sequence #
                            wave = p.make_highres_waveform([
                                ('delay',self.dx),
                                ('function',lambda x: self.a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p0]),
                                ('delay',self.d1),
                                ('function',lambda x: self.a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                                ('delay',dELDOR),
                                ('function',lambda x: self.a3*np.exp(1j*ph2Value)*np.exp(1j*2*np.pi*(self.freqOffsetELDOR+self.modFreq)*x),r_[0,self.p3]),
                                ('delay',self.d2 - self.d3 - self.p3),
                                ('function',lambda x: self.a1*np.exp(1j*ph3Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                                ('delay',9.5e-6 - self.dx - self.d1 - self.d2 - self.p0 - 2*self.p1)],
                                resolution=1e-9)


                            p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
                            

                            dataTemp = a.Waveform_auto()
                            dataTemp.ft('t')
                            dataTemp['t',lambda x: abs(x+self.modFreq) > self.bandpassFilter/2.] = 0
                            dataTemp.ift('t')
                            dataTemp.data *= np.exp(1j*2*np.pi*self.modFreq*dataTemp.getaxis('t').copy())

                            receiverPhase = self.rph0[ph0Ix]+self.rph1[ph1Ix]+self.rph2[ph2Ix]+self.rph3[ph3Ix]
                            dataTemp.data = dataTemp.data*np.exp(1j*receiverPhase)


                            self.data += dataTemp


        a.run()
        self.data.labels(['t'],[dataTemp.copy().getaxis('t')])

        # apply phase shift
        phaseShift = np.arctan(np.sum(np.imag(data.copy().data))/np.sum(np.real(data.copy().data)))
        data.data *= np.exp(-1j*phaseShift)
        if np.sum(np.real(data.copy().data)) < 0:
            data.data *= -1.

        # plot result
        close('all')
        figure('ELDOR setup')
        plot(self.data.runcopy(real),label = 'real',linewidth = 2.,alpha = 0.7)
        plot(self.data.runcopy(imag),label = 'imag',linewidth = 2.,alpha = 0.7)
        legend()
        show()


    def DEER4p(self):
        ''' 4-pulse ELDOR Experiment'''
        self.setupParams() # pull parameters from server
        self.determinePhaseCycle(self.phaseCycle)

        paramsDict = self.paramsDict
        # Add Experiment Specific tags to paramsDict #
        paramsDict['exp'] = ['HahnEcho']
        paramsDict['epochTime'] = time.time()
        paramsDict['time'] = recvTime()
        paramsDict['date'] = recvDate()

        delayELDOR = np.r_[self.d3:(self.nptsELDOR-1)*self.d30+self.d3:1j*self.nptsELDOR]

        ### Verify ELDOR delay will not exceed d2 ###
        if (self.d2 - np.max(delayELDOR) - self.p3) < 0.0:
            print '*'*50
            print('\tWARNING!!!\n\tdELDOR + pELDOR > d2\n\tautomatically correcting length of ELDOR trace')
            self.nptsELDOR = int(np.floor((self.d2 - self.p3 - self.d3) / self.d30))
            delayELDOR = np.r_[self.d3:(self.nptsELDOR-1)*self.d30+self.d3:1j*self.nptsELDOR]
            print('\tnptsELDOR = %i'%(self.nptsELDOR))
            print '*'*50

        dataShape = ndshape([len(delayELDOR)],['tELDOR'])
        self.data = dataShape.alloc(dtype = 'complex')
        self.data.other_info = self.paramsDict
        
        a.acquire(self.averages)

        agilentPosition = self.dx + 0.5*self.p0 + self.p1 + 2*self.d2 + self.d0
        a.position(agilentPosition)
        
        for scan in range(self.scans):

            for delayIx, delay in enumerate(delayELDOR): 
                print('%i of %i'%(scan+1,self.scans))
                print('\t%i of %i'%(delayIx+1,len(delayELDOR)))
                dELDOR = delay

                # Phase Cycle #
                for ph0Ix,ph0Value in enumerate(self.ph0):
                    print('\t%i of %i'%(ph0Ix+1,len(self.ph0)))
                    for ph1Ix,ph1Value in enumerate(self.ph1):
                        print('\t\t%i of %i'%(ph1Ix+1,len(self.ph1)))
                        for ph2Ix,ph2Value in enumerate(self.ph2):
                            print('\t\t\t%i of %i'%(ph2Ix+1,len(self.ph2)))
                            for ph3Ix,ph3Value in enumerate(self.ph3):
                                print('\t\t\t\t%i of %i'%(ph3Ix+1,len(self.ph3)))

                                # Pulse Sequence #
                                wave = p.make_highres_waveform([
                                    ('delay',self.dx),
                                    ('function',lambda x: self.a0*np.exp(1j*ph0Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p0]),
                                    ('delay',self.d1),
                                    ('function',lambda x: self.a1*np.exp(1j*ph1Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                                    ('delay',dELDOR),
                                    ('function',lambda x: self.a3*np.exp(1j*ph2Value)*np.exp(1j*2*np.pi*(self.freqOffsetELDOR+self.modFreq)*x),r_[0,self.p3]),
                                    ('delay',self.d2 - dELDOR - self.p3),
                                    ('function',lambda x: self.a1*np.exp(1j*ph3Value)*np.exp(1j*2*np.pi*self.modFreq*x),np.r_[0,self.p1]),
                                    ('delay',9.5e-6 - self.dx - self.d1 - self.d2 - self.p0 - 2*self.p1)],
                                    resolution=1e-9)


                                p.synthesize(wave,autoSynthSwitch = True,autoReceiverSwitch = True,autoTWTSwitch = True, longDelay = 3e-4)
                                

                                dataTemp = a.Waveform_auto()
                                dataTemp.ft('t')
                                dataTemp['t',lambda x: abs(x+self.modFreq) > self.bandpassFilter/2.] = 0
                                dataTemp.ift('t')
                                dataTemp.data *= np.exp(1j*2*np.pi*self.modFreq*dataTemp.getaxis('t').copy())

                                receiverPhase = self.rph0[ph0Ix]+self.rph1[ph1Ix]+self.rph2[ph2Ix]+self.rph3[ph3Ix]
                                dataTemp.data = dataTemp.data*np.exp(1j*receiverPhase)


                                # Set data to zero outside integration region of echo
                                dataTemp['t',lambda x: abs(x - np.mean(dataTemp.getaxis('t'))) > self.integrationWindow/2.] = 0

                                # Add to data array
                                self.data.data[delayIx] += np.sum(dataTemp.data)


        a.run()
        self.data.labels(['tELDOR'],[delayELDOR])

        # apply phase shift
        phaseShift = np.arctan(np.sum(np.imag(data.copy().data))/np.sum(np.real(data.copy().data)))
        data.data *= np.exp(-1j*phaseShift)
        if np.sum(np.real(data.copy().data)) < 0:
            data.data *= -1.

        # plot result
        close('all')
        figure('ELDOR setup')
        plot(self.data.runcopy(real),label = 'real',linewidth = 2.,alpha = 0.7)
        plot(self.data.runcopy(imag),label = 'imag',linewidth = 2.,alpha = 0.7)
        legend()
        show()
    def DEER5p(self):
        pass




if __name__ == '__main__':
    d = DEER()

#    d.hahnEcho()
#    d.optPump()
#    d.setupELDOR()
    d.DEER4p()
#    close('all')
#    figure()
#    plot(d.data.runcopy(real),label = 'real',linewidth = 2.)
#    plot(d.data.runcopy(imag),label = 'imag',linewidth = 2.)
#    legend()
#    show()



