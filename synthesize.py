from matlablike import * # I like working with the nddata stuff however it's not used very much... This should change.
import os
import sys
import time
import labrad
from labrad.units import V, mV, us, ns, GHz, MHz
from workflow import switchSession as pss #(P)yle(S)witch(S)ession
import scipy.optimize as o
import numpy as np
from servers.GHzDACs.Cleanup import dac as dacModule

sys.path.append('C:\Users\hanlab\Desktop\GHz DAC\fpgaTest')
FPGA_SERVER = 'ghz_fpgas'
board = 'Han Lab DAC 1'
DAC_ZERO_PAD_LEN = 16


class pulsegen ():
    ### Import calibration will import calibration parameter from a file if False it wont
    def __init__(self,import_inpcal = False,import_detcal = False):  #{{{
        self.res = 1e-11     ### this is the desired resolution of all calibration waveforms ###
        self.cxn = labrad.connect()
        self.switchSession(user='TestUser')
        self.fpga = self.cxn.ghz_fpgas
        self.fpga.select_device(board)
        return#}}}
    def switchSession(self,session=None, user=None):#{{{
        r'''Switch the current session, using the global connection object'''
        global ses
        if user is None:
            user = ses._dir[1]
        # ses = pss(self.cxn, user, session, useDataVault=True) 
        ses = pss(self.cxn, user, session, useDataVault=False)#}}}
    def make_highres_waveform(self,listoftuples,#{{{
            resolution = 1e-9,
            verbose = False):
        r'''generates a waveform which is a list of tuples, in the following possible formats:
        ('delay',len)
        ('function',function,taxis)  <-- taxis i either a number (for length), or an array
        ('rect',phase,len)
        phase can be in format number, for degrees, or '+x','x','-y',etc.
        resolution can be specified in seconds.
        use as follows
        wave = self.make_highres_waveform([('delay',100e-9),('rect','x',20e-9),('function',lambda x: sinc(2*pi*x),100e-9),('delay',10e-6-100e-9 - 20e-9 - 100e-9)])
        this generates a rectangle with x phase and a sinc shaped pulse 
        '''
        # if 1e-9 % resolution < 1e-22 or resolution % 1e-9 < 1e-22:
        testfn = lambda x: x+1 # so I can test against the type
        current_waveform = zeros(0,dtype = 'complex128') # start with zero length
        for wavepart in listoftuples:
            #{{{ calculate "thispart" based on what type the tuple is
            if wavepart[0] == 'delay':
                thispart = zeros(int(round(wavepart[1]/resolution)))
            if wavepart[0] == 'function':
                if type(wavepart[1]) is type(testfn):
                    if isscalar(wavepart[2]):
                        t = double(r_[0:wavepart[2]:resolution])-wavepart[2]/2.0
                        t /= t[0]
                    elif type(wavepart[2]) in [list,ndarray]:
                        if len(wavepart[2]) == 2:
                            t = r_[wavepart[2][0]:wavepart[2][1]:resolution]
                        else:
                            raise TypeError('the third element in the tuple',wavepart,'must be a number, or a list or array giving just the start and stop times!')
                    else:
                        raise TypeError('the third element in the tuple',wavepart,'must be a number, or a list or array giving just the start and stop times!')
                    myfn = wavepart[1]
                    thispart = myfn(t)
                else:
                    raise TypeError('The second argument to a function tuple must be a function!')
            if wavepart[0] == 'rect':
                if type(wavepart[1]) is str:
                    phasestring = wavepart[1]
                    negative = 1.
                    if phasestring[0] == '-':
                        negative = -1.
                        phasestring = phasestring[1:]
                    elif phasestring[0] == '+':
                        phasestring = phasestring[1:]
                    if phasestring == 'x':
                        phase = 1.
                    elif phasestring == 'y':
                        phase = 1j
                    else:
                        raise ValueError("I don't understand the phase"+phasestring)
                else:
                    negative = 1.
                    phase = exp(1j*double(wavepart[1])/180.*pi)
                try:
                    thispart = negative * phase * ones(int(round(wavepart[2]/resolution)))
                except IndexError:
                    raise ValueError("You probably entered a tuple of the wrong format --> use something like this ('rect','x',100)")
            if wavepart[0] == 'train':
                # takes a list of lists with [[a1,p1],[a2,p2],...] defining a pulse train with 1 ns steps.
                # resolution of output can still be specified.
                res_factor = int(round(1e-9/resolution))
                if verbose: print wavepart[1]
                zippart = zip(wavepart[1][0],wavepart[1][1])
                if verbose: print zippart
                thispart = ones(len(zippart)*res_factor) * 1j
                for i in range(len(zippart)):
                    negative = 1.
                    amplitude = zippart[i][0]
                    phase = exp(1j*double(zippart[i][1])/180.*pi)
                    try:
                        for j in range(res_factor):
                            thispart[(i*res_factor)+j] = negative * phase * amplitude
                    except IndexError:
                        raise ValueError("You probably entered a tuple of the wrong format --> use something like this ('train',[(1,0.9),(0,90)]), where the first tuple defines the amplitudes, the second one the phase")
            #}}}
            current_waveform = r_[current_waveform,thispart]
        return nddata(current_waveform,[-1],['t'],axis_coords = [resolution*r_[0:size(current_waveform)]]).set_units('t','s')#}}}
    #{{{ basic functions for the operation codes.
    def check_5char_hex(self,a):
        int(round(a))
        if a > 2**(5*4)-1:
            raise ValueError("too big!!")
        if a < 0:
            raise ValueError("can't be less than zero!")
        return a
    def gen_code(self,opcode,number):
        if opcode not in [1,2,3,4,8,10,12,15]:
            raise ValueError("This is not a valid opcode!")
        return [opcode * (1<<(5*4)) + self.check_5char_hex(number)] #0x100000
    #}}}
    #{{{ and the actual operation codes
    def Bluebox(self,bluebox_number,x):
        return gen_code(1,x)
    def delay(self,x):
        return [self.gen_code(3,int(round(25.e6*x)))[0] - 100] # give delay in seconds, it converts to clock cycles (2e-3 -> 50000, since 25MHz clock), where the 100 is added in the code, and I have no idea what it is --> it could be from Thomas + incorrect
    def SRAM_start_address(self,x):
        return self.gen_code(8,x)
    def SRAM_stop_address(self,x):
        return self.gen_code(0xa,x)
    def SRAM_range(self,start,length):
        # this sets the range of the SRAM that will be played
        return self.SRAM_start_address(start) + self.SRAM_stop_address(start+length-1)
    #}}}
    def dacSignal(self,sram, reps=100000, getTimingData=False, delay = 10e-4):#{{{
        # Now make a memory list to send to the dac so we can get a repetition delay longer that 10 us.
        clockCycles = delay / 4e-9 # number of cycles to sleep
        sramLen = len(sram)
        # use Daniel's method of generating memory sequence from the DAC module
        memory=dacModule.MemorySequence()
        memory.noOp().sramStartAddress(0).sramEndAddress(sramLen-1).runSram().delayCycles(int(clockCycles)).branchToStart()
        # generate maximum number of repetitions that the memory size allows for
        self._sendDac(memory,sram,self.fpga)
        self.fpga.run_sequence(reps, getTimingData)#}}}
    def _sendDac(self,memory, sram, server):#{{{
        pack = server.packet()
        pack.select_device(board)
        pack.memory(memory)
        pack.sram(sram)
        pack.send()#}}}
    def synthesize(self,data, zero_cal = False, do_normalize = 0.8, max_reps = False,autoSynthSwitch = False,autoReceiverSwitch = False,autoTWTSwitch = False, frontBufferSynth = 25e-9,rearBufferSynth = -15.0e-9,frontBufferReceiver = 200.0e-9, rearBufferReceiver = 100.0e-9, offsetReceiver = 0.0e-9,frontBufferTWT = 170e-9,rearBufferTWT = 10.0e-9,offsetTWT = 150e-9,longDelay = False,manualTrigger = False, manualTriggerChannel = 1,**kwargs):#{{{
            
        if longDelay > 10e-4:
            raise ValueError("The delay is too long, do something less that 10e-4, note this will ultimately give you a 10 ms delay")
        try: # connect to LabRAD unless connection has already been established 
            self.cxn
        except:
            labrad_connect()
        #{{{ Check for start of pulse, throw error if pulse starts too soon.
        findStart = data.copy()
        findStart.data = findStart.runcopy(abs).data
        timeHigh = []
        for count,value in enumerate(findStart.data):
            if value != 0.0:
                timeHigh.append(findStart.getaxis('t')[count])
        timeHigh = array(timeHigh)
        if (timeHigh.min() <= 500e-9) and autoTWTSwitch:
            raise ValueError("The first 500 ns of the pulse need to be zero put a 500 ns delay to start the sequence.")#}}}
        if do_normalize:
            waveI = data.runcopy(real).data * do_normalize
            waveQ = data.runcopy(imag).data * do_normalize
        else:
            waveI = data.runcopy(real).data
            waveQ = data.runcopy(imag).data
        if zero_cal: # this needs to be done!!
            offset_I = 1*self.zero_cal_data[0]
            offset_Q = 1*self.zero_cal_data[1]
            waveI += offset_I
            waveQ += offset_Q
        wave = waveI + 1j*waveQ # put wave back together for hand-off
        try:
            sram = self.wave2sram(wave) # convert waveform to SRAM data
        except ValueError:
            if isnan(real(wave)[0]):
                raise ValueError('real part of wave is NaN')
            elif isnan(imag(wave)[0]):
                raise ValueError('imaginary part of wave is NaN')
            else:
                raise ValueError('value error, but neither real nor imaginary part of wave is NaN')
        if autoSynthSwitch: # Here add a sequence to the sram that puts out a TTL pulse gate to drive a switch from the j24 and j25 ECL outputs. #{{{
            address = 0x40000000
            switchGate = data.copy()
            switchGate.data = abs(switchGate.data)
            # find the bounding values of the pulse
            timeHigh = []
            for count,value in enumerate(switchGate.data):
                if value != 0.0:
                    timeHigh.append(switchGate.getaxis('t')[count])
            switchGate['t',:] = 1.0 # clear all data now and make gate 
            timeHigh = array(timeHigh)
            res = 2*abs(switchGate.getaxis('t')[1] - switchGate.getaxis('t')[0])
            jumps = []
            jumps.append(timeHigh.min())
            jumps.append(timeHigh.max())
            for count in range(1,len(timeHigh)): # look at count val and count-1 val
                if abs(timeHigh[count] - timeHigh[count-1]) > res: # we've hit a jump
                    jumps.append(timeHigh[count -1])
                    jumps.append(timeHigh[count])
            jumps.sort()
            bounds = []
            count = 0
            while count < len(jumps):
                bounds.append([jumps[count],jumps[count+1]])
                count += 2
            switchGate['t',:] = 1.0
            for bound in bounds:
                switchGate['t',lambda x: logical_and(x >= bound[0] - frontBufferSynth, x <= bound[1] + rearBufferSynth)] = 0.0
            for v, val in enumerate(switchGate.data):
                if val > 0.0:
                    try:
                        sram[v] |= address
                    except:
                        pass
        if autoReceiverSwitch: # Here add a sequence to the sram that puts out a TTL pulse gate to drive a switch from the j24 and j25 ECL outputs. #{{{
            address = 0x20000000
            switchGate = data.copy()
            switchGate.data = abs(switchGate.data)

            # find the bounding values of the pulse
            timeHigh = []
            for count,value in enumerate(switchGate.data):
                if value != 0.0:
                    timeHigh.append(switchGate.getaxis('t')[count])
             
            switchGate['t',:] = 1.0 # clear all data now and make gate 
            timeHigh = array(timeHigh)
            res = 2*abs(switchGate.getaxis('t')[1] - switchGate.getaxis('t')[0])
            jumps = []
            jumps.append(timeHigh.min())
            jumps.append(timeHigh.max())
            for count in range(1,len(timeHigh)): # look at count val and count-1 val
                if abs(timeHigh[count] - timeHigh[count-1]) > res: # we've hit a jump
                    jumps.append(timeHigh[count -1])
                    jumps.append(timeHigh[count])
            jumps.sort()
            bounds = []
            count = 0
            while count < len(jumps):
                bounds.append([jumps[count],jumps[count+1]])
                count += 2
            switchGate['t',:] = 0.0
            for bound in bounds:
                switchGate['t',lambda x: logical_and(x >= bound[0] - frontBufferReceiver - offsetReceiver, x <= bound[1] + rearBufferReceiver - offsetReceiver)] = 1.0
            for v, val in enumerate(switchGate.data):
                if val > 0.0:
                    try:
                        sram[v] |= address
                    except:
                        pass
        if autoTWTSwitch: # Here add a sequence to the sram that puts out a TTL pulse gate to drive a switch from the j24 and j25 ECL outputs. #{{{
            address = 0x80000000
            switchGate = data.copy()
            switchGate.data = abs(switchGate.data)
            # find the bounding values of the pulse
            timeHigh = []
            for count,value in enumerate(switchGate.data):
                if value != 0.0:
                    timeHigh.append(switchGate.getaxis('t')[count])
             
            switchGate['t',:] = 1.0 # clear all data now and make gate 
            timeHigh = array(timeHigh)
            res = 2*abs(switchGate.getaxis('t')[1] - switchGate.getaxis('t')[0])
            jumps = []
            jumps.append(timeHigh.min())
            jumps.append(timeHigh.max())
            for count in range(1,len(timeHigh)): # look at count val and count-1 val
                if abs(timeHigh[count] - timeHigh[count-1]) > res: # we've hit a jump
                    jumps.append(timeHigh[count -1])
                    jumps.append(timeHigh[count])
            jumps.sort()
            bounds = []
            count = 0
            while count < len(jumps):
                bounds.append([jumps[count],jumps[count+1]])
                count += 2
            switchGate['t',:] = 0.0
            for bound in bounds:
                switchGate['t',lambda x: logical_and(x >= bound[0] - frontBufferTWT - offsetTWT, x <= bound[1] + rearBufferTWT - offsetTWT)] = 1.0
            for v, val in enumerate(switchGate.data):
                if val > 0.0:
                    try:
                        sram[v] |= address
                    except:
                        pass
        if manualTrigger is not False:
            addressDict = {
                    1 : 0x20000000, # 1 -> reciever switch
                    2 : 0x40000000, # 2 -> transmitter switch
                    3 : 0x80000000, # 3 -> twt switch
                    }
            try:
                manualTriggerAddress = addressDict[manualTriggerChannel]
            except:
                raise ValueError('The manual trigger channel must be 1, 2, or 3')
            for trigger in manualTrigger: # manual trigger is a list of tuples with format -> (position,length) units of ns -> i.e. position and length must be integers
                position = trigger[0]
                length = trigger[1]
                for i in range(position,position+length):
                    sram[i] |= manualTriggerAddress
        if longDelay:
            for i in range(5,20):
                sram[i] |= 0x10000000 # add trigger pulse at beginning of sequence
            self.dacSignal(sram,delay = longDelay)
        else:
            sram[0] |= 0x10000000 # add trigger pulse at beginning of sequence
            self.fpga.dac_run_sram(sram, True)#}}}
    def wave2sram(self,wave):#{{{
        r'''Construct sram sequence for waveform. This takes python array and converts it to sram data for hand off to the FPGA. Wave cannot be nddata - this is stupid...'''
        waveA = real(wave)
        waveB = imag(wave)
        if not len(waveA)==len(waveB):
            raise Exception('Lengths of DAC A and DAC B waveforms must be equal.')
        dataA=[long(floor(0x1FFF*y)) for y in waveA] # Multiply wave by full scale of DAC
        dataB=[long(floor(0x1FFF*y)) for y in waveB]
        truncatedA=[y & 0x3FFF for y in dataA] # Chop off everything except lowest 14 bits
        truncatedB=[y & 0x3FFF for y in dataB]
        dacAData=truncatedA
        dacBData=[y<<14 for y in truncatedB] # Shift DAC B data by 14 bits, why is this done??
        sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))] # Combine DAC A and DAC B
        return sram#}}}
    def downsample(self,inputdata, bandwidth = 1e9):#{{{
        data = inputdata.copy()
        x = data.getaxis('t')
        data.ft('t', shift=True)
        data = data['t',lambda x: abs(x)<5e8] # slice out the center
        f = data.getaxis('t')
        data.data *= exp(-(f**2)/(2.0*((bandwidth/6.)**2))) # multiply by gaussian
        data.ift('t',shift=True)
        return data#}}}

