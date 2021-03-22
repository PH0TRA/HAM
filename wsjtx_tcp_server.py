# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 16:27:17 2020

@author: marc
"""


import socket  # Import socket module
#import RPi.GPIO as GPIO
import spectra_analysis_FT8_win as FT8
import time, threading, queue
import argparse

#import re
qdata=queue.Queue(maxsize=7)

usage='Script to determine dominant frequency of analog output WSJTX program'
usage_host='IP or name of device on which to push data'
usage_port='Port to connect to. Default 50,000'

p=argparse.ArgumentParser(description=usage)

##p.add_argument('-f','--FT8', action='store_true', dest='FT8',
##    help='Transmit on base frequency shifted with tone input of WSJTX'
##    )
p.add_argument('-i','--interface', action='store', dest='host', help=usage_host, default='127.0.0.1', type=str)
p.add_argument('-p','--port', action='store', dest='port', help=usage_port, default='50000', type=int)

output = p.parse_args()

port = output.port  # Reserve a port for your service every new transfer wants a new port or you must wait.
host = output.host 

if __name__ == '__main__':
    
    s = socket.socket()  # Create a socket object
    
    s.connect((host, port)) 
    while True:
        data = (s.recv(1024)).decode()
        if data:
             print(data)
#             x += 1
             break
         
#         else:
#             print('no data received')
    
    
    t = threading.Thread(target=FT8.AudioStream, args = (qdata, ))
    t.start() ##starts the class Audiostream
    print('thread running')
    #time.sleep(2)
    frame_count = 0
    start_time = time.time()

    try:
        while True:#not qdata.empty():
            #pass
            d=qdata.get(timeout=2)
            if d != 0:
                FT8_freq=str(d)
                
            else:
                FT8_freq=str(0)
                d='-'
            s.sendall(FT8_freq.encode())
            
            print(d,end='/')
            frame_count += 1
            
    except queue.Empty:#(queue.Empty,KeyboardInterrupt) as exc: 
        fr = frame_count / (time.time() - start_time-2)
        t.join()
        #s.shutdown()
        s.close()
        print()
        print('average frame rate = {0:.3f} FPS'.format(fr))
        print('program finished')
        
    except KeyboardInterrupt: 
        fr = frame_count / (time.time() - start_time)
        t.join()
        #s.shutdown()
        s.close()
        print()
        print('average frame rate = {0:.3f} FPS'.format(fr))
        print('program finished')

    

