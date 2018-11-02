from ..hdl_parser.decorators import receive_num_outputs

@receive_num_outputs
def join_wire(_input, num_outputs):
    return [_input]*num_outputs