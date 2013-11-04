#!/usr/bin/env python
from compiler.sample_language.defs import *
from compiler.ir import IRGenerator

class TestSemantic(object):

    def __init__(self, program):
        self.program = program

    def get_blocks(self):
        return [self.program]

    def get_definitions(self):
        return []

if __name__ == '__main__':
    # int i;
    # int counter;
    # i = 0;
    # counter = 0;
    # while (i < 100) {
    #   if (i % 2 == 0) {
    #       counter = counter + 1;
    #   }
    # }
    program = BlockExpression(
        DefinitionExpression('int', 'i'),
        BlockExpression(
            DefinitionExpression('int', 'counter'),
            BlockExpression(
                AssignmentExpression(
                    SymbolExpression('i'),
                    ConstExpression(0)
                ),
                BlockExpression(
                    AssignmentExpression(
                        SymbolExpression('counter'),
                        ConstExpression(0)
                    ),
                    WhileExpression(
                        ComparisonExpression(
                            '<',
                            SymbolExpression('i'),
                            ConstExpression(100)
                        ),
                        IfExpression(
                            ComparisonExpression(
                                '==',
                                OperationExpression(
                                    '%',
                                    SymbolExpression('i'),
                                    ConstExpression(2)
                                ),
                                ConstExpression(0)
                            ),
                            AssignmentExpression(
                                SymbolExpression('counter'),
                                OperationExpression(
                                    '+',
                                    SymbolExpression('counter'),
                                    ConstExpression(1)
                                )
                            ),
                            None # else
                        )
                    )
                )
            )
        )
    )
    sem = TestSemantic(program)
    gen = IRGenerator(sem)
    for program in gen.generate():
        print str(program)

