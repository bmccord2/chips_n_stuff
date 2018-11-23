import wx
import re
from collections import OrderedDict

from ..util.number_conv import (unsigned_decimal_to_binary_ints,
    signed_decimal_to_binary_ints, unsigned_binary_to_decimal,
    signed_binary_to_decimal, binary_ints_to_str)

array_regex = r"([a-zA-Z_0-9]+)\[(\d+)\]"

tEVT_OUTPUT = wx.NewEventType()
EVT_OUTPUT = wx.PyEventBinder(tEVT_OUTPUT, 1)

def as_array_value(name):
    r = re.search(array_regex, name)
    if r:
        basename = r.group(1)
        index = int(r.group(2))
        return basename, index
    return None

class OutputEvent(wx.PyCommandEvent):
    def __init__(self, output_name, value, all_outputs):
        wx.PyCommandEvent.__init__(self, tEVT_OUTPUT, -1)
        self.output_name = output_name
        self.value = value
        self.all_outputs = all_outputs


class IO(object):
    def __init__(self, name, value=0):
        self.name = name
        if isinstance(value, str):
            self.value = int(value)
        else:
            self.value = 0
        self.value = min(1, self.value)

    def update_from_event(self, event):
        if event.output_name == self.name:
            self.value = int(event.value)

    def formatted_value(self):
        return str(self.value)

    def get_changed(self, previous):
        if previous.value != self.value:
            return {self.name: self.value}
        return {}

class ArrayIO(object):

    def __init__(self, basename, first, last, value=0):
        self.basename = basename
        self.first = first
        self.last = last
        self.format = 'dec'

        self.set_value(value)

    def size(self):
        return self.last - self.first + 1
    
    def in_range(self, index):
        return index >= self.first and index <= self.last

    def is_member(self, output_name):
        try:
            basename, index = as_array_value(output_name)
            return self.basename == basename and self.in_range(index)
        except TypeError:
            return False

    def unsigned_bin_str(self):
        bin_vals = unsigned_decimal_to_binary_ints(self.value, self.size())
        return binary_ints_to_str(bin_vals)

    def signed_bin_str(self):
        bin_vals = signed_decimal_to_binary_ints(self.value, self.size())
        return binary_ints_to_str(bin_vals)

    def signed_decimal_str(self):
        return str(self.value)

    def update_from_event(self, event):
        if self.is_member(event.output_name):
            members = [(name, wire) for name, wire in event.all_outputs.items() if self.is_member(name)]
            indexed_values = [(int(as_array_value(name)[-1]), int(wire.get_value())) for name, wire in members]
            indexed_values.sort(key=lambda x: x[0])
            str_val = binary_ints_to_str([x[1] for x in indexed_values])
            if self.format.startswith('u'):
                self.set_value(str_val, format='ubin')
            else:
                self.set_value(str_val, format='bin')

    def formatted_value(self, format=None):
        if format is None:
            format = self.format
        if format == 'ubin':
            return self.unsigned_bin_str()
        elif format == 'bin':
            return self.signed_bin_str()
        elif format == 'dec':
            return self.signed_decimal_str()
        else:
            raise ValueError("Unknown format '{}'".format(format))

    def set_value(self, value, format=None):
        if format is None:
            format = self.format
        if isinstance(value, str):
            if format == 'ubin':
                self.value = unsigned_binary_to_decimal([int(x) for x in value])
            elif format == 'bin':
                self.value = signed_binary_to_decimal([int(x) for x in value])
            elif format == 'dec':
                self.value = int(value)
            else:
                raise ValueError("Unknown format '{}'".format(format))
        elif isinstance(value, int):
            self.value = value
        else:
            raise TypeError("Invalid type for value: '{}'".format(value))

    def get_changed(self, previous):
        if self.format.startswith('u'):
            format = 'ubin'
        else:
            format = 'bin'
        previous_bin = previous.formatted_value(format)
        self_bin = self.formatted_value(format)
        changed = {}
        i = self.first
        for prev, curr in zip(previous_bin, self_bin):
            if prev != curr:
                changed['{}[{}]'.format(self.basename, i)] = curr
            i += 1
        return changed


    @property
    def name(self):
        return "{}[{}:{}]".format(self.basename, self.first, self.last)


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

    def __init__(self, parent, io, onchange=None):
        self.io = io
        self.previous_io = self.io
        self.onchange = onchange
        wx.TextCtrl.__init__(self, parent, value=self.io.formatted_value(), 
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_change)
        self.Bind(wx.EVT_KILL_FOCUS, self.lost_focus)

    def lost_focus(self, evt):
        self.handle_change(evt)
        evt.Skip()

    def handle_change(self, evt):
        # TODO check input
        if isinstance(self.io, IO):
            print(self.GetValue())
            self.io = IO(self.io.name, self.GetValue())
            print(self.io.value)
        else:
            self.io = ArrayIO(self.previous_io.basename, self.previous_io.first,
                self.previous_io.last, self.GetValue())

        if self.onchange is not None:
            changed = self.get_changed()
            self.onchange(changed)
        self.previous_io = self.io
        self.SetValue(self.io.formatted_value())

    def get_changed(self):
        return self.io.get_changed(self.previous_io)

class OutputField(wx.StaticText):

    def __init__(self, parent, io):
        self.io = io
        wx.StaticText.__init__(self, parent, label=self.io.formatted_value())
        self.Bind(EVT_OUTPUT, self.update_value)

    def update_value(self, event):
        self.io.update_from_event(event)
        self.SetLabel(self.io.formatted_value())

class InputPanel(wx.Panel):
    def __init__(self, parent, input_names, runner_set_input):
        wx.Panel.__init__(self, parent)
        self.runner_set_input = runner_set_input
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
            inp_field = InputField(self, inp, onchange=self.set_inputs)
            input_sizer = wx.BoxSizer(wx.HORIZONTAL)
            input_sizer.Add(label, 0, wx.ALL|wx.EXPAND, border=5)
            input_sizer.Add(inp_field, 1, wx.ALL|wx.EXPAND, border=5)
            self.input_fields[inp] = inp_field
            self.sizer.Add(input_sizer, 0, wx.ALL|wx.EXPAND, border=5)

    def set_inputs(self, changed):
        for input_name, value in changed.items():
            self.runner_set_input(input_name, value)

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
    def __init__(self, input_names, output_names, set_input):
        wx.Frame.__init__(self, None, title="GUI", size=(640,480))
        self.set_input = set_input
        self.main_panel = wx.Panel(self)
        self.input_panel = InputPanel(self.main_panel, input_names,
            set_input)
        self.output_panel = OutputPanel(self.main_panel, output_names)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_panel.SetSizer(self.panel_sizer)
        self.panel_sizer.Add(self.input_panel, 1, wx.ALL|wx.EXPAND)
        self.panel_sizer.Add(self.output_panel, 1, wx.ALL|wx.EXPAND)


    def OnCloseWindow(self, e):
        self.Destroy()

class App(wx.App):

    def __init__(self, chip, *args, **kwargs):
        self.chip = chip

        from ..hdl_parser.hdl_interpreter import RunnerThread
        self.runner = RunnerThread(chip, self)
        wx.App.__init__(self, *args, **kwargs)

    def OnInit(self):
        self.frame = MainFrame(self.chip.chip_definition.inputs, 
            self.chip.chip_definition.outputs, self.runner.set_input)
        self.frame.Show()
        return True

    def MainLoop(self):
        self.runner.start()
        wx.App.MainLoop(self)

def create_output_event(app, output_name, value, output_wires_dict):
    def _create_output_event():
        evt = OutputEvent(output_name, int(value), output_wires_dict)
        # TODO not this, definitely need to fix
        for output_field in app.frame.output_panel.output_fields:
            wx.PostEvent(output_field, evt)
    return _create_output_event