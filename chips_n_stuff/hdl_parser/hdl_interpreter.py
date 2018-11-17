from random import shuffle

from ..gates.nand import nand
from ..gates.join_wire import join_wire
from ..gates.io import (input_chip, output_chip, decimal_input_chip,
    decimal_output_chip, signed_decimal_input_chip, signed_decimal_output_chip)
from .hdl_parser import parser
from .exceptions import HdlInterpreterError

builtin_chips = {
    'nand': nand,
    'join_wire': join_wire,
    'input_chip': input_chip,
    'output_chip': output_chip,
    'decimal_input_chip': decimal_input_chip,
    'decimal_output_chip': decimal_output_chip,
    'signed_decimal_input_chip': signed_decimal_input_chip,
    'signed_decimal_output_chip': signed_decimal_output_chip,
}

chips = {}

def get_chip(name):
    try:
        return chips[name]
    except KeyError:
        try:
            return builtin_chips[name]
        except KeyError:
            raise ValueError("'%s' not found in builtins or chips" % name)


class Wire(object):

    def __init__(self, initial_value=False):
        self._value = bool(initial_value)
        self.listeners = []

    def update(self, value):
        new_value = bool(value)
        if self._value != new_value:
            self._value = new_value
            self.notify()

    def get_value(self):
        return self._value

    def add_listener(self, callback):
        self.listeners.append(callback)

    def notify(self):
        shuffle(self.listeners)
        for listener in self.listeners:
            #print("listener called, value is %s" % self._value)
            listener()


class ExecutableBase(object):

    def __init__(self, input_wires, output_wires):
        self.input_wires = input_wires
        self.output_wires = output_wires

class ExecutableBuiltin(ExecutableBase):

    def __init__(self, name, func, input_wires, output_wires):
        super(ExecutableBuiltin, self).__init__(input_wires, output_wires)
        self.name = name
        self.func = func

        self._initialize_callbacks()

    def _initialize_callbacks(self):
        for wire in self.input_wires:
            wire.add_listener(self.run)

    def run(self):
        #print("Running %s" % self.name)
        kwargs = {}
        if getattr(self.func, 'receive_num_outputs', False):
            kwargs['num_outputs'] = len(self.output_wires)

        output_values = self.func(*([i.get_value() for i in self.input_wires]), **kwargs)
        if output_values is None:
            output_values = []
        elif not hasattr(output_values, '__iter__'):
            output_values = (output_values,)

        if len(output_values) < len(self.output_wires):
            raise HdlInterpreterError("Not enough outputs for chip '%s'"
                % self.name)
        elif len(output_values) > len(self.output_wires):
            raise HdlInterpreterError("Too many outputs for chip '%s'"
                % self.name)

        for output_wire, output_value in zip(self.output_wires, output_values):
            output_wire.update(output_value)

class ExecutableChip(ExecutableBase):

    def __init__(self, chip_definition, input_wires, output_wires):
        super(ExecutableChip, self).__init__(input_wires, output_wires)
        self.chip_definition = chip_definition

        self.wires = {}
        self.internal_chips = {}

        self._initialize_internals()
        #print("Creating new '%s' chip" % chip_definition.name)

        # for name in chip_definition.inputs + chip_definition.outputs:
        #     self.wires[name] = Wire(0)

    def _initialize_internals(self):
        for wire_name, wire in zip(self.chip_definition.inputs, self.input_wires):
            self.wires[wire_name] = wire
        for wire_name, wire in zip(self.chip_definition.outputs, self.output_wires):
            self.wires[wire_name] = wire

        for chip_id, statement in enumerate(self.chip_definition.logic):
            input_wires = []
            output_wires = []
            for wire_name in statement.inputs:
                if not self.wires.get(wire_name):
                    self.wires[wire_name] = Wire()
                input_wires.append(self.wires[wire_name])

            for wire_name in statement.outputs:
                if not self.wires.get(wire_name):
                    self.wires[wire_name] = Wire()
                output_wires.append(self.wires[wire_name])
                    
            chip_definition = get_chip(statement.chip_name)
            if callable(chip_definition):
                self.internal_chips[chip_id] = ExecutableBuiltin(statement.chip_name, chip_definition, 
                    input_wires, output_wires)
            else:
                self.internal_chips[chip_id] = ExecutableChip(chip_definition, input_wires, output_wires)

    def run(self):
        chips = list(self.internal_chips.values())
        shuffle(chips)
        for chip in chips:
            chip.run()

class ExecutableCommand(object):

    def __init__(self, command):
        self.command = command

    def run(self):
        params = self.command.params
        if self.command.name == 'RUN':
            chip_name = params[0]
            chip_definition = get_chip(chip_name)
            
            num_outputs = len(chip_definition.outputs)
            input_params = params[1:]
            num_expected_in = len(chip_definition.inputs)
            num_actual_in = len(input_params)
            if num_actual_in > num_expected_in:
                raise HdlInterpreterError("Too many input params, expected '%s' got '%s'"
                    % (num_expected_in, num_actual_in))
            elif num_actual_in < num_expected_in:
                print("Got less params than needed, initializing rest to 0")
                input_params = [0 for i in range(num_expected_in - num_actual_in)]

            inputs = [Wire(input_value) for input_value in input_params]
            outputs = [Wire(0) for i in range(num_outputs)]
            chip = ExecutableChip(chip_definition, inputs, outputs)
            chip.run()
            return [wire.get_value() for wire in chip.output_wires]
        else:
            raise ValueError("Unknown command '%s'" % self.command.name)

def interpret(data):
    text = None
    if hasattr(data, "readlines"):
        text = ''.join(data.readlines())
    else:
        text = data

    if not text.endswith('\n'):
        text += '\n'
    instructions = parser.parse(text)

    for chip_definition in instructions.definitions:
        chips[chip_definition.name] = chip_definition

    for chip_name, chip_definition in chips.items():
        used_inputs = set()
        used_outputs = set()

        for statement in chip_definition.logic:
            used_inputs.update(statement.inputs)
            used_outputs.update(statement.outputs)

        if not used_inputs.issuperset(chip_definition.inputs):
            unused = [x for x in chip_definition.inputs if x not in used_inputs]
            print("WARNING: not all inputs used by chip '%s'. Unused: %s" 
                % (chip_name, unused))
        if not used_outputs.issuperset(chip_definition.outputs):
            unused = [x for x in chip_definition.outputs if x not in used_inputs]
            print("WARNING: not all outputs used by chip '%s'. Unused: %s" 
                % (chip_name, unused))

    for command in instructions.commands:
        exec_command = ExecutableCommand(command)
        result = exec_command.run()
        if result:
            print('Result: {}'.format([int(x) for x in result]))
