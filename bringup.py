from __future__ import with_statement

import random
import time
import os

import labrad
from math import sin, pi
from msvcrt import getch, kbhit

FPGA_SERVER='ghz_fpgas'

def bringupBoard(fpga, board, verbose = False):
    print 'Bringing up %s...' % board
        
    """Bringup a single board connected to the given fpga server."""
    fpga.select_device(board)
    
    print
    print ' Initializing PLL...', 
    fpga.pll_reset()
    time.sleep(0.100)
    fpga.pll_init()
    print '            success'
    
    okay = []
    for dac in ['A', 'B']:
        print ''
        print ' Initializing DAC %s...' % dac
        fpga.dac_init(dac, True)

        print '  Setting DAC %s LVDS Offset...' % dac,
        lvds = fpga.dac_lvds(dac)
        if verbose: 
            print '  SD: %d' % lvds[2]
            print '  y:  ' + ''.join('_-'[ind[0]] for ind in lvds[3])
            print '  z:  ' + ''.join('_-'[ind[1]] for ind in lvds[3])
        print '  success'
        
        print '  Setting DAC %s FIFO Offset...' % dac,
        fifo = fpga.dac_fifo(dac)
        okFifo = (fifo[4]==3)
        print '  success' if okFifo else '  FAILURE!'
        if verbose: 
            print '  Operating SD:  %2d' % fifo[0]
            print '  Stable SD:     %2d' % fifo[1]
            print '  Clk Polarity:  %1d' % fifo[2]
            print '  FIFO Offset:   %1d' % fifo[3]
            print '  FIFO Counter:  %1d (should be 3)' % fifo[4]
        
        print '  Running DAC %s BIST...' % dac,
        bistdata = [random.randint(0, 0x3FFF) for i in range(1000)]
        success, thy, lvds, fifo = fpga.dac_bist(dac, bistdata)
        print '         success' if success else '         FAILURE!'
        if verbose: 
            print '  Theory: %08X, %08X' % thy
            print '  LDVS:   %08X, %08X' % lvds
            print '  FIFO:   %08X, %08X' % fifo
        okay.append(success and okFifo)
        print
        
    return all(okay)

def getBuildNumber(fpga, board):
    """Use the FPGA server to get a board build number."""
    fpga.select_device(board)
    buildNumber = fpga.build_number()
    return buildNumber    
    
def checkBoard(verbose = False):
    print 'Trying to connect to the DAC board...'
    print
    with labrad.connect() as cxn:
        fpga = cxn[FPGA_SERVER]
        boards = fpga.list_devices()
        bold = '\033[1m'
        nobold = '\033[0;0m'
        
        while len(boards) == 0:
            print 'FAILURE: The board was off when you started the GHz DAC Server.'
            print 'Turn on (and connect) the DAC board, close and restart the DAC server and press any key...'
            raw_input()
            boards = fpga.list_devices()
        board = boards[0][1]
        
        while True:
            try:
                getBuildNumber(fpga, board)
                break
            except:
                print 'FAILURE: The DAC board seems to be turned off.'
                print 'Turn on (and connect) the board and press any key...'
                raw_input()
                
        print 'Bring up successfully completed!' if bringupBoard(fpga, board, verbose = verbose) else 'Something went wrong! See above for details.'
        
if __name__ == '__main__':
    os.system('cls')
    checkBoard(verbose = False)
