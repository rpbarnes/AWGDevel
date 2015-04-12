"""Collect phase cycled signal using the bandpass filters on the video amplifiers and the DAC board to modulate the pulse by 300 MHz."""
close('all')
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

a.timebase(50e-9)
a.setvoltage(0.01)
a.acquire(256)
sampleSet = a.Waveform_auto()
yig.set_mwfreq(9.701e9)
fc.set_field(3355.7)

from matlablike import *
import synthesize as s
p = s.pulsegen()

wave = p.make_highres_waveform([('delay',500e-9),('rect','x',16e-9),('delay',15e-6 - 516e-9)],resolution=1e-9)

modFreq = -300e6
modulation = nddata(exp(1j*2*pi*modFreq*wave.getaxis('t'))).rename('value','t').labels('t',wave.getaxis('t'))

phaselist = ['x','y','-x','-y']
dataShape = ndshape([len(sampleSet.getaxis('t')),len(phaselist)],['t','phc'])
data = dataShape.alloc(dtype='complex128')
data.labels(['t','phc'],[sampleSet.getaxis('t'),r_[0:len(phaselist)]*pi/4])


for count,phase in enumerate(phaselist):
    wave = p.make_highres_waveform([('delay',500e-9),('rect',phase,16e-9),('delay',15e-6 - 516e-9)],resolution=1e-9)
    modWave = modulation.copy() * wave.copy()
    p.synthesize(modWave,autoTWTSwitch=True,autoSynthSwitch=True)
    data['phc',count] = a.Waveform_auto()


data.ft('phc',shift = True)

figure()
image(data)


figure()
for count in range(len(data.getaxis('phc'))):
    plot(data['phc',count],label='dim = %d'%count)
legend()

data.ft('t',shift = True)

figure()
colorlist = ['g','r','b','c']
for count in range(len(data.getaxis('phc'))):
    plot(data['phc',count].runcopy(real),linestyle = '-',alpha = 0.5,color = colorlist[count],label='real dim = %d'%count)
    plot(data['phc',count].runcopy(imag),linestyle = '--',alpha = 0.5,color = colorlist[count],label='imag dim = %d'%count)
legend()

show()
