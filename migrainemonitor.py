#!/usr/bin/python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Can enable debug output by uncommenting:
#import logging
#logging.basicConfig(level=logging.DEBUG)
from datetime import datetime
import time
import thread
import Adafruit_BMP.BMP085 as BMP085
import os
import RPi.GPIO as GPIO

def ButtonThread(a, *args):
  fo = open('migraine_start_log.txt', 'a')
  while True:
    GPIO.wait_for_edge(23, GPIO.FALLING)
    dt = datetime.now().isoformat()
    fo.write('{0}\n'.format(dt))
    fo.flush()
    time.sleep(0.25) # debouncing delay

def SetLED(v):
  GPIO.output(21, v)

time.sleep(5) # give the OS plenty of time to boot

GPIO.setmode(GPIO.BCM)
# set GPIO21 to be the LED
GPIO.setup(21, GPIO.OUT)
# set GPIO23 to be the button
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
thread.start_new_thread(ButtonThread, ('', ''))

# Default constructor will pick a default I2C bus.
#
# For the Raspberry Pi this means you should hook up to the only exposed I2C bus
# from the main GPIO header and the library will figure out the bus number based
# on the Pi's revision.
#
# For the Beaglebone Black the library will assume bus 1 by default, which is
# exposed with SCL = P9_19 and SDA = P9_20.
sensor = BMP085.BMP085()

# You can also optionally change the BMP085 mode to one of BMP085_ULTRALOWPOWER,
# BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES.  See the BMP085
# datasheet for more details on the meanings of each mode (accuracy and power
# consumption are primarily the differences).  The default mode is STANDARD.
sensor = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)

fo = open('migraine_pressure_log.txt', 'a')
while True:
  dt = datetime.now().isoformat()
  temperature = sensor.read_temperature()
  pressure = sensor.read_pressure()
  altitude = sensor.read_altitude()
  sealevel_pressure = sensor.read_sealevel_pressure()  
  fo.write('{0},{1:0.2f},{2:0.2f},{3:0.2f},{4:0.2f}\n'.format(dt, temperature, pressure, altitude, sealevel_pressure))
  fo.flush()
  time.sleep(4.8)
  SetLED(True)
  time.sleep(0.2)
  SetLED(False)
  
