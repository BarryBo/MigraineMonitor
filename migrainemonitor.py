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

# requires:
# python pillow - 'pip install pillow'
# Adafruit_Python_BMP-master.zip - downloaded from git.  The BMP085 sensor driver is needed.
#
# auto-run on Pi by adding this line to /etc/profile:
#   python <path_to>/migrainemonitor.py &

# Can enable debug output by uncommenting:
#import logging
#logging.basicConfig(level=logging.DEBUG)
import datetime
import time
import threading
import math
import Adafruit_BMP.BMP085 as BMP085
import os
import RPi.GPIO as GPIO
import smbus
import sys

import spidev as SPI
import SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import collections

address = 0x20 # Buzzer and LED2 is controlled by PCF8574 at i2c 0x20
LED = 26 # GPIO pin, 21 on my breadboard 
KEY = 20 # GPIO pin for joystick.  Button was 23 on my breadboard

pressurelog = collections.deque(maxlen=128)

bus = smbus.SMBus(1)

def beep_on():
	bus.write_byte(address,0x7F&bus.read_byte(address))
def beep_off():
	bus.write_byte(address,0x80|bus.read_byte(address))

class ButtonThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  def run(self):
    fo = open('migraine_start_log.txt', 'a')
    while True:
      GPIO.wait_for_edge(KEY, GPIO.FALLING) # can read from 'address' to check which direction the joystick has been moved
      beep_on()
      dt = datetime.now().isoformat()
      fo.write('{0},localtime\n'.format(dt))
      fo.flush()
      time.sleep(0.25) # debouncing delay
      beep_off()

def SetLED(v):
  GPIO.output(LED, v)

def DrawCentered(draw, font, y, m):
   draw.polygon([(0, y), (0,63), (127,63),(127,y)], fill=0)
   (w,h) = draw.textsize(m, font)
   x = (128-w)/2
   draw.text((x,y), m, font=font, fill=255)

spi = SPI.SpiDev(0,0)
disp = SSD1306.SSD1306(19,16,spi)
disp.begin()
disp.clear()
disp.display()
image = Image.new('1', (disp.width, disp.height))
draw = ImageDraw.Draw(image)
fontheader = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf',14)
font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf',20)
disp.set_contrast(0)

# Light blue region is 128x48
# Yellow region is 128x16
def UpdateDisplay(pressure):
   msg = '{0}.{1} kPa'.format((int)(pressure/1000), (int)(pressure%1000))
   DrawCentered(draw, fontheader, 48, msg)
   pressurelog.append(pressure)
   minp = math.floor(min(pressurelog))
   rangep = math.ceil(max(pressurelog)) - minp
   if rangep < 100:
    rangep = 100;
   x=0
   for p in pressurelog:
    p = p - minp
    y = (p*48)/rangep
    draw.line([(x,0),(x,48)]) # erase the old pixel in this column
    draw.point((x,(48-y)), fill=255) # draw the new one
    x = x+1   
   disp.image(image)
   disp.display()
   
class UIThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  def run(self):
    while True:
     time.sleep(4.8)
     SetLED(GPIO.HIGH)
     time.sleep(0.2)
     SetLED(GPIO.LOW)

log_enabled = True if len(sys.argv) > 1 else False
if not log_enabled:
    print("Simple configuration: no logging")
else:
    print("Complex configuration: logging is enabled")

time.sleep(5) # give the OS plenty of time to boot

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
GPIO.setup(KEY, GPIO.IN, GPIO.PUD_UP)
if log_enabled:
  buttonthread = ButtonThread()
  buttonthread.start()
uithread = UIThread()
uithread.start()

# Default constructor will pick a default I2C bus.
#
# For the Raspberry Pi this means you should hook up to the only exposed I2C bus
# from the main GPIO header and the library will figure out the bus number based
# on the Pi's revision.
#
# For the Beaglebone Black the library will assume bus 1 by default, which is
# exposed with SCL = P9_19 and SDA = P9_20.
#sensor = BMP085.BMP085()

# You can also optionally change the BMP085 mode to one of BMP085_ULTRALOWPOWER,
# BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES.  See the BMP085
# datasheet for more details on the meanings of each mode (accuracy and power
# consumption are primarily the differences).  The default mode is STANDARD.
sensor = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)

while True:
  dt = datetime.datetime.today().isoformat()
  temperature = sensor.read_temperature()
  pressure = sensor.read_pressure()
  altitude = sensor.read_altitude()
  sealevel_pressure = sensor.read_sealevel_pressure()
  if log_enabled == True:
    fo = open('migraine_pressure_log_' + str(datetime.date.today())+'.txt', 'a')
    fo.write('{0},{1:0.2f},{2:0.2f},{3:0.2f},{4:0.2f},localtime\n'.format(dt, temperature, pressure, altitude, sealevel_pressure))
    fo.flush()
    fo.close()
  UpdateDisplay(pressure)
  time.sleep(60)
  
