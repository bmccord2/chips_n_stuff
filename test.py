from chips_n_stuff.hdl_parser.hdl_interpreter import (ExecutableChip, 
    interpret, get_chip)

"""
xor:
a b o
0 0 0
0 1 1
1 0 1
1 1 0

nand:
a b o
0 0 1
0 1 1
1 0 1
1 1 0

or:
a b o
0 0 0
0 1 1
1 0 1
1 1 1

    xor (a, b) => (output) {

    }
"""

test = """
    not (a b) => (output) {
        nand [a a] [output] 
    }

    and (a b) => (output) {
        nand [a b] [c]
        not [c] [output]
    }

    or (a b) => (output) {
        not [a] [not_a]
        not [b] [not_b]
        nand [not_a not_b] [output]
    }

    xor (a b) => (output) {
        not [a] [not_a]
        not [b] [not_b]
        and [a not_b] [a_notb]
        and [b not_a] [notb_a]
        or [a_notb notb_a] [output]
    }

    half_adder (a b) => (sum carry) {
        xor [a b] [sum]
        and [a b] [carry]
    }

    full_adder (a b carry_in) => (sum carry_out) {
        half_adder [a b] [s1 c1]
        half_adder [carry_in s1] [sum c2]
        or [c1 c2] [carry_out]
    }

    4adder (a0 a1 a2 a3 b0 b1 b2 b3 carry_in) => (s0 s1 s2 s3 carry_out) {
        full_adder [a0 b0 carry_in] [s0 c0]
        full_adder [a1 b1 c0] [s1 c1]
        full_adder [a2 b2 c1] [s2 c2]
        full_adder [a3 b3 c2] [s3 carry_out]
    }

    my_chip () => () {
        decimal_input_chip [] [a0 a1 a2 a3]
        decimal_input_chip [] [b0 b1 b2 b3]
        4adder [a0 a1 a2 a3 b0 b1 b2 b3] [s0 s1 s2 s3 carry_out]
        decimal_output_chip [s0 s1 s2 s3 carry_out] []
        output_chip [s0 s1 s2 s3 carry_out] []
    }

    RUN my_chip
"""

interpret(test)

# not_chip = ExecutableChip(get_chip('not'))

# print(not_chip.run(1))