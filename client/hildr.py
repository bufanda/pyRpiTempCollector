#!/usr/bin/env python
# py-tempserver is a udp server where clients can json formmated communicate
# the cpu core temperature the server shall be expanded later on
# with a fan controlling function to control
# a chassis fan
#
# This project is intended to control fans in an enclousre with several
# rasperry pi or similar boards

# import modules
import re
import socket
import time
import json
import platform
import subprocess
import yaml
import syslog
import argparse

ENABLE_LOGGING = True
LOG_LEVEL = 0
UDP_SERVER_ADDRESS = "192.168.178.12"
UDP_LISTEN_PORT = 1337

BSD_NAME = "FreeBSD"
LINUX_NAME = "Linux"

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--log-level', type=int, default='0', choices=[0, 1, 2, 3], help='set log-level (0|1|2|3)')
args = parser.parse_args()

if args.log_level:
	LOG_LEVEL = args.log_level

def log_message ( msg , prio=0):
	if ENABLE_LOGGING:
		if prio <= LOG_LEVEL:
			syslog.syslog(syslog.LOG_INFO, msg)

def main ():
    log_message(msg="py-tempclient started.")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

    data = {'host': platform.node(), 'state': 'ok', 'msg': ''}

    with open("/etc/hildr/hildr.yml", "r") as stream:
        settings = yaml.load(stream)

    if settings["server"]:
        UDP_SERVER_ADDRESS = settings["server"]

    if settings["port"]:
        UDP_LISTEN_PORT = settings["port"]

    while True:
        if platform.system() == LINUX_NAME:
            f = open("/sys/class/thermal/thermal_zone0/temp")
            cpuTemp = f.read()
            cpuTemp = float(cpuTemp)/1000
            data['msg'] = str(cpuTemp)
        elif platform.system() == BSD_NAME:
            cpuTemp = subprocess.check_output(['sysctl', 'dev.cpu.0.temperature'])
            cpuTemp = re.search('dev.cpu.0.temperature:\s([0-9\.]*)C', cpuTemp).group(1)
            data['msg'] = cpuTemp
        else:
            data['msg'] = "Unsupported System"
            data['state'] = "error"

        msg = json.dumps(data)
        log_message(msg, 2)
        sock.sendto(json.dumps(data), (UDP_SERVER_ADDRESS, UDP_LISTEN_PORT))
        time.sleep(60)

main ()
