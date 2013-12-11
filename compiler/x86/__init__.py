

class CodeGenerator(object):

    def __init__(self, qtable, env):
        self.basic_blocks = qtable.get_basic_blocks()
        self.current = 0
        self.env = env
        self.variables = []
        self.prefix = ' ' * 4
        for variable, info in env.env.iteritems():
            if not info.get('temp', False):
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

        main_code = self._generate_preserve_variables(main_code, to_preserve)
        main_code = self._generate_preamble() + main_code
        main_code.extend(self._generate_end())
        main_code.append(self.prefix + 'ret')
        return lines + main_code

    def _generate_preamble(self)
        return []

    def _generate_end(self):
        return []

    def _generate_preserve_variables(self, assembly, to_preserve):
        preserve_inst = [self.prefix + 'pushl ' + preserve
                         for preserve in to_preserve]
        post_preserver_inst = [self.prefix + 'popl' + preserve
                               for preserve in reversed(to_preserve)]

        return preserve_inst + assembly + post_preserver_inst

    def _generate_jump_code(self, assembly, block, line):
        assembly.append(
            self.prefix + 'jmp L' + str(block.get_jump(line.result))
        )

    def _generate_assembly(self, block, to_preserve):
        self._reset_register_descriptors()
        self._reset_address_descriptors()
        assembly = ['L' + str(block.id_) + ':']
        for line in block:
            if line.op == 'goto':
                self._generate_jump_code(assembly, block, line)


                return assembly

    def _reset_register_descriptors(self):
        self.registers = {
            'eax': {'variables': [], 'preserve': False},
            'ebx': {'variables': [], 'preserve': True},
            'ecx': {'variables': [], 'preserve': False},
            'edx': {'variables': [], 'preserve': False},
            'edi': {'variables': [], 'preserve': True},
            'esi': {'variables': [], 'preserve': True}
        }

    def _reset_address_descriptors(self):
        self.address = {
            var: {'registers': [], 'memory': True}
            for var in self.variables
        }

    def _get_registers(self, op, arg1, arg2, result):
        pass

