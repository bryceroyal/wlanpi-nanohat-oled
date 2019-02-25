#!/usr/bin/env python
#
# BakeBit example for the basic functions of BakeBit 128x64 OLED (http://wiki.friendlyarm.com/wiki/index.php/BakeBit_-_OLED_128x64)
#
# The BakeBit connects the NanoPi NEO and BakeBit sensors.
# You can learn more about BakeBit here:  http://wiki.friendlyarm.com/BakeBit
#
# Have a question about this example?  Ask on the forums here:  http://www.friendlyarm.com/Forum/
#
'''
## License

The MIT License (MIT)

BakeBit: an open source platform for connecting BakeBit Sensors to the NanoPi NEO.
Copyright (C) 2016 FriendlyARM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import threading
import signal
import os
import socket

global width
width=128
global height
height=64

global pageCount
pageCount=3
global pageIndex
pageIndex=0
global showPageIndicator
showPageIndicator=False
global showButtonIndicator
showButtonIndicator=True

global pageSleep
pageSleep=300
global pageSleepCountdown
pageSleepCountdown=pageSleep

oled.init()  #initialze SEEED OLED display
oled.setNormalDisplay()      #Set display to normal mode (i.e non-inverse mode)
oled.setHorizontalMode()

global drawing
drawing = False

global image
image = Image.new('1', (width, height))
global draw
draw = ImageDraw.Draw(image)
global fontb24
fontb24 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24);
global font14
font14 = ImageFont.truetype('DejaVuSansMono.ttf', 14);
global smartFont
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10);
global fontb14
fontb14 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14);
global font11
font11 = ImageFont.truetype('DejaVuSansMono.ttf', 11);

global lock
lock = threading.Lock()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def draw_page():
    global drawing
    global image
    global draw
    global oled
    global font
    global font14
    global smartFont
    global width
    global height
    global pageCount
    global pageIndex
    global showPageIndicator
    global width
    global height
    global lock
    global pageSleepCountdown

    lock.acquire()
    is_drawing = drawing
    page_index = pageIndex
    lock.release()

    if is_drawing:
        return

    #if the countdown is zero we should be sleeping (blank the display to reduce screenburn)
    if pageSleepCountdown == 0:
        oled.clearDisplay()
        return

    pageSleepCountdown = pageSleepCountdown - 1

    lock.acquire()
    drawing = True
    lock.release()

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    # Draw current page indicator
    if showPageIndicator:
        dotWidth=4
        dotPadding=2
        dotX=width-dotWidth-1
        dotTop=(height-pageCount*dotWidth-(pageCount-1)*dotPadding)/2
        for i in range(pageCount):
            if i==page_index:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=255)
            else:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=0)
            dotTop=dotTop+dotWidth+dotPadding

    # Draw bottom of screen button indicators
    bottomLine=55   # Define the starting vertical pixel

    if showButtonIndicator:
        draw.text((0,bottomLine),"Home",font=smartFont,fill=255)
        draw.text((50,bottomLine),"Next",font=smartFont,fill=255)
        draw.text((93,bottomLine),"Select",font=smartFont,fill=255)

    if page_index==0:   # Default page, shows WLANpi version, hostname, and eth0 IP address 
        ver = "grep \"WLAN Pi v\" /var/www/html/index.html | sed \"s/<[^>]\+>//g\"" # Pull the version from a file by building the command
        VER = subprocess.check_output(ver, shell = True )                           #  and saving the result
        draw.text((0,1),str(VER),font=smartFont,fill=255)                           #  and then draw it on screen
        HOSTNAME = subprocess.check_output('hostname', shell = True)                # Get the current device hostname
        draw.text((0,11),str(HOSTNAME),font=font11,fill=255)                        #  and then draw it on screen
        draw.text((95,20),"eth0",font=smartFont,fill=255)
        ip_eth0 = "ip addr show eth0 | grep -Po \'inet \K[\d.]+\'"                  # Pull the IP address for eth0 by building the command
        IP_ETH0 = subprocess.check_output(ip_eth0, shell = True )                   #  and saving the result
        draw.text((0,29),str(IP_ETH0),font=font14,fill=255)                         #  and then draw it on screen
    
    elif page_index==1: # Displays IP for usb0, wlan1, and CPU temp
        draw.text((95,0),"usb0",font=smartFont,fill=255)                           # usb0 interface marker
        ip_usb0 = "ip addr show usb0 | grep -Po \'inet \K[\d.]+\'"                  # Pull the IP address for usb0 by building the command
        IP_USB0 = subprocess.check_output(ip_usb0, shell = True )                   #  and saving the result
        draw.text((0,9),str(IP_USB0),font=font14,fill=255)                          #  and then draw it on screen
        
        # This check does not work consistently for wlan1.  The APIPA address takes a long time to appear, and until it does this check will
        #  pass as the path exists.  The address has not always populated, and so the subprocess.check_output function fails
        #  Currently unsure of a fix for this.
        #if os.path.exists('/sys/class/net/wlan1'):                                  # If the directory doesn't exist do not display wlan1
        #    draw.text((95,23),"wlan1",font=smartFont,fill=255)                          # wlan1 interface marker
        #    ip_wlan1 = "ip addr show wlan1 | grep -Po \'inet \K[\d.]+\'"                # Pull the IP address for wlan1 by building the command
        #    IP_WLAN1 = subprocess.check_output(ip_wlan1, shell = True )                 #  and saving the result
        #    draw.text((0,31),str(IP_WLAN1),font=font14,fill=255)                        #  and then draw it on screen
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = 2
        top = padding
        bottom = height-padding
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0
        tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read());
        if tempI>1000:
            tempI = tempI/1000
        tempStr = "CPU TEMP: %sC" % str(tempI)
        draw.text((x,40),    tempStr,  font=font11, fill=255)

    elif page_index==2: #shutdown -- yes
        draw.text((2, 2),  'Shutdown?',  font=fontb14, fill=255)

        draw.rectangle((2,20,width-4,20+16), outline=0, fill=255)
        draw.text((4, 22),  'B3 to confirm',  font=font11, fill=0)

        #draw.rectangle((2,38,width-4,38+16), outline=0, fill=0)
        #draw.text((4, 40),  'No',  font=font11, fill=255)

    elif page_index==3:
        draw.text((2, 2),  'Shutting down',  font=fontb14, fill=255)
        draw.text((2, 20),  'Please wait',  font=font11, fill=255)

    oled.drawImage(image)

    lock.acquire()
    drawing = False
    lock.release()


def is_showing_power_msgbox():
    global pageIndex
    lock.acquire()
    page_index = pageIndex
    lock.release()
    if page_index==2 or page_index==3:
        return True
    return False


def update_page_index(pi):
    global pageIndex
    lock.acquire()
    pageIndex = pi
    lock.release()

def receive_signal(signum, stack):
    global pageIndex
    global pageSleepCountdown
    global pageSleep

    pageSleepCountdown = pageSleep #user pressed a button, reset the sleep counter

    lock.acquire()
    page_index = pageIndex
    lock.release()

    if page_index==5:
        return

    if signum == signal.SIGUSR1:    # This is Button 1 - Go to the home screen
        print 'Button 1 pressed, go to Home screen'
        update_page_index(0)            # Update the global page index value
        draw_page()                     # Redraw the page after changing index

#        if is_showing_power_msgbox():
#            if page_index==3:
#                update_page_index(4)
#            else:
#                update_page_index(3)
#            draw_page()
#        else:
#            pageIndex=0
#            draw_page()

    if signum == signal.SIGUSR2:        # This is Button 2 - Cycle through the menu
        if page_index < (pageCount-1):          # If the page index is not at the last page
            page_index += 1                 #  Increment the page index value
        elif page_index == (pageCount-1):        # If the page index is at the last page
            page_index = 0                  #  loop back to the home page index
            
        update_page_index(page_index)   # Set the global page index
        
        print 'Button 2 pressed, go to next menu item', page_index  # Debug output

    if signum == signal.SIGALRM:    # This is Button 3 - Select an item
        if is_showing_power_msgbox():
            if page_index == 2:
                update_page_index(3)
                draw_page()
            else:                   # If we aren't on page 2 then don't do anything, just redraw.
                draw_page()
        else:                       # If we aren't showing the power message box don't do anything, just redraw.
            draw_page()
        print 'Button 3 pressed, select an item'    # Debug output


#image0 = Image.open('friendllyelec.png').convert('1')
image0 = Image.open('wlanprologo.png').convert('1')
oled.drawImage(image0)
time.sleep(2)

signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

while True:
    try:
        draw_page()

        lock.acquire()
        page_index = pageIndex
        lock.release()

        if page_index==3:   # This code runs when page 5 is visible
            time.sleep(2)
            while True:
                lock.acquire()
                is_drawing = drawing
                lock.release()
                if not is_drawing:
                    lock.acquire()
                    drawing = True
                    lock.release()
                    page_index==0
                    oled.clearDisplay()
                    break
                else:
                    time.sleep(.1)
                    continue
            time.sleep(1)
            os.system('systemctl poweroff --message=Shutdown_By_OLED_Menu')     # Shutdown and add message for reason
            break
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except IOError:
        print ("Error")
