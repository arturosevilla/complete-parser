from collections import namedtuple

_temp_counter = 0

def get_next_temp():
    global _temp_counter
    _temp_counter += 1
    return _temp_counter

class Quadruple(object):
    def __init__(self, op, arg1, arg2, result):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):
        if self.op == 'goto':
            return 'goto L' + self.result
        elif self.op[:2] == 'if':
            return 'if ' + self.arg1 + ' ' + self.op[2:] + ' ' + self.arg2 + \
                   ' goto L' + self.result
        else:
            line = self.result + ' = ' + self.arg1
            if self.op != '=':
                line += ' ' + self.op + ' ' + self.arg2
            return line


class BasicBlock(object):
    def __init__(self, instructions):
        self.instructions = instructions

    def __str__(self):
        code = []
        for q in self.instructions:
            code.append(' ' * 8 + str(q))
        return '\n'.join(code)


class QTable(object):

    def __init__(self):
        self.qtable = []
        self.next_instruction = 0

    def append(self, instruction):
        self.qtable.append(instruction)
        self.next_instruction += 1

    def get_basic_blocks(self):
        leaders = []
        next_is_leader = False
        for i, inst in enumerate(self.qtable):
            if next_is_leader:
                leaders.append(i)
                next_is_leader = False
            if inst.op == 'goto' or inst.op[:2] == 'if': 
                target = int(inst.result)
                if target < len(self.qtable):
                    leaders.append(int(inst.result))
                next_is_leader = True
        last_leader = 0
        leaders.sort()
        for leader in set(leaders):
            block = BasicBlock(self.qtable[last_leader:leader])
            last_leader = leader
            yield block
        yield BasicBlock(self.qtable[last_leader:])

    def __getitem__(self, index):
        return self.qtable[index]

    def __str__(self):
        code = []
        labels = []
        for q in self.qtable:
            if q.op == 'goto':
                labels.append((int(q.result), 'L' + q.result + ':'))
            elif q.op[:2] == 'if':
                labels.append((int(q.result), 'L' + q.result + ':'))
            code.append(' ' * 8 + str(q))
        for label in labels:
            try:
                code[label[0]] = label[1] + code[label[0]][len(label[1]):]
            except IndexError:
                code.append(label[1])
        return '\n'.join(code)

class UndefinedVariableException(Exception):
    def __init__(self, var):
        self.var = var
    
    def __str__(self):
        return 'Undefined variable: ' + self.var


class RedefinitionException(Exception):
    def __init__(self, var):
        self.var = var

    def __str__(self):
        return '%s was redefined' % self.var


class Environment(object):

    def __init__(self, parent_env=None):
        self.parent_env = parent_env
        self.label_counter = -1
        self.env = {}

    def get(self, name):
        var = self.env.get(name)
        if var is None and self.parent_env is None:
            return None
        if var is not None:
            return var
        return self.parent_env.get(name)
    
    def put(self, name, info, allow_redefines=False):
        if self.env.get(name) is not None and not allow_redefines:
            raise RedefinitionException(name)
        self.env[name] = info

    def update(self, name, info):
        if self.env.get(name) is None:
            raise ValueError('Unknown variable')
        self.env[name].update(info)

class IRGenerator(object):

    def __init__(self, semantic):
        self.semantic = semantic

    def generate(self):
        asts = self.semantic.get_blocks()
        global_env = Environment()
        for def_ in self.semantic.get_definitions():
            global_env.put(*def_)

        for ast in asts:
            qtable = QTable()
            ast.generate_ir(qtable, global_env)
            yield qtable

