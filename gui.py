import event

import gi
import OpenGL
import OpenGL.GL

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

class Interface(object):    

    def __render_path(self, widget, context, extradata):
        OpenGL.GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)
        OpenGL.GL.glFlush()
        return True

    def __init__(self):
        self.load_file        = event.EventEmitter()
        self.start_clicked    = event.EventEmitter()
        self.continue_clicked = event.EventEmitter()
        self.pause_clicked    = event.EventEmitter()
        self.stop_clicked     = event.EventEmitter()

        builder = Gtk.Builder()
        builder.add_from_file("interface.glade")
        self.window = builder.get_object("window")
        self.window.show_all()

        self.window.connect('destroy', Gtk.main_quit)

        load_menu = builder.get_object("open")
        load_menu.connect('activate', self.__load_menu_event)

        self.glarea = builder.get_object("model")
        self.glarea.connect('render', self.__render_path, None)

        self.gstore = builder.get_object("gcodeline")
        self.gcodeview = builder.get_object("gcode")
        linecolumn = Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=0)
        self.gcodeview.append_column(linecolumn)
        codecolumn = Gtk.TreeViewColumn("Code", Gtk.CellRendererText(), text=1)
        self.gcodeview.append_column(codecolumn)

        start = builder.get_object("start")
        start.connect("clicked", self.__start_program)

        cont = builder.get_object("continue")
        cont.connect("clicked", self.__continue_program)

        stop = builder.get_object("stop")
        stop.connect("clicked", self.__stop_program)


    def __start_program(self, widget):
        self.start_clicked()
    
    def __continue_program(self, widget):
        self.continue_clicked()

    def __stop_program(self, widget):
        self.stop_clicked()
    

    def __load_menu_event(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a g-code", self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()
        return True
    
    def clear_commands(self):
        self.gstore.clear()
        self.id = 1

    def add_command(self, line):
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

    def run(self):
        Gtk.main()
