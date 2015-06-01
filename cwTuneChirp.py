
### Define parameters for chirp pulse ###


wave.data /= np.max(wave.data)

dx = 5000e-9
k = 50e6/9e-6
f0 = 200e6 # starting frequency
p0 = 9e-6 # length of chirp
dtotal = 9.9e-6 # total length of sequence
dx = 500e-9
phase = pi/2. # in radians

#wave = p.make_highres_waveform([('delay',dx),('function',lambda x: np.exp(+1j*(phase + (2*np.pi*(f0*x + (k/2.)*(x**2.))))),r_[0,p0]),('delay',dtotal - dx - p0)],1.e-9)
wave = p.make_highres_waveform([('delay',dx),('function',lambda x: (1 + np.cos(2*np.pi))*np.exp(+1j*(2*np.pi*(f0*x))),r_[0,p0]),('delay',dtotal - dx - p0)],1.e-9)

p.synthesize(wave,manualTrigger = [(0,5000)])
close('all')
#figure()
#plot(wave)
#show()
