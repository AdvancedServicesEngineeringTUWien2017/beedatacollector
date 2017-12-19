'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import logging
import time
import argparse
import re
import datetime
from random import randint

#get local timestamp
def getTimestamp():
   ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
   ts = ts.replace(' ','T')+'Z'
   return ts

#returns simulated weight
def getRandomWeight(lastweight):
   if(randint(0,10) > 8):
      lastweight = (lastweight - randint(1,12))
   if(randint(0,10) > 9):
      lastweight = (lastweight + randint(1,10))
   return lastweight

#read temperature sensor
def readSensor(path):
   value = 'U'
   try:
      f = open(path, 'r')
      line = f.readline()
      if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
         line = f.readline()
         m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
         if m:
            value = str(float(m.group(2)) / 1000.0)
      f.close()
   except (IOError), e:
      print time.strftime("%x %X"), "Error reading", path, ": ", e
   return value


# Custom MQTT message callback
#def customCallback(client, userdata, message):
#	print("Received a new message: ")
#	print(message.payload)
#	print("from topic: ")
#	print(message.topic)
#	print("--------------\n\n")

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                    help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub", help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
	parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
	exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
	parser.error("Missing credentials for authentication.")
	exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
	myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
	myAWSIoTMQTTClient.configureEndpoint(host, 443)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
	myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
tpath = '/sys/bus/w1/devices/28-000005a1bacf/w1_slave'
sensor = "BeePi01"
lastweight = 27349 #initial simulated weight

while True:
   t = str(readSensor(tpath))
   lts = getTimestamp()
   lastweight = getRandomWeight(lastweight)

   message = '{'+'"DeviceId":"{}", "LocalTimeStamp":"{}", "Temperature":"{}", "Weight":"{}"'.format(sensor, lts, t, lastweight)+'}'
   #print message
   myAWSIoTMQTTClient.publish(topic, message, 1)
   #myAWSIoTMQTTClient.disconnect()
   time.sleep(599)
