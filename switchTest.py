from matlablike import *
import numpy as np
close('all')
import synthesize as s
p = s.pulsegen()
import gpib_eth as g
a = g.agilent()
#a.setvoltage(100e-3)
#a.timebase(100e-9)
a.acquire(1024)


### ECL Outputs ###
# 0x10000000 ### starting trigger
# 0x20000000 ### Adress to transmitter switch
# 0x40000000 ### Adress to reciever switch
# 0x80000000 ### Adress to twt gate

### Receiver Switch Test ###

# Test waveform
#wave = p.make_highres_waveform([('delay',500e-9),('delay',16e-9),('delay',10e-6-516e-9)])
wave = p.make_highres_waveform([('delay',500e-9),('rect','x',16e-9),('delay',10e-6-516e-9)])
#wave = p.make_highres_waveform([('delay',500e-9),('function',lambda x: np.exp(-1j*2*np.pi*300e6*x),16e-9),('delay',10e-6-516e-9)])

# Test Without Switch #

sram = p.wave2sram(wave.data)

sram[0] |= 0x10000000 # starting trigger

p.fpga.dac_run_sram(sram,True)

data_without = a.Waveform_auto()

# Test with Switch #

sram = p.wave2sram(wave.data)

sram[0] |= 0x10000000 # starting trigger

#for i in range(100,2100):
#    sram[i] |= 0x40000000 ### Adress to reciever switch 

p.fpga.dac_run_sram(sram,True)

data_with = a.Waveform_auto()
a.run()

data_with.getaxis('t')[:] *= 1e9 # convert to ns
#data_without.getaxis('t')[:] *= 1e9 # convert to ns


figure()
plot(data_without.runcopy(real),'b-',label = 'Without Protection Pulse, real')
plot(data_without.runcopy(imag),'b--',label = 'Without Protection Pulse, imaginary')
plot(data_with.runcopy(real),'g-', label = 'With Protection Pulse, real')
plot(data_with.runcopy(imag),'g--', label = 'With Protection Pulse, imaginary')
legend()

xlabel('Time (ns)')
ylabel('Signal (V)')

show()


