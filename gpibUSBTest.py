import gpib_eth as g

#try:
#    conn = g.gpib_usb(5)
#except:
#    print "fuck you windows"

# test connection to the field controller.

# talk means device talks, computer listens; listen means device listens, computer talks
talkaddr = 4
listenaddr = 36
conn.setaddr(listenaddr)
conn.serial.write('FC\r')
#conn.setaddr(talkaddr)
#print conn.serial.readline()
print conn.read(talkaddr)


#conn.close()
#del conn

