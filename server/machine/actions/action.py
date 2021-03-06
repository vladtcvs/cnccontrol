import abc
import threading
import copy
import common
from common import event

# Basic class for all actions
class Action(object):
    def __init__(self, **kwargs):
        self.dropped = False
        self.breaked = False
        self.completed = threading.Event()
        self.finished = threading.Event()
        self.action_completed = event.EventEmitter()
        self.action_started = event.EventEmitter()
        self.caching = False
        self.is_pause = False
        self.is_moving = False
        self.error = False

    def run(self):
        return self.act()

    def dispose(self):
        pass

    def abort(self):
        self.breaked = True
        self.finished.set()

    @abc.abstractmethod
    def act(self):
        return False

# Local actions
class InstantAction(Action):

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        self.action_started(self)
        res = self.perform()
        self.completed.set()
        self.finished.set()
        self.action_completed(self)
        return res

# Actions, which generates commands for Tool

class ToolAction(Action):

    def __init__(self, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = False
        self.sender = None
        self.Nid = -1

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        self.action_started(self)
        res = self.perform()
        self.completed.set()
        self.finished.set()
        self.action_completed(self)
        return res

# Actions, which generates commands for MCU
class MCUAction(Action):

    def __init__(self, sender, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = True
        self.table_sender = sender
        self.Nid = None
        self.table_sender.dropped += self.__received_dropped
        self.table_sender.completed += self.__received_completed
        self.table_sender.started += self.__received_started
        self.table_sender.error += self.__received_error
        self.table_sender.queued += self.__received_queued
        self.__sending = False
        self.command_received = threading.Event()
        self.crc_error = False
        self.is_received = False

    @abc.abstractmethod
    def command(self):
        return ""

    @abc.abstractmethod
    def on_completed(self, response):
        pass

    def dispose(self):
        Action.dispose(self)
        self.table_sender.dropped -= self.__received_dropped
        self.table_sender.completed -= self.__received_completed
        self.table_sender.started -= self.__received_started
        self.table_sender.queued -= self.__received_queued
        self.table_sender.error -= self.__received_error

    def __indexed(self, nid):
        self.Nid = int(nid)

    def __received_queued(self, nid):
        if int(nid) == self.Nid:       
            self.command_received.set()
            self.is_received = True

    def __received_started(self, nid):
        if int(nid) == self.Nid:
            self.action_started(self)

    def __received_dropped(self, nid):
        nid = int(nid)
        if nid == self.Nid:
            self.is_received = True
            self.dropped = True
            self.finished.set()
            self.command_received.set()

    def __received_error(self, error):
        if self.is_received:
            return
        if error[-9:] == "CRC error":
            self.crc_error = True
        self.error = True

    def __received_completed(self, nid, response):
        nid = int(nid)
        if nid == self.Nid:
            print("Action %i completed" % nid)
            self.completed.set()
            self.finished.set()
            self.on_completed(response)
            self.action_completed(self)

    def act(self):
        self.table_sender.indexed += self.__indexed
        cmd = self.command()
        self.completed.clear()
        if not self.table_sender.has_slots.is_set():
            print("No slots")
            return False
        self.table_sender.send_command(cmd)
        self.table_sender.indexed -= self.__indexed
        return True

# Movement actions
class Movement(MCUAction):
    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    @abc.abstractmethod
    def length(self):
        return None

    def __init__(self, feed, acc, **kwargs):
        MCUAction.__init__(self, **kwargs)
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
        self.is_moving = True

    def _convert_axes(self, delta):
        # inverting axes
        if common.config.X_INVERT:
            x = -delta.x
        else:
            x = delta.x

        if common.config.Y_INVERT:
            y = -delta.y
        else:
            y = delta.y
        
        if common.config.Z_INVERT:
            z = -delta.z
        else:
            z = delta.z
        
        return x, y, z

class MCUCmd(MCUAction):

    def __init__(self, cmd, cacheable=False, *args, **kwargs):
        MCUAction.__init__(self, *args, **kwargs)
        self.cmd = cmd
        self.caching = cacheable

    def command(self):
        return self.cmd
