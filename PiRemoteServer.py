#!/usr/bin/python3

# -*- coding: utf-8 -*-
# PiReMonitor Server
#
# Author: JVaassen, based on Xorfor's PiMonitor

import os
from lxml import etree
import socket
import _thread

HOST='192.168.0.95'
PORT=8085

class output:

  global _last_idle, _last_total
  _last_idle = _last_total = 0

  # Return % of CPU used by user
  # Based on: https://rosettacode.org/wiki/Linux_CPU_utilization#Python
  def getCPUuse(self):
   	global _last_idle, _last_total
   	try:
      	 with open('/proc/stat') as f:
              fields = [float(column) for column in f.readline().strip().split()[1:]]
      	 idle, total = fields[3], sum(fields)
      	 idle_delta, total_delta = idle - _last_idle, total - _last_total
      	 _last_idle, _last_total = idle, total
      	 res = round(100.0 * (1.0 - idle_delta / total_delta), 2 )
   	except:
      	 res = 0.0
   	return res

  def getCPUcount(self):
   	return os.cpu_count()

  def getCPUuptime(self):
   	try:
      	 with open('/proc/uptime') as f:
              fields = [float(column) for column in f.readline().strip().split()]
      	 res = round(fields[0])
   	except:
      	 res = 0.0
   	return res

  # Return number of network connections
  def getNetworkConnections(self,state):
   	res = 0
   	try:
      	 for line in os.popen("netstat -tun").readlines():
              if line.find(state) >= 0:
               	res += 1
   	except:
      	 res = 0
   	return res

  # Return GPU temperature
  def getGPUtemperature(self):
   	try:
      	 res = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline().replace("temp=", "").replace("'C\n", "")
      	 if (res==""):
         	 res = "0"
   	except:
      	 res = "0"
   	return float(res)

  def getGPUmemory(self):
   	try:
      	 res = os.popen("/opt/vc/bin/vcgencmd get_mem gpu").readline().replace("gpu=", "").replace("M\n", "")
      	 if (res==""):
         	 res = 0
   	except:
      	 res = "0"
   	return float(res)

  def getCPUmemory(self):
   	try:
      	 res = os.popen("/opt/vc/bin/vcgencmd get_mem arm").readline().replace("arm=", "").replace("M\n", "")
      	 if (res==""):
         	 res = 0
   	except:
      	 res = "0"
   	return float(res)

  # Return CPU temperature
  def getCPUtemperature(self):
   	try:
      	 res = os.popen("cat /sys/class/thermal/thermal_zone0/temp").readline()
      	 if (res==""):
         	 res = 0
   	except:
      	 res = "0"
   	return round(float(res)/1000,1)

  # Return CPU speed in Mhz
  def getCPUcurrentSpeed(self):
   	try:
      	 res = os.popen("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").readline()
   	except:
      	 res = "0"
   	return round(int(res)/1000)

  # Return RAM information in a list
  # Based on: https://gist.github.com/funvill/5252169
  def getRAMinfo(self):
   	p = os.popen("free -b")
   	i = 0
   	while 1:
      	 i = i + 1
      	 line = p.readline()
      	 if i == 2:
              res = line.split()[1:4]
              # Index 0: total RAM
              # Index 1: used RAM
              # Index 2: free RAM
              return round(100 * int(res[1]) / int(res[0]), 2 )
  # http://www.microcasts.tv/episodes/2014/03/15/memory-usage-on-the-raspberry-pi/
  # https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=164787
  # https://stackoverflow.com/questions/22102999/get-total-physical-memory-in-python/28161352
  # https://stackoverflow.com/questions/17718449/determine-free-ram-in-python
  # https://www.reddit.com/r/raspberry_pi/comments/60h5qv/trying_to_make_a_system_info_monitor_with_an_lcd/

  # Get uptime of RPi
  # Based on: http://cagewebdev.com/raspberry-pi-showing-some-system-info-with-a-python-script/
  def getUpStats(self):
   	#Returns a tuple (uptime, 5 min load average)
   	try:
      	 s = os.popen("uptime").readline()
      	 load_split = s.split("load average: ")
      	 load_five = float(load_split[1].split(",")[1])
      	 up = load_split[0]
      	 up_pos = up.rfind(",", 0, len(up)-4)
      	 up = up[:up_pos].split("up ")[1]
      	 return up
   	except:
      	 return ""

  # Get voltage
  # Based on: https://www.raspberrypi.org/forums/viewtopic.php?t=30697
  def getVoltage(self,p):
   	if p in ["core", "sdram_c", "sdram_i", "sdram_p"]:
      	 try:
              res = os.popen(
               	"/opt/vc/bin/vcgencmd measure_volts {}".format(p)).readline().replace("volt=", "").replace("V", "")
              if (res==""):
                 res = 0
      	 except:
              res = "0"
   	else:
      	 res = "0"
   	return float(res)

  # ps aux | grep domoticz | awk '{sum=sum+$6}; END {print sum}'
  def getDomoticzMemory(self):
   	try:
      	 res = os.popen(
              "ps aux | grep domoticz | awk '{sum=sum+$6}; END {print sum}'").readline().replace("\n", "")
   	except:
      	 res = "0"
   	return float(res)

  def encodee(self):
      root = etree.Element("root")
     
      etree.SubElement(root,"getVoltageCore").text = str(self.getVoltage("core"))
      etree.SubElement(root,"getVoltageSdRam_C").text = str(self.getVoltage("sdram_c"))
      etree.SubElement(root,"getVoltageSdRam_I").text = str(self.getVoltage("sdram_i"))
      etree.SubElement(root,"getVoltageSdRam_P").text = str(self.getVoltage("sdram_p"))
      etree.SubElement(root,"getCPUcount").text = str(self.getCPUcount())
      etree.SubElement(root,"getCPUcurrentSpeed").text = str(self.getCPUcurrentSpeed())
      etree.SubElement(root,"getCPUmemory").text = str(self.getCPUmemory())
      etree.SubElement(root,"getCPUtemperature").text = str(self.getCPUtemperature())
      etree.SubElement(root,"getCPUuse").text = str(self.getCPUuse())
      etree.SubElement(root,"getDomoticzMemory").text = str(self.getDomoticzMemory())
      etree.SubElement(root,"getGPUmemory").text = str(self.getGPUmemory())
      etree.SubElement(root,"getGPUtemperature").text = str(self.getGPUtemperature())
      etree.SubElement(root,"getRAMinfo").text = str(self.getRAMinfo())
      etree.SubElement(root,"getNetworkConnections").text = str(self.getNetworkConnections("ESTABLISHED"))
      etree.SubElement(root,"getCPUuptime").text = str(self.getCPUuptime())

      # print( "bla = "+  str(etree.tostring(root, pretty_print=True)))
      return etree.tostring(root)

def server():
  global HOST,PORT
 
  def on_new_client(csocket,addr):
     print("Connection from: " + str(addr))
     while True:
        data = csocket.recv(1024).decode('utf-8')
        MyO = output()
        csocket.send(MyO.encodee())
     csocket.close()
        

  #host = socket.gethostname()   # get local machine name
  #port = 8085  # Make sure it's within the > 1024 $$ <65535 range
  #print("Host : " + str(host))

  #while True:
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #hostIP = socket.gethostbyname((host))
  #s.bind((hostIP, port))
  s.bind((HOST, PORT))
  #s.bind(('127.0.0.1', port))
  s.listen(1)
  while True:
     c, addr = s.accept()
     _thread.start_new_thread(on_new_client,(c,addr))

#     print("Connection from: " + str(addr))
#     try:
#        while True:
#           data = c.recv(1024).decode('utf-8')
#           # if not data:
           #   break
           # print('From online user: ' + data)
#           MyO = output()
#           c.send(MyO.encodee())
#     except BaseException as error: 
#        print ("Error x"+ str(error))
#        c.close()
#        s.close()

  c.close()
  s.close()

if __name__ == '__main__':
  server()

