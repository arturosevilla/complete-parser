#!/usr/bin/env python

# A Lexer generator

class UnexpectedRegexToken(Exception):
    def __init__(self, msg, lexer):
        self.msg = msg
        self.near = lexer.code[
            max(0, lexer.current - 3):lexer.current
        ]
        self.numline = str(lexer.numline)

    def __str__(self):
        return 'Unexpected token: ' + self.msg + ' near ' + \
               self.near + ' in line ' + self.numline

class KleeneStarExpression(object):
    def __init__(self, expr):
        self.expr = expr


class OrExpression(object):
    def __init__(self, *expressions):
        self.expressions = expressions


class CharExpression(object):
    def __init__(self, char):
        self.char = char


class ConcatenationExpression(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class RegexToken(object):
    def __init__(self, type_, lexeme):
        self.type_ = type_
        self.lexeme = lexeme


class LocalLexer(object):
    def __init__(self, code, numline):
        self.code = code
        self.current = 0
        self.numline = numline

    def _getchar(self):
        if self.current >= len(self.code):
            return None
        return self.code[self.current]

    def get_next_token(self, or_context=False):
        input_ = self._getchar()
        while input_ in [' ', '\t', '\n']:
            self.current += 1
            input_ = self._getchar()
        if input_ is None:
            return None
        if input_ == '|':
            self.current += 1
            return RegexToken('OR', '|')
        if input_ == '*':
            self.current += 1
            return RegexToken('KLEENE', '*')
        if input_ == '\\':
            self.current += 1
            return RegexToken('ESCAPE', '\\')
        if input_ == '(':
            self.current += 1
            return RegexToken('OPEN_PARENS', '(')
        if input_ == ')':
            self.current += 1
            return RegexToken('CLOSE_PARENS', ')')
        if input_ == '[':
            self.current += 1
            return RegexToken('OPEN_BRACKET', '[')
        if input_ == ']':
            self.current += 1
            return RegexToken('CLOSE_BRACKET', ']')
        if input_ == '-' and or_context:
            self.current += 1
            return RegexToken('DASH', '-')
        self.current += 1
        return RegexToken('CHAR', input_)


class NFA(dict):
    """
    So we can put attributes into it, and auto generate rules
    """
    def __getitem__(self, state):
        if state not in self.keys():
            self[state] = {}
        return super(NFA, self).__getitem__(state)

LEXER_TEMPLATE = """
class Token(object):
    def __init__(self, type_, lexeme):
        self.type_ = type_
        self.lexeme = lexeme


class Lexer(object):
    def __init__(self, code):
        self.code = code
        self.stop_chars = [' ', '\\t', '\\n']
        # black magic incantions go here (autogenerated NFA)
%s
        self.reset()

    def eclosure(self, states):
        closed = set(states)
        for state in states:
            closed.update(
                self.eclosure(self.goto_nfa.get(state, {}).get('', []))
            )
        return closed

    def reset(self):
        self.current = 0
        self.state = self.eclosure([0])

    def _getchar(self):
        if self.current >= len(self.code):
            return None
        input_ = self.code[self.current]
        return input_

    def get_next_token(self):
        input_ = self._getchar()
        self.state = self.eclosure([0])
        while input_ in self.stop_chars:
            self.current += 1
            input_ = self._getchar()
        if input_ is None:
            return None
        lexeme_begin = self.current
        # hokus pokus (NFA simulation)
        while input_ is not None:
            next_state = set()
            for state in self.state:
                transition = self.goto_nfa.get(state, {}).get(input_)
                if transition is not None:
                    for new_state in self.eclosure(transition):
                        next_state.add(new_state)
            if len(next_state) == 0:
                break
            self.state = next_state
            self.current += 1
            input_ = self._getchar()
        lexeme = self.code[lexeme_begin:self.current].strip()
        if len(self.state) == 0:
            raise ValueError('Unknown lexeme: ' + lexeme)

        # we look for the first defined rule
        min_state = lexeme_type = None
        for state in self.state:
            if state < min_state or min_state is None:
                possible_type = self.final_states.get(state)
                if possible_type is not None:
                    min_state = state
                    lexeme_type = possible_type

        if lexeme_type is None:
            raise ValueError('Unknown lexeme: ' + lexeme)
        return Token(lexeme_type, lexeme)
"""


class Flexer(object):
    def __init__(self, code, verbose=False):
        self.lines = [line.strip() for line in code.strip().split('\n')
                      if line.strip()[0] != '#' and len(line.strip()) > 0]
        self.verbose = verbose
        self.state_counter = 1

    def match(self, lexer, token_types, allow_empty=False, or_context=False):
        if lexer.peek is not None:
            p = lexer.peek
            lexer.peek = None
            token = p
        else:
            token = lexer.get_next_token(or_context=or_context)
        if token is None:
            if allow_empty:
                return None
            else:
                raise UnexpectedRegexToken('End of data')
        if not isinstance(token_types, list):
            token_types = [token_types]
        if token.type_ not in token_types and not allow_empty:
            raise UnexpectedRegexToken(token.lexeme, lexer)
        if token.type_ not in token_types:
            lexer.peek = token
            return None
        return token

    def peek(self, lexer, or_context=False):
        if lexer.peek is not None:
            return lexer.peek
        token = lexer.get_next_token(or_context=or_context)
        lexer.peek = token
        return token

    def parse(self, code, numline=0):
        lexer = LocalLexer(code, numline)
        lexer.peek = None
        if self.verbose:
            print 'Regex expression:'
        return self.regex(lexer, '-')

    def regex(self, lexer, prefix):
        term = self.term(lexer, prefix)
        return self.regex_rest(term, lexer, prefix)

    def regex_rest(self, term, lexer, prefix):
        token = self.match(lexer, 'OR', True)
        if token is None:
            return term
        if self.verbose:
            print prefix + '> Or expression: '
        return OrExpression(term, self.regex(lexer, prefix + '-'))

    def term(self, lexer, prefix):
        factor = self.factor(lexer, prefix)
        peek = self.peek(lexer)
        if peek is None or peek.type_ not in [
            'CHAR', 'OPEN_PARENS', 'OPEN_BRACKET'
        ]:
            return factor
        if self.verbose:
            print prefix + '> Concatenation expression: '
        return ConcatenationExpression(factor, self.term(lexer, prefix + '-'))

    def factor(self, lexer, prefix):
        base = self.base(lexer, prefix)
        return self.kleene(base, lexer, prefix)

    def kleene(self, base, lexer, prefix):
        token = self.match(lexer, 'KLEENE', True)
        if token is None:
            return base
        if self.verbose:
            print prefix + '> Kleene\'s star expression'
        return self.kleene(KleeneStarExpression(base), lexer, prefix + '-')

    def base(self, lexer, prefix):
        token = self.match(
            lexer,
            ['CHAR', 'ESCAPE', 'OPEN_PARENS', 'OPEN_BRACKET']
        )
        if token.type_ == 'CHAR':
            if self.verbose:
                print prefix + '> Char expression: ' + token.lexeme
            return CharExpression(token.lexeme)
        if token.type_ == 'ESCAPE':
            token = self.match(
                lexer,
                ['ESCAPE', 'OPEN_PARENS', 'CLOSE_PARENS', 'KLEENE',
                 'OPEN_BRACKET', 'CLOSE_BRACKET', 'OR']
            )
            if self.verbose:
                print prefix + '> Char expression: ' + token.lexeme
            return CharExpression(token.lexeme)
        if token.type_ == 'OPEN_BRACKET':
            if self.verbose:
                print prefix + '> Multiple Or expression: '
            or_ = self.multiple_or(lexer, prefix + '-')
            self.match(lexer, 'CLOSE_BRACKET')
            return or_

        if self.verbose:
            print prefix + '> Regex expression:'
        expr = self.regex(lexer, prefix + '-')
        self.match(lexer, 'CLOSE_PARENS')
        return expr

    def multiple_or(self, lexer, prefix):
        or_terms = self.or_terms(lexer, prefix)
        return self.or_rest(or_terms, lexer, prefix)
    
    def or_rest(self, or_terms, lexer, prefix):
        peek = self.peek(lexer, or_context=True)
        if peek is None or peek.type_ not in ['CHAR', 'ESCAPE']:
            return OrExpression(*or_terms)
        while peek.type_ != 'CLOSE_BRACKET':
            or_terms.extend(self.or_terms(lexer, prefix))
            peek = self.peek(lexer, or_context=True)
        return OrExpression(*or_terms)

    def char_range(self, start, end):
        for c in xrange(ord(start), ord(end) + 1):
            yield chr(c) 

    def or_terms(self, lexer, prefix):
        token = self.match(lexer, ['CHAR', 'ESCAPE'])
        if token.type_ == 'CHAR':
            next_token = self.peek(lexer, or_context=True)
            if next_token is not None and next_token.type_ == 'DASH':
                self.match(lexer, 'DASH', or_context=True)
                end = self.match(lexer, ['CHAR', 'ESCAPE'], or_context=True)
                if end.type_ == 'ESCAPE':
                    end = self.match(
                        lexer,
                        ['ESCAPE', 'OPEN_PARENS', 'CLOSE_PARENS', 'KLEENE',
                         'OPEN_BRACKET', 'CLOSE_BRACKET', 'DASH', 'OR'],
                        or_context=True
                    )

                if ord(end.lexeme) < ord(token.lexeme):
                    raise UnexpectedRegexToken(
                        'Incorrect range in or clause',
                        lexer
                    )
                chars = []
                for c in self.char_range(token.lexeme, end.lexeme):
                    if self.verbose:
                        print prefix + '> Char expression: ' + c
                    chars.append(CharExpression(c))
                return chars
            elif self.verbose:
                print prefix + '> Char expression: ' + token.lexeme

            return [CharExpression(token.lexeme)]
        # escape
        token = self.match(
            lexer,
            ['ESCAPE', 'OPEN_PARENS', 'CLOSE_PARENS', 'KLEENE',
             'OPEN_BRACKET', 'CLOSE_BRACKET', 'DASH', 'OR'],
            or_context=True
        )
        if self.verbose:
            print prefix + '> Char expression: ' + token.lexeme
        return [CharExpression(token.lexeme)]

    def generate_line(self, line, numline):
        try:
            code, token_type = line.split('\t', 1)
        except ValueError:
            raise ValueError(
                'We require that each line contains the code and the type'
            )
        if self.verbose:
            print 'Processing regex: ' + code
        ast = self.parse(code.strip(), numline)
        nfa = self.generate_nfa(ast)
        self.final_states[nfa.accepting] = token_type.strip()
        return nfa

    def generate_nfa(self, ast):
        if isinstance(ast, CharExpression):
            curr = self.state_counter
            nfa = NFA()
            nfa[curr][ast.char] = [curr + 1]
            nfa.initial = curr
            nfa.accepting = curr + 1
            self.state_counter += 2
        elif isinstance(ast, OrExpression):
            curr = self.state_counter
            self.state_counter += 1
            nfa = NFA()
            nfa.initial = curr
            nfa[curr][''] = []
            accepting_states = []
            # first generate all subexpressions
            for expression in ast.expressions:
                nfa_temp = self.generate_nfa(expression)
                nfa.update(nfa_temp)
                nfa[curr][''].append(nfa_temp.initial)
                accepting_states.append(nfa_temp.accepting)
            # and joined them in the accepting state
            for accepting in accepting_states:
                nfa[accepting][''] = [self.state_counter]
            nfa.accepting = self.state_counter
            self.state_counter += 1
        elif isinstance(ast, ConcatenationExpression):
            nfa_left = self.generate_nfa(ast.left)
            nfa_right = self.generate_nfa(ast.right)
            nfa = NFA()
            nfa.initial = nfa_left.initial
            nfa.accepting = nfa_right.accepting
            nfa.update(nfa_left)
            nfa.update(nfa_right)
            nfa[nfa_left.accepting][''] = [nfa_right.initial]
        elif isinstance(ast, KleeneStarExpression):
            curr = self.state_counter
            self.state_counter += 1
            nfa_expr = self.generate_nfa(ast.expr)
            nfa = NFA()
            nfa.update(nfa_expr)
            nfa[curr][''] = [nfa_expr.initial, self.state_counter]
            nfa[nfa_expr.accepting][''] = [
                nfa_expr.initial,
                self.state_counter
            ]
            nfa.initial = curr
            nfa.accepting = self.state_counter
            self.state_counter += 1
        return nfa

    def generate(self):
        self.final_states = {}
        nfa = NFA()
        nfa.initial = 0
        nfa[0][''] = []
        for numline, line in enumerate(self.lines):
            line_nfa = self.generate_line(line, numline + 1)
            nfa.update(line_nfa)
            nfa[0][''].append(line_nfa.initial)
        # generate code with 4 spaces
        # nfa code will be inside a method, so in total: 8 spaces
        nfa_code  = '        self.goto_nfa = ' + str(nfa) + '\n'
        nfa_code += '        self.final_states= ' + str(self.final_states) + '\n'
        return LEXER_TEMPLATE % nfa_code


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise ValueError('Required argument missing')
    verbose = len(sys.argv) == 3 and sys.argv[2] == '-v'
    with open(sys.argv[1]) as f:
        flexer = Flexer(f.read(), verbose)
    print flexer.generate()
    

