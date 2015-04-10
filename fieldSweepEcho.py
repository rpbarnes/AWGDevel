import gpib_eth as g
import time as timing 
import threading

# test to see if we already have control of the spectrometer components
try:
    wave = p.make_highres_waveform([('delay',100e-9)])
except:
    print "p does not exist"
    p = m.pulsegen(True,True)
try:
    yig
except:
    from yig import _yig as yig
try:
    a.run()
except:
    a = g.agilent()
try:
    fc
except:
    fc = g.field_controller()

def voltageLog(fileName,name,connection,stopEvent,*args):
    connection.setaddr(7)
    timeList = []
    voltage = []
    count = 0
    start = timing.time() 
    while (not stopEvent.is_set()):
        try:
            volt = float(multiMeter.respond('MEAS:VOLT:DC?'))
            voltage.append(volt)
        except:
            print "There is garbage coming from device, will skip this round"
        print "I just recorded this voltage: ", volt
        timeList.append(timing.time() - start)
        timing.sleep(5)
        count += 1
        if int(count/50.) - (count/50.) == 0: # if we're at a multiple of 50 counts save the list
            try:
                h5file,childnode = h5nodebypath(fileName +'/'+name,check_only = True)
                h5file.removeNode(childnode,recursive = True)
                h5file.close()
            except:
                pass
            save = nddata(array(voltage)).rename('value','t').labels(['t'],[array(timeList)])
            save.name(name)
            save.hdf5_write(fileName)
            print "I just saved the power file!"
    try:
        h5file,childnode = h5nodebypath(fileName +'/'+name,check_only = True)
        h5file.removeNode(childnode,recursive = True)
        h5file.close()
    except:
        pass
    save = nddata(array(voltage)).rename('value','t').labels(['t'],[array(timeList)])
    save.name(name)
    save.hdf5_write(fileName)
    print "I just saved the power file!"

### To track the temperature
try:
    del multiMeter
except:
    "multiMeter does not exist"

save = False
ip = '192.168.0.12'
multiMeter = g.gpib(ip)
multiMeter.setaddr(7) # address 7
fileName = '140920VoltagesEcho.h5'
name = 'voltage2'
voltageStop = threading.Event()
if save:
    voltage = threading.Thread(target = voltageLog,args = (fileName,name,multiMeter,voltageStop,1))
    voltage.start()

freqCenter = 9.2185e9 
yig.set_mwfreq(freqCenter)
resRatio = 3363.2 / 9.4275e9 # G / Hz
fieldCenter = freqCenter * resRatio 
fieldWidth = 20.0
fieldRes = 1 
fields = r_[fieldCenter-fieldWidth:fieldCenter+fieldWidth:fieldRes]
print fieldCenter
fc.set_width(0)
fc.set_field(round(fieldCenter,1))

phase180 = ['x','y','-x','-y']
#phase180 = ['x','-x']
phasecyc = ['x','y','-x','-y']

pulseLength = 30e-9 # this is the 90 time

pulseSpacing = 300e-9
preDelay = pulseSpacing + 500e-9
end180 = preDelay + 3*pulseLength + 45e-9
a.timebase(100e-9)
a.position(end180 + pulseSpacing)
a.setvoltage(0.01)
a.acquire(50)
scopeCapture = a.Waveform_auto()
signal = ndshape([len(scopeCapture.getaxis('t')),len(fields),len(phasecyc),len(phase180)],['t','field','phyc','phyc180'])
signal = signal.alloc(dtype = 'complex')
signal.labels(['t','field','phyc','phyc180'],[scopeCapture.getaxis('t'),fields,r_[0:len(phasecyc)],r_[0:len(phase180)]])
a.position(end180 + pulseSpacing + 75e-9) # shift the position to keep ontop of the echo
for fieldCount,field in enumerate(fields):
    startTime = timing.time()
    print "Running field offset: ", field
    fc.set_field(round(field,1))
    fc.set_width(0)
    for ph180Count,ph180 in enumerate(phase180):
        for phyCount,phase in enumerate(phasecyc):
            wave = p.make_highres_waveform([('delay',preDelay - pulseSpacing),('rect',phase,pulseLength),('delay',pulseSpacing),('rect',ph180,2*pulseLength),('delay',10e-6 - preDelay - 3*pulseLength)])
            p.digitize(wave,do_normalize = True,autoGateSwitch = True, frontBuffer = 40e-9,rearBuffer = 0.0e-9,longDelay = 2000e-6)
            signal['field',fieldCount,'phyc',phyCount,'phyc180',ph180Count] = a.Waveform_auto()
    stopTime = timing.time()
    loopTime = (stopTime - startTime)
    print "This loop took %0.2f seconds. I predict the experiment will take another %0.2f minutes"%(loopTime,(loopTime * (len(fields) - fieldCount)/60.))

voltageStop.set()
echo = signal.copy().ft('phyc',shift = True).ft('phyc180',shift = True)
echo = echo['phyc',3,'phyc180',1]
figure()
image(echo)
title('Echo Signal')
figure()
plot(echo['field',:])
show()

