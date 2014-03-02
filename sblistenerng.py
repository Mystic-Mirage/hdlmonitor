from os import linesep

try:
    import Tkinter as tk
    import ttk
except:
    import tkinter as tk
    from tkinter import ttk

import smartbus


__updated__ = '2014-03-02-20-00-59'


def version():
    b1, b2, c, d1, d2, d3 = map(int, __updated__.split('-'))
    a = 1
    b = b1 - 2014 + b2
    d = d1 * 3600 + d2 * 60 + d3
    return '.'.join(map(str, (a, b, c, d)))


__version__ = version()


class Column(ttk.Frame):

    def __init__(self, top, text, width, yscrollcmd):
        ttk.Frame.__init__(self, top)
        self.pack(expand=tk.TRUE, fill=tk.Y, side=tk.LEFT)
        self.label = ttk.Label(self, text=text, anchor=tk.CENTER,
            justify=tk.CENTER, relief=tk.GROOVE, padding=5)
        self.label.pack(expand=tk.TRUE, fill=tk.BOTH)
        self.listbox = tk.Listbox(self, activestyle=tk.NONE,
            exportselection=tk.FALSE, font='Courier', height=24,
            highlightthickness=0, selectmode=tk.EXTENDED,
            yscrollcommand=yscrollcmd, width=width)
        self.listbox.pack(fill=tk.X)
        self.listbox.bind('<Enter>', self.on_enter)

    def on_enter(self, _):
        self.listbox.focus_set()

    def selection_get(self):
        selection = []
        for i in self.listbox.curselection():
            selection.append(self.listbox.get(int(i)))
        return selection


class Table(ttk.Frame):

    def __init__(self, top, columns, select_callback, autoscroll_var):
        ttk.Frame.__init__(self, top)
        self.pack(fill=tk.BOTH, expand=tk.TRUE, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(self, command=self.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.bind('<Button-4>', self.on_button4)
        self.scrollbar.bind('<Button-5>', self.on_button5)

        self.columns = []

        for text, width in columns:
            column = Column(self, text=text, width=width,
                yscrollcmd=self.scroll_set)
            column.listbox.bind('<MouseWheel>', self.on_mousewheel)
            column.listbox.bind('<Button-4>', self.on_button4)
            column.listbox.bind('<Button-5>', self.on_button5)
            column.listbox.bind('<<ListboxSelect>>', self.on_select)
            self.columns.append(column)

        self.select_callback = select_callback

        self.colors = ('white', 'white smoke')
        self.colors_num = len(self.colors)
        self.count = 0

        self.autoscroll = autoscroll_var

    def append(self, row):
        color = self.colors[self.count % self.colors_num]
        for subrow in row:
            for column, value in zip(self.columns, subrow):
                column.listbox.insert(tk.END, value)
                column.listbox.itemconfig(tk.END, bg=color)
                if self.autoscroll.get():
                    column.listbox.see(tk.END)
        self.count += 1

    def clear(self):
        for column in self.columns:
            column.listbox.delete(0, tk.END)

    def on_button4(self, _):
        delta = -5
        return self.yscroll(delta)

    def on_button5(self, _):
        delta = 5
        return self.yscroll(delta)

    def on_mousewheel(self, event):
        delta = event.delta / -30
        return self.yscroll(delta)

    def on_select(self, event):
        selection = event.widget.curselection()
        for column in self.columns:
            column.listbox.selection_clear(0, tk.END)
            if selection:
                column.listbox.selection_set(selection[0], selection[-1])
        self.select_callback(selection)

    def scroll_set(self, lo, hi):
        self.yview(tk.MOVETO, lo)
        self.scrollbar.set(lo, hi)

    def selection_get(self):
        selection = []
        for column in self.columns:
            selection.append(column.selection_get())
        return zip(*selection)

    def yscroll(self, delta):
        self.yview(tk.SCROLL, delta, tk.UNITS)
        return 'break'

    def yview(self, *args):
        for column in self.columns:
            column.listbox.yview(*args)


class ListenerGui(ttk.Frame):

    def __init__(self):
        ttk.Frame.__init__(self)
        style = ttk.Style()
        if style.theme_use() == 'default':
            style.theme_use('alt')
        self.master.resizable(0, 0)
        self.master.title('SmartBus Listener NG ({0})'.format(__version__))
        try:
            self.master.iconbitmap('sblistenerng.ico')
        except:
            ttk.Style().theme_use('alt')
            icon = tk.PhotoImage(file='sblistenerng.gif')
            self.master.tk.call('wm', 'iconphoto', self.master._w, icon)

        self.pack(fill=tk.BOTH, expand=tk.TRUE, padx=5, pady=5)

        buttonbar = ttk.Frame(self)
        buttonbar.pack(fill=tk.X, padx=5, pady=5)

        self.btn_start = ttk.Button(buttonbar, text='Start',
            command=self.start, width=10)

        self.btn_stop = ttk.Button(buttonbar, text='Stop',
            command=self.stop, width=10)

        buttongroup = ttk.Frame(buttonbar)
        buttongroup.pack(expand=tk.TRUE, fill=tk.X, side=tk.RIGHT)

        autoscroll_var = tk.IntVar()
        autoscroll_var.set(tk.TRUE)

        autoscroll_cb = ttk.Checkbutton(buttongroup, text='Autoscroll',
            var=autoscroll_var)
        autoscroll_cb.pack(padx=5, side=tk.LEFT)

        self.btn_copy = ttk.Button(buttongroup,
            text='Copy to clipboard', command=self.copy,
            state=tk.DISABLED)
        self.btn_copy.pack(side=tk.RIGHT)

        self.btn_clear = ttk.Button(buttongroup, text='Clear',
            command=self.clear, state=tk.DISABLED)
        self.btn_clear.pack(side=tk.RIGHT)

        self.table = Table(self, (
            ('Source\nSubnetID', 5),
            ('Source\nDeviceID', 5),
            ('Source\nDevice Type', 7),
            ('Command\n(hex)', 6),
            ('Destination\nSubnetID', 5),
            ('Destination\nDeviceID', 5),
            ('Data (hex)', 25),
            ('Data (ASCII)', 10),
        ),
        self.select_callback,
        autoscroll_var)

        self.listener = smartbus.Device(register=False)
        self.listener.receive_func = self.receive_func

        self.packets = []
        self.processing = True

        self.append = self.append_1

        self.start()
        self.mainloop()

    def append_1(self, packet):
        self.btn_clear.config(state=tk.NORMAL)
        self.append = self.append_n
        self.append(packet)

    def append_n(self, packet):
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
                format(packet.src_netid, '>4d'),
                format(packet.src_devid, '>4d'),
                format(packet.src_devtype, '>6d'),
                format(packet.opcode_hex0, '>5s'),
                format(packet.netid, '>4d'),
                format(packet.devid, '>4d'),
                ' {0:23s}'.format(data[0][0]),
                ' {0:8s}'.format(data[0][1]),
            ]]
            for d in data[1:]:
                row.append([
                    '    ',
                    '    ',
                    '      ',
                    '     ',
                    '    ',
                    '    ',
                    ' {0:23s}'.format(d[0]),
                    ' {0:8s}'.format(d[1]),
                ])
        else:
            row = [[
                format(packet.src_netid, '>4d'),
                format(packet.src_devid, '>4d'),
                format(packet.src_devtype, '>6d'),
                format(packet.opcode_hex0, '>5s'),
                format(packet.netid, '>4d'),
                format(packet.devid, '>4d'),
                '',
                '',
            ]]

        self.table.append(row)

    def clear(self):
        self.packets = []
        self.table.clear()
        self.btn_clear.config(state=tk.DISABLED)
        self.btn_copy.config(state=tk.DISABLED)
        self.append = self.append_1

    def copy(self):
        rows = []
        for row in self.table.selection_get():
            rows.append(' '.join(row)[1:])
        text = linesep.join(rows) + linesep
        self.clipboard_clear()
        self.clipboard_append(text)

    def receive_func(self, packet):
        self.packets.append(packet)

        if self.processing:
            self.append(packet)

    def select_callback(self, selection):
        if selection:
            self.btn_copy.config(state=tk.NORMAL)
        else:
            self.btn_copy.config(state=tk.DISABLED)

    def start(self):
        self.btn_start.pack_forget()
        self.btn_stop.pack(side=tk.LEFT)
        self.listener.register()

    def stop(self):
        self.btn_stop.pack_forget()
        self.btn_start.pack(side=tk.LEFT)
        self.listener.unregister()


if __name__ == '__main__':
    smartbus.init()
    ListenerGui()
    smartbus.quit()
