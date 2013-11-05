from ..ir import Quadruple, get_next_temp, UndefinedVariableException


class Expression(object):
    
    def generate_ir(self, qtable, env):
        raise NotImplementedError()


class BoolExpression(Expression):
    
    def __init__(self):
        self.true = []
        self.false = []


class SymbolBoolExpression(BoolExpression):
    
    def __init__(self, symbol):
        super(SymbolBoolExpression, self).__init__()
        self.symbol = symbol


    def generate_ir(self, qtable, env):
        self.true.append(qtable.next_instruction)
        self.false.append(qtable.next_instruction + 1)
        qtable.append(Quadruple(
            'if',
            self.symbol.generate_ir(qtable, env),
            None,
            None # will change
        ))
        qtable.append(Quadruple(
            'goto',
            None,
            None,
            None # will change
        ))


class BoolOperationExpression(BoolExpression):
    """For &&, ||, and !"""

    def __init__(self, op, left, right):
        super(BoolOperationExpression, self).__init__()
        self.left = left
        self.right = right
        self.op = op

    def generate_ir(self, qtable, env):
        self.left.generate_ir(qtable, env)
        if self.op == 'or':
            self.true.extend(self.left.true)
            for inst in self.left.false:
                qtable[inst].result = str(qtable.next_instruction)
            self.right.generate_ir(qtable, env)
            self.true.extend(self.right.true)
            self.false.extend(self.right.false)
        elif self.op == 'and':
            self.false.extend(self.left.false)
            for inst in self.left.true:
                qtable[inst].result = str(qtable.next_instruction)
            self.right.generate_ir(qtable, env)
            self.true.extend(self.right.true)
            self.false.extend(self.right.false)
        elif self.op == 'not':
            self.true.extend(self.left.false)
            self.false.extend(self.right.true)
        else:
            raise ValueError('Unknown bool operator: ' + self.op)


class ComparisonExpression(BoolExpression):

    def __init__(self, op, left, right):
        super(ComparisonExpression, self).__init__()
        self.op = op
        self.left = left
        self.right = right

    def generate_ir(self, qtable, env):
        left = self.left.generate_ir(qtable, env)
        right = self.right.generate_ir(qtable, env)
        self.true.append(qtable.next_instruction)
        self.false.append(qtable.next_instruction + 1)
        qtable.append(Quadruple(
            'if' + self.op,
            left,
            right,
            None # will change
        ))
        qtable.append(Quadruple(
            'goto',
            None,
            None,
            None # will change
        ))


class ConstBoolExpression(BoolExpression):

    def __init__(self, value):
        super(ConstBoolExpression, self).__init__()
        self.value = value

    def generate_ir(self, qtable, env):
        if self.value.trim() == 'true':
            self.true.append(qtable.next_instruction)
        else:
            self.false.append(qtable.next_instruction)
        qtable.append(Quadruple(
            'goto',
            None,
            None,
            None # should change
        ))


class OperationExpression(Expression):

    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def generate_ir(self, qtable, env):
        gen_result = Temp('int').generate_ir(qtable, env)
        expr1_result = self.left.generate_ir(qtable, env)
        expr2_result = self.right.generate_ir(qtable, env)
        qtable.append(Quadruple(
            self.op,
            expr1_result,
            expr2_result,
            gen_result
        ))
        return gen_result


class AssignmentExpression(Expression):

    def __init__(self, symbol, expression):
        self.symbol = symbol
        self.expression = expression

    def generate_ir(self, qtable, env):
        result = self.expression.generate_ir(qtable, env)
        gen_result = self.symbol.name
        qtable.append(Quadruple(
            '=',
            result,
            None,
            gen_result
        ))
        return gen_result


class IfExpression(Expression):
    
    def __init__(self, condition, on_true, else_):
        self.condition = condition
        self.on_true = on_true
        self.else_ = else_

    def generate_ir(self, qtable, env):
        self.condition.generate_ir(qtable, env)
        label_true = qtable.next_instruction
        for inst in self.condition.true:
            qtable[inst].result = str(label_true)
        self.on_true.generate_ir(qtable, env)
        if self.else_ is not None:
            jump_after_else = qtable.next_instruction
            qtable.append(Quadruple(
                'goto',
                None,
                None,
                None # will change
            ))
            self.else_.generate_ir(qtable, env)
            self.qtable[jump_after_else].result = str(qtable.next_instruction)
        next_ = qtable.next_instruction
        for inst in self.condition.false:
            qtable[inst].result = str(next_)


class BlockExpression(Expression):

    def __init__(self, expr1, expr2):
        self.expr1 = expr1
        self.expr2 = expr2

    def generate_ir(self, qtable, env):
        self.expr1.generate_ir(qtable, env)
        self.expr2.generate_ir(qtable, env)


class WhileExpression(Expression):
    
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

    def generate_ir(self, qtable, env):
        before_loop = qtable.next_instruction
        self.condition.generate_ir(qtable, env)
        label_true = qtable.next_instruction
        self.block.generate_ir(qtable, env)
        qtable.append(Quadruple(
            'goto',
            None,
            None,
            str(before_loop)
        ))
        next_ = qtable.next_instruction
        for inst in self.condition.true:
            qtable[inst].result = str(label_true)
        for inst in self.condition.false:
            qtable[inst].result = str(next_)


class DefinitionExpression(Expression):

    def __init__(self, type_, name):
        self.name = name
        self.type_ = type_

    def generate_ir(self, qtable, env):
        env.put(self.name, {'type': self.type_, 'name': self.name})
        return None


class ConstExpression(Expression):
    def __init__(self, const):
        self.const = const

    def generate_ir(self, qtable, env):
        return str(self.const)


class SymbolExpression(Expression):

    def __init__(self, name):
        self.name = name

    def generate_ir(self, qtable, env):
        symbol = env.get(self.name)
        if symbol is None:
            raise UndefinedVariableException(self.name)
        return symbol['name']


class Temp(SymbolExpression):
    
    def __init__(self, type_):
        name = 't' + str(get_next_temp())
        self.type_ = type_
        super(Temp, self).__init__(name)

    def generate_ir(self, qtable, env):
        if env.get(self.name) is None:
            env.put(
                self.name,
                {'type': self.type_, 'name': self.name, 'temp': True}
            )
        return self.name


class ParamExpression(Expression):
    
    def __init__(self, type_, name):
        self.name = name
        self.type_ = type_

    def generate_ir(self, qtable, env):
        pass


class FunctionExpression(Expression):

    def __init__(self, name, params, block):
        self.name = name
        self.params = params
        self.block = block

    def generate_ir(self, qtable, env):
        pass

