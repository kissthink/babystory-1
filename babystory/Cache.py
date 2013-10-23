
# Copyright (C) 2013 LiuLang <gsushzhsosgsu@gmail.com>

# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html

from gi.repository import GLib
from gi.repository import Gtk

from babystory import Widgets
from babystory import Net


class Cache(Gtk.Dialog):
    def __init__(self, app):
        self.app = app
        super().__init__('Caching job', app.window, 0,
                (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE, ))
        self.set_modal(True)
        self.set_transient_for(app.window)
        self.set_default_size(800, 480)
        self.set_border_width(5)
        self.connect('destroy', self.on_dialog_destroyed)

        box = self.get_content_area()
        box.set_spacing(5)

        control_button = Gtk.Button('Start Caching')
        control_button.connect('clicked', self.on_control_button_clicked)
        box.pack_start(control_button, False, False, 0)
        self.control_button = control_button

        songs_win = Gtk.ScrolledWindow()
        box.pack_start(songs_win, True, True, 0)

        # title, size, duration, url, percent
        self.liststore = Gtk.ListStore(str, str, str, str, int)
        songs_tv = Gtk.TreeView(model=self.liststore)
        songs_win.add(songs_tv)
        self.songs_tv = songs_tv

        title_cell = Gtk.CellRendererText()
        title_col = Widgets.ExpandedTreeViewColumn('Title', title_cell,
                text=0)
        songs_tv.append_column(title_col)

        proc_cell = Gtk.CellRendererText()
        proc_col = Gtk.TreeViewColumn('Process', proc_cell, text=4)
        songs_tv.append_column(proc_col)

        size_cell = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn('Size', size_cell, text=1)
        songs_tv.append_column(size_col)

        duration_cell = Gtk.CellRendererText()
        duration_col = Gtk.TreeViewColumn('Duration', duration_cell, text=2)
        songs_tv.append_column(duration_col)

        for song in app.playlist.right_liststore:
            self.liststore.append([song[0], song[1], song[2], song[3], 0, ])

        self.curr_index = 0
        self.async_job = None

        box.show_all()

    def on_dialog_destroyed(self, dialog):
        if self.async_job:
            self.async_job.destroy()
        return True

    def on_control_button_clicked(self, button):
        if self.curr_index >= len(self.liststore) - 1:
            return

        if self.async_job is None:
            button.set_label('Stop Caching')
            self.get_song()
        else:
            button.set_label('Start Caching')
            self.async_job.destroy()
            self.async_job = None

    def on_chunk_received(self, widget, percent):
        def _update_process():
            self.liststore[self.curr_index][4] = percent
        GLib.idle_add(_update_process)

    def on_song_downloaded(self, widget, song_path):
        self.liststore[self.curr_index][4] = 100
        if self.curr_index >= len(self.liststore) - 1:
            self.control_button.set_label('Finished')
            return
        self.curr_index += 1
        self.get_song()
    
    def get_song(self):
        path = Gtk.TreePath(self.curr_index)
        self.songs_tv.get_selection().select_path(path)
        song = self.app.playlist.get_song_from_index(self.curr_index)

        self.async_job = Net.AsyncSong(self.app)
        self.async_job.connect('chunk-received', self.on_chunk_received)
        self.async_job.connect('downloaded', self.on_song_downloaded)
        self.async_job.get_song(song)
