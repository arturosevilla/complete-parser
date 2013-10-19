"""
Simple parser and structure containing the grammar defined in BNF
"""

from .bnf_lexer import Lexer
import re

class UnexpectedBNFToken(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Unexpected token: ' + self.msg


class Grammar(object):
    def __init__(self, variables, terminals, start, prods):
        self.variables = variables
        self.variables.add('#')
        self.terminals = terminals
        self.start = '#'
        # augmented grammar
        self.productions = prods + [Production(Variable('#'), [start])]
        self.prods_per_var = {}
        self.cached_firsts = {}
        self.cached_follows = {}
        for p in self.productions:
            if p.variable.name not in self.prods_per_var.keys():
                self.prods_per_var[p.variable.name] = []
            self.prods_per_var[p.variable.name].append(p)
        self._build_follow()

    def is_terminal(self, symbol):
        return symbol in self.terminals

    def is_variable(self, symbol):
        return symbol in self.variables

    def get_productions_for_variable(self, var):
        return self.prods_per_var.get(var, [])

    def _get_first(self, symbol):
        if self.is_terminal(symbol):
            return set([symbol])
        firsts = set()
        prods = self.get_productions_for_variable(symbol)
        for prod in prods:
            if len(prod.production) == 1 and prod.production[0] == '':
                # empty production
                firsts.add('')
            else:
                for prod_symbol in prod.production:
                    if prod_symbol.name == symbol:
                        continue
                    current_first = self.first(prod_symbol.name)
                    firsts.update(current_first)
                    if '' not in current_first:
                        break
        return firsts

    def _build_follow(self):
        if len(self.cached_follows) == 0:
            for var in self.variables:
                self.cached_follows[var] = set()
            self.cached_follows['#'].add('$')

        pending = {var: set() for var in self.variables}
        for prod in self.productions:
            for i, sym in enumerate(prod.production):
                if sym == '' or self.is_terminal(sym.name):
                    continue
                if i < len(prod.production) - 1:
                    current_first = ['']
                    with_empty = False
                    while '' in current_first and i < len(prod.production) - 1:
                        current_first = self.first(prod.production[i + 1].name)
                        with_empty = '' in current_first
                        self.cached_follows[sym.name].update(
                            current_first.difference(set(['']))
                        )
                        i += 1
                    if i == len(prod.production) - 1 and \
                       prod.variable.name != sym.name and \
                       with_empty:
                        pending[prod.variable.name].add(sym.name)
                elif sym.name != prod.variable.name:
                    pending[prod.variable.name].add(sym.name)

        for var, pend in pending.iteritems():
            self._update_follow(pending, var)

    def _update_follow(self, pending, symbol):
            current_follow = self.cached_follows[symbol]
            for var in pending[symbol]:
                if var == symbol:
                    continue
                len_previous = len(self.cached_follows[var])
                self.cached_follows[var].update(current_follow)
                if len(self.cached_follows[var]) > len_previous:
                    self._update_follow(pending, var)


    def first(self, symbol):
        first = self.cached_firsts.get(symbol)
        if first is None:
            first = self._get_first(symbol)
            self.cached_firsts[symbol] = first
        return first

    def follow(self, symbol):
        if self.is_terminal(symbol):
            raise ValueError('Follow only defined for variables')
        return self.cached_follows[symbol]



class Production(object):
    def __init__(self, variable, production):
        self.variable = variable
        self.production = production


class Variable(object):
    def __init__(self, name):
        self.name = re.sub('<|>', '', name)


class Terminal(object):
    def __init__(self, name):
        self.name = re.sub('"', '', name)


def build_grammar(code):
    lines = [line.strip() for line in code.strip().split('\n')
             if line.strip()[0] != '#' and len(line.strip()) > 0]
    rules = []
    terminals = set()
    variables = set()
    start_symbol = None
    for line in lines:
        lexer = Lexer(line)
        for prod in _parse_line(lexer):
            rules.append(prod)
            if start_symbol is None:
                # first defined rule is start symbol
                start_symbol = prod.variable
            for symbol in prod.production:
                if isinstance(symbol, Variable):
                    variables.add(symbol.name)
                elif isinstance(symbol, Terminal):
                    terminals.add(symbol.name)
    return Grammar(variables, terminals, start_symbol, rules)

def _match(lexer, token_types, allow_empty=False):
    if not isinstance(token_types, list):
        token_types = [token_types]
    token = lexer.get_next_token()
    if token is None:
        if allow_empty:
            return None
        else:
            raise UnexpectedBNFToken('End of data')
    if token.type_ not in token_types:
        if allow_empty:
            return None
        raise UnexpectedBNFToken(token.type_)
    return token

def _parse_line(lexer):
    rule_name = Variable(_match(lexer, 'RULE_NAME').lexeme)
    _match(lexer, 'RULE_DEFINITION')
    productions = _parse_productions(lexer)
    for prod in productions:
        yield Production(rule_name, prod)

def _parse_productions(lexer):
    rules = []
    prod = _parse_production(lexer)
    if prod is None:
        raise UnexpectedBNFToken('Empty rule')

    while prod is not None:
        rules.append(prod)
        prod = _parse_production(lexer)

    return rules

def _parse_production(lexer):
    token = _match(lexer, ['EMPTY', 'RULE_NAME', 'RULE_TERMINAL'], True)
    if token is None:
        return None
    if token.type_ == 'EMPTY':
        _match(lexer, 'OR', True)
        return ['']
    prod = []
    while token is not None:
        if token.type_ == 'RULE_NAME':
            prod.append(Variable(token.lexeme))
        else:
            prod.append(Terminal(token.lexeme))
        token = _match(lexer, ['RULE_NAME', 'RULE_TERMINAL', 'OR'], True)
        if token is not None and token.type_ == 'OR':
            token = None
    return prod
 
