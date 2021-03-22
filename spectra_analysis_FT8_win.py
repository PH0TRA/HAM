# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 20:43:54 2019

@author: marcburgmeijer
"""

"""
if you don't have pyaudio, then run
>>> pip install pyaudio
info used while programming MBu
https://stackoverflow.com/questions/35970282/what-are-chunks-samples-and-frames-when-using-pyaudio
    
Adapted for transferring the audio tone of WSJTX to an DDS syntheziser
in order to directly generate a FT8 FSK signal. 
FT8 generates 79 bits in 12.6 seconds, so the frame rate must be 6.250 frames/second to
capture every tone. The tone spacing is 6.25 Hz.

"""


import numpy as np
import pyaudio
import queue
import struct
from scipy.fftpack import fft
from datetime import datetime
import time
import sys



class AudioStream(object):
    def __init__(self, Workqueue):
        self.qdata=Workqueue
        self.pause = False
          
        # stream constants
        self.CHUNK = int(7056)#gives 6,25 Hz spacing
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = int(44100)#native samplerate otherwise pyaudio won't work
        self.min_freq=200
        self.min_sample=self.min_freq*self.CHUNK//self.RATE ##set underlimit of frequency
        
        # stream object
        #with noalsaerr():
        self.p = pyaudio.PyAudio()
        self.audiostream()
        self.calculate_plot()
        

    def audiostream(self):
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )    

    def calculate_plot(self):

        print('stream started')
        frame_count = 0
        start_time = time.time()
        fr=0
        last_seq=0
        #last_d_freq = 0       
        
        while not self.pause:
                       
            data = self.stream.read(self.CHUNK) ##stream of binary data
            data_int = struct.unpack(str(2 * self.CHUNK) + 'B', data)
            
            # compute FFT and update line
            yf = fft(data_int) ##compute FFT
            ydata=np.abs((yf[0:self.CHUNK]) / (128 * self.CHUNK))##normalized levels to max 1 value and absolute out of complex
            
            ydata_amax=np.max(ydata[self.min_sample:self.CHUNK//2])##return maximum value maximum half samplerate otherwise aliasing occurs
            ydata_argmax=np.argmax(ydata[self.min_sample:self.CHUNK//2])+self.min_sample## return position  of maximum value (check but remember 1st is skipped)
            
            fr = frame_count / (time.time() - start_time)
            
            d_freq=(ydata_argmax)*self.RATE/(self.CHUNK)
            
            if ydata_amax <= 0.2 or d_freq >=2700 : ##test maximum value and return frequency
                d_freq=0
                            
            try:
                self.qdata.put_nowait(d_freq)
                #self.qdata.put(d_freq,timeout=2)
            except queue.Full:
                self.pause=True
                     
            sys.stdout.flush()
            frame_count += 1

            now = datetime.now()
            seconds=float(now.strftime("%S.%f"))
            seq=int((seconds+1)//15) ##
            if seq != last_seq and seq != 0:
                wait=seq*15-seconds-3*0.16#-0.04##start 3 intervals before next sequence
                if wait > 0:
                    self.p.close(self.stream)
                    time.sleep(wait)
                    self.audiostream()
                last_seq=seq
            
        else:
            fr = frame_count / (time.time() - start_time)
            print('average frame rate = {0:.3f} FPS'.format(fr))
            print('number of lines:', len(ydata))
            print('linewidth = {0:.3f} Hz'.format(self.RATE/len(ydata)))
            self.exit_app()
    

    def exit_app(self):
        print('stream closed')
        self.p.close(self.stream)
        

    def onClick(self, event):
        self.pause = True
        
    

