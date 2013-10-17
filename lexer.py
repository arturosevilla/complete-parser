#!/usr/bin/env python
# define a lexer based on the following tokens:
# * if
# * (
# * )
# * relop
# * semicolon
# * OP
# * {
# * }
# * id
# * =
# * while
# * return

# Regex compiled by hand


class Token(object):
    def __init__(self, type_, lexeme):
        self.type_ = type_
        self.lexeme = lexeme


class Lexer(object):
    
    def __init__(self, code):
        self.code = code
        self.stop_chars = [' ', '\t', '\n']
        self.build_nfa()
        self.reset()

    def build_nfa(self):
        self.goto_nfa = [
            {
                'i': [1, 31],
                '(': [3],
                ')': [4],
                '<': [5, 7],
                '>': [6, 9],
                '=': [11, 33],
                ';': [13],
                '+': [14],
                '*': [15],
                '-': [16],
                '/': [17],
                '{': [18],
                '}': [19],
                'w': [20, 31],
                'r': [25, 31],
                'a': [31],
                'b': [31],
                'c': [31],
                'd': [31],
                'e': [31],
                'f': [31],
                'g': [31],
                'h': [31],
                'j': [31],
                'k': [31],
                'l': [31],
                'm': [31],
                'n': [31],
                'o': [31],
                'p': [31],
                'q': [31],
                's': [31],
                't': [31],
                'u': [31],
                'v': [31],
                'x': [31],
                'y': [31],
                'z': [31],
                'A': [31],
                'B': [31],
                'C': [31],
                'D': [31],
                'E': [31],
                'F': [31],
                'G': [31],
                'H': [31],
                'I': [31],
                'J': [31],
                'K': [31],
                'L': [31],
                'M': [31],
                'N': [31],
                'O': [31],
                'P': [31],
                'R': [31],
                'Q': [31],
                'S': [31],
                'T': [31],
                'U': [31],
                'V': [31],
                'X': [31],
                'W': [31],
                'Y': [31],
                'Z': [31],
                '_': [31],
                '0': [32],
                '1': [32],
                '2': [32],
                '3': [32],
                '4': [32],
                '5': [32],
                '6': [32],
                '7': [32],
                '8': [32],
                '9': [32]
            },
            {
                'f': [2]
            },
            {}, # 2
            {}, # 3
            {}, # 4
            {}, # 5
            {}, # 6
            {
                '=': [8]
            },
            {}, # 8
            {
                '=': [10]
            },
            {}, #10
            {
                '=' : [12]
            },
            {}, # 12
            {}, # 13
            {}, # 14
            {}, # 15
            {}, # 16
            {}, # 17
            {}, # 18
            {}, # 19
            {
                'h': [21, 31]
            },
            {
                'i': [22, 31]
            },
            {
                'l': [23, 31]
            },
            {
                'e': [24, 31]
            }, # 23
            {}, # 24
            {
                'e': [26, 31]
            },
            {
                't': [27, 31]
            },
            {
                'u': [28, 31]
            },
            {
                'r': [29, 31]
            },
            {
                'n': [30, 31]
            },
            {}, #30
            {
                'a': [31],
                'b': [31],
                'c': [31],
                'd': [31],
                'e': [31],
                'f': [31],
                'g': [31],
                'h': [31],
                'i': [31],
                'j': [31],
                'k': [31],
                'l': [31],
                'm': [31],
                'n': [31],
                'o': [31],
                'p': [31],
                'q': [31],
                'r': [31],
                's': [31],
                't': [31],
                'u': [31],
                'v': [31],
                'w': [31],
                'x': [31],
                'y': [31],
                'z': [31],
                'A': [31],
                'B': [31],
                'C': [31],
                'D': [31],
                'E': [31],
                'F': [31],
                'G': [31],
                'H': [31],
                'I': [31],
                'J': [31],
                'K': [31],
                'L': [31],
                'M': [31],
                'N': [31],
                'O': [31],
                'P': [31],
                'R': [31],
                'Q': [31],
                'S': [31],
                'T': [31],
                'U': [31],
                'V': [31],
                'X': [31],
                'W': [31],
                'Y': [31],
                'Z': [31],
                '_': [31],
                '0': [32],
                '1': [32],
                '2': [32],
                '3': [32],
                '4': [32],
                '5': [32],
                '6': [32],
                '7': [32],
                '8': [32],
                '9': [32]
            },
            {
                '0': [32],
                '1': [32],
                '2': [32],
                '3': [32],
                '4': [32],
                '5': [32],
                '6': [32],
                '7': [32],
                '8': [32],
                '9': [32]
            },
            {} # 33
        ]
        self.final_states = {
            2: 'IF',
            3: 'OPEN_PARENS',
            4: 'CLOSE_PARENS',
            5: 'RELOP',
            6: 'RELOP',
            8: 'RELOP',
            10: 'RELOP',
            12: 'RELOP',
            13: 'SEMICOLON',
            14: 'OPERATOR',
            15: 'OPERATOR',
            16: 'OPERATOR',
            17: 'OPERATOR',
            18: 'OPEN_BRACES',
            19: 'CLOSE_BRACES',
            24: 'WHILE',
            30: 'RETURN',
            31: 'ID',
            32: 'NUMBER',
            33: 'ASSIGN'
        }

    def reset(self):
        self.current = 0
        self.state = set([0])

    def _getchar(self):
        if self.current >= len(self.code):
            return None
        input_ = self.code[self.current]
        return input_

    def get_next_token(self):
        input_ = self._getchar()
        self.state = set([0])
        while input_ in self.stop_chars:
            self.current += 1
            input_ = self._getchar()
        if input_ is None:
            return None
        lexeme_begin = self.current
        while input_ is not None:
            next_state = set()
            for state in self.state:
                transition = self.goto_nfa[state].get(input_)
                if transition is not None:
                    for new_state in transition:
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

if __name__ == '__main__':
    # TESTING FOR Lexer CLASS
    if_ = Lexer('if').get_next_token()
    print if_, if_.lexeme, if_.type_

    multiple_tokens = Lexer(' if abc 3 123  ( ) { } ; < <= ==  = > ifi+3')
    t = multiple_tokens.get_next_token()
    # should print:
    # Token instance, if, IF
    # Token instance, abc, ID
    # Token instance, 3, NUMBER
    # Token instance, 123, NUMBER
    # Token instance, (, OPEN_PARENS
    # Token instance, ), CLOSE_PARENS
    # Token instance, {, OPEN_BRACES
    # Token instance, }, CLOSE_BRACES
    # Token instance, ;, SEMICOLON
    # Token instance, <, RELOP
    # Token instance, <=, RELOP
    # Token instance, ==, RELOP
    # Token instance, =, ASSIGN
    # Token instance, >, RELOP
    # Token instance, ifi, ID
    # Token instance, +, OPERATOR
    # Token instance, 3, NUMBER
    while t is not None:
        print t, t.lexeme, t.type_
        t = multiple_tokens.get_next_token()

