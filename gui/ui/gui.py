from common import event
import threading
import queue
import enum
import time
import os

import gi
import OpenGL
import OpenGL.GL

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

class Interface(object):    

    def __render_path(self, widget, context, extradata):
        context.make_current()
        OpenGL.GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)
        OpenGL.GL.glFlush()
        return True

    def __resize(self, widget, width, height):
        widget.queue_draw()
        return True

    def __init__(self):
        self.load_file       = event.EventEmitter()
        self.start_clicked    = event.EventEmitter()
        self.continue_clicked = event.EventEmitter()
        self.pause_clicked    = event.EventEmitter()
        self.stop_clicked     = event.EventEmitter()
        self.home_clicked     = event.EventEmitter()
        self.probe_clicked    = event.EventEmitter()

        builder = Gtk.Builder()
        path = os.path.dirname(__file__)
        builder.add_from_file(path + "/interface.glade")
        self.window = builder.get_object("window")
        self.window.show_all()

        self.window.connect('destroy', Gtk.main_quit)

        load_menu = builder.get_object("open")
        load_menu.connect('activate', self.__load_menu_event)

        self.ffilter = Gtk.FileFilter()
        self.ffilter.set_name("G-Code")
        self.ffilter.add_pattern("*.gcode")
        self.affilter = Gtk.FileFilter()
        self.affilter.set_name("All files")
        self.affilter.add_pattern("*")

        self.glarea = builder.get_object("model")
        self.glarea.connect('render', self.__render_path, None)
        self.glarea.connect('resize', self.__resize)

        #region code area
        self.gstore = builder.get_object("gcodeline")
        self.gcodeview = builder.get_object("gcode")

        renderer = Gtk.CellRendererText()
        renderer.set_padding(0, 0)
        renderer.set_property("font", "Monospace")
        renderer.set_fixed_height_from_font(1)

        linecolumn = Gtk.TreeViewColumn("Line", renderer, text=0)
        self.gcodeview.append_column(linecolumn)
        codecolumn = Gtk.TreeViewColumn("Code", renderer, text=1)
        self.gcodeview.append_column(codecolumn)

        #endregion code area

        self.pause_btn = builder.get_object("pause")
        self.pause_btn.connect("clicked", self.__pause_program)

        self.start_btn = builder.get_object("start")
        self.start_btn.connect("clicked", self.__start_program)

        self.continue_btn = builder.get_object("continue")
        self.continue_btn.connect("clicked", self.__continue_program)

        self.stop_btn = builder.get_object("stop")
        self.stop_btn.connect("clicked", self.__stop_program)

        self.home_btn = builder.get_object("home")
        self.home_btn.connect("clicked", self.__home_all)

        self.probe_btn = builder.get_object("probe_z")
        self.probe_btn.connect("clicked", self.__probe)

        self.clear_commands()

    def __start_program(self, widget):
        self.start_clicked()
    
    def __continue_program(self, widget):
        self.continue_clicked()

    def __stop_program(self, widget):
        self.stop_clicked()
    
    def __pause_program(self, widget):
        self.pause_clicked()

    def __home_all(self, widget):
        self.home_clicked()

    def __probe(self, widget):
        self.probe_clicked()

    def __load_menu_event(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a g-code", self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.add_filter(self.ffilter)
        dialog.add_filter(self.affilter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()
        return True
    
    def clear_commands(self):
        self.gstore.clear()
        self.id = 1

    def add_command(self, line):
        line = line.strip()
        self.gstore.append([self.id, line])
        self.id += 1

    def show_ok(self, text):
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "OK")
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

    def select_line(self, line):
        path = Gtk.TreePath(line)
        selection = self.gcodeview.get_selection()
        selection.select_path(path)

    def switch_to_initial_mode(self):
        self.start_btn.set_sensitive(True)
        self.continue_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(False)
        self.pause_btn.set_sensitive(False)
        self.home_btn.set_sensitive(True)
        self.probe_btn.set_sensitive(True)

    def switch_to_paused_mode(self):
        self.start_btn.set_sensitive(False)
        self.continue_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(True)
        self.pause_btn.set_sensitive(False)
        self.home_btn.set_sensitive(False)
        self.probe_btn.set_sensitive(False)

    def switch_to_running_mode(self):
        self.start_btn.set_sensitive(False)
        self.continue_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.pause_btn.set_sensitive(True)
        self.home_btn.set_sensitive(False)
        self.probe_btn.set_sensitive(False)

    def run(self):
        Gtk.main()
