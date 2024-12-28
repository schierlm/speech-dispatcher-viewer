#!/usr/bin/python3
import gi, sys, threading, time, socket, os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

SOCKET_PATH = '/run/user/%d/speech-dispatcher/viewer.sock' % os.getuid()

class SpeechWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="speech-dispatcher Speech Viewer", border_width=10)
        self.set_default_size(400, 900)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        self.settings_expander = Gtk.Expander(label="Settings")
        vbox.pack_start(self.settings_expander, False, False, 0)
        expander_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.settings_expander.add(expander_vbox)
        self.update_cb = Gtk.CheckButton.new_with_mnemonic("_Update text")
        self.update_cb.set_active(True)
        self.update_cb.connect("toggled", self.update_expander)
        sf = Gtk.Frame(label_widget=self.update_cb)
        expander_vbox.pack_start(sf, False, False, 0)
        grid = Gtk.Grid(border_width=5)
        grid.attach(Gtk.Label(label="Detail:"), 0, 0, 1, 1)
        self.detail_combo = Gtk.ComboBoxText()
        self.detail_combo.set_entry_text_column(0)
        self.detail_combo.set_hexpand(True)
        for i in range(1,6):
            self.detail_combo.append_text("%d" % i)
        self.detail_combo.set_active(4)
        grid.attach(self.detail_combo, 1, 0, 1, 1)
        button = Gtk.Button(label="Clear")
        button.connect("clicked", self.on_clear_clicked)
        grid.attach(button, 0, 1, 2, 1)
        sf.add(grid)
        self.update_expander(None)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        self.textbuf = Gtk.TextBuffer()
        self.green_tag = self.textbuf.create_tag(None, foreground="green")
        self.blue_tag = self.textbuf.create_tag(None, foreground="blue")
        self.gray_tag = self.textbuf.create_tag(None, foreground="#666")
        self.bold_tag = self.textbuf.create_tag(None, weight=700)
        self.italic_tag = self.textbuf.create_tag(None, style="italic")
        self.scrolled_window.add(Gtk.TextView(buffer=self.textbuf, editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR))
        vbox.pack_start(self.scrolled_window, True, True, 0)
        self.connect("destroy", Gtk.main_quit)

    def update_expander(self, button):
        u = self.update_cb.get_active()
        l = "Settings (Not active)"
        if u:
            l = "Settings (Updating)"
        self.settings_expander.set_label(l)

    def on_clear_clicked(self, button):
        self.textbuf.delete( self.textbuf.get_start_iter(), self.textbuf.get_end_iter())

    def message_received(self, text):
        parts = text.split(" ", 1)
        if self.update_cb.get_active():
            level = self.detail_combo.get_active() + 1
            show = level > 3
            say = parts[0].startswith("SAY")
            color_tag = self.blue_tag
            if parts[0].startswith("SET"):
                show = level == 5
                color_tag = self.green_tag
            elif say:
                show = level > 2
            if show or say:
                mark = self.textbuf.create_mark(None, self.textbuf.get_end_iter(), True)
                if show:
                    self.textbuf.insert(self.textbuf.get_end_iter(), parts[0] + " ", -1)
                    self.textbuf.apply_tag(color_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                    self.textbuf.apply_tag(self.italic_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                    self.textbuf.move_mark(mark, self.textbuf.get_end_iter())
                    if not say:
                        self.textbuf.insert(self.textbuf.get_end_iter(), parts[1] + "\n", -1)
                        self.textbuf.apply_tag(color_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                if say:
                    saytext = parts[1]
                    while "<" in saytext:
                        sayparts = saytext.split('<', 1)
                        self.textbuf.insert(self.textbuf.get_end_iter(), sayparts[0], -1)
                        self.textbuf.apply_tag(self.bold_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                        self.textbuf.move_mark(mark, self.textbuf.get_end_iter())
                        sayparts = sayparts[1].split('>', 1)
                        if len(sayparts) == 1:
                            sayparts = [sayparts[0], ""]
                        else:
                            sayparts[0] +='>'
                        if level > 1:
                            self.textbuf.insert(self.textbuf.get_end_iter(), "<" + sayparts[0], -1)
                            self.textbuf.apply_tag(self.gray_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                            self.textbuf.move_mark(mark, self.textbuf.get_end_iter())
                        saytext = sayparts[1]
                    self.textbuf.insert(self.textbuf.get_end_iter(), saytext + "\n", -1)
                    self.textbuf.apply_tag(self.bold_tag, self.textbuf.get_iter_at_mark(mark), self.textbuf.get_end_iter())
                self.textbuf.delete_mark(mark)
                self.scroll_down()
                GLib.idle_add(self.scroll_down)
        return GLib.SOURCE_REMOVE

    def scroll_down(self):
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_upper())


def handle_socket(win,sock):
    GLib.idle_add(win.message_received, "INIT Speech dispatcher viewer loaded successfully")
    try:
        while True:
            data = sock.recv(102400)
            if not data:
                break
            GLib.idle_add(win.message_received, data.decode().rstrip("\0"))
    finally:
        sock.close()
        os.unlink(SOCKET_PATH)

try:
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok = True)
    os.unlink(SOCKET_PATH)
except OSError:
    if os.path.exists(SOCKET_PATH):
        raise

sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
sock.bind(SOCKET_PATH)
win = SpeechWindow()
thread = threading.Thread(target=handle_socket, args=(win,sock))
thread.daemon = True
thread.start()
win.show_all()
Gtk.main()
