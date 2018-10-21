from ply import yacc

from .hdl_lexer import tokens


class ChipStatement(object):

    def __init__(self, chip_name, inputs, outputs):
        self.chip_name = chip_name
        self.inputs = inputs
        self.outputs = outputs

    def __repr__(self):
        return ("STATEMENT: %s in=%s out=%s" % 
                (self.chip_name, self.inputs, self.outputs))

class ChipDefinition(object):

    def __init__(self, chip_declaration, logic):
        self.name = chip_declaration.name
        self.inputs = chip_declaration.inputs
        self.outputs = chip_declaration.outputs
        self.logic = logic

    def __repr__(self):
        return ("DEFINITION: %s in=%s out=%s logic=%s" % 
                (self.name, self.inputs, self.outputs, self.logic))

class ChipDeclaration(object):

    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

class Command(object):

    def __init__(self, name, *params):
        self.name = name
        self.params = params

class Instructions(object):

    def __init__(self, instruction=None):
        self.definitions = []
        self.commands = []
        if instruction:
            self.add(instruction)

    def add(self, instruction):
        if isinstance(instruction, ChipDefinition):
            self.definitions.append(instruction)
        elif isinstance(instruction, Command):
            self.commands.append(instruction)
        else:
            raise ValueError("Unknown instruction '%s'" % instruction)
        return self


def p_instructions_1(p):
    """
    chip_instructions : chip_definition
                      | command
    """
    p[0] = Instructions(p[1])

def p_instructions_2(p):
    """
    chip_instructions : chip_instructions chip_definition
                      | chip_instructions command
    """
    p[0] = p[1].add(p[2])


def p_command(p):
    """
    command : run_command
    """
    p[0] = p[1]

def p_run_command_1(p):
    """
    run_command : RUN NAME
    """
    p[0] = Command(p[1], p[2])

def p_run_command_2(p):
    """
    run_command : run_command BOOLEAN
    """
    p[0].params.append(p[1])

# 
# def p_chip_definitions_1(p):
#     """
#     chip_definitions : chip_definition
#     """
#     p[0] = [p[1]]

# def p_chip_definition_2(p):
#     """
#     chip_definitions : chip_definition chip_definition
#     """
#     p[0] = p[1] + [p[2]]

def p_chip_definition(p):
    """
    chip_definition : chip_declaration chip_logic
    """
    p[0] = ChipDefinition(p[1], p[2])

def p_chip_declaration(p):
    """
    chip_declaration : NAME chip_io CHIP_FUNC_OP chip_io
    """
    p[0] = ChipDeclaration(p[1], p[2], p[4])

def p_chip_logic(p):
    """
    chip_logic : OPEN_BRACE chip_statements CLOSE_BRACE
    """
    p[0] = p[2]

def p_chip_io_1(p):
    """
    chip_io : OPEN_PARENS name_sequence CLOSE_PARENS
    """
    p[0] = p[2]

def p_chip_io_2(p):
    """
    chip_io : OPEN_PARENS CLOSE_PARENS
    """
    p[0] = []

def p_name_sequence_1(p):
    """
    name_sequence : NAME
    """
    p[0] = [p[1]]

def p_name_sequence_2(p):
    """
    name_sequence : name_sequence NAME
    """
    p[0] = p[1] + [p[2]]

def p_chip_statements_1(p):
    """
    chip_statements : chip_statement
    """
    p[0] = [p[1]]

def p_chip_statements_2(p):
    """
    chip_statements : chip_statements chip_statement
    """
    p[0] = p[1] + [p[2]]

def p_chip_statement(p):
    """
    chip_statement : NAME chip_statement_io chip_statement_io 
    """
    p[0] = ChipStatement(p[1], p[2], p[3])

def p_chip_statement_io_1(p):
    """
    chip_statement_io : OPEN_SQUARE name_sequence CLOSE_SQUARE
    """
    p[0] = p[2]

def p_chip_statement_io_2(p):
    """
    chip_statement_io : OPEN_SQUARE CLOSE_SQUARE
    """
    p[0] = []

def p_error(p):
    raise TypeError("unknown text at %r type %r" % (p.value,p.type))

parser = yacc.yacc()

# test = """
#     not (a b) => (output) {
#         nand [a a] [output] 
#     }
# """
# #test = "name_1 name_2"

# result = parser.parse(test)
# print(result)