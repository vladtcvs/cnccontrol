#!/usr/bin/env python3

import subprocess
import os
from common import config
import getopt
import sys
import signal

path = os.path.abspath(os.path.dirname(__file__))
default_server = os.path.normpath(path + "/server/server.py")
default_gui = os.path.normpath(path + "/gui/gcodeconvert.py")

class ServerLauncher(object):
    def __init__(self, server=default_server, emulate_table=True, emulate_spindel=True, port=config.TABLE_PORT, baudrate=config.BAUDRATE):
        self.server = server
        self.emulate_table = emulate_table
        self.emulate_spindel = emulate_spindel
        self.port = port
        self.baurdate = baudrate
        self.proc = None

    def start(self):
        args = [self.server]
        if self.emulate_table:
            args.append("-e")
        else:
            args += ["-p", self.port]
            args += ["-b", str(self.baurdate)]
        if self.emulate_spindel:
            args.append("-E")

        self.proc = subprocess.Popen(args)

    def wait(self):
        if self.proc is None:
            return
        self.proc.wait()
        self.proc = None

class GuiLauncher(object):
    def __init__(self, gui=default_gui):
        self.gui = gui
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen([self.gui])

    def wait(self):
        if self.proc is None:
            return
        self.proc.wait()
        self.proc = None

emulate_table = False
emulate_spindel = False
port = config.TABLE_PORT
brate = config.BAUDRATE

try:
    opts, args = getopt.getopt(sys.argv[1:], "eEp:b:", ["port=", "baudrate="])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    sys.exit(2)

for o, a in opts:
    if o == "-e":
        emulate_table = True
    elif o == "-E":
        emulate_spindel = True
    elif o in ("-p", "--port"):
        port = a
    elif o in ("-b", "--baudrate"):
        brate = int(a)
    else:
        assert False, "unhandled option"


gui = GuiLauncher()
server = ServerLauncher(emulate_table=emulate_table, emulate_spindel=emulate_spindel, port=port, baudrate=brate)

server.start()
gui.start()

gui.wait()

os.killpg(os.getpgid(server.proc.pid), signal.SIGTERM)

server.wait()
