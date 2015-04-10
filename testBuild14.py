import labrad
import time
import fpgaTest as ft # This is kind of messy. I'll just call jumptables as ft.jt. - 


# Script to test build 14 with most recent code from 'servers' on 'jump_table_bench_test' branch. Also using most recent pull of 'pylabrad' on 'master' branch. 

cxn = labrad.connect()
fpga = cxn.ghz_fpgas
fpga.select_device('Han Lab DAC 1')
print fpga.build_number()
de = cxn.han_direct_ethernet


# I copy past from test_jump_table_idle() but put here for clarity and also so I can mess with the code.
idle_cycles = 100
waveform, tab = ft.jt.testIdle(idle_cycles)
p = de.packet()
de.connect(0)  # This connects to ethernet connection made in direct ethernet. I've checked and made sure this is the ethernet connection that is talking to the dac board.
de.destination_mac('00:01:CA:AA:00:01') # This is the board's mac. I verufy this by changing last to 03 and see that nothing gets sent to the board.
sram = ft.dacify(waveform, waveform)
sram = np.array(sram, dtype='<u4')

# Write sram
ft.sram_write_packet(p, sram, 0)
# Write jump table
ft.jump_table_write_packet(p, tab)
# Go!
ft.register_write_packet(p)
p.send()
# fpga.run_sequence(50000,False) # This definitely throws an error...


print "sleeping for 10 seconds"
time.sleep(10)

# I insert code here that works to play sram sequence on board.
fpga.dac_run_sram(sram,True) # This just infinitely loops over the sram sequence. I do this to check that I'm communicating with the board and this does indeed work and plays the waveform defined by sram.

