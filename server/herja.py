#!/usr/bin/python -u
# py-tempserver is a udp server where clients can json formmated
# communicate the cpu core temperature the server shall be expanded later
# on with a fan controlling function to control a chassis fan
#
# This project is intended to control fans in an enclousre with several
# rasperry pi or similar boards

# import modules
import os
import socket
import json
import syslog
import argparse
import yaml

ENABLE_LOGGING = True
ENABLE_GPIO = False
LOG_LEVEL = 0
UDP_LISTEN_ADDRESS = "0.0.0.0"
UDP_LISTEN_PORT = 1337
WEIGHTS_FILE = "/etc/herja/weights.yml"
GPIO_DEF = "/etc/herja/gpio.yml"
GPIO_LIST = {"gpio": [3, 15, 27, 10, 7, 5, 13, 21]}

parser = argparse.ArgumentParser()
parser.add_argument('-g', '--gpio', action='store_true', help='enable gpio support')
parser.add_argument('-l', '--log-level', type=int, default='0', choices=[0, 1, 2, 3], help='set log-level (0|1|2|3)')
args = parser.parse_args()

if args.gpio:
	ENABLE_GPIO = True

if args.log_level:
	LOG_LEVEL = args.log_level

if ENABLE_GPIO:
	import RPi.GPIO as gpio
	gpio.setmode(gpio.BCM)

if ENABLE_GPIO:
	with open(GPIO_DEF, "r") as stream:
		GPIO_LIST = yaml.load(stream)
		for g in range(len(GPIO_LIST["gpio"])):
			if GPIO_LIST["usage"][g] != "ignore":
				gpio.setup(GPIO_LIST["gpio"][g], gpio.OUT)
				gpio.output(GPIO_LIST["gpio"][g], gpio.LOW)


with open(WEIGHTS_FILE, "r") as stream:
	weight = yaml.load(stream)

temperatures = {}

for i in weight.keys():
	temperatures[i] = 0

def set_gpio (gpioName, value=0):
	if ENABLE_GPIO:
		for g in range(len(GPIO_LIST["gpio"])):
			if GPIO_LIST["usage"][g] == gpioName:
				if value == 0:
					gpio.output(GPIO_LIST["gpio"][g], gpio.LOW)
				else:
					gpio.output(GPIO_LIST["gpio"][g], gpio.HIGH)

def log_message (msg , prio=0):
	if ENABLE_LOGGING:
		if prio <= LOG_LEVEL:
			syslog.syslog(syslog.LOG_INFO, msg)


def main ():
	mwtemp = 0

	log_message(msg="py-tempserver started.")

	sock = socket.socket(socket.AF_INET,  # Internet
			socket.SOCK_DGRAM)  # UDP
	sock.bind((UDP_LISTEN_ADDRESS, UDP_LISTEN_PORT))

	if ENABLE_LOGGING:
		logmsg = "listen to " + str(UDP_LISTEN_PORT)
		log_message(msg=logmsg)

	while True:
		data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
		logmsg = "recived packet from "+ str(addr) + " message says: " + str(data)
		log_message(msg=logmsg,prio=3)
		dat = json.loads(data)
		if dat['state'] == "ok":
			temperatures[dat['host']] = float(dat['msg'])
			mwtemp_old = mwtemp
			mwtemp = 0
			devider = 0
			for t in temperatures:
				mwtemp = mwtemp + (float(temperatures[t]) * float(weight[t]))
				devider = devider + float(weight[t])
			mwtemp = mwtemp / devider
			if mwtemp != mwtemp_old:
				logmsg = "Mean Value of Cores: " + str(mwtemp)
				log_message(msg=logmsg, prio=2)

			if ENABLE_GPIO:
				if mwtemp > 60:
					set_gpio("alarm", 1)
				else:
					set_gpio("alarm", 0)

				if mwtemp > 55:
					set_gpio("temphigh", 1)
				else:
					set_gpio("temphigh", 0)

				set_gpio("tempnorm", 1)


main()
