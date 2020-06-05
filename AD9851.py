#!/usr/bin/python3
#written by Marc Burgmeijer 2017

import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)
GPIO.setup(25,GPIO.OUT) #test
#DATA=GPIO.PWM(24,1)
W_CLK=18
FQ_UD=23
DATA=24
RESET=25
GPIO.output(DATA,0)

def reset():
    GPIO.output(RESET,1)
    GPIO.output(RESET,0)
    GPIO.output(W_CLK,1)
    GPIO.output(W_CLK,0)
    GPIO.output(FQ_UD,1)
    GPIO.output(FQ_UD,0)

reset()

WORD0='00001001'
OFFSET=0

_160m = 1.836600 ## 1.838000 - 1.838200
_80m = 3.592600 ## 3.594000 - 3.594200
_60m = 5.287200 ## 5.288600 - 5.288800
_40m = 7.038600 ## 7.040000 - 7.040200
_30m = 10.138700 ## 10.140100 - 10.140300
_20m = 14.095600 ## 14.097000 - 14.097200
_17m = 18.104600 ## 18.106000 - 18.106200
_15m = 21.094600 ## 21.096000 - 21.096200
_12m= 24.924600	## 24.926000 - 24.926200
_10m = 28.124600	## 28.126000 - 28.126200
_6m = 50.293000	## 50.294400 - 50.294600

# give desired frequency
while True:
    
    while True:
        try:
            freq=float(input("Give desired frequency in MHz?\t") or 1)
            freq_MHz=int(freq*1e6)
            break
        except KeyboardInterrupt:
            reset()
            exit()
        except:
            pass    
    # calculate binary frequencyword
    freq_word_int=int((freq*1e6)*(2**32)/(6*30e6+OFFSET)) ##6xrefclock turned on in WORD0 
    FREQWORD='{0:032b}'.format(freq_word_int)

    SERIALWORD=WORD0+FREQWORD

    ##!
    FREQWORD_INT=int(FREQWORD,2)
    freq=(FREQWORD_INT*30e6/2**32)
    freq_6xrefclk=(FREQWORD_INT*6*30e6/2**32)
    print('check of send frequency:')
    print('{0:,.0f} Hz'.format(freq_6xrefclk))
    
    ##!


    for i in range(39,-1,-1):
        GPIO.output(W_CLK,0)
        if int(SERIALWORD[i]):
            GPIO.output(DATA,1)
        #time.sleep(0.01)
        GPIO.output(W_CLK,1)
        #time.sleep(0.01)
        GPIO.output(DATA,0)
        GPIO.output(W_CLK,0)
    GPIO.output(FQ_UD,1)
    #time.sleep(0.01)
    GPIO.output(FQ_UD,0)


#WORDJ=''.join(WORDF)
#print(WORDJ)
#WORDF=str(WORDF).replace(', ','')#
##FQ=int(FREQWORD,2)
##Freq=180*10**6*FQ/2**32
##print(Freq)



##    print(WORDF[i],end=',')
##    freq=int(WORDF[i])**i
##    print(freq)
##for i in reversed(WORDF):




##blinks = 0
##
##while blinks < 10:
##    GPIO.output(RESET,1)

##    GPIO.output(RESET,0)

##    blinks = blinks+1
##GPIO.output(18,GPIO.LOW)
GPIO.cleanup()
