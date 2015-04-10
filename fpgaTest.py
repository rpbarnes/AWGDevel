# Author: Daniel Sank
# Created: 2010

# CHANGELOG
#
# 2012 Sep 26 - Jim Wenner
# Added documentation. Added adcAmpToVoltage, dacAmpToAdcAmp, dacAmpToVoltage to calibrate
# adc/dac wrt Volts. Code debugging.
#
# 2011 Feb 10 - Daniel Sank
# Added the instructions

# + STARTUP INSTRUCTIONS
# In order to use fpgaTest.py follow these instructions:
# 1. Make a shortcut to Ipython.
# 2. Set up the shortcut to run the conf.py file found in this directory
  # a. Right click on the shorcut and choose Properties.
  # b. In the Target field add "<labrad path>\scripts\fpgaTest\conf.py"
  #    The complete target path should be something like this:
  #    C:\Python26\python.exe C:\Python26\scripts\ipython <labrad path>\scripts\fpgaTest\conf.py
  # c. Set the Start In field to "<labradPath>\scripts\fpgaTest"
# 3. Make sure you are connected to the LabRAD system, either through Commando using Putty or by working on a computer that's on the Gbit network.
  # a. Make sure you have the direct ethernet and GHzFPGA servers running
# 4. Set up the LabRAD registry
  # a. Create a directory in the LabRAD registry called TestUser
  # b. Inside TestUser create
    # i. directory 'fpgaTest'
    # ii. key sample = ['fpgaTest']
  # c. Inside fpgaTest create
    # i. key config = [<boardName0>,<boardName1>,...].
    #    Board names must match the names you get when you call the list_devices() setting on the GHzFPGA server.
    # ii. directories <boardName0>, <boardName1>,...
  # d. Create waveform definition keys in the directory for each board.
    # i. DAC
      # I.      _id = <boardName>, must match name of directory
      # II.     signalAmplitude = [amplitudeDacA,amplitudeDacB],    eg. [0.5,0.3]
      # III.    signalDc = [dcLevelDacA,dcLevelDacB],               eg. [0.001,0.000]
      # IV.     signalFrequency = [freqDacA,freqDacB],              eg. [2.0 MHz, 5.0 MHz]
      # V.      signalPhase = [phaseDacA,phaseDacB],                eg. [0.0, 0.01] (this is in CYCLES)
      # VI.     signalTime = totalWaveformTime                      eg. 3.0 us
      #VII.     signalWaveform = [waveformDacA,waveformDacB]        eg. ['sine','square']
    # ii. ADC
      # I.      _id = <boardName>, must match name of directory
      # II.     demods = [(ch0Freq,ch0Phase,ch0CosAmp,ch0SinAmp),...(ch3Freq,ch3Phase,ch3CosAmp,ch3SinAmp)],
      #         eg. [(10.0 MHz, 0, 255, 255),...]
      # III.    filterFunc = (type,width)                           eg. ('gaussian',0.1)
      # IV.     filterStretchAt = index to use for the stretch ,    eg. 0
      # V.      filterStretchLen = length of filter stretch         eg. 0
      # Using 0 for filterAt and filterStretch gives you no stretch, use nonzero values to get stretch
# 5. Double click the shortcut you made in steps 1 and 2.
# 6. You now have an open python session. To use the functions in fpgaTest.py enter commands as follows:
# >> fpgaTest.functionName(s,fpga, <other arguments>) or fpgaTest.functionName(s,cxn, <other arguments>)
# The first argument "s" gives the program information about what boards you're
# running. The second argument essentially gives the program a LabRAD connection object
# so that it can make requests on the LabRAD system.
# inf. Read the source code to see what functions are available. Have fun :)
# 

#TODO
#
# In ADC scans, use all four available demod channels to make things run faster

import sys
import time
import numpy as np
#from msvcrt import getch, kbhit  # Disabled by Evan because it won't import on Linux.  Should find a better fix
import matplotlib.pyplot as plt
import scipy
from scipy.optimize import curve_fit
from scipy.special import erf
import scipy.interpolate
import labrad
from labrad.units import Value, GHz, MHz, Hz, ns, us, V

FPGA_SERVER = 'ghz_fpgas'
DATA_VAULT = 'data_vault'

from servers.GHzDACs.Cleanup import dac as dacModule
#from servers.GHzDACs.Cleanup import adc as adcModule
#import pyle.registry
#import pyle.dataking.util as dataUtil
#import pyle.util.sweeptools as st
#from pyle import envelopes as env
#from pyle.util.structures import ValueArray
#import pyle.analysis.signalProcessing as sp

#from fpgaTestUtil import loadDacsAdcs, boardName2Info

import servers.GHzDACs.jumpTable as jt

ADC_DEMOD_CHANNELS = 12
#ADC_DEMOD_CHANNELS = 4
DAC_ZERO_PAD_LEN = 0
DAC_CHANNELS=2

DIRECT_ETHERNET = None

def get_direct_ethernet(sample):
    if "DirectEthernet" in sample:
        return sample['DirectEthernet']
    else:
        if not DIRECT_ETHERNET:
            DIRECT_ETHERNET=raw_input('direct ethernet server: ')
    return DIRECT_ETHERNET

#########################
## Communication check ##
#########################
    
def pingBoardDirect(de, port, boardName, verbose=False):
    """Use the direct ethernet server directly to ping a board
    Do not call this function is someone is taking data!!! You are bypassing
    the FPGA server and therefore can muck up synchronized operation. If you run
    this function
    PARAMETERS
    ----------
    de: server wrapper
        Object pointing to the direct ethernet server talking to the board you
        want to ping.
    port: number
        Port number, on the direct ethernet server, connected to your board.
    boardName: str
        The board's name, eg. 'Vince DAC 11'
        
    OUTPUT
    ----------
    (str - raw packet response from board, dict - parsed response)

    See the processReadback functions in adc.py and dac.py for format of
    parsed responses.
    """
    boardNumber, boardType = boardName2Info(boardName)
    if boardType == 'DAC':
        module = dacModule
    elif boardType == 'ADC':
        module = adcModule
    else:
        raise Exception('Board type not recognized')
    mac = module.macFor(boardNumber)
    ctxt = de.context()                     #Get a new context to work with
    try:
        p = de.packet(context=ctxt)
        p.connect(port, context=ctxt)           #Choose ethernet port
        p.require_source_mac(mac, context=ctxt) #Receive only packets from the board's mac address
        p.destination_mac(mac, context=ctxt)    #Set the destination mac of our outgoing packets
        p.listen(context=ctxt)                  #Start listening for packets
        boardPkt = module.regPing()
        p.write(boardPkt.tostring())            #Convert the board packet to a byte string and write it out over the wire
        p.timeout(1.0)
        p.read()
        result = p.send()                       #Send the direct ethernet server packet and get the result
        raw = result.read
        src, dst, eth, data = raw
        parsedInfo = module.processReadback(data)
        if verbose:
            print '\n'
            print 'Response from direct ethernet server: \n'
            print raw[3]
            print '\n'
            print 'Parsed response:'
            for key,value in parsedInfo.items():
                print key,value
    finally:
        de._cxn.manager.expire_context(context=ctxt)
    return (raw,parsedInfo)
    
def getBuildNumber(fpga, device):
    """Use the FPGA server to get a board build number.
    PARAMETERS
    ---------
    device - str: Name of device
    
    OUTPUT
    ---------
    str - board build number
    """
    fpga.select_device(device)
    buildNumber = fpga.build_number()
    return buildNumber
    
def hammarEthernet(de, port, boards, numRuns):
    """Send many register ping packets to the boards to check reliability of ethernet connection
    
    Packets for each board are sent sequentially, ie. not at the same time. This means we are
    testing only the bare ethernet communication for individual channels and are not sensitive
    to packet collision type failure modes.
    """
    boardInfo = [boardName2Info(board) for board in boards]
    boardRegs = []
    ctxts = []
    macs = []
    modules = {'DAC': dacModule, 'ADC': adcModule}
    #Get a direct ethernet context, MAC, and register packet for each board
    for num, boardType in zip(boards, boardInfo):
        module = modules[boardType]
        boardRegs.append(module.regPing())
        ctxts.append(de.context())
        macs.append(module.macFor(num))
    #Set up connection to direct ethernet, one context per board
    for ctxt, mac in zip(ctxts, macs):
        p = de.packet(context=ctxt)
        p.timeout(1.0)
        p.connect(port, context=ctxt)                   #Choose ethernet port
        p.require_source_mac(mac, context=ctxt)         #Receive only packets from the board's mac address
        p.destination_mac(mac, context=ctxt)            #Set the destination mac of our outgoing packets
        p.listen(context=ctxt)                          #Start listening for packets
        p.send()
    #Ping the boards a lot
    for _ in range(numRuns):
        for regs, ctxt in zip(boardRegs, ctxts):
            p = de.packet(context=ctxt)
            p.write(regs.tostring(), context=ctxt)      #Convert the board packet to a byte string and write it out over the wire
            p.send()                                    #Send the direct ethernet server packet
    #Check to see that number of returned packets is as expected
    try:
        for ctxt in ctxts:
            p = de.packet(context=ctxt)
            p.timeout(10)
            p.collect(numRuns)
            p.send()
    except Exception:
        print Exception
        print 'Some boards dropped packets'
    finally:
        print 'Sequence done'
        print 'Check packet buffer. Number of packets should be %d' %numRuns
        print 'Then hit any key to continue'
        while kbhit():
            getch()
        getch()
        for ctxt in ctxts:
            de._cxn.manager.expire_context(context=ctxt)
    
def daisyCheck(sample, cxn, iterations, repsPerIteration, runTimers, getData=True):
    """Set up a synchronized sequence on multiple boards and run it many times
    
    This function is designed to make sure the daisychain is working. It can
    also be used to check whether the boards are running the correct number
    of times.
    
    INPUTS
    iterations, int: number of time to run run_sequence
    repsPerIteration, int: number of reps per run_sequence
    runTimers, bool: True will run timers on DAC boards. False will not.
    
    RETURNS
    Array of size (iterations x N) where N is number of boards returning
    timing data. Entry  ij is the number of times the jth board executed
    on the ith iteration.
    
    It is possible to use this function in a way such that no data is
    returned by any boards. If you do this, the expected number of
    packets returned to the direct ethernet server is zero, so the
    collect call returns immediately, even if the sequence is still
    running. In that case, this function's call to execution_count
    can happen before the boards are actually done executing. In this
    case the execution count will come back with a random number that is
    lower than the intended number. If you then check execution count
    again, the boards will have finished and the count will be what you
    expected.
    """
    fpga = cxn.ghz_fpgas
    de = cxn[sample['directEthernet']]
    dacs, adcs = loadDacsAdcs(sample)
    for dac in dacs:
        dac['signalTime'] = 4.0*us
        sramLen = int(dac['signalTime']['ns'])
        #Construct the memory sequence for the DAC boards.
        #Note that the total memory sequence times are longer than the
        #packet transmission time of 10us. Also note that we include
        #an explicit delay in the DAC boards after running SRAM
        #to allow for the ADC boards to finish demodulating.
        memorySequence = [0x000000, # NoOp                                         1 cycle
                          0x800000, # SRAM start address                           1 cycle
                          0xA00000 + sramLen - 1, # SRAM end address               1 cycle
                          0xC00000, # call SRAM                                  100 cycles for 4us (300 assumed by fpga server)
                          0x300190] # Delay 400+1 cycles = 16us for ADC demod    401 cycles ... total 504 cycles
        
        if runTimers:
            memorySequence.extend([0x400000,  # start timer                        1 cycle
                                   0x300064,  # Delay 100+1 cycles, 4us          101 cycles
                                   0x400001]) # stop timer                         1 cycle ... 103 cycles
                                   
        memorySequence.extend([0xF00000]) # Branch back to start                   2 cycles... 2 cycles
        
        #Sequence times
        # With timers = 609 actual = 24.3us
        # No timers   = 506 actual = 20.2us
        #Note that the GHzFPGA server will always assume the SRAM is 12us long = 300 cycles
        #when estimating sequence length.
        
        dac['memory'] = memorySequence
        waves=makeDacWaveforms(dac)
        dac['sram']=waves2sram(waves[0],waves[1], triggerIndices=range(100))
    for adc in adcs:
        adc['runMode'] = 'demodulate'
    daisychainList = [dac['_id'] for dac in dacs] + [adc['_id'] for adc in adcs]
    #Timing data includes the ADC always, and the DACs if we ran the timers
    timingOrderList = ['%s::%d' %(adc['_id'],chan) for adc in adcs for chan in range(ADC_DEMOD_CHANNELS)]
    if runTimers:
        timingOrderList.extend([dac['_id'] for dac in dacs])
    executions = np.array([])
    for iteration in range(iterations):
        print 'Running iteration %d' %iteration
        #Set up DAC
        [_sendDac(dac,fpga) for dac in dacs]
        #Set up ADC
        [_sendAdc(adc,fpga) for adc in adcs]
        #Set up board group
        fpga.daisy_chain(daisychainList)
        fpga.timing_order(timingOrderList)
        #Run the sequence
        try:
            result = fpga.run_sequence(repsPerIteration, getData)
        except Exception, e:
            print 'Error in sequence run: %s'%e
        #Whether or not there is an error, ping all boards to check how many times they executed
        finally:
            for board in dacs+adcs:
                name = board['_id']
                fpga.select_device(name)
                resp = fpga.execution_count()
                executions = np.hstack((executions, resp))
    print [board['_id'] for board in dacs+adcs]
    return np.reshape(executions, (iterations,-1))


###############
## PLL CHECK ##
###############

def initializePll(fpga, device):
    """Reset DAC PLL"""
    fpga.select_device(device)
    fpga.pll_init()

###############
## DAC CHECK ##
###############

def dacSignal(sample, fpga, reps=30, loop=False, getTimingData=False, trigger=None, dacs=None):
    """Send SRAM sequences out of DAC boards.
    
    PARAMETERS
    --------------
    reps - int: number of times to repeat SRAM sequence. Only used when loop=False.
    
    loop - bool: If True, each board will loop through its SRAM sequence
    continuously until stopped (ie. told to do something else).  This
    uses fpga.dac_run_sram which is completely asynchronous execution,
    (ie. daisychain not used, boards not synched together).
    If False, each board will run through its SRAM a number of times
    determined by reps, and will then idle at the first SRAM value.
    (I don't know if this is the first physical SRAM address or the
    one given by the SRAM start address, ie. memory code 0x8...)
    This uses fpga.run_sequence which _does_ use the daisychain and
    therefore ensures that each board starts at the same time. However,
    boards with different SRAM lengths won't line up after the rep.
    
    getTimingData - bool: Whether or not to collect timing data from the
    boards. If true, the data is returned.
    
    trigger - iterable: sequence defining trigger output. For alternating
    on/off use trigger = np.array([1,0,1,0,...]) etc.
    1=trigger on, 0=trigger off
    
    OUTPUT
    ----------
    Array of timing results. See fpga server for details.
    """
    if dacs is None:
        dacs,adcs = loadDacsAdcs(sample)
    
    for dac in dacs:
        #Set up DAC
        sramLen = int(dac['signalTime']['ns'])
        #memory Sequence
        memory=dacModule.MemorySequence()
        memory.noOp().sramStartAddress(0).sramEndAddress(sramLen-1)\
        .runSram().delayCycles(200).branchToStart()
        dac['memory']=memory
        
        #sram
        waves=makeDacWaveforms(dac)
        dac['sram'] = waves2sram(waves[0],waves[1])
        #Optional custom trigger
        if trigger is not None:
            dac['sram'] = dacTrigger(dac['sram'][:],trigger)
            
        _sendDac(dac,fpga)
    
    #Set up board group
    daisychainList=[dac['_id'] for dac in dacs]
    timingOrderList=[dac['_id'] for dac in dacs]
    fpga.daisy_chain(daisychainList)
    fpga.timing_order(timingOrderList)

    if loop:
        for dac in dacs:
            fpga.select_device(dac['_id'])
            fpga.dac_run_sram(dac['sram'], loop)
    else:
        if getTimingData:
            return fpga.run_sequence(reps, getTimingData)
        else:
            fpga.run_sequence(reps, getTimingData)
    
def commensurateFrequency(freq, bufferLen, sampleRate = 1.0*GHz):
    x = (freq / sampleRate).value
    cycles = int(round(x*bufferLen))
    freq_fix = cycles * sampleRate / bufferLen
    buf = np.sin(np.arange(bufferLen) * (2 * np.pi * cycles) / bufferLen)
    return buf, freq_fix
    
def correctSram(cxn, dac, I, Q, loop=False):
    """Correct IQ data with deconvolution server
    
    Keeps a dynamic reserve of 2x
    """
    z = I + 1.0j*Q
    cal = cxn.dac_calibration
    p = cal.packet()
    p.board(dac['_id'])
    p.frequency(dac['carrierFrequency'])
    p.loop(loop)
    p.correct(z, key='corrected')
    result = p.send()
    correctedSram = result['corrected']
    return correctedSram[0],correctedSram[1]
    
def correctSram_z(cxn, board, data, loop=False):
    cal = cxn.dac_calibration
    p = cal.packet()
    p.board(board['_id'])
    p.loop(loop)
    p.dac(0)
    p.correct(data, key='corrected')
    result = p.send()
    correctedData = result['corrected']
    return correctedData
    
def dacify(I, Q):
    """Takes I and Q waveforms in DAC click units and returns packed SRAM data
    
    Trigger on for first 200 samples

    Returns:
        List of long ints. Each one tostrings to a DAC word.
    """
    sramI = [long(i) for i in I]
    sramQ = [long(q) for q in Q]
    truncatedI=[y & 0x3FFF for y in sramI]  # Keep lower 14 bits
    truncatedQ=[y & 0x3FFF for y in sramQ]  # Keep lower 14 bits
    dacAData = truncatedI
    dacBData=[y<<14 for y in truncatedQ]
    sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))]
    for i in range(10):
        sram[i] |= 0xF0000000
    return sram
    
def dacSignalCorrected(sample, fpga, numSamples, sbFreqs_GHz, amps, phases=[0.0,0.0], trigger=None, dac=None, loop=True):
    """Run looping SRAM corrected by deconvolution server
    
    This is designed to give a calibration of uwave power vs DAC
    amplitude when the deconvolution server is in effect.
    
    PARAMETERS:
    sbFreq_GHz - float: Frequency of the GHz DACs. This will sideband mix
        with the carrier frequency
        
    TODO:
    Make sure sbFreq_GHz is not specified beyond a MHz.
    """
    print 'you are not crazy'
    cxn = sample._cxn
    if dac is None:
        dacs,adcs = loadDacsAdcs(sample)
        if len(dacs)>1:
            raise Exception('Only one dac allowed')
        dac = dacs[0]
    
    #Set carrier
    carrierServer = sample._cxn[dac['uwSourceServer']]
    carrierServer.select_device(dac['uwSourceId'])
    carrierHarmonic = dac.get('carrierHarmonic',1.0)
    carrierServer.frequency(dac['carrierFrequency']/carrierHarmonic)
    carrierServer.amplitude(dac['uwSourcePower'])
    #Signal parameters
    dac['signalDC'] = [0, 0]
    sramLen = numSamples
    #MEMORY
    memory = [
        0x000000, # NoOp
        0x800000, # SRAM start address
        0xA00000 + sramLen - 1, # SRAM end address
        0xC00000, # call SRAM
        0x3000FF, # Delay 255+1 clock cycles 
        0xF00000, # Branch back to start
    ]
    dac['memory']=memory
    #SRAM
    t_ns = np.arange(numSamples)
    I = sum([a*np.cos(2*np.pi*(t_ns*sbFreq_GHz - 0.25 + phase)) for a,sbFreq_GHz,phase in zip(amps, sbFreqs_GHz,phases)])
    Q = sum([a*np.cos(2*np.pi*(t_ns*sbFreq_GHz + phase)) for a,sbFreq_GHz,phase in zip(amps, sbFreqs_GHz,phases)])
    waves = [I,Q]
    #waves = [amp*np.cos(2*np.pi*(t_ns*sbFreq_GHz - 0.25 + phase)),amp*np.cos(2*np.pi*(t_ns*sbFreq_GHz + phase))]
    #correct signal
    correctedI, correctedQ = correctSram(cxn, dac, waves[0], waves[1], loop=loop)
    #Pack data for fpga server
    dac['sram'] = dacify(correctedI,correctedQ)
    #Optional custom trigger
    if trigger is not None:
        dac['sram'] = dacTrigger(dac['sram'][:],trigger)
    _sendDac(dac,fpga)
    
    #Set up board group
    daisychainList=[dac['_id']]
    timingOrderList=[dac['_id']]
    fpga.daisy_chain(daisychainList)
    fpga.timing_order(timingOrderList)
    #If looping mode, just start each dac running asynchronously
    if loop:
        fpga.select_device(dac['_id'])
        fpga.dac_run_sram(dac['sram'], True)
    else:
        fpga.run_sequence(args)
    
def correctedStep(sample, fpga, amp=None, trigger=None, dacs=None,pulseLength=400*ns,correct=True):
    """Run a deconolved step function from an analog board"""
    if dacs is None:
        dacs,adcs = loadDacsAdcs(sample)
    
    for dac in dacs:
        #Set up DAC
        dac['signalWaveform'] = ['step', 'step']
        dac['signalDC'] = [0, 0]
        dac['signalTime'] = 6*us
        dac['pulseLength']=pulseLength
        if amp is not None:
            dac['signalAmplitude'] = [amp, amp]
        sramLen = int(dac['signalTime']['ns'])
        memory = [
            0x000000, # NoOp
            0x800000, # SRAM start address
            0xA00000 + sramLen - 1, # SRAM end address
            0xC00000, # call SRAM
            0x3000FF, # Delay 255+1 clock cycles 
            0xF00000, # Branch back to start
        ]
        dac['memory']=memory
        
        #sram
        waves=makeDacWaveforms(dac)
        #correct signal
        if correct:
            calibration = sample._cxn.dac_calibration
            p = calibration.packet()
            p.board(dac['_id'])
            p.loop(True)
            p.dac(0)
            p.correct(waves[0], key='correctedI')
            p.dac(1)
            p.correct(waves[1], key='correctedQ')
            result = p.send()
            correctedI = result['correctedI']
            correctedQ = result['correctedQ']
        else:
            correctedI =waves[0]*2**12
            correctedQ =waves[1]*2**12
        plt.figure()
        plt.plot(waves[0]*2**12)
        plt.plot(waves[1]*2**12)
        plt.plot(correctedI)
        plt.plot(correctedQ)
        sramI = [long(i) for i in correctedI]
        sramQ = [long(q) for q in correctedQ]
        truncatedI=[y & 0x3FFF for y in sramI]
        truncatedQ=[y & 0x3FFF for y in sramQ]
        dacAData = truncatedI
        dacBData=[y<<14 for y in truncatedQ]
        sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))] #Combine DAC A and DAC B
        for i in range(32):
            sram[i] |= 0xF0000000
        dac['sram'] = sram
        #Optional custom trigger
        if trigger is not None:
            dac['sram'] = dacTrigger(dac['sram'][:],trigger)
        _sendDac(dac,fpga)
    
    #Set up board group
    daisychainList=[dac['_id'] for dac in dacs]
    timingOrderList=[dac['_id'] for dac in dacs]
    fpga.daisy_chain(daisychainList)
    fpga.timing_order(timingOrderList)

    for dac in dacs:
        fpga.select_device(dac['_id'])
        fpga.dac_run_sram(dac['sram'], True)
        
def correctedPulse(sample, fpga, pulse='step', amp=None, trigger=None, dacs=None,pulseLength=400*ns,correct=True):
    """Run looping SRAM corrected by deconvolution server
    """
    if dacs is None:
        dacs,adcs = loadDacsAdcs(sample)
    
    for dac in dacs:
        #Set up DAC
        dac['signalWaveform'] = [pulse, pulse]
        dac['signalDC'] = [0, 0]
        dac['signalTime'] = 6*us
        dac['pulseLength']=pulseLength
        if amp is not None:
            dac['signalAmplitude'] = [amp, amp]
        sramLen = int(dac['signalTime']['ns'])
        memory = [
            0x000000, # NoOp
            0x800000, # SRAM start address
            0xA00000 + sramLen - 1, # SRAM end address
            0xC00000, # call SRAM
            0x3000FF, # Delay 255+1 clock cycles 
            0xF00000, # Branch back to start
        ]
        dac['memory']=memory
        
        #sram
        waves=makeDacWaveforms(dac)
        #correct signal
        if correct:
            calibration = sample._cxn.dac_calibration
            p = calibration.packet()
            p.board(dac['_id'])
            p.loop(True)
            p.dac(0)
            p.correct(waves[0], key='correctedI')
            p.dac(1)
            p.correct(waves[1], key='correctedQ')
            result = p.send()
            correctedI = result['correctedI']
            correctedQ = result['correctedQ']
        else:
            correctedI =waves[0]*2**12
            correctedQ =waves[1]*2**12
        plt.figure()
        plt.plot(waves[0]*2**12)
        plt.plot(waves[1]*2**12)
        plt.plot(correctedI)
        plt.plot(correctedQ)
        sramI = [long(i) for i in correctedI]
        sramQ = [long(q) for q in correctedQ]
        truncatedI=[y & 0x3FFF for y in sramI]
        truncatedQ=[y & 0x3FFF for y in sramQ]
        dacAData = truncatedI
        dacBData=[y<<14 for y in truncatedQ]
        sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))] #Combine DAC A and DAC B
        for i in range(32):
            sram[i] |= 0xF0000000
        dac['sram'] = sram
        #Optional custom trigger
        if trigger is not None:
            dac['sram'] = dacTrigger(dac['sram'][:],trigger)
        _sendDac(dac,fpga)
    
    #Set up board group
    daisychainList=[dac['_id'] for dac in dacs]
    timingOrderList=[dac['_id'] for dac in dacs]
    fpga.daisy_chain(daisychainList)
    fpga.timing_order(timingOrderList)

    for dac in dacs:
        fpga.select_device(dac['_id'])
        fpga.dac_run_sram(dac['sram'], True)


################
## JUMP TABLE ##
################

# Write data to board

def sram_write_packet(p, sram, derp):
    """Update a de packet to write sram.

    Args:
        sram - ndarray, dtype <u4: Each element is a single SRAM word,
            i.e. 1ns of data.
    """

    # SRAM_WRITE_LEN = 1026

    pkt = np.zeros(2, dtype='<u1')
    # DAC firmware assumes SRAM write address lowest 8 bits = 0, so here
    # we're only setting the middle and high byte. This is good, because
    # it means that each time we increment derp by 1, we increment our
    # SRAM write address by 256, ie. one derp.
    pkt[0] = (derp >> 0) & 0xFF
    pkt[1] = (derp >> 8) & 0xFF
    s = pkt.tostring() + sram.tostring()
    p.write(s)

def jump_table_write_packet(p, table):
    """Modify a direct ethernet packet to write the jump table.

    Args:
        p: the packet to update
        table: JumpTable instance to be serialized and written
    """
    print len(table.toString())
    p.write(table.toString())

def register_write_packet(p):
    """Modify a packet to send a register start.

    Values are hardcoded because physics.
    """
    pkt = np.zeros(56, dtype='<u1')
    pkt[0] = 1  # master start
    pkt[13] = 1  # 1 cycle
    pkt[17] = 0  # Which jump table to count activations of
    pkt[51] = 2  # Monitor 0
    pkt[52] = 2  # Monitor 1
    p.write(pkt.tostring())


def test_jump_table_normal(fpga, de, length=60):
    waveform, table = jt.testNormal(length)
    p = de.packet()
    de.connect(0)  # Yes, hardcode is bad.
    de.destination_mac('00:01:CA:AA:00:01')
    sram = dacify(waveform, waveform)
    sram = np.array(sram, dtype='<u4')
    # Write sram
    sram_write_packet(p, sram, 0)

    # write an extra derp of 0's
    sram_write_packet(p, np.zeros_like(sram), 1)

    # Write jump table
    jump_table_write_packet(p, table)
    # Go!
    register_write_packet(p)
    p.send()


def test_jump_table_idle(fpga, de, idle_cycles):
    waveform, table = jt.testIdle(idle_cycles)
    p = de.packet()
    de.connect(0)  # Yes, hardcode is bad.
    de.destination_mac('00:01:CA:AA:00:01')
    sram = dacify(waveform, waveform)
    sram = np.array(sram, dtype='<u4')
    # Write sram
    sram_write_packet(p, sram, 0)

    # Write jump table
    jump_table_write_packet(p, table)
    # Go!
    register_write_packet(p)
    p.send()


def test_jump_table_jump(fpga, de):
    waveform, table = jt.testJump()
    p = de.packet()
    de.connect(0)
    de.destination_mac('00:01:CA:AA:00:01')
    sram = dacify(waveform, waveform)
    sram = np.array(sram, dtype='<u4')
    # Write sram
    sram_write_packet(p, sram, 0)

    # Write jump table
    jump_table_write_packet(p, table)
    # Go!
    register_write_packet(p)
    p.send()


def test_jump_table_cycle(fpga, de, num_cycles=10):
    waveform, table = jt.testCycle(num_cycles)
    p = de.packet()
    de.connect(0)
    de.destination_mac('00:01:CA:AA:00:01')
    sram = dacify(waveform, waveform)
    sram = np.array(sram, dtype='<u4')
    # Write sram
    sram_write_packet(p, sram, 0)

    # Write jump table
    jump_table_write_packet(p, table)
    # Go!
    register_write_packet(p)
    p.send()
