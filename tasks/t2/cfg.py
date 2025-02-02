import sys
import json


class Instruction:
    def is_terminator(inst):
        if 'op' not in inst:
            return False
        op = inst['op']
        return op == 'jmp' or op == 'br' or op == 'ret'

    def get_callee(call_inst):
        callee = call_inst['funcs']
        assert (len(callee) == 1 and "Call instruction has more than one dest")
        return callee[0]

    def get_label(jmp_inst):
        label = jmp_inst['labels']
        assert (len(label) == 1 and "Jump instruction more than one dest")
        return label[0]


class BasicBlock:
    name = ''
    instructions = None
    begins_function = False

    def __init__(self, name: str, begins_function: bool = False):
        self.name = name
        self.instructions = []
        self.begins_function = begins_function

    def append(self, instruction):
        self.instructions.append(instruction)

    def create_name(function_name: str, inst_num: int, label: str) -> str:
        if label:
            return "_".join((function_name, label))
        else:
            return "_".join((function_name, str(inst_num)))

    def is_empty(self):
        return len(self.instructions) == 0

    def __str__(self):
        s = "[{}]:\n".format(self.name)
        for inst in self.instructions:
            s += "  " + str(inst) + "\n"
        return s


class CFG:
    basic_blocks = None
    edges = None

    def __init__(self):
        self.basic_blocks = []
        self.edges = {}

    def __init__(self, functions):
        self.basic_blocks = []
        self.edges = {}
        self.build_cfg(functions)

    def add_edge(self, start: str, end: str):
        # Find the basic blocks corresponding to these names
        for bb in self.basic_blocks:
            if bb.name == start:
                bb_start = bb
            if bb.name == end:
                bb_end = bb
        assert (bb_start and bb_end)

        if start not in self.edges:
            self.edges[bb_start] = set()

        self.edges[bb_start].add(bb_end)

    def add_basic_block(self, bb: BasicBlock):
        # Don't add empty basic blocks
        if bb.is_empty():
            return
        return self.basic_blocks.append(bb)

    def parse_function(self, function):
        fname = function['name']
        instructions = function['instrs']

        bb_begins_fn = True
        curr_bb = BasicBlock(fname, bb_begins_fn)
        for i, inst in enumerate(instructions):
            # Add the current instruction to the basic block (if it's an actual
            # instruction and not a label)
            if not 'label' in inst:
                curr_bb.append(inst)

            if 'op' in inst and inst['op'] == 'call':
                # Call instructions will simply get handled by adding an edge
                # from the caller BB to the callee BB. We do not consider call
                # instructions to be terminators. The reason for this is that
                # the leader of the basic blocks will still dominate all of the
                # instructions after the call.
                # Furthermore, we do not add an edge from the callee back to the
                # caller. This is to prevent paths in the CFG that are
                # unrealizable during the execution of the program. For
                # instance, if we had
                # foo (a):
                #   ...
                #   helper(a)
                #   ...
                # bar (a):
                #   ...
                #   helper(a)
                #   ...
                # We don't to have a path foo -> helper -> bar in the CFG, which
                # would occur if we had edges from callees to callers. This will
                # likely get handled in the inter-procedural analysis
                # assignments.
                callee = Instruction.get_callee(inst)
                self.add_edge(fname, callee)

            elif Instruction.is_terminator(inst):
                # If the instruction is a terminator, we need to form a new
                # basic block
                self.add_basic_block(curr_bb)
                new_name = BasicBlock.create_name(fname, i, None)
                curr_bb = BasicBlock(new_name)

            elif 'label' in inst:
                # If we encounter a label, we need to start a new basic block
                # since we maybe have a jump instruction or branch instruction
                # that lands here.
                # FIXME: If we want to have maximal basic blocks, we should
                # actually check that there's an instruction that lands here.
                self.add_basic_block(curr_bb)
                curr_bb = BasicBlock(
                    BasicBlock.create_name(fname, i, inst['label']))
                # Add the label to the start of the new block
                curr_bb.append(inst)

        self.add_basic_block(curr_bb)

    def build_edges(self):
        for bb in self.basic_blocks:
            start = bb.name
            # BB name is func_inum or func_label
            func_name = bb.name.split("_")[0]

            last_instruction = bb.instructions[-1]
            if 'op' in last_instruction and last_instruction['op'] == 'jmp':
                label = Instruction.get_label(last_instruction)

                end = BasicBlock.create_name(func_name, -1, label)
                self.add_edge(start, end)

            if 'op' in last_instruction and last_instruction['op'] == 'br':
                assert (len(last_instruction['labels']) == 2
                        and "Branch doesn't have two destinations")
                left, right = last_instruction['labels']

                left_end = BasicBlock.create_name(func_name, -1, left)
                right_end = BasicBlock.create_name(func_name, -1, right)
                self.add_edge(start, left_end)
                self.add_edge(start, right_end)

    def build_cfg(self, functions):
        for function in functions:
            self.parse_function(function)
        self.build_edges()

    def __str__(self):
        s = "Basic Blocks\n"
        for i, v in enumerate(self.basic_blocks):
            s += "BB{} [{}]:\n".format(i, v.name)
            for inst in v.instructions:
                s += "  " + str(sorted(inst.items())) + "\n"

        s += "Edges\n"
        for k in self.edges:
            s += "  {} -> {}\n".format(k.name,
                                       ",".join([bb.name for bb in self.edges[k]]))

        return s

    # Is this basic block the end of a function?
    def end_of_function(self, bb: BasicBlock):
        if bb not in self.edges:
            return True

        # Any successors must be function entry BBs
        for successor in self.edges[bb]:
            if not successor.begins_function:
                return False

        return True


def load_functions():
    if (len(sys.argv) != 2):
        print("usage: <infile path>")
        exit(1)

    infile = sys.argv[1]
    with open(infile) as f:
        prog = json.load(f)

    functions = prog['functions']


def load_functions_from_stdin():
    return json.load(sys.stdin)['functions']


if __name__ == '__main__':
    functions = load_functions()
    cfg = CFG()
    cfg.build_cfg(functions)
    print(cfg)
