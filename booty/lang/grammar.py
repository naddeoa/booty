grammar = r"""
%import common.SH_COMMENT
%import common.WS_INLINE
%ignore SH_COMMENT
%ignore WS_INLINE


start: (recipe | target | dependency | _NEW_LINE)*

recipe: "recipe" RECIPE_NAME "(" [arguments] ")" ":" _NEW_LINE def+

target: target_name ":" (_NEW_LINE def | recipe_invocation)

dependency: depends_on | depended_upon

depended_upon: NAME "<-" NAME+ 

depends_on: NAME "->" NAME+

def: (single_line_def | multi_line_def)+

def_body: (shell_line | recipe_invocation)*

single_line_def.1: implements ":" (shell_line | recipe_invocation) _NEW_LINE*

multi_line_def.1: implements ":" _NEW_LINE def_body _NEW_LINE*

recipe_invocation.1: NAME "(" recipe_parameter_list ")" _NEW_LINE

recipe_parameter_list: recipe_parameter ("," recipe_parameter)*

recipe_parameter: (INVOCATION_ARGS | _NEW_LINE)*

implements: IMPLEMENTS_NAME

shell_line: SHELL_LINE _NEW_LINE

SHELL_LINE: /[^\n]+/

INVOCATION_ARGS: /[^\n \t\),]+/

target_name: NAME

arguments: ARGUMENT_NAME*
ARGUMENT_NAME: /[a-zA-Z0-9_\.-]+/

NAME: /[a-zA-Z0-9_\.-]+/
RECIPE_NAME: /[a-zA-Z0-9_\.-]+/

# Note the leadering space before implements. It has to be indented somewhat.
IMPLEMENTS_NAME: /[ \t]+[a-zA-Z0-9_\.-]+/
_NEW_LINE: /\n/
"""
