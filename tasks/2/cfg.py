import sys
import json


class BasicBlock:
    name = ''
    instructions = None

    def __init__(self, name):
        self.name = name
        self.instructions = []

    def append(self, instruction):
        self.instructions.append(instruction)


def get_function(functions, name):
    for f in functions:
        if f['name'] == name:
            return f
    raise ValueError("Didn't find function {}".format(name))


def is_visited_bb(basic_blocks, name):
    for bb in basic_blocks:
        if bb.name == name:
            return bb
    return None


def parse_function(functions, name, basic_blocks, edges):
    func = get_function(functions, name)

    # Start a new basic block upon function entry
    basic_blocks.append(BasicBlock(name))

    bb_idx = len(basic_blocks) - 1
    top_level_bb_idx = bb_idx
    edges[bb_idx] = set()
    instructions = func['instrs']

    for i, inst in enumerate(instructions):
        if inst['op'] == 'call':
            callee = inst['funcs']
            assert (len(callee) == 1 and "Call should only be to one function")
            callee = callee[0]

            # If we have a call, we need to parse the basic blocks within that
            # function
            calleebb = parse_function(functions, callee, basic_blocks, edges)

            # We need an edge from the current basic block to the callee
            edges[bb_idx].add(calleebb)

            # We need to create a new basic block now, and add an edge from the
            # callee to the new block
            basic_blocks.append(BasicBlock(name + "_inst_" + str(i)))
            bb_idx = len(basic_blocks) - 1
            edges[calleebb].add(bb_idx)

        elif inst['op'] == 'jmp':
            label = inst['labels']
            assert (len(label) == 1 and "Jumping to multiple labels!")
            label = label[0]

            prev_bb = is_visited_bb(name + "_" + label)
            if (prev_bb):
                edges[bb_idx].add(prev_bb.name)
            else:
                print("At jump")

            exit(1)

        else:
            basic_blocks[bb_idx].append(inst)

    return top_level_bb_idx


def build_cfg(functions):
    basic_blocks = []
    edges = {}
    parse_function(functions, 'main', basic_blocks, edges)
    return basic_blocks, edges


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print("usage: <infile path>")
        exit(1)

    infile = sys.argv[1]
    with open(infile) as f:
        d = json.load(f)

    top_level = "functions"
    functions = d[top_level]

    basic_blocks, edges = build_cfg(functions)
    print("Basic Blocks")
    for i, v in enumerate(basic_blocks):
        print("BB[{}] = {}:".format(i, v.name))
        for inst in v.instructions:
            print(inst)

    print("Edges")
    for k in edges:
        print("Edges from {}:".format(k))
        print(edges[k])