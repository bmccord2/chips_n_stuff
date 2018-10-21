from ..hdl_parser.decorators import receive_num_outputs

@receive_num_outputs
def input_chip(num_outputs):
    result = None
    while not result:
        try:
            raw_values = input('Enter binary of length %s: ' % num_outputs)
            if raw_values.lower() == 'x':
                exit()
            values = []
            for token in ''.join(raw_values.split()):
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
            raw_values = input('Enter number (binary length %s): ' % num_outputs)
            if raw_values.lower() == 'x':
                exit()
            try:
                numeric = int(raw_values.strip())
                values_str = '{{0:0{}b}}'.format(num_outputs).format(numeric)
            except ValueError as e:
                raise ValueError("Invalid input '%s'" % raw_values)
            result = list(reversed([int(x) for x in values_str]))
        except ValueError as e:
            print(e)

    return result

def output_chip(*values):
    print("Result: %s" % [int(x) for x in values])

def decimal_output_chip(*values):
    binary = list(reversed([str(int(x)) for x in values]))
    decimal = int(''.join(binary), 2)
    print("Result: %s" % decimal)