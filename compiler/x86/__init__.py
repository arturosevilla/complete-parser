

class CodeGenerator(object):

    def __init__(self, qtable, env):
        self.basic_blocks = qtable.get_basic_blocks()
        self.current = 0
        self.env = env
        self.variables = []
        self.temp_variables = {}
        self.prefix = ' ' * 4
        self.jump_types = {
            '>': 'jg',
            '<': 'jl',
            '>=': 'jge',
            '<=': 'jle',
            '==': 'jz',
            '!=': 'jnz'
        }
        offset = 4
        for variable, info in env.env.iteritems():
            if info.get('temp', False):
                self.temp_variables[variable] = offset
                offset += 4
            else:
                self.variables.append(variable)


    def generate(self):
        lines = ['.bss']
        for variable in self.variables:
            lines.append(self.prefix + '.lcomm ' + variable + ', 4')
        lines.extend([
            '.text',
            '_start:',
            self.prefix + 'call main',
            self.prefix + 'movl $1, %eax',
            self.prefix + 'movl $0, %ebx',
            self.prefix + 'int $0x80',
            self.prefix + 'hlt',
            'main:',
        ])
        main_code = []
        to_preserve = set()
        for block in self.basic_blocks:
            main_code.extend(self._generate_assembly(block, to_preserve))
        main_code.append('LEND:')
        main_code = self._generate_preserve_variables(main_code, to_preserve)
        main_code = self._generate_preamble() + main_code
        main_code.extend(self._generate_end())
        main_code.append(self.prefix + 'ret')
        return lines + main_code

    def _generate_preamble(self):
        preamble = [self.prefix + 'pushl %ebp', self.prefix + 'movl %esp, %ebp']
        if len(self.temp_variables) > 0:
            preamble.append('subl $' + len(self.temp_variables) + ', %esp')
        return preamble

    def _generate_end(self):
        return [self.prefix + 'movl %ebp, %esp', self.prefix + 'popl %ebp']

    def _is_constant(self, value):
        return isinstance(value, int)

    def _generate_preserve_variables(self, assembly, to_preserve):
        to_preserve = list(to_preserve)
        preserve_inst = [self.prefix + 'pushl %' + preserve
                         for preserve in to_preserve]
        post_preserver_inst = [self.prefix + 'popl %' + preserve
                               for preserve in reversed(to_preserve)]

        return preserve_inst + assembly + post_preserver_inst

    def _generate_jump_code(self, assembly, block, line):
        return [self.prefix + 'jmpl L' + str(block.get_jump(line.result))]

    def _issue_load(self, assembly, source, destination):
        self.registers[destination]['variables'] = set()
        if self._is_constant(source):
            source = '$' + str(source)
        else:
            source = self._get_store(source)
            self.registers[destination]['variables'].add(source)
            self.address[source]['registers'].add(destination)
        assembly.append(
            self.prefix + 'movl ' + source + ', %' + destination
        )

    def _get_store(self, variable):
        offset = self.address[variable].get('offset', 0)
        if offset == 0:
            return variable
        return '-' + str(offset) + '(%ebp)'

    def _issue_store(self, assembly, source, variable):
        assembly.append(
            self.prefix + 'movl %' + source + ', ' + self._get_store(variable)
        )
        self.address[variable]['memory'] = True

    def _handle_argument(self, assembly, argument, register):
        if self._is_constant(argument) or \
           not argument in self.registers[register]['variables']:
            self._issue_load(assembly, argument, register)

    def _generate_conditional_code(self, assembly, block, line, to_preserve):
        reg_res, reg_arg1, reg_arg2 = self._get_registers(
            assembly,
            line.op,
            line.arg1,
            line.arg2,
            line.result,
            to_preserve
        )
        self._handle_argument(assembly, line.arg1, reg_arg1)
        self._handle_argument(assembly, line.arg2, reg_arg2)
        after_store = [self.prefix + 'cmpl %' + reg_arg2 + ', %' + reg_arg1]
        jump_type = self.jump_types.get(line.op[2:])
        if jump_type is None:
            raise NotImplementedError(self.op + ' operator unknown')
        after_store.append(
            self.prefix + jump_type + ' L' + str(block.get_jump(line.result))
        )
        return after_store

    def _generate_assignment(self, assembly, block, line, to_preserve):
        reg_res, reg_arg1, _ = self._get_registers(
            assembly,
            line.op,
            line.arg1,
            None,
            line.result,
            to_preserve
        )
        self._handle_argument(self, assembly, line.arg1, reg_arg1)
        # assume reg_arg1 == reg_res
        self.registers[reg_arg1]['variables'].add(line.result)
        self.address[line.result]['registers'] = set([reg_arg1])
        self.address[line.result]['memory'] = False

    def _handle_sum(self, instruction, assembly, line, to_preserve):
        # x86 handles addition and substraction with source and destination
        # registers, so addl a, b means b += a so first we need to check if
        # argument b is loaded in memory, if not, then issue a store
        # instruction, before making the assignment UNLESS the result is going
        # to be stored on the same spot, i.e., original instruction: a += b
        # Afterwards we need to tell the address descriptor and register
        # descriptor that we are holding the value of our target
        reg_res, reg_arg1, reg_arg2 = self._get_registers(
            assembly,
            '+',
            line.arg1,
            line.arg2,
            line.result,
            to_preserve
        )
        self._handle_argument(assembly, line.arg1, reg_arg1)
        if self._is_constant(line.arg2):
            value_arg2 = '$' + str(line.arg2)
        else:
            self._handle_argument(assembly, line.arg2, reg_arg2)
            value_arg2 = '%' + reg_arg2

        if not self._is_constant(line.arg1):
            self.registers[reg_arg1]['variables'].discard(line.arg1)
            self.address[line.arg1]['registers'].discard(reg_arg1)
        if len(self.address[line.arg1]['registers']) == 0 and \
           not self.address[line.arg1]['memory']:
            self._issue_store(assembly, reg_arg1, line.arg1)

        assembly.append(
            self.prefix + instruction + ' ' + value_arg2 + ', %' + reg_arg1
        )
        self.registers[reg_arg1]['variables'].add(line.result)
        self.address[line.result]['registers'] = set([reg_arg1])
        self.address[line.result]['memory'] = False

    def _generate_arithmetic(self, assembly, block, line, to_preserve):
        if line.op == '+' or line.op == '-':
            self._handle_sum(
                'addl' if line.op == '+' else 'subl',
                assembly,
                line,
                to_preserve
            )

    def _generate_assembly(self, block, to_preserve):
        self._reset_register_descriptors()
        self._reset_address_descriptors()
        assembly = ['L' + str(block.id_) + ':']
        after_store = []
        for line in block:
            if line.op == 'goto':
                after_store = self._generate_jump_code(assembly, block, line)
            elif line.op[:2] == 'if':
                after_store = self._generate_conditional_code(
                    assembly,
                    block,
                    line,
                    to_preserve
                )
            elif line.op == '=':
                self._generate_assignment(assembly, block, line, to_preserve)
            else:
                self._generate_arithmetic(assembly, block, line, to_preserve)

        for variable, descriptor in self.address.iteritems():
            if descriptor['memory'] or descriptor.get('offset', 0) > 0:
                continue
            if len(descriptor['registers']) == 0:
                raise ValueError(
                    'Variable ' + variable + ' no where to be found'
                )
            # retrieve only one element from set
            source_reg = iter(descriptor['registers']).next()
            self._issue_store(assembly, source_reg, variable)

        if len(after_store) > 0:
            assembly.extend(after_store)

        return assembly

    def _reset_register_descriptors(self):
        self.registers = {
            'eax': {'variables': set(), 'preserve': False},
            'ebx': {'variables': set(), 'preserve': True},
            'ecx': {'variables': set(), 'preserve': False},
            'edx': {'variables': set(), 'preserve': False},
            'edi': {'variables': set(), 'preserve': True},
            'esi': {'variables': set(), 'preserve': True}
        }

    def _reset_address_descriptors(self):
        self.address = {
            var: {'registers': set(), 'memory': True}
            for var in self.variables
        }
        for temp, offset in self.temp_variables.iteritems():
            self.address[temp] = {
                'registers': set(),
                'memory': True,
                'offset': offset
            }

    def _get_argument_register(
        self,
        assembly,
        argument,
        other_argument,
        to_preserve
    ):
        if argument is None:
            return None
        try:
            # grab any register for the argument
            if not self._is_constant(argument):
                register = iter(self.address[argument]['registers']).next()
                if self.registers[register]['preserve']:
                    to_preserve.add(register)
                return register
        except StopIteration:
            # no registers set
            pass

        for register, descriptor in self.registers.iteritems():
            if len(descriptor['variables']) == 0:
                if descriptor['preserve']:
                    to_preserve.add(register)
                return register

        # still no luck with the registers
        # first look for registers with variables in any other place
        min_spill = len(self.registers) * 2
        min_spill_register = None
        for register, descriptor in self.registers.iteritems():
            register_spill = 0
            for variable in descriptor['variables']:
                if self.address[variable]['memory']:
                    continue
                other_places = False
                for other_register in self.address[variable]['registers']:
                    if other_register != register:
                        other_places = True
                        break
                if other_places:
                    continue
                if not (self._is_constant(argument) or
                        self._is_constant(other_argument)) and \
                   argument == other_argument:
                    continue
                register_spill += 1

            if register_spill <= min_spill:
                min_spill = register_spill
                min_spill_register = register

        if min_spill_register is None:
            raise NotImplementedError('Internal error: no registers?')

        if min_spill > 0:
            for variable in self.registers[register]['variables']:
                self._issue_store(assembly, register, variable)

        if self.registers[register]['preserve']:
            to_preserve.add(register)
        return register


    def _get_registers(self, assembly, op, arg1, arg2, result, to_preserve):
        reg_arg1 = self._get_argument_register(assembly, arg1, arg2, to_preserve)
        reg_arg2 = self._get_argument_register(assembly, arg2, arg1, to_preserve)
        if op == '=' or op == '+':
            reg_result = reg_arg1
        else:
            # pending
            reg_result = None
        return reg_result, reg_arg1, reg_arg2

