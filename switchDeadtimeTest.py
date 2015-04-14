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

a.acquire(1)

yig.set_mwfreq(9.701e9)
fc.set_field(3355.7)

wave = p.make_highres_waveform([('delay',500e-9),('function',lambda x: np.exp(-1j*2*np.pi*-300e6*x),r_[0,16e-9]),('delay',15e-6-516e-9)])

#p.zero_cal_data = [-0.028901, 0.0399005]
#p.zero_cal_data = [0,0]

p.synthesize(wave,zero_cal = True, autoReceiverSwitch = True,autoTWTSwitch = True,frontBufferTWT = 150e-9,frontBufferReceiver = 400e-9,rearBufferReceiver = 100e-9)




