# Prototype for Monitoring a Beehive

The idea of this work is to extract data from a beehive without disturbing the hive. To accomplish the first stage of this task, I decided to use several sensors as data sources. Furthermore, the collected data can be used to derive the general state of the bee colony. In other words, the advantage of this setup is that eventual problems can be detected without the need of opening the beehive.


## Overview

The initial plan was to collect at least temperature and weight data every minute with a Raspberry Pi. Consequently, the gathered data will be pushed into AWS DynamoDB. A Spring Boot Application accesses and aggregates the data, and further makes the results available for users (e.g. Angular front-end). However, this very first prototype covers only the data collection part and its transmission to AWS DynamoDB.

## Installation

### Raspberry Pi Setup

The Raspberry Pi Setup is mainly based on the following tutorial: [http://projects.privateeyepi.com/home/temperature-sensor-project-using-ds18b20](http://projects.privateeyepi.com/home/temperature-sensor-project-using-ds18b20 "http://projects.privateeyepi.com/home/temperature-sensor-project-using-ds18b20")

For the first setup, including the ability to measure temperature only, a DS18B20 sensor, a 4.7kOhm resistor (which functions as pull-up resistor), jumpers and a breadboard are required. Certainly, a Raspberry Pi is needed, whereas any model can be used. The temperature sensor uses the wire-1 protocol for communication. Consequently, after the circuit is built on the breadboard, the following settings have to be made.

1. add `dtoverlay=w1-gpio, gpiopin=4, pullup=on` to \boot\config.txt (as long as GPIO pin 4 is connected to pin 2 of the temperature sensor; otherwise use the particular GPIO pin)
2. execute the command `sudo modprobe w1-gpio pullup=1`
3. execute the command `sudo modprobe w1-therm`

Afterwards you will find your sensor in the directory `/sys/bus/w1/`. Otherwise, reboot your Pi. Each connected temperature sensor has its own ID. Furthermore, the sensor data can be displayed by executing `cat /sys/bus/w1/<your-sensor-id>/w1_slave`. The output consists of two lines, whereas the second line represents the current temperature in celsius.

### Push Data into AWS DynamoDB

To connect the Pi with AWS, the service AWS IoT was used. More precisely, Amazon provides an IoT device Python SDK which can be configured (and downloaded) within the AWS Console. Otherwise, the source is also available on [github](https://github.com/aws/aws-iot-device-sdk-python "aws-iot-device-sdk-python"). However, it is advantageous to get the package from the AWS Console, because keys and certificates for authentication can be configured in the setup. Consequently they are already part of the downloaded package and must not be heeded separately. The device configuration within the console allows choosing between several programming languages and operating systems.

The script `pubBeeData.py`, which is based on the pubSub sample of the aws-iot-device-sdk-python, reads the sensor data and pushes it periodically into your iotconsole. Furthermore, it is possible to subscribe a determined topic and test the communication with the MQTT client in the iotconsole. 

To execute `pubBeeData.py`, the script `start.sh` in the root directory of the SDK package must be adopted: `python aws-iot-device-sdk-python/collector/pubBeeData.py -e <endpoint> -r <root-CA-file-path> -c <cert-file-path> -k <private-key-file-path> -t <your-topic>`

If everything works to this point, create a rule in the iotconsole to push the data into DynamoDB. First, the source of messages has to be defined. This is done by the select statement `SELECT * FROM <your-topic>`. Consequently some action is needed. This is the part where the data gets inserted in a DynamoDB table. Therefore I defined `device_id` as hash key and `timestamp` as range key. Both fields are of type string. The hash key value is `${DeviceId}` and the range key value `${timestamp()}`. The last field represents the payload. Therefore insert `payload` into the last field, to push the whole payload into your DynamoDB table. In addition, a role must be specified to finish the rule creation. 

Certainly, it is possible to publish any other data too. Therefore, `pubBeeData.py` additionally contains the simulated weight which is pushed together with the temperature data to DynamoDB. The simulated weight might be replaced by weight cells in future. 