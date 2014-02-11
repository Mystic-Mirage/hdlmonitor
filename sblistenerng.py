from __future__ import division, print_function, unicode_literals

from os import linesep

try:
    import Tkinter as tkinter
    import ttk
except:
    import tkinter
    from tkinter import ttk

import smartbus


class Column(ttk.Frame):

    def __init__(self, top, text, width, yscrollcmd):
        ttk.Frame.__init__(self, top)
        ttk.Style().configure('TLabel', anchor=tkinter.CENTER,
            justify=tkinter.CENTER, relief=tkinter.GROOVE, padding=5)
        self.pack(expand=tkinter.TRUE, fill=tkinter.Y, side=tkinter.LEFT)
        self.label = ttk.Label(self, text=text)
        self.label.pack(expand=tkinter.TRUE, fill=tkinter.BOTH)
        self.listbox = tkinter.Listbox(self, activestyle=tkinter.NONE,
            exportselection=tkinter.FALSE, font='Courier', height=24,
            highlightthickness=0, selectmode=tkinter.EXTENDED,
            yscrollcommand=yscrollcmd, width=width)
        self.listbox.pack(fill=tkinter.X)
        self.listbox.bind('<Enter>', self.on_enter)

    def on_enter(self, _):
        self.listbox.focus_set()

    def selection_get(self):
        selection = []
        for i in self.listbox.curselection():
            selection.append(self.listbox.get(int(i)))
        return selection


class Table(ttk.Frame):

    def __init__(self, top, columns, select_callback):
        ttk.Frame.__init__(self, top)
        self.pack(fill=tkinter.BOTH, expand=tkinter.TRUE, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(self, command=self.yview)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        self.columns = []

        for text, width in columns:
            column = Column(self, text=text, width=width,
                yscrollcmd=self.scrollbar.set)
            column.listbox.bind('<MouseWheel>', self.on_mousewheel)
            column.listbox.bind('<Button-4>', self.on_button4)
            column.listbox.bind('<Button-5>', self.on_button5)
            column.listbox.bind('<<ListboxSelect>>', self.on_select)
            self.columns.append(column)

        self.select_callback = select_callback

        self.colors = ('white', 'white smoke')
        self.colors_num = len(self.colors)
        self.count = 0

        self.bottom = True

    def append(self, row):
        color = self.colors[self.count % self.colors_num]
        for subrow in row:
            for column, value in zip(self.columns, subrow):
                column.listbox.insert(tkinter.END, value)
                column.listbox.itemconfig(tkinter.END, bg=color)
                if self.bottom:
                    column.listbox.see(tkinter.END)
        self.count += 1

    def clear(self):
        for column in self.columns:
            column.listbox.delete(0, tkinter.END)

    def on_button4(self, _):
        delta = -5
        return self.yscroll(delta)

    def on_button5(self, _):
        delta = 5
        return self.yscroll(delta)

    def on_mousewheel(self, event):
        delta = event.delta // -30
        return self.yscroll(delta)

    def on_select(self, event):
        selection = event.widget.curselection()
        for column in self.columns:
            column.listbox.selection_clear(0, tkinter.END)
            if selection:
                column.listbox.selection_set(selection[0], selection[-1])
        self.select_callback(selection)

    def selection_get(self):
        selection = []
        for column in self.columns:
            selection.append(column.selection_get())
        return zip(*selection)

    def yscroll(self, delta):
        for column in self.columns:
            column.listbox.yview(tkinter.SCROLL, delta, tkinter.UNITS)
        return 'break'

    def yview(self, *args):
        self.bottom = self.scrollbar.get()[1] == 1.0
        for column in self.columns:
            column.listbox.yview(*args)


class ListenerGui(ttk.Frame):

    def __init__(self):
        ttk.Frame.__init__(self)
        self.master.resizable(0, 0)
        self.master.title('SmartBus Listener NG')
        try:
            self.master.iconbitmap('sblistenerng.ico')
        except:
            icon = tkinter.PhotoImage(file='sblistenerng.gif')
            self.master.tk.call('wm', 'iconphoto', self.master._w, icon)

        self.pack(fill=tkinter.BOTH, expand=tkinter.TRUE, padx=5, pady=5)

        self.buttonbar = ttk.Frame(self)
        self.buttonbar.pack(fill=tkinter.X, padx=5, pady=5)

        self.btn_start = ttk.Button(self.buttonbar, text='Start',
            command=self.start, width=10)

        self.btn_stop = ttk.Button(self.buttonbar, text='Stop',
            command=self.stop, width=10)

        self.btn_copy = ttk.Button(self.buttonbar,
            text='Copy to clipboard', command=self.copy,
            state=tkinter.DISABLED)
        self.btn_copy.pack(side=tkinter.RIGHT)

        self.btn_clear = ttk.Button(self.buttonbar, text='Clear',
            command=self.clear, state=tkinter.DISABLED)
        self.btn_clear.pack(side=tkinter.RIGHT)

        self.table = Table(self, (
            ('Source\nSubnetID', 5),
            ('Source\nDeviceID', 5),
            ('Source\nDevice Type', 7),
            ('Command\n(hex)', 8),
            ('Destination\nSubnetID', 5),
            ('Destination\nDeviceID', 5),
            ('Data (hex)', 25),
            ('Data (ASCII)', 10),
        ),
        self.select_callback)

        self.listener = smartbus.Device(register=False)
        self.listener.receive_func = self.receive_func

        self.start()
        self.mainloop()

    def clear(self):
        self.table.clear()
        self.btn_clear.config(state=tkinter.DISABLED)
        self.btn_copy.config(state=tkinter.DISABLED)

    def copy(self):
        rows = []
        for row in self.table.selection_get():
            rows.append(' '.join(row)[1:])
        text = linesep.join(rows) + linesep
        self.clipboard_clear()
        self.clipboard_append(text)

    def receive_func(self, packet):
        packet_len = len(packet.data)

        data = []

        for d in range(0, packet_len, 8):
            data_hex = []
            data_ascii = []
            for i in packet.data[d:d + 8]:
                data_hex.append(format(i, '02x'))
                data_ascii.append(chr(i) if i >= 0x20 and i < 0x7f else '.')
            data.append([' '.join(data_hex), ''.join(data_ascii)])

        if data:
            row = [[
                ' {0:-3d}'.format(packet.src_netid),
                ' {0:-3d}'.format(packet.src_devid),
                ' {0:-5d}'.format(packet.src_devtype),
                ' {0:4s}'.format(packet.opcode_hex[2:]),
                ' {0:-3d}'.format(packet.netid),
                ' {0:-3d}'.format(packet.devid),
                ' {0:23s}'.format(data[0][0]),
                ' {0:8s}'.format(data[0][1]),
            ]]
            for d in data[1:]:
                row.append([
                    ' ' * 4,
                    ' ' * 4,
                    ' ' * 6,
                    ' ' * 5,
                    ' ' * 4,
                    ' ' * 4,
                    ' {0:23s}'.format(d[0]),
                    ' {0:8s}'.format(d[1]),
                ])
        else:
            row = [[
                ' {0:-3d}'.format(packet.src_netid),
                ' {0:-3d}'.format(packet.src_devid),
                ' {0:-5d}'.format(packet.src_devtype),
                ' {0:4s}'.format(packet.opcode_hex[2:]),
                ' {0:-3d}'.format(packet.netid),
                ' {0:-3d}'.format(packet.devid),
                '',
                '',
            ]]

        self.table.append(row)
        self.btn_clear.config(state=tkinter.NORMAL)

    def select_callback(self, selection):
        if selection:
            self.btn_copy.config(state=tkinter.NORMAL)
        else:
            self.btn_copy.config(state=tkinter.DISABLED)

    def start(self):
        self.btn_start.pack_forget()
        self.btn_stop.pack(side=tkinter.LEFT)
        self.listener.register()

    def stop(self):
        self.btn_stop.pack_forget()
        self.btn_start.pack(side=tkinter.LEFT)
        self.listener.unregister()


if __name__ == '__main__':
    smartbus.init()
    ListenerGui()
    smartbus.quit()
