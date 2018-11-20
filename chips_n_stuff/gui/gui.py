import wx
import re
from collections import OrderedDict

from ..util.number_conv import (unsigned_decimal_to_binary_ints,
    signed_decimal_to_binary_ints, unsigned_binary_to_decimal,
    signed_binary_to_decimal, binary_ints_to_str)

array_regex = r"([a-zA-Z_0-9]+)\[(\d+)\]"

class BaseIO(object):

    def formatted_value(self):
        return self.value

class IO(BaseIO):
    def __init__(self, name):
        self.name = name
        self.value = 0

    def formatted_value(self):
        return str(self.value)

class ArrayIO(BaseIO):

    def __init__(self, basename, first, last):
        self.basename = basename
        self.first = first
        self.last = last
        self.value = 0
        self.format = 'ubin'

    def size(self):
        return self.last - self.first + 1
    
    def in_range(self, index):
        return index >= first and index <= last

    def unsigned_bin_str(self):
        bin_vals = unsigned_decimal_to_binary_ints(self.value, self.size())
        return binary_ints_to_str(bin_vals)

    def formatted_value(self):
        if self.format == 'ubin':
            return self.unsigned_bin_str()
        else:
            raise ValueError("Unknown format '{}'".format(self.format))

    @property
    def name(self):
        return "{}[{}:{}]".format(self.basename, self.first, self.last)

def as_array_value(name):
    r = re.search(array_regex, name)
    if r:
        basename = r.group(1)
        index = int(r.group(2))
        return basename, index
    return None

def condensed_io_fields(names):
    condensed = []
    arrays = {}
    for name in names:
        array_value = as_array_value(name)
        if array_value is not None:
            basename, index = array_value
            try:
                arrays[basename].append(index)
            except KeyError:
                arrays[basename] = [index]
        else:
            condensed.append(IO(name))

    # create continuous ranges
    for basename, indices in arrays.items():
        current_range = []
        indices.sort()
        for enum_i, array_ind in enumerate(indices):
            if not current_range or array_ind == current_range[-1] + 1:
                current_range.append(array_ind)
            else:
                a = ArrayIO(basename, current_range[0], current_range[-1])
                condensed.append(a)
                current_range = []
            if current_range and enum_i == len(indices) - 1:
                a = ArrayIO(basename, current_range[0], current_range[-1])
                condensed.append(a)
    
    # restore original order
    def k(x):
        if isinstance(x, ArrayIO):
            return names.index("{}[{}]".format(x.basename, x.first))
        else:
            return names.index(x.name)

    condensed.sort(key=k)
    return condensed

class InputField(wx.TextCtrl):

    def __init__(self, parent, io):
        self.io = io
        wx.TextCtrl.__init__(self, parent, value=self.io.formatted_value())
        self.Bind(wx.EVT_CHAR, self.handle_change)

    def handle_change(self):
        # TODO check input
        if self.onchange is not None:
            self.onchange()

class OutputField(wx.StaticText):

    def __init__(self, parent, io):
        self.io = io
        wx.StaticText.__init__(self, parent, label=self.io.formatted_value())

class InputPanel(wx.Panel):
    def __init__(self, parent, input_names):
        wx.Panel.__init__(self, parent)
        self.inputs = condensed_io_fields(input_names)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self._init_inputs()

    def _init_inputs(self):
        self.input_fields = {}
        for inp in self.inputs:
            if isinstance(inp, ArrayIO):
                value = inp.unsigned_bin_str()
            else:
                value = "0"

            label = wx.StaticText(self, label='{}: '.format(inp.name))
            inp_field = InputField(self, inp)
            input_sizer = wx.BoxSizer(wx.HORIZONTAL)
            input_sizer.Add(label, 0, wx.ALL|wx.EXPAND, border=5)
            input_sizer.Add(inp_field, 1, wx.ALL|wx.EXPAND, border=5)
            self.input_fields[inp] = inp_field
            self.sizer.Add(input_sizer, 0, wx.ALL|wx.EXPAND, border=5)

class OutputPanel(wx.Panel):
    def __init__(self, parent, output_names):
        wx.Panel.__init__(self, parent)
        self.outputs = condensed_io_fields(output_names)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self._init_outputs()

    def _init_outputs(self):
        self.output_fields = []
        for out in self.outputs:
            if isinstance(out, ArrayIO):
                value = out.unsigned_bin_str()
            else:
                value = "0"
            label = wx.StaticText(self, label='{}: '.format(out.name))
            out_field = OutputField(self, out)
            output_sizer = wx.BoxSizer(wx.HORIZONTAL)
            output_sizer.Add(label, 0, wx.ALL|wx.EXPAND, border=5)
            output_sizer.Add(out_field, 1, wx.ALL|wx.EXPAND, border=5)
            self.output_fields.append(out_field)
            self.sizer.Add(output_sizer, 0, wx.ALL|wx.EXPAND, border=5)

class MainFrame(wx.Frame):
    def __init__(self, input_names, output_names):
        wx.Frame.__init__(self, None, title="GUI", size=(640,480))
        self.main_panel = wx.Panel(self)
        self.input_panel = InputPanel(self.main_panel, input_names)
        self.output_panel = OutputPanel(self.main_panel, output_names)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_panel.SetSizer(self.panel_sizer)
        self.panel_sizer.Add(self.input_panel, 1, wx.ALL|wx.EXPAND)
        self.panel_sizer.Add(self.output_panel, 1, wx.ALL|wx.EXPAND)


    def OnCloseWindow(self, e):
        self.Destroy()

class App(wx.App):

    def __init__(self, input_names, output_names, *args, **kwargs):
        self.input_names = input_names
        self.output_names = output_names
        wx.App.__init__(self, *args, **kwargs)

    def OnInit(self):
        frame = MainFrame(self.input_names, self.output_names)
        frame.Show()
        return True

    def MainLoop(self):
        if hasattr(self, 'onload'):
            self.onload()
        wx.App.MainLoop(self)
