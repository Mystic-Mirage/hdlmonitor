from datetime import datetime
from itertools import cycle
from os import linesep

try:
    import Tkinter as tk
    import ttk
except ImportError:
    import tkinter as tk
    from tkinter import ttk

import hdlmiracle


__version__ = '0.3.2'

TITLE = 'HDL Buspro Monitor ({0})'.format(__version__)


class Column(ttk.Frame):
    def __init__(self, top, text, width):
        ttk.Frame.__init__(self, top)
        self.pack(expand=tk.TRUE, fill=tk.Y, side=tk.LEFT)
        self.label = ttk.Label(self, text=text, anchor=tk.CENTER,
                               justify=tk.CENTER, relief=tk.GROOVE, padding=5)
        self.label.pack(expand=tk.TRUE, fill=tk.BOTH)
        self.listbox = tk.Listbox(self, activestyle=tk.NONE,
                                  exportselection=tk.FALSE,
                                  font='Courier', height=24,
                                  highlightthickness=0, selectmode=tk.EXTENDED,
                                  width=width)
        self.listbox.pack(fill=tk.X)
        self.listbox.bind('<Enter>', self.on_enter)

    def on_enter(self, _):
        self.listbox.focus_set()

    def selection_get(self):
        selection = []
        for i in self.listbox.curselection():
            selection.append(self.listbox.get(int(i)))
        return selection

    def yscroll(self, lo, _):
        self.listbox.yview(tk.MOVETO, lo)
        return 'break'


class Table(ttk.Frame):
    def __init__(self, top, columns, select_callback, autoscroll_var,
                 copy_callback):
        ttk.Frame.__init__(self, top)
        self.pack(fill=tk.BOTH, expand=tk.TRUE, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.bind('<Button-4>', self.on_button4)
        self.scrollbar.bind('<Button-5>', self.on_button5)

        self.columns = []

        for text, width in columns:
            column = Column(self, text=text, width=width)
            column.listbox.bind('<MouseWheel>', self.on_mousewheel)
            column.listbox.bind('<Button-4>', self.on_button4)
            column.listbox.bind('<Button-5>', self.on_button5)
            column.listbox.bind('<<ListboxSelect>>', self.on_select)
            column.listbox.bind('<<Copy>>', copy_callback)
            self.columns.append(column)

        self.columns[0].listbox.config(yscrollcommand=self.scrollbar.set)
        for col1, col2 in zip(self.columns[:-1], self.columns[1:]):
            col2.listbox.config(yscrollcommand=col1.yscroll)
        self.scrollbar.config(command=column.listbox.yview)

        self.select_callback = select_callback

        self.colors = ('white', 'white smoke')
        self.color = cycle(self.colors)

        self.autoscroll = autoscroll_var

    def append(self, row):
        color = next(self.color)
        for subrow in row:
            for column, value in zip(self.columns, subrow):
                column.listbox.insert(tk.END, value)
                column.listbox.itemconfig(tk.END, bg=color)
                if self.autoscroll.get():
                    column.listbox.see(tk.END)

    def clear(self):
        self.color = cycle(self.colors)
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
        column.listbox.focus_set()
        self.select_callback(selection)

    def selection_get(self):
        selection = []
        for column in self.columns:
            selection.append(column.selection_get())
        return zip(*selection)

    def yscroll(self, delta):
        for column in self.columns:
            column.listbox.yview(tk.SCROLL, delta, tk.UNITS)
        return 'break'


class Filter(ttk.Frame):
    list = []
    conditions_list = []

    def __init__(self, top, filter_entries, indent):
        ttk.Frame.__init__(self, top)
        self.pack(fill=tk.X, expand=tk.TRUE, padx=5, pady=0)

        self.error = tk.StringVar()
        frm_error = tk.Frame(self, width=indent)
        frm_error.pack_propagate(tk.FALSE)
        frm_error.pack(side=tk.LEFT, fill=tk.Y)

        lbl_error = ttk.Label(frm_error, anchor=tk.CENTER, justify=tk.CENTER,
                              textvariable=self.error)
        lbl_error.pack(side=tk.LEFT, expand=tk.TRUE)

        self.conditions = []
        for key, width, base, validator, fmt in filter_entries:
            frame = tk.Frame(self, width=width)
            frame.pack_propagate(tk.FALSE)
            frame.pack(side=tk.LEFT, fill=tk.Y)
            if base is str and isinstance(validator, (list, tuple)):
                widget = ttk.Combobox(frame)
                widget['values'] = validator
                widget.pack(side=tk.LEFT, expand=tk.TRUE)
            else:
                widget = ttk.Entry(frame)
                widget.pack(side=tk.LEFT)
            self.conditions.append((key, (widget, base, validator, fmt)))

        self.btn_remove = ttk.Button(self, text='Remove', command=self.delete)
        self.btn_remove.pack(side=tk.LEFT)
        self.append(self)

    @classmethod
    def append(cls, instance):
        cls.list.append(instance)

    @classmethod
    def remove(cls, instance):
        cls.list.remove(instance)
        if (not any((cls.conditions_list, cls.list)) and
                hasattr(cls, 'empty_callback')):
            cls.empty_callback()

    @classmethod
    def filter(cls, packet):
        if cls.conditions_list:
            for conditions in cls.conditions_list:
                if cls.check(packet, conditions):
                    return True
            return False
        return True

    @classmethod
    def validate(cls):
        conditions_list = []
        not_valid_list = []
        for f in cls.list:
            nv = f.valid()
            if nv:
                not_valid_list.append(nv)
            else:
                f_conditions = []
                for condition in f.conditions:
                    key, (entry, base, _, _) = condition
                    _value = entry.get()
                    if base is str:
                        value = _value if _value else None
                    else:
                        try:
                            value = int(_value, base)
                        except ValueError:
                            value = None
                    f_conditions.append((key, value))
                conditions_list.append(f_conditions)
        if not_valid_list:
            not_valid_list[0][0].selection_range(0, tk.END)
            not_valid_list[0][0].focus()
        else:
            cls.conditions_list = conditions_list
        if not cls.list and hasattr(cls, 'empty_callback'):
            cls.empty_callback()
        return not_valid_list

    @staticmethod
    def check(packet, conditions):
        for key, value in conditions:
            packet_value = getattr(packet, key)
            if value is None or value == packet_value:
                continue
            return False
        return True

    def delete(self):
        self.pack_forget()
        self.remove(self)

    def valid(self):
        not_valid = []
        filled = 0
        first = None
        for _, value in self.conditions:
            entry, base, validator, fmt = value
            if not first and base is not str:
                first = entry
            try:
                value = entry.get().strip()
                if value:
                    if base is str:
                        if callable(validator):
                            try:
                                validator(value)
                            except:
                                raise ValueError
                        else:
                            value = format(value[:10], fmt)
                    else:
                        minimum, maximum = validator
                        i_value = int(value, base)
                        if not minimum <= i_value <= maximum:
                            raise ValueError('not in range')
                        value = format(i_value, fmt)
                    filled += 1
                entry.delete(0, tk.END)
                entry.insert(0, value)
            except ValueError:
                not_valid.append(entry)
                break
        if not filled:
            not_valid.append(first)
        if not_valid:
            self.error.set('Error!')
            return not_valid
        else:
            self.error.set('')


class MonitorGui(ttk.Frame):
    def __init__(self):
        ttk.Frame.__init__(self)
        style = ttk.Style()
        if style.theme_use() == 'default':
            style.theme_use('alt')
        self.master.resizable(tk.FALSE, tk.FALSE)
        self.master.title(TITLE)
        try:
            self.master.iconbitmap('hdlmonitor.ico')
        except tk.TclError:
            ttk.Style().theme_use('alt')
            icon = tk.PhotoImage(file='hdlmonitor.gif')
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

        self.table = Table(
            self,
            (
                ('Timestamp', 14),
                ('IP Address', 17),
                ('Head', 12),
                ('Subnet ID', 5),
                ('Device ID', 5),
                ('Device Type', 7),
                ('Operation\nCode (hex)', 6),
                ('Target\nSubnet ID', 5),
                ('Target\nDevice ID', 5),
                ('Content (hex)', 25),
                ('Content (ASCII)', 10),
            ),
            self.select_callback,
            autoscroll_var,
            self.copy
        )

        self.filters = ttk.Frame(self)
        self.filters.pack(expand=tk.TRUE, fill=tk.X)

        filterbuttons = ttk.Frame(self.filters)
        filterbuttons.pack(expand=tk.TRUE, fill=tk.X, padx=5, pady=5)

        Filter.empty_callback = self.empty_filters

        btn_addfilter = ttk.Button(filterbuttons, text='Add filter',
                                   command=self.add_filter)
        btn_addfilter.pack(side=tk.LEFT)

        self.btn_applyfilter = ttk.Button(filterbuttons, text='Apply',
                                          command=self.apply_filters,
                                          state=tk.DISABLED)
        self.btn_applyfilter.pack(side=tk.LEFT)

        self.monitor = hdlmiracle.Monitor()
        self.monitor.receive = self.receive

        self.bus = hdlmiracle.IPBus(strict=False)
        self.bus.start()

        self.packets = []
        self.processing = True

        self.append = self.append_1

        self.start()
        self.mainloop()

    def add_filter(self):
        columns = [column.label.winfo_width() for column in self.table.columns]
        combo_values = ['']
        combo_values.extend(x.decode() for x in hdlmiracle.HEADS)
        Filter(
            self.filters,
            (
                ('ipaddress', columns[1], str, hdlmiracle.IPAddress, '15s'),
                ('head', columns[2], str, combo_values, '10s'),
                ('subnet_id', columns[3], 10, (0, 255), 'd'),
                ('device_id', columns[4], 10, (0, 255), 'd'),
                ('device_type', columns[5], 10, (0, 65535), 'd'),
                ('operation_code', columns[6], 16, (0, 0xffff), '04x'),
                ('target_subnet_id', columns[7], 10, (0, 255), 'd'),
                ('target_device_id', columns[8], 10, (0, 255), 'd'),
            ),
            columns[0],
        )
        self.btn_applyfilter.config(state=tk.NORMAL)

    def empty_filters(self):
        self.btn_applyfilter.config(state=tk.DISABLED)

    def apply_filters(self):
        nv = Filter.validate()
        if not nv:
            self.table.clear()
            for now, packet in self.packets:
                if Filter.filter(packet):
                    self.append_n(now, packet)

    def append_1(self, now, packet):
        self.btn_clear.config(state=tk.NORMAL)
        self.append = self.append_n
        self.append(now, packet)

    def append_n(self, now, packet):
        data = [(str(line), line.ascii()) for line in packet.content.step()]

        if data:
            row = [[
                ' {0:12s}'.format(str(now)),
                ' {0:15s}'.format(str(packet.ipaddress)),
                ' {0:10s}'.format(packet.head),
                '{0:>4d}'.format(packet.subnet_id),
                '{0:>4d}'.format(packet.device_id),
                '{0:>6d}'.format(packet.device_type),
                '{0:>5s}'.format(str(packet.operation_code)),
                '{0:>4d}'.format(packet.target_subnet_id),
                '{0:>4d}'.format(packet.target_device_id),
                ' {0:23s}'.format(data[0][0]),
                ' {0:8s}'.format(data[0][1]),
            ]]
            for _hex, ascii in data[1:]:
                row.append([
                    ' ' * 13,
                    ' ' * 16,
                    ' ' * 11,
                    ' ' * 4,
                    ' ' * 4,
                    ' ' * 6,
                    ' ' * 5,
                    ' ' * 4,
                    ' ' * 4,
                    ' {0:23s}'.format(_hex),
                    ' {0:8s}'.format(ascii),
                ])
        else:
            row = [[
                ' {0:12s}'.format(str(now)),
                ' {0:15s}'.format(str(packet.ipaddress)),
                ' {0:10s}'.format(packet.head),
                '{0:>4d}'.format(packet.subnet_id),
                '{0:>4d}'.format(packet.device_id),
                '{0:>6d}'.format(packet.device_type),
                '{0:>5s}'.format(str(packet.operation_code)),
                '{0:>4d}'.format(packet.target_subnet_id),
                '{0:>4d}'.format(packet.target_device_id),
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

    def copy(self, *_):
        rows = []
        for row in self.table.selection_get():
            rows.append(' '.join(row)[1:].rstrip())
        text = linesep.join(rows) + linesep
        self.clipboard_clear()
        self.clipboard_append(text)

    def receive(self, packet):
        _now = datetime.now().time()
        now = '{0.hour:02d}:{0.minute:02d}:{0.second:02d}.{1:03d}'.format(
            _now, _now.microsecond // 1000
        )
        self.packets.append((now, packet))

        if self.processing and Filter.filter(packet):
            self.append(now, packet)

    def select_callback(self, selection):
        if selection:
            self.btn_copy.config(state=tk.NORMAL)
        else:
            self.btn_copy.config(state=tk.DISABLED)

    def start(self):
        self.btn_start.pack_forget()
        self.btn_stop.pack(side=tk.LEFT)
        self.bus.attach(self.monitor)

    def stop(self):
        self.btn_stop.pack_forget()
        self.btn_start.pack(side=tk.LEFT)
        self.bus.detach(self.monitor)


if __name__ == '__main__':
    MonitorGui()
