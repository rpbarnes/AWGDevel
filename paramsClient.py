import os
import sys
from socket import *
import time


def recvParams():
    ''' Retrieve dataDict from Server Program'''
    serverHost = 'localhost'
    serverPort = 50007
    message = [b'handshake']

    sockobj = socket(AF_INET, SOCK_STREAM)
    sockobj.connect((serverHost, serverPort))
    for line in message:
        sockobj.send(line)
        data = sockobj.recv(1024)
    sockobj.close()
    return data

def recvDate():
    dateInfo = time.localtime()
    dateString = str(dateInfo[2]) + '/' + str(dateInfo[1]) + '/' + str(dateInfo[0])
    return dateString


def recvTime():
    dateInfo = time.localtime()
    hours = dateInfo[3]
    minutes = dateInfo[4]

    # Determine if AM or PM
    AM_or_PM = 'PM'
    if hours % 12 == hours:
        AM_or_PM = 'AM'

    # convert to standard hours format
    hours = hours % 12 
    if hours == 0:
        hours = 12

    timeString = str(hours) + ':' + str(minutes) + AM_or_PM
    return timeString

    
