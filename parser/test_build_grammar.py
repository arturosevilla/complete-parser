#!/usr/bin/env python
from bnf_parser import build_grammar_and_commands
from slr import items
from itertools import chain
import sys

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        code = f.read()
    g, commands = build_grammar_and_commands(code)
    print str(g.variables)
    print str(g.terminals)
    print str(g.productions)
    print 'Firsts'
    for symbol in chain(g.variables, g.terminals):
        print 'first(', symbol, ') = ', g.first(symbol)
    print 'Follows'
    for symbol in g.variables:
        print 'follow(', symbol, ') = ', g.follow(symbol)
    print 'Items'
    print items(g)
