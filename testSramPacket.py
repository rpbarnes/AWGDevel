import synthesize as s
p = s.pulsegen()


wave = p.make_highres_waveform([('delay',500e-9),('rect','x',50e-9),('delay',1e-6-550e-9)],resolution = 1e-9) # make sure we specify resolution appropriately.
longDelay = 10e-6

reps = 50000
getTimingData = False

sram = p.wave2sram(wave.data) ### Make sram data packet
sram[16] |= 0x30000000 ### Add trigger for scopes

sramLen = len(sram)
# memory sequence
NoOp = [0x000000]
start_timer = p.gen_code(4,0)
stop_timer = p.gen_code(4,1)
sram_based_timer = p.gen_code(4,2) # documentation says not implemented yet
play_SRAM = p.gen_code(0xC,0) # he calls this "call SRAM"
end_of_sequence = p.gen_code(0xF,0) # branch to beginning --> takes two clocks

# make the memory to write to the sram.
#memory = NoOp + p.SRAM_range(0,sramLen) + play_SRAM + p.delay(longDelay) +  end_of_sequence
memory = NoOp + p.SRAM_range(0,sramLen) + play_SRAM + p.delay(longDelay) +  end_of_sequence

# test memory list, lets see what it does...
memoryTest = [
    0x000000, # NoOp
    0x800000, # SRAM start address
    0xA00000 + sramLen - 1, # SRAM end address
    0xC00000, # call SRAM
    # 0x3186A0, # Delay 4ms to ensure average mode readback completes on A/D
    0x30C350 - 100, # Delay 2ms (50000 cycles = 2ms since clock is 25 MHz)
    # Don't know why I need the delay 300 ns shorter, but this gives me an exact 
    # repetition frequency of 500 Hz.
    0x400000, # start timer
    0x400001, # stop timer
    0xF00000, # branch back to start
]



for i in range(81):
    memory.insert(5, 0x30C350 - 100)
    memory.insert(5, 0xC00000)

p._sendDac(memoryTest,sram,p.fpga)
p.fpga.run_sequence(reps, getTimingData)#}}}
#p.fpga.dac_run_sram(sram,True)

del p
