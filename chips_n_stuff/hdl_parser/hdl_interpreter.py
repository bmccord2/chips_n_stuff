from ..gates.nand import nand
from ..gates.io import (input_chip, output_chip, decimal_input_chip,
    decimal_output_chip)
from .hdl_parser import parser
from .exceptions import HdlInterpreterError

builtin_chips = {
    'nand': nand,
    'input_chip': input_chip,
    'output_chip': output_chip,
    'decimal_input_chip': decimal_input_chip,
    'decimal_output_chip': decimal_output_chip
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

    def __init__(self, value):
        self.value = value

class ExecutableChip(object):

    def __init__(self, chip_definition):
        self.chip_definition = chip_definition
        self.wires = {}
        self.internal_chips = {}

        #print("Creating new '%s' chip" % chip_definition.name)

        for name in chip_definition.inputs + chip_definition.outputs:
            self.wires[name] = Wire(0)

    def run(self, *input_values):
        # This executes sequentially so it is not realistic and
        # does not display race conditions that it should
        for input_ind, input_value in enumerate(input_values):
            input_name = self.chip_definition.inputs[input_ind]
            self.wires[input_name].value = input_value

        for chip_ind, statement in enumerate(self.chip_definition.logic):
            try:
                child_chip = self.internal_chips[chip_ind] 
            except KeyError:
                child_chip_definition = get_chip(statement.chip_name)
                if callable(child_chip_definition):
                    #print("Creating new '%s' chip (builtin)" % statement.chip_name)
                    child_chip = self.internal_chips[chip_ind] = child_chip_definition
                else:
                    child_chip = self.internal_chips[chip_ind] = ExecutableChip(child_chip_definition)

            child_inputs = []
            for i, input_name in enumerate(statement.inputs):
                try:
                    input_wire = self.wires[input_name]
                except KeyError as e:
                    input_wire = self.wires[input_name] = Wire(0)
                child_inputs.append(input_wire)

            child_outputs = []
            for i, output_name in enumerate(statement.outputs):
                try:
                    output_wire = self.wires[output_name]
                except KeyError as e:
                    output_wire = self.wires[output_name] = Wire(0)
                child_outputs.append(output_wire)

            if callable(child_chip):
                kwargs = {}
                if getattr(child_chip, 'receive_num_outputs', False):
                    kwargs['num_outputs'] = len(statement.outputs)
                output_values = child_chip(*([i.value for i in child_inputs]), **kwargs)
            else:
                output_values = child_chip.run(*([i.value for i in child_inputs]))

            if output_values is None:
                output_values = []
            elif not hasattr(output_values, '__iter__'):
                output_values = (output_values,)

            if len(output_values) < len(child_outputs):
                raise HdlInterpreterError("Not enough outputs for chip '%s'"
                    % statement.chip_name)
            elif len(output_values) > len(child_outputs):
                raise HdlInterpreterError("Too many outputs for chip '%s'"
                    % statement.chip_name)

            for i, output_value in enumerate(output_values):
                child_outputs[i].value = output_value


        final_output_values = []
        for i, output_name in enumerate(self.chip_definition.outputs):
            final_output_values.append(self.wires[output_name].value)
        return final_output_values


class ExecutableCommand(object):

    def __init__(self, command):
        self.command = command

    def run(self):
        if self.command.name == 'RUN':
            chip_name = self.command.params[0]
            chip = ExecutableChip(get_chip(chip_name))
        else:
            raise ValueError("Unknown command '%s'" % self.command.name)
        chip.run()

def interpret(text):
    instructions = parser.parse(text)

    for chip_definition in instructions.definitions:
        chips[chip_definition.name] = chip_definition

    for command in instructions.commands:
        exec_command = ExecutableCommand(command)
        exec_command.run()
