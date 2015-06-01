import numpy as np
close('all')

fileName = '150415Experiments.h5'
fseList = []
nameList = ['50mM4ohtFSE0','50mM4ohtFSE1','50mM4ohtFSE2','50mM4ohtFSE3','50mMohtFSE4','50mMohtFSE5','50mM4ohtFSE6','50mM4ohtFSE7','50mM4ohtFSE8','50mM4ohtFSE9']
for name in nameList:
    print name
    dataMatrix = nddata_hdf5(fileName +'/'+ name)
    dataMatrixFt = dataMatrix.copy().ft('t',shift = True)
    centerFrequency = 300e6
    bandpassFilter = 100e6
#    figure('slice')
#    image(dataMatrixFt.runcopy(abs))
#    title(name)
    dataMatrixFt['t',lambda x: bandpassFilter/2. < abs(x-centerFrequency)] = 0
#    figure('slice bandpass')
#    image(dataMatrixFt.runcopy(abs),label = 'abs')
#    title(name)
    fseAbs = dataMatrixFt.copy().runcopy(abs).sum('t') 

    # Normalize data
    fseAbs.data -= fseAbs.data[-1]
    fseAbs.data /= np.max(fseAbs.data)

#    figure('decay')
#    plot(decay)
#    title(name)
#    xlabel('Time (ns)') 
    fseAbs.other_info = dataMatrix.other_info
    fseList.append(fseAbs)

figure()
for dataSet in fseList:
    plot(dataSet,label='Amplitude: %0.2f'%(dataSet.other_info.get('a0')),alpha = 0.5,linewidth = 2.)

xlabel('Field (G)',fontsize = 24)
ylabel('Integrated Abs Ft of Echo',fontsize = 24)
legend(prop = {'size':24})
expand_y()


show()


