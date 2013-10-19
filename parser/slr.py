from .bnf_parser import Item, Variable, Terminal

def closure(items, grammar):
    closed = set(items)
    added = True
    last_size = len(closed)
    while added:
        added = False
        for item in closed:
            len_right = len(item.production)
            pos = item.production.find('.')
            if pos == -1 or pos == len_right - 1:
                continue
            next_symbol = item.production[pos + 1]
            if grammar.is_variable(next_symbol.name):
                for rule in grammar.get_productions_for_variable(
                    next_symbol.name
                ):
                    closed.add(Item(rule, 0))
                    added = len(closed) > last_size
                    if added:
                        last_size = len(closed)
    return closed

def goto(items, symbol, grammar):
    acc = set()
    for item in items:
        acc.update(_individual_goto(item, symbol, grammar))
    return acc

def _individual_goto(item, symbol, grammar):
    pos = item.production.find('.')
    if grammar.is_terminal(symbol):
        symbol = Terminal(symbol)
    elif grammar.is_variable(symbol):
        symbol = Variable(symbol)
    if pos == -1 or pos == len(item.production) - 1 or \
       item.production[pos + 1] != symbol:
        return set()
    new_item = item.advance()
    return closure(new_item, grammar)

