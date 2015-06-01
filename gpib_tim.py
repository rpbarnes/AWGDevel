import numpy as np
import socket


#ip = '127.0.0.1' # socket IP Address
ip = '192.168.0.8' # socket IP Address, (IP address for prologix)
timeout = 4.0 # timeout for socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#, socket.IPPROTO_TCP)
socket.settimeout(timeout) # set timeout for socket connection
port = 1234 # Determined by Prologix

gpibAddress = 6 # Device GPIB Address

### setup connection with prologix controller ###
socket.connect((ip, port))

def test_and_close():
    print '*'*50
    print('Initializing Proligix Settings')
    print '*'*50
    ### initialize Prologix Settings ##
    # Set Mode
    socket.send('++mode 1\n')
    socket.send('++mode\n')
    mode = socket.recv(1024)
    print 'Mode:', repr(mode)

    # EOI, enables or disables assertion of EOI signal with last character of command sent over GPIB port
    socket.send('++eoi 0\n')
    socket.send('++eoi\n')
    eoi = socket.recv(1024)
    print 'EOI:', repr(eoi)

    # EOS, appended termination character to data by Prologix
    socket.send('++eos 2\n')
    socket.send('++eos\n')
    eos = socket.recv(1024)
    print 'EOS:', repr(eos)

    # EOT, enable or disable appending user specified character to network output when reading
    socket.send('++eot_enable 0\n')
    socket.send('++eot_enable\n')
    eot_enable = socket.recv(1024)
    print 'EOT Enable:', repr(eot_enable)

    # EOT char, character to append network output when eot_enable is 1 or EOI detected
    socket.send('++eot_char 10\n')
    socket.send('++eot_char\n')
    eot_char = socket.recv(1024)
    print 'EOT Char:', repr(eot_char)

    # Address, Set GPIB Address
    socket.send('++addr ' + str(gpibAddress) + '\n')
    socket.send('++addr\n')
    addr = socket.recv(1024)
    print 'Addr:',repr(addr)

    # Auto, Automatically read-after-write
    socket.send('++auto 1\n')
    socket.send('++auto\n')
    auto = socket.recv(1024)
    print 'Auto:', repr(auto)

    socket.send('++read_tmo_ms 1000\n')


    print '*'*50
    print('Connecting to Device')
    print '*'*50
    #socket.send('*IDN?\n')
    # perform serial poll
    #socket.send('++ifc\n') # asserts GPIB IFC signal for 150 us
    #socket.send('++spoll\n')
    #data = socket.recv(1024)
    #print 'spoll:', repr(data)
    socket.send('*IDN? \n\n')
    #socket.send('++read 10\n')
    idString = socket.recv(1024)
    print 'Device:', repr(idString)


    socket.close()

def test_fc_and_close():
    print '*'*50
    print('Initializing Proligix Settings')
    print '*'*50
    ### initialize Prologix Settings ##
    # Set Mode
    socket.send('++mode 1\n')
    socket.send('++mode\n')
    mode = socket.recv(1024)
    print 'Mode:', repr(mode)

    # EOI, enables or disables assertion of EOI signal with last character of command sent over GPIB port
    socket.send('++eoi 0\n')
    socket.send('++eoi\n')
    eoi = socket.recv(1024)
    print 'EOI:', repr(eoi)

    # EOS, appended termination character to data by Prologix
    socket.send('++eos 2\n')
    socket.send('++eos\n')
    eos = socket.recv(1024)
    print 'EOS:', repr(eos)

    # EOT, enable or disable appending user specified character to network output when reading
    socket.send('++eot_enable 0\n')
    socket.send('++eot_enable\n')
    eot_enable = socket.recv(1024)
    print 'EOT Enable:', repr(eot_enable)

    # EOT char, character to append network output when eot_enable is 1 or EOI detected
    socket.send('++eot_char 10\n')
    socket.send('++eot_char\n')
    eot_char = socket.recv(1024)
    print 'EOT Char:', repr(eot_char)

    # Address, Set GPIB Address

    # Auto, Automatically read-after-write
    socket.send('++auto 1\n')
    socket.send('++auto\n')
    auto = socket.recv(1024)
    print 'Auto:', repr(auto)

    socket.send('++read_tmo_ms 1000\n')


    print '*'*50
    print('Connecting to Device')
    print '*'*50

    # set address for write
    socket.send('++addr ' + str(4) + '\n')
    socket.send('++addr\n')
    addr = socket.recv(1024)
    print 'Address:',repr(addr)
    socket.send('FC\n')

    # set address for read
#    socket.send('++addr ' + str(36) + '\n')
#    socket.send('++addr\n')
#    addr = socket.recv(1024)
#    print 'Address:',repr(addr)



#    socket.send('++read 10\n')
    idString = socket.recv(1024)
    print 'Device:', repr(idString)

    socket.close()


test_fc_and_close()
import socket

### Multiple Devices, must change address during communication ###

# IP of agilent scope: 192.168.0.10
# arp -n, determine from physcial address MAC

#
# call instance of gpib class inside other classes, initialize inside gpib class
class gpib(): # Class to control prologix Ethernet GPIB
    '''gpib class handles standard communication between computer and prologix'''
    def __init__(self,gpibAddress = 1,port = 1234, ipAddress = '192.168.0.8',timeout = 4.0,connect = True):
        '''Initialize Prologix Controller'''
        if connect:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#, socket.IPPROTO_TCP)
            self.sock.settimeout(timeout) # set timeout for socket connection
            self.sock.connect((ip, port))

        self.sock.send('++mode 1\n')    # set to controller mode
        self.sock.send('++eoi 0\n')     # disable eoi assertion with last character
        self.sock.send('++eos 2\n')     # append termination character to commands sent
        self.sock.send('++eot_enable 0\n') # disable appending char when reading
        self.sock.send('++eot_char 10\n')  # eot character to append if enabled

        self.sock.send('++addr ' + str(gpibAddress) + '\n')
        self.sock.send('++auto 1\n') # automatically read-after-write
        self.sock.send('++ver\n')
        prologixVersion = self.sock.recv(1024)
        print 'Connected to:', prologixVersion.strip()

    def readAfterWrite(self,command,gpibAddress):
        self.sock.send('++addr ' + str(gpibAddress) + '\n')
        self.sock.send('++auto 1\n')
        self.sock.send(str(command) + '\n')
        return self.sock.recv(1024)
    def write(self, command, gpibAddress):
        self.sock.send('++addr ' + str(gpibAddress) + '\n')
        self.sock.send('++auto 0\n')
        self.sock.send(str(command) + '\n')
    def read(self, gpibAddress, readUntil = ''):
        '''Read does not change the GPIB Address, it only reads what is in the Prologix buffer'''
        self.sock.send('++addr ' + str(gpibAddress) + '\n') 
        self.sock.send('++read ' + readUntil +  '\n') # this must be adjusted
        return self.sock.recv(1024)
    def close(self):
        self.sock.close()


class lockinAmp():
    def __init__(self,gpibInstance,gpibAddress = 6):
        self.g = gpibInstance
        self.gpibAddress = gpibAddress
        try:
            idString = g.readAfterWrite('*IDN?',gpibAddress)
        except:
            raise ValueError('Unable to identify Lockin-Amp')
        print 'Device:', idString.strip()
    def read(self):
        x = float(g.readAfterWrite('OUTP?1',self.gpibAddress))
        y = float(g.readAfterWrite('OUTP?2',self.gpibAddress))
        return x + 1j*y
class fieldController():
    def __init__(self,gpibInstance,gpibAddress = 4):
        self.g = gpibInstance
#        self.gpibReadAddress = gpibReadAddress
        self.gpibAddress = gpibAddress
#        try:
#        g.write('FC',self.gpibWriteAddress) # 36
#        idString = g.read(self.gpibReadAddress,'10') # 4
        idString = self.g.readAfterWrite('FC',self.gpibAddress)
        print 'Connected to Field Controller.\nCurrent Field:', idString[3:].strip()
    def readField(self):
        self.currentField = float(self.g.readAfterWrite('FC',self.gpibAddress)[3:])
        return self.currentField
    def setField(self,field):
        field = np.round(float(field),2) # round to 2 decimal points
        self.g.write('CF'+str(field),self.gpibAddress)
#        except:
#            raise ValueError('Field controller is not responding!')


    





import time
if __name__ == '__main__':
    pass
    g = gpib()
    lockin = lockinAmp(g)
    fc = fieldController(g)

    for i in range(10):
        fc.setField(3450.111+i)
        data = lockin.read()
        field = fc.readField()
        print 'field: %0.1f\tdata: %0.2e + 1j*%0.2e'%(field,np.real(data),np.imag(data))
#    idString = g.readAfterWrite('*IDN?',6)
#    print repr(idString)
#    for i in range(10):
#        start_time = time.time()
#        data = lockin.read()
#        end_time = time.time()
#        print data
#        print end_time - start_time
#    g.close()

