import gpib_eth as g
from matlablike import *

lsb = r_[10:226]

for bit in lsb:
    ip = '192.168.0.%d'%bit
    try:
        print "Tyring IP = ",ip
        conn = g.gpib(ip=ip,timeout=1.0)
        print "the address is ",ip
        break
    except:
        print "didn't work"

