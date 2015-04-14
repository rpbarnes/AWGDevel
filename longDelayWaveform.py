import labrad
import pylab as py
import time 
from servers.GHzDACs.Cleanup import dac as dacModule

### Function copied from fpgaTest.py#{{{
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
    for i in range(2): 
        sram[i] |= 0x30000000
    return sram#}}}
def wave2sram(waveA,waveB):#{{{
    r'''Construct sram sequence for waveform. This takes python array and converts it to sram data for hand off to the FPGA. Wave cannot be nddata - this is stupid...'''
    if not len(waveA)==len(waveB):
        raise Exception('Lengths of DAC A and DAC B waveforms must be equal.')
    dataA=[long(py.floor(0x1FFF*y)) for y in waveA] # Multiply wave by full scale of DAC
    dataB=[long(py.floor(0x1FFF*y)) for y in waveB]
    truncatedA=[y & 0x3FFF for y in dataA] # Chop off everything except lowest 14 bits
    truncatedB=[y & 0x3FFF for y in dataB]
    dacAData=truncatedA
    dacBData=[y<<14 for y in truncatedB] # Shift DAC B data by 14 bits, why is this done??
    sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))] # Combine DAC A and DAC B
    return sram#}}}

# bring the fpga to life
cxn = labrad.connect()
fpga = cxn.ghz_fpgas
server = cxn.han_direct_ethernet
boards = fpga.list_devices()
board = boards[0][1]
fpga.select_device(board)

# a simple waveform to send to the DAC
sram = py.zeros([2,1000]) # [[real],[imag]]
sram[0][150:200] = 0.10 # a 50 ns long pulse 

sram = wave2sram(sram[0],sram[1])
for i in range(5,20):
    sram[i] |= 0x30000000 # add trigger pulse at beginning of sequence

fpga.dac_run_sram(sram,True) # just test to make sure we can play a waveform.
print "I'm sleeping for 5 seconds"
time.sleep(5)
print "Done sleeping, now loading new memory"

# Now make a memory list to send to the dac so we can get a repetition delay longer that 10 us.
sramLen = len(sram)
#memory = [
#    0x000000, # NoOp
#    0x800000, # SRAM start address
#    0xA00000 + sramLen - 1, # SRAM end address
#    0xC00000, # call SRAM
#    0x30C350, # Delay 2ms (50000 cycles = 2ms since clock is 25 MHz)
#    0x400000, # start timer
#    0x400001, # stop timer
#    0xF00000, # branch back to start
#]
#memory = [
#    0x000000, # NoOp
#    0x800000, # SRAM start address
#    0xA00000 + sramLen - 1, # SRAM end address
#    0xC00000, # call SRAM
#    0x3000FF, # Delay 255+1 clock cycles 
#    0xF00000, # Branch back to start
#]


# use Daniel's method of generating memory sequence from the DAC module
memory=dacModule.MemorySequence()
memory.noOp().sramStartAddress(0).sramEndAddress(sramLen-1).runSram().delayCycles(2000).branchToStart()


# is it possible that this is looking for direct ethernet connection instead of fpga? No, it doesn't want a direct ethernet connection....
p = fpga.packet()
p.select_device(board)
p.memory(memory)
p.sram(sram)
p.send()

try:
    while True:
        fpga.run_sequence(50000, False)
except KeyboardInterrupt:
    print "Exiting code"

