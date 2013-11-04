from .bnf_parser import build_grammar
import sys

def _get_chained_first(grammar, production):
    if production[0] == '':
        return ['']

    current_first = ['']
    firsts = set()
    while '' in current_first and len(production) > 0:
        current_first = grammar.first(production[0])
        production = production[1:]
        firsts.update(current_first.difference(set([''])))
    if len(production) == 0:
        firsts.add('')
    return firsts


def add_to_parse_table(parse_table, var, term, prod):
    #if parse_table[var][term] is not None:
    #    raise ValueError('Ambiguous grammar!')
    # TODO: Check if productions is really equal to another, if not, then raise
    # an error!
    parse_table[var][term] = prod


def build_parser_table(grammar):
    parse_table = {}
    for var in grammar.variables:
        parse_table[var] = {}
        for term in grammar.terminals:
            parse_table[var][term] = None
    for prod in grammar.productions:
        var = prod.variable.name
        for term in grammar.first(var):
            if term == '':
                continue
            add_to_parse_table(parse_table, var, term, prod)
        if '' in _get_chained_first(grammar, prod.production):
            for term in grammar.follow(var):
                add_to_parse_table(parse_table, var, term, prod)
    return parse_table

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        code = f.read()
    g = build_grammar(code)
    print build_parser_table(g)

