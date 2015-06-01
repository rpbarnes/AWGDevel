from gpib_tim import gpib
import numpy as np
close('all')

try:
    g
except NameError:
    g = gpib()
    try:
        del lockin
    except:
        pass
    try:
        del fc
    except:
        pass

try:
    lockin
except NameError:
    lockin = lockinAmp(g)
try:
    fc
except NameError:
    fc = fieldController(g)

### Define the CW waveform parameters ###
fcarrier = 10e6 # carrier frequency
df = 20e6 # modulation frequency
fm = 200e3 # modulation amplitude

### Create Waveform ###
#wave = p.make_highres_waveform([('function',lambda x: np.exp(1j*(2*np.pi*fcarrier*x + (df/fm)*np.cos(2.*np.pi*fm*x))),np.r_[0,10e-6])],1.e-9)
wave = p.make_highres_waveform([('function',lambda x: (1 + 0.5*np.cos(2*np.pi*fm*x))*np.exp(1j*(2*np.pi*(fcarrier*x))),np.r_[0,9998e-9])],1.e-9)
wave.data /= np.max(np.abs(wave.data))

figure()
plot(wave.runcopy(real))

show()
### Synthesize waveform ###
#p.synthesize(wave,manualTrigger = [(0,5000)])
p.synthesize(wave,manualTrigger = [(0,2500),(5000,2498)])
print('Waiting for lockin to stabilize')
time.sleep(2)

### Define axis for field ###
fieldPoints = 101
centerField = 3455.
sweepWidth = 100.
fieldArray = np.r_[-1*sweepWidth/2.:sweepWidth/2.:1j*fieldPoints] + centerField

### Pre-allocate data array ###
dataShape = ndshape([fieldPoints],['field'])
data = dataShape.alloc(dtype = 'complex')

### Loop over fields and acquire data ###
for fieldIx, fieldValue in enumerate(fieldArray):
    print('%i of %i'%(fieldIx+1,len(fieldArray)))
    fc.setField(np.round(fieldValue,2))
    if fieldIx == 0:
        print('Waiting for field to stabilize...')
        time.sleep(2)
    else:
        time.sleep(.01)

    data['field',fieldIx] = lockin.read()

data.labels(['field'],[fieldArray])
fc.setField(np.round(centerField,1))



figure('spectrum')
plot(data.runcopy(real),label = 'real')
plot(data.runcopy(imag),label = 'imag')
plot(data.runcopy(abs),label = 'abs')
legend()
xlabel('Field (G)')

show()
