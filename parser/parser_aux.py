"""
Auxiliary functions as given in the Dragon book
"""
from .bnf_parser import Grammar

def first(symbol, grammar):
    if grammar.is_terminal(symbol):
        return set([symbol])


def follow(symbol, grammar):
    pass

def action():
    pass

def goto():
    pass



