#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # # # # # # # #
# Ilya Mazlov # https://github.com/wi1k1n #
# # # # # # # # # # # # # # # # # # # # # #

import os, sys, os.path as op, getpass, subprocess, platform
from util.os_utils import *

def is_root():
	return os.geteuid() == 0

def tryRunFunc(callBack, *args, **kwargs):
	try:
		callBack(*args, **kwargs)
	except Exception as e:
		print('\t> Exception: {0}'.format(e))
		return False
	return True

def runFuncOrExit(printMsg, callBack, *args, **kwargs):
	if len(printMsg):
		print(printMsg)
	if callBack(*args, **kwargs):
		print('\t\t..done')
	else:
		print('\t\t..failed')
		sys.exit()

def generateService(serviceName, scriptPath, interpreterPath, workingDir, listOfArgs=[]):
	if op.isfile(serviceName):
		inp = input('\t> File {0} already exists. Overwrite? [yN]: '.format(op.abspath(serviceName)))
		if inp.lower() != 'y':
			sys.exit()
	def createServiceFile():
		with open(serviceName, 'w') as file:
			file.write("""\
[Unit]
Description=Home Assistant Bot
[Service]
Type=simple
User={username}
WorkingDirectory={workingdir}
ExecStart={interpreter} {scriptpath} {arguments}
Restart=always
[Install]
WantedBy=default.target
""".format(username=getpass.getuser(),
			scriptpath=op.abspath(op.join(os.getcwd(), scriptPath)),
			interpreter=interpreterPath,
			workingdir=workingDir,
			arguments=' '.join([str(a) for a in listOfArgs])
			))
	return tryRunFunc(createServiceFile)

def createServiceLink(serviceName):
	systemServiceLink = op.abspath('/etc/systemd/system/{}'.format(serviceName))
	if op.isfile(systemServiceLink):
		inp = input('\t> File {0} already exists. Overwrite? [yN]: '.format(systemServiceLink))
		if inp.lower() != 'y':
			sys.exit()
		tryRunFunc(os.remove, systemServiceLink)
		# tryRunFunc(subprocess.check_output, 'sudo rm {0}'.format(systemServiceLink))
	return tryRunFunc(os.symlink, op.abspath(op.join(os.getcwd(), serviceName)), systemServiceLink)

def enableService(serviceName):
	return tryRunFunc(subprocess.check_output, 'systemctl enable {}'.format(serviceName), shell=True)
def restartService(serviceName):
	return tryRunFunc(subprocess.check_output, 'systemctl restart {}'.format(serviceName), shell=True)

# Install as service
def main():
	if Windows():
		print('Only supported on Linux')
		sys.exit()

	# Need to be run with priveleges
	if not is_root():
		print('Please run with sudo!')
		sys.exit()

	inp = input('>>> Do you want to install HAFraBot as a service? [yN]: ')
	if inp.lower() == 'y':
		print('> Current dir: {0}'.format(os.getcwd()))

		serviceName = 'hafrabot.service'
		scriptPath = 'main.py'
		interpreterPath = '/home/pi/scripts/hafrapybot/venv/bin/python'
		workingDir = os.getcwd()
		runFuncOrExit('> Generating {}..'.format(serviceName), generateService, serviceName, scriptPath, interpreterPath, workingDir)

		runFuncOrExit('> Creating link to fanctl.service..', createServiceLink, serviceName)
		runFuncOrExit('> Enabling {}..'.format(serviceName), enableService, serviceName)
		runFuncOrExit('> Starting {}..'.format(serviceName), restartService, serviceName)
	sys.exit()

if __name__ == '__main__':
	main()