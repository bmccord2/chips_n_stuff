from ply import yacc

from .hdl_lexer import tokens
from .exceptions import HdlParsingError


def anydup(thelist):
  seen = set()
  for x in thelist:
    if x in seen: return x
    seen.add(x)
  return None

class ArrayInitialization(object):

    def __init__(self, base_name, size):
        self.base_name = base_name
        self.size = size


    def expand(self):
        if self.size < 1:
            raise HdlParsingError('Array names must range from 1 and up.')
        return ['{}[{}]'.format(self.base_name, index) for index in range(self.size)]

class IndexingName(object):

    def __init__(self, base_name, i0, i1=None):
        self.base_name = base_name

        self.i0 = i0
        self.i1 = i1

    def expand(self):
        # [i0:i1] - i0 inclusive, i1 exclusive
        # [i0] - single
        if self.i1 is None:
            index = self.i0
            return ['{}[{}]'.format(self.base_name, index)]
        else:
            start = self.i0
            end = self.i1
        if start < 0:
            raise HdlParsingError('Indexes must start from 0 and up.')
        if end < start:
            raise HdlParsingError('Index end must be greater than or equal to start')

        return ['{}[{}]'.format(self.base_name, index) for index in range(start, end)]

class ChipStatement(object):

    def __init__(self, chip_name, inputs, outputs):
        self.chip_name = chip_name
        self.inputs = []
        self.outputs = []

        for val in inputs:
            if isinstance(val, IndexingName) or isinstance(val, ArrayInitialization):
                self.inputs += val.expand()
            else:
                self.inputs.append(val)
        for val in outputs:
            if isinstance(val, IndexingName) or isinstance(val, ArrayInitialization):
                self.outputs += val.expand()
            else:
                self.outputs.append(val)

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
        self.inputs = []
        self.outputs = []

        for val in inputs:
            if isinstance(val, ArrayInitialization):
                self.inputs += val.expand()
            elif isinstance(val, IndexingName):
                raise HdlParsingError("Error in inputs for chip declaration '{}'. "
                    "Cannot index array name in chip declaration".format(self.name))
            else:
                self.inputs.append(val)
        for val in outputs:
            if isinstance(val, ArrayInitialization):
                self.outputs += val.expand()
            elif isinstance(val, IndexingName):
                raise HdlParsingError("Error in outputs for chip declaration '{}'. "
                    "Cannot index array name in chip declaration".format(self.name))
            else:
                self.outputs.append(val)

        indup = anydup(self.inputs)
        if indup is not None:
            raise HdlParsingError("Duplicate input '{}' in chip declaration '{}'"
                .format(indup, self.name))
        outdup = anydup(self.outputs)
        if outdup is not None:
            raise HdlParsingError("Duplicate output '{}' in chip declaration '{}'"
                .format(outdup, self.name))

class Command(object):

    def __init__(self, name, *params):
        self.name = name
        self.params = list(params)

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
    run_command : run_command BINNUM
    """
    binnum = p[2][2:]
    digits = [bool(int(x)) for x in binnum]
    p[1].params += digits
    p[0] = p[1]

# def p_run_command_2(p):
#     """
#     run_command : run_command NUMBER
#     """
#     p[1].params.append(bool(int(p[2])))
#     p[0] = p[1]

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
    chip_statement : NAME chip_io CHIP_FUNC_OP chip_io 
    """
    p[0] = ChipStatement(p[1], p[2], p[4])

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
                  | indexing_name
                  | array_init
    """
    p[0] = [p[1]]

def p_name_sequence_2(p):
    """
    name_sequence : name_sequence NAME
                  | name_sequence indexing_name
                  | name_sequence array_init
    """
    p[0] = p[1] + [p[2]]

def p_indexing_name_1(p):
    """
    indexing_name : NAME OPEN_SQUARE NUMBER CLOSE_SQUARE
    """
    base_name = p[1]
    num = int(p[3])
    p[0] = IndexingName(base_name, num)


def p_indexing_name_2(p):
    """
    indexing_name : NAME OPEN_SQUARE NUMBER COLON NUMBER CLOSE_SQUARE
    """
    base_name = p[1]
    start = int(p[3])
    end = int(p[5])
    p[0] = IndexingName(base_name, start, end)

def p_indexing_name_3(p):
    """
    indexing_name : NAME OPEN_SQUARE COLON NUMBER CLOSE_SQUARE
    """
    base_name = p[1]
    start = 0
    end = int(p[4])
    p[0] = IndexingName(base_name, start, end)

def p_array_init(p):
    """
    array_init : NAME OPEN_SQUARE DOLLAR NUMBER CLOSE_SQUARE
    """
    base_name = p[1]
    num = int(p[4])
    p[0] = ArrayInitialization(base_name, num)


def p_error(p):
    if p is not None:
        raise HdlParsingError("Line %s, illegal token %s" % (p.lineno, p.value))
    else:
        raise HdlParsingError('Unexpected end of input');

parser = yacc.yacc()

# test = """
#     not (a b) => (output) {
#         nand [a a] [output] 
#     }
# """
# #test = "name_1 name_2"

# result = parser.parse(test)
# print(result)