from tasks.t3.tdce import *

# Implementation of local value numbering for a basic block.


def get_index(inst, table):
    for i, (row, _) in enumerate(table):
        if inst == row:
            return i
    return -1


def lvn_bb(bb: BasicBlock):
    # The principal data structure here will be a table of values and their
    # canonical locations. The way we will represent a value will be to have a
    # tuple of (op, args...), where the args will be indices into the LVN table.
    # For auxiliary purposes, we also keep a map from local variables to rows in
    # the LVN table. This map is the compilation context.
    table = []
    lv_map = {}

    print(bb)

    for inst in bb.instructions:
        definition = inst.get('dest')
        uses = inst.get('args')
        op = inst.get('op')

        if op == 'const':
            new_instruction = [op, inst['value']]
            table.append([new_instruction, definition])
            lv_map[definition] = len(table) - 1
            continue

        new_args = []
        for arg in uses:
            new_args.append(lv_map[arg])

        new_inst = [op, new_args]

        table_idx = get_index(new_inst, table)
        if table_idx >= 0:
            # Already in the table, so just map the value
            print(
                "Already have value for {} at {}".format(
                    definition, table_idx))
            lv_map[definition] = table_idx
        else:
            table.append([new_inst, definition])
            lv_map[definition] = len(table) - 1

    for row in table:
        print(row)

    for v in lv_map:
        print("{} -> {}".format(v, lv_map[v]))


def lvn(cfg: CFG):
    for bb in cfg.basic_blocks:
        lvn_bb(bb)


if __name__ == '__main__':
    functions = load_functions_from_stdin()
    cfg = CFG(functions)
    lvn(cfg)
