#!/usr/bin/python3

##libraries
import RPi.GPIO as GPIO
import spectra_analysis_FT8 as FT8
import time, sys, spidev, argparse, re, threading, queue

FT8_freq={  '160m' : '1840000',
            '80m' : '3573000',
            '40m' : '7074000',
            '30m' : '10136000',
            '20m' : '14074000',
            '17m' : '18100000',
            '15m' : '21074000',
            '12m' : '24915000',
            '10m' : '28074000',
            '6m' : '50313000'
            }

# set variables
W_CLK=18
FQ_UD=23
DATA=24
RESET=25
offset=0
WORD1='00000001'#W0 multiplier6x, power up
WORD0='00000101'#W0 power down, multiplier6x

# setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(W_CLK,GPIO.OUT)
GPIO.setup(FQ_UD,GPIO.OUT)
GPIO.setup(DATA,GPIO.OUT)
GPIO.setup(RESET,GPIO.OUT) 

GPIO.output(DATA,0)

def reset():
    GPIO.output(RESET,1)
    GPIO.output(RESET,0)
    GPIO.output(W_CLK,1)
    GPIO.output(W_CLK,0)
    GPIO.output(FQ_UD,1)
    GPIO.output(FQ_UD,0)
    return()

def AD9851(freq,WORD):
    if freq > 70000000:
        print('AD9851: frequency must be lower than 70 mHz',file=sys.stderr) 
        sys.exit(-1)
    freq_word_int=int((freq*2**32)/(6*30e6+offset)) ##6xrefclock turned on in WORD0 
    FREQWORD='{0:032b}'.format(freq_word_int)
    SERIALWORD=WORD+FREQWORD
    #print(SERIALWORD)
    for i in range(39,-1,-1):
        GPIO.output(W_CLK,0)
        if int(SERIALWORD[i]):
            GPIO.output(DATA,1)
        GPIO.output(W_CLK,1)
        GPIO.output(DATA,0)
        GPIO.output(W_CLK,0)
    GPIO.output(FQ_UD,1)
    GPIO.output(FQ_UD,0)
    return()
	   
		   
frequencies=[]
qdata=queue.Queue(maxsize=7)


#%% Argument parser

usage='Script to control Analog Devices AD9851'
usage_freq='Frequency in Hz or standard FT8 frequency e.g. "14097100" or "10m". "K"(Hz) or "M"(Hz) may be used.'
p=argparse.ArgumentParser(description=usage)

p.add_argument('-f','--FT8', action='store_true', dest='FT8',
    help='Transmit on base frequency shifted with tone input of WSJTX'
    )
p.add_argument('-c','--continuous', action='store_true', dest='cont',
    help='Do not autoshutdown testtone (default 5 minutes)'
    )


p.add_argument('frequencies', metavar='F', nargs=1, help=usage_freq)

output = p.parse_args()
#print(output)


for frequency in output.frequencies:#get the frequencies from the list
    #print(frequency)
    try:
        f=int(FT8_freq[frequency]) #get known WSPR frequency
        frequencies.append(f)
    except:
        try:
            if re.search('[K]$',frequency):
                frequency=frequency.replace('K','000')
            if re.search('[M]$',frequency):
                frequency=frequency.replace('M','000000')      
            f=int(frequency) #else it must be an integer value
            frequencies.append(f)
        except:
            print('Malformed frequency.',file=sys.stderr) 
            print(usage_freq, file=sys.stderr)
            sys.exit(-1)

print("Channel 0 set to: {0:,} Hz".format(frequencies[0]))


if __name__ == '__main__':

    #%% Reset and setup 
##    GPIO.output(RESET,1)
##    time.sleep(0.01)
##    GPIO.output(RESET,0)
    reset()
    
    #%%
    if output.FT8:
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
                    FT8_freq=frequencies[0]+d
                else:
                    FT8_freq=0
                AD9851(FT8_freq,WORD1)
                print(d, end=',')
                frame_count += 1
                
        except queue.Empty:#(queue.Empty,KeyboardInterrupt) as exc: 
            fr = frame_count / (time.time() - start_time-2)
            t.join()
            print()
            print('average frame rate = {0:.3f} FPS'.format(fr))
            print('program finished')
            
        except KeyboardInterrupt: 
            fr = frame_count / (time.time() - start_time)
            t.join()
            print()
            print('average frame rate = {0:.3f} FPS'.format(fr))
            print('program finished')

    else:
        if output.cont:
            t=(24*60*60)
        else:
            t=300
        AD9851(frequencies[0],WORD1)
        try:
            time.sleep(t)
        except KeyboardInterrupt:
            AD9851(0,WORD0)
        AD9851(0,WORD0)
