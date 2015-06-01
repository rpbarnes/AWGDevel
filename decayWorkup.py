from matlablike import *
close('all')

fileName = '150416Experiments.h5'
decayList = []
#nameList = ['50mM4OHT50pGly1','50mM4OHT50pGly3']
#nameList = ['50mM4OHT50pGly1','50mM4OHT50pGly3','50mM4OHT50pGly5','50mM4OHT50pGly7','50mM4OHT50pGly9','50mM4OHT50pGly11','50mM4OHT50Gly13']
#nameList = ['50mM4OHT50pGly5','50mM4OHT50pGly7','50mM4OHT50pGly11','50mM4OHT50Gly13','50mM4OHT50pGly9']
#nameList = ['50mM4oht_50pGly_Tm_16_100_28dBHP','50mM4oht_50pGly_Tm_100_100_28dBHP']
#nameList = ['50mM4oht_50pGly_Tm_16_300_28dBHP','50mM4oht_50pGly_Tm_300_300_28dBHp']

### NOTE DAY 2 ### 
#nameList = ['50mM4oht_Tm_16_32_pi_22dBHP','50mM4oht_Tm_16_32_p5pi_22dBHP','50mM4oht_Tm_16_32_p125pi_22dBHP']
nameList = ['50mM4oht_Tm_32_32_pi_22dBHP','50mM4oht_Tm_32_32_p5pi_22dBHP','50mM4oht_Tm_32_32_p125pi_22dBHP']


# load the set
for name in nameList:
    dataMatrix = nddata_hdf5(fileName +'/'+ name)
    dataMatrixFt = dataMatrix.copy().ft('phcyc90').ft('phcyc180') # how do you pick which signal is positive and which is negative...
    dataMatrixFt = dataMatrixFt.ft('t',shift = True)
    centerFrequency = 300e6
    bandpassFilter = 100e6
    figure('slice')
    image(dataMatrixFt.runcopy(abs)['phcyc90',1,'phcyc180',2],label = 'abs')
    title(name)
    dataMatrixFt['t',lambda x: bandpassFilter/2. < abs(x-centerFrequency)] = 0
    figure('slice bandpass')
    image(dataMatrixFt.runcopy(abs)['phcyc90',1,'phcyc180',2],label = 'abs')
    title(name)
    decay = dataMatrixFt.copy()['phcyc90',1,'phcyc180',2].runcopy(abs).sum('t') 
#    decay.data /= decay.data[14]
    decay.data -= decay.data[-1]
    decay.data /= decay.data[40]
    figure('decay')
    plot(decay)
    title(name)
    xlabel('Time (ns)') 
    decay.other_info = dataMatrix.other_info
    decayList.append(decay)

figure()
for dataSet in decayList:
    p0 = dataSet.other_info.get('p0')*1e9
    p1 = dataSet.other_info.get('p1')*1e9
    a0 = dataSet.other_info.get('a0')
    a1 = dataSet.other_info.get('a1')
    dataSet.getaxis('tau')[:] *= 1e9
    plot(dataSet,label=' 90-pulse: %0.3f Amp %0.0f ns\n180-pulse: %0.3f Amp %0.0f ns'%(a0,p0,a1,p1),alpha = 0.5,linewidth = 2.)
legend(prop = {'size':24})
xlabel('Time (ns)',fontsize = 24)
ylabel('Integrated Abs Ft of Echo',fontsize = 24)
expand_y()



show()

