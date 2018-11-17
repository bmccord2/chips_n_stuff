from ..util.number_conv import (signed_decimal_to_binary_ints,
    unsigned_decimal_to_binary_ints, unsigned_binary_to_decimal,
    signed_binary_to_decimal)
from ..hdl_parser.decorators import receive_num_outputs

@receive_num_outputs
def input_chip(num_outputs):
    result = None
    while not result:
        try:
            str_value = input('Enter binary of length %s: ' % num_outputs)
            if str_value.lower() == 'x':
                exit()
            values = []
            for token in ''.join(str_value.split()):
                if not (token == '0' or token == '1'):
                    raise ValueError("Invalid input '%s'" % token)
                values.append(int(token))
            result = values
        except ValueError as e:
            print(e)

    return result

@receive_num_outputs
def decimal_input_chip(num_outputs):
    result = None
    while not result:
        try:
            str_value = input('Enter number (binary length %s): ' % num_outputs)
            if str_value.lower() == 'x':
                exit()
            result = unsigned_decimal_to_binary_ints(str_value, num_outputs)
        except ValueError as e:
            print(e)

    return result

@receive_num_outputs
def signed_decimal_input_chip(num_outputs):
    result = None
    while not result:
        try:
            str_value = input('Enter number (binary length %s): ' % num_outputs)
            if str_value.lower() == 'x':
                exit()
            result = signed_decimal_to_binary_ints(str_value, num_outputs)
        except ValueError as e:
            print(e)

    return result

def output_chip(*values):
    print("Current output: %s" % [int(x) for x in values])

def decimal_output_chip(*values):
    decimal = unsigned_binary_to_decimal(values)
    print("Current output: %s" % decimal)

def signed_decimal_output_chip(*values):
    decimal = signed_binary_to_decimal(values)
    print("Current output: %s" % decimal)