from ply import lex

# syntax 
# chip_name (input_1 input_2) => (output_1 output_2) {
#   some_chip [input_1] [wire_1]
#   some_chip [wire_1] [output_1]
# }

tokens = (
    'NAME',
    'CHIP_FUNC_OP',
    'OPEN_PARENS',
    'CLOSE_PARENS',
    'OPEN_BRACE',
    'CLOSE_BRACE',
    'OPEN_SQUARE',
    'CLOSE_SQUARE',
    'NUMBER',
    'BINNUM',
    'COLON',
    'DOLLAR',
    'RUN',
)

# t_NAME is not a RUN command or a number
t_NAME = r'(?!RUN)(?!(0b[0-1]*|[0-9]+)([^a-zA-Z_0-9]|$))[a-zA-Z_0-9]+'
t_CHIP_FUNC_OP = r'\=\>'
t_OPEN_PARENS = r'\('
t_CLOSE_PARENS = r'\)'
t_OPEN_BRACE = r'\{'
t_CLOSE_BRACE = r'\}'
t_OPEN_SQUARE = r"\["
t_CLOSE_SQUARE = r"\]"
t_DOLLAR = r'\$'
t_NUMBER = r"[0-9]+"
t_BINNUM = r"0b[0-1]+"
t_COLON = r":"
t_RUN = r"RUN"

t_ignore = ' \t\r'
t_ignore_COMMENT = r'\#.*'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise TypeError("Unknown text '%s' at line %s" % (t.value,t.lexer.lineno))


lex.lex()


# test = 'not (a) => (output) {'

# test = """
#     not (a) => (output) {
#         nand [a a] [output] 
#     }
# """

# lex.input(test)
# for tok in iter(lex.token, None):
#     print(str(tok.type), str(tok.value))