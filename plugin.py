#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PiReMonitor Plugin
#
# Author: JVaassen, based on Xorfor's PiMonitor 
"""
<plugin key="jva_pimonitor" name="PiReMonitor" author="Jvaassen" version="0.0.1" wikilink="####https://github.com/Xorfor/Domoticz-PiMonitor-Plugin">
    <params>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
        <param field="Address" label="Host Address" width="75px" default="127.0.0.1">
        </param>
        <param field="Port" label="Host Port" width="75px" default = "8085">
        </param>
    </params>
</plugin>
"""

import sys
sys.path.append('/usr/lib/python3/dist-packages')

import socket
import lxml
import Domoticz
import os

global sockserv

class BasePlugin:

    __HEARTBEATS2MIN = 6
    __MINUTES = 1

    # Device units
    __UNIT_CPUTEMP = 1
    __UNIT_GPUTEMP = 2
    __UNIT_RAMUSE = 3
    __UNIT_CPUUSE = 4
    __UNIT_CPUSPEED = 5
    __UNIT_UPTIME = 6
    __UNIT_CPUMEMORY = 7
    __UNIT_GPUMEMORY = 8
    __UNIT_CPUCOUNT = 9
    __UNIT_CONNECTIONS = 10
    __UNIT_COREVOLTAGE = 11
    __UNIT_SDRAMCVOLTAGE = 12
    __UNIT_SDRAMIVOLTAGE = 13
    __UNIT_SDRAMPVOLTAGE = 14
    __UNIT_DOMOTICZMEMORY = 15

    __UNITS = [
        # Unit, Name, Type, Subtype, Options, Used
        [__UNIT_CPUTEMP, "CPU temperature", 243, 31, {"Custom": "0.0;C"}, 1],
        [__UNIT_GPUTEMP, "GPU temperature", 243, 31, {"Custom": "0.0;C"}, 1],
        [__UNIT_RAMUSE, "Memory usage", 243, 31, {"Custom": "0;%"}, 1],
        [__UNIT_CPUUSE, "CPU usage", 243, 31, {"Custom": "0;%"}, 1],
        [__UNIT_CPUSPEED, "CPU speed", 243, 31, {"Custom": "0;Mhz"}, 1],
        [__UNIT_UPTIME, "Up time", 243, 31, {"Custom": "0;sec"}, 1],
        [__UNIT_CPUMEMORY, "CPU memory", 243, 31, {"Custom": "0;MB"}, 1],
        [__UNIT_GPUMEMORY, "GPU memory", 243, 31, {"Custom": "0;MB"}, 1],
        [__UNIT_CPUCOUNT, "CPU count", 243, 31, {}, 1],
        [__UNIT_CONNECTIONS, "Connections", 243, 31, {}, 1],
        [__UNIT_COREVOLTAGE, "Core voltage", 243, 31, {"Custom": "0;V"}, 1],
        [__UNIT_SDRAMCVOLTAGE, "SDRAM C voltage", 243, 31, {"Custom": "0;V"}, 1],
        [__UNIT_SDRAMIVOLTAGE, "SDRAM I voltage", 243, 31, {"Custom": "0;V"}, 1],
        [__UNIT_SDRAMPVOLTAGE, "SDRAM P voltage", 243, 31, {"Custom": "0;V"}, 1],
        [__UNIT_DOMOTICZMEMORY, "Domoticz memory", 243, 31, {"Custom": "0;KB"}, 1],
    ]


    def __init__(self):
        self.__runAgain = 0
        return

    def onStart(self):
        global sockserv
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)
        # Validate parameters
        # Images
        # Check if images are in database
        if "xfrpimonitor" not in Images:
            Domoticz.Image("xfrpimonitor.zip").Create()
        image = Images["xfrpimonitor"].ID
        Domoticz.Debug("Image created. ID: "+str(image))
        #connect to server

        host = Parameters["Address"]
        port = Parameters["Port"]
        sockserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Domoticz.Debug("connect to "+ host +" "+ str(int(port)))
        sockserv.connect((host, int(port)))

        # Create devices
        if len(Devices) == 0:
            for unit in self.__UNITS:
                Domoticz.Device(Unit=unit[0],
                                Name=unit[1],
                                Type=unit[2],
                                Subtype=unit[3],
                                Options=unit[4],
                                Used=unit[5],
                                Image=image).Create()
        # Log config

        DumpAllToLog()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        global sockserv
        Domoticz.Debug("onDisconnect called")
        sockserv.close()

    def onHeartbeat(self):
        global sockserv
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            self.__runAgain = self.__HEARTBEATS2MIN * self.__MINUTES
            # Execute your command
            #
            message="request"
            try: 
               sockserv.send(message.encode('utf-8'))
            except socket.error: 
               # reconnect to server 
               host = Parameters["Address"]
               port = Parameters["Port"]
               sockserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               Domoticz.Debug("re-connect to "+ host +" "+ str(int(port)))
               sockserv.connect((host, int(port)))
               # resend request message
               sockserv.send(message.encode('utf-8'))

            
            data = sockserv.recv(1024).decode('utf-8')
            Domoticz.Debug('Received from server: ' + str(data))

            from lxml import objectify

            tree = objectify.fromstring(str(data))
            #print ("GPU = " + str(tree.GPUTemp.text))
            #print ("CPU = " + str(tree.CPUUptime.text))

            fnumber = tree.getCPUcount.text
            Domoticz.Debug("CPU count...: {}".format(fnumber))
            UpdateDevice(self.__UNIT_CPUCOUNT, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getCPUtemperature.text)
            Domoticz.Debug("CPU temp....: {} C".format(fnumber))
            UpdateDevice(self.__UNIT_CPUTEMP, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getGPUtemperature.text)
            Domoticz.Debug("GPU temp....: {} C".format(fnumber))
            UpdateDevice(self.__UNIT_GPUTEMP, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getGPUmemory.text)
            Domoticz.Debug("GPU memory..: {} Mb".format(fnumber))
            UpdateDevice(self.__UNIT_GPUMEMORY, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getCPUmemory.text)
            Domoticz.Debug("CPU memory..: {} Mb".format(fnumber))
            UpdateDevice(self.__UNIT_CPUMEMORY, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getCPUuse.text)
            Domoticz.Debug("CPU use.....: {} %".format(fnumber))
            UpdateDevice(self.__UNIT_CPUUSE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getRAMinfo.text)
            Domoticz.Debug("RAM use.....: {} %".format(fnumber))
            UpdateDevice(self.__UNIT_RAMUSE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = int(tree.getCPUcurrentSpeed.text)
            Domoticz.Debug("CPU speed...: {} Mhz".format(fnumber))
            UpdateDevice(self.__UNIT_CPUSPEED, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = round(float(tree.getVoltageCore.text), 2 )
            Domoticz.Debug("Core voltage...: {} V".format(fnumber))
            UpdateDevice(self.__UNIT_COREVOLTAGE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = round(float(tree.getVoltageSdRam_C.text), 2)
            Domoticz.Debug("SDRAM C...: {} V".format(fnumber))
            UpdateDevice(self.__UNIT_SDRAMCVOLTAGE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = round(float(tree.getVoltageSdRam_I.text), 2 )
            Domoticz.Debug("SDRAM I...: {} V".format(fnumber))
            UpdateDevice(self.__UNIT_SDRAMIVOLTAGE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            fnumber = round(float(tree.getVoltageSdRam_P.text), 2 )
            Domoticz.Debug("SDRAM P...: {} V".format(fnumber))
            UpdateDevice(self.__UNIT_SDRAMPVOLTAGE, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
            res = int(tree.getCPUuptime.text)  # in sec
            Domoticz.Debug("Up time.....: {} sec".format(res))
            # if res < 60:
            fnumber = round(res, 2)
            options = {"Custom": "0;s"}
            # UpdateDeviceOptions(self.__UNIT_UPTIME, {"Custom": "0;s"})
            if res >= 60:
                fnumber = round(res / (60), 2)
                options = {"Custom": "0;min"}
                # UpdateDeviceOptions(self.__UNIT_UPTIME, {"Custom": "0;min"})
            if res >= 60 * 60:
                fnumber = round(res / (60 * 60), 2)
                options = {"Custom": "0;h"}
                # UpdateDeviceOptions(self.__UNIT_UPTIME, {"Custom": "0;h"})
            if res >= 60 * 60 * 24:
                fnumber = round(res / (60 * 60 * 24), 2)
                options = {"Custom": "0;d"}
                # UpdateDeviceOptions(self.__UNIT_UPTIME, {"Custom": "0;d"})
            UpdateDeviceOptions(self.__UNIT_UPTIME, options)
            UpdateDevice(self.__UNIT_UPTIME, int(fnumber), str(fnumber), AlwaysUpdate=True)
            #
            inumber = int(tree.getNetworkConnections.text)
            Domoticz.Debug("Connections.....: {}".format(inumber))
            UpdateDevice(self.__UNIT_CONNECTIONS, inumber, str(inumber), AlwaysUpdate=True)
            #
            fnumber = float(tree.getDomoticzMemory.text)
            Domoticz.Debug("Domoticz memory...: {} KB".format(fnumber))
            UpdateDevice(self.__UNIT_DOMOTICZMEMORY, int(fnumber),
                         str(fnumber), AlwaysUpdate=True)
            #
        else:
            Domoticz.Debug(
                "onHeartbeat called, run again in {} heartbeats.".format(self.__runAgain))

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

################################################################################
# Generic helper functions
################################################################################
def DumpDevicesToLog():
    # Show devices
    Domoticz.Debug("Device count.........: {}".format(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device...............: {} - {}".format(x, Devices[x]))
        Domoticz.Debug("Device Idx...........: {}".format(Devices[x].ID))
        Domoticz.Debug(
            "Device Type..........: {} / {}".format(Devices[x].Type, Devices[x].SubType))
        Domoticz.Debug("Device Name..........: '{}'".format(Devices[x].Name))
        Domoticz.Debug("Device nValue........: {}".format(Devices[x].nValue))
        Domoticz.Debug("Device sValue........: '{}'".format(Devices[x].sValue))
        Domoticz.Debug(
            "Device Options.......: '{}'".format(Devices[x].Options))
        Domoticz.Debug("Device Used..........: {}".format(Devices[x].Used))
        Domoticz.Debug(
            "Device ID............: '{}'".format(Devices[x].DeviceID))
        Domoticz.Debug("Device LastLevel.....: {}".format(
            Devices[x].LastLevel))
        Domoticz.Debug("Device Image.........: {}".format(Devices[x].Image))


def DumpImagesToLog():
    # Show images
    Domoticz.Debug("Image count..........: {}".format((len(Images))))
    for x in Images:
        Domoticz.Debug("Image '{}'...: '{}'".format(x, Images[x]))


def DumpParametersToLog():
    # Show parameters
    Domoticz.Debug("Parameters count.....: {}".format(len(Parameters)))
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("Parameter '{}'...: '{}'".format(x, Parameters[x]))


def DumpSettingsToLog():
    # Show settings
    Domoticz.Debug("Settings count.......: {}".format(len(Settings)))
    for x in Settings:
        Domoticz.Debug("Setting '{}'...: '{}'".format(x, Settings[x]))


def DumpAllToLog():
    DumpDevicesToLog()
    DumpImagesToLog()
    DumpParametersToLog()
    DumpSettingsToLog()


def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details (" + str(len(httpDict)) + "):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug(
                    "....'" + x + " (" + str(len(httpDict[x])) + "):")
                for y in httpDict[x]:
                    Domoticz.Debug("........'" + y + "':'" +
                                   str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("....'" + x + "':'" + str(httpDict[x]) + "'")


def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[
                Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(
                nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            # Domoticz.Debug("Update {}: {} - '{}'".format(Devices[Unit].Name, nValue, sValue))


def UpdateDeviceOptions(Unit, Options={}):
    if Unit in Devices:
        if Devices[Unit].Options != Options:
            Devices[Unit].Update(nValue=Devices[Unit].nValue,
                                 sValue=Devices[Unit].sValue, Options=Options)
            Domoticz.Debug("Device Options update: {} = {}".format(
                Devices[Unit].Name, Options))


def UpdateDeviceImage(Unit, Image):
    if Unit in Devices and Image in Images:
        if Devices[Unit].Image != Images[Image].ID:
            Devices[Unit].Update(nValue=Devices[Unit].nValue,
                                 sValue=Devices[Unit].sValue, Image=Images[Image].ID)
            Domoticz.Debug("Device Image update: {} = {}".format(
                Devices[Unit].Name, Images[Image].ID))

#--- EOF
