from bnf_parser import Item, Variable, Terminal
from itertools import chain

def closure(items, grammar):
    closed = set(items)
    added = True
    last_size = len(closed)
    while added:
        added = False
        closed_iter = set(closed)
        for item in closed:
            len_right = len(item.production)
            pos = item.production.index('.')
            if pos == -1 or pos == len_right - 1:
                continue
            next_symbol = item.production[pos + 1]
            if grammar.is_variable(next_symbol.name):
                for rule in grammar.get_productions_for_variable(
                    next_symbol.name
                ):
                    closed_iter.add(Item(rule, 0))
                    added = len(closed_iter) > last_size
                    if added:
                        last_size = len(closed_iter)
        closed = closed_iter
    return closed

def goto(items, symbol, grammar):
    acc = set()
    for item in items:
        acc.update(_individual_goto(item, symbol, grammar))
    return acc

def _individual_goto(item, symbol, grammar):
    pos = item.production.index('.')
    if grammar.is_terminal(symbol):
        symbol = Terminal(symbol)
    elif grammar.is_variable(symbol):
        symbol = Variable(symbol)
    if pos == -1 or pos == len(item.production) - 1 or \
       item.production[pos + 1] != symbol:
        return set()
    new_item = item.advance()
    return closure(new_item, grammar)

def items(grammar):
    c = [
        closure(
            [Item(grammar.get_productions_for_variable('#')[0], 0)],
            grammar
        )
    ]
    added = True
    while added:
        added = False
        update_set = set()
        last_size = len(c)
        print c
        for citems in c:
            for symbol in chain(grammar.terminals, grammar.variables):
                goto_symbols = goto(citems, symbol, grammar)
                if len(goto_symbols) > 0:
                    update_set.update(goto_symbols)
        if len(update_set) > 0:
            c.append(update_set)
        added = len(c) > last_size
        last_size = len(c)
    return c

