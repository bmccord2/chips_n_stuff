
def unsigned_decimal_to_binary_ints(str_value, num_outputs):
    # output is little endian array of ints (0 or 1)
    try:
        numeric = int(str_value.strip())
    except ValueError as e:
        raise ValueError("Not a valid number '{}'".format(str_value))

    if numeric < 0:
        raise ValueError("Not a positive number (or zero): {}".format(str_value))
    values_str = '{{0:0{}b}}'.format(num_outputs).format(numeric)
    if len(values_str) > num_outputs:
        raise ValueError("Overflow.")
    return list(reversed([int(x) for x in values_str]))

def signed_decimal_to_binary_ints(str_value, num_outputs):
    # output is little endian array of ints (0 or 1)
    # converts as two's compliment
    try:
        numeric = int(str_value.strip())
    except ValueError as e:
        raise ValueError("Not a valid number '%s'" % str_value)

    is_negative = numeric < 0
    sign_dig = "1" if is_negative else "0"
    binary_str = '{{0:0{}b}}'.format(num_outputs - 1).format(abs(numeric))
    if sign_dig == "1":
        # two's compliment - flip bits
        binary_str = "".join(["1" if c == "0" else "0" for c in binary_str])
    
    binary_str = sign_dig + binary_str
    
    # two's compliment - add one
    if is_negative:
        plus_one = int(binary_str, 2) + 1
        binary_str = '{{0:0{}b}}'.format(num_outputs).format(plus_one)

    # currently big endian, convert to little endian
    binary_int_array = list(reversed([int(x) for x in binary_str]))
    if len(binary_str) > num_outputs or str(binary_int_array[-1]) != sign_dig:
        raise ValueError("Overflow.")

    return binary_int_array

def unsigned_binary_to_decimal(values):
    # input should be unsigned little endian array of numbers
    # or booleans
    # output is integer
    binary = list(reversed([str(int(x)) for x in values]))
    decimal = int(''.join(binary), 2)
    return decimal

def signed_binary_to_decimal(values):
    # input should be signed little endian array of numbers
    # or booleans
    # output is integer
    # converts as two's compliment
    
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

    return decimal