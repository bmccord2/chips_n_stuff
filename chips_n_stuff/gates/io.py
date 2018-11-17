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
            if len(values_str) > num_outputs:
                raise ValueError("Overflow.")
            result = list(reversed([int(x) for x in values_str]))
        except ValueError as e:
            print(e)

    return result

@receive_num_outputs
def signed_decimal_input_chip(num_outputs):
    result = None
    while not result:
        try:
            raw_values = input('Enter number (binary length %s): ' % num_outputs)
            if raw_values.lower() == 'x':
                exit()
            try:
                numeric = int(raw_values.strip())
                is_negative = numeric < 0
                sign_dig = "1" if is_negative else "0"
                values_str = '{{0:0{}b}}'.format(num_outputs - 1).format(abs(numeric))
                if sign_dig == "1":
                    # two's compliment - flip bits
                    values_str = "".join(["1" if c == "0" else "0" for c in values_str])
                
                values_str = sign_dig + values_str
                
                # two's compliment - add one
                if is_negative:
                    plus_one = int(values_str, 2) + 1
                    values_str = '{{0:0{}b}}'.format(num_outputs).format(plus_one)

                # currently big endian, convert to little endian
                binary = list(reversed([int(x) for x in values_str]))
                print(binary)
            except ValueError as e:
                raise ValueError("Invalid input '%s'" % raw_values)
            if len(values_str) > num_outputs or str(binary[-1]) != sign_dig:
                print(result)
                raise ValueError("Overflow.")

            result = binary
        except ValueError as e:
            print(e)

    return result

def output_chip(*values):
    print("Current output: %s" % [int(x) for x in values])

def decimal_output_chip(*values):
    binary = list(reversed([str(int(x)) for x in values]))
    decimal = int(''.join(binary), 2)
    print("Current output: %s" % decimal)

def signed_decimal_output_chip(*values):
    # values received as little endian
    sign = -1 if len(values) > 0 and values[-1] else 1
    binary = list(reversed([str(int(x)) for x in values[:-1]]))
    if sign == -1:
        # two's compliment - flip bits
        binary = ["1" if c == "0" else "0" for c in binary]
    decimal = sign * int(''.join(binary), 2)
    if sign == -1:
        # two's compliment - subtract one
        decimal -= 1
    print("Current output: %s" % decimal)