from tasks.t3.tdce import *
from functools import cmp_to_key


def is_commutative(op):
    commutative_ops = ['add', 'mul', 'eq', 'and', 'or']
    return op in commutative_ops


def get_index(inst, table):
    # Return the index of this instruction value in the table, otherwise return
    # -1
    for i, (row, _) in enumerate(table):
        if inst == row:
            return i
    return -1


def default_compare(a, b):
    if a > b:
        return 1
    if a == b:
        return 0
    return -1


def compare_args(a, b):
    # Used for argument cannonicalization. If both are indices into the table,
    # compare as integers. If one is a global name, which is a str, give str
    # precedence.
    if isinstance(a, str) and isinstance(b, str):
        return default_compare(a, b)

    if isinstance(a, str):
        return 1

    if isinstance(b, str):
        return -1

    return default_compare(a, b)


def convert_table_to_instructions(table, types):
    # Convert the LVN table into actual instructions
    new_instrs = []
    for i, (inst, definition) in enumerate(table):
        op = inst[0]
        args = inst[1]

        if 'label' in inst:
            ninst = {'label': definition}
            new_instrs.append(ninst)
            continue

        ninst = {}
        ninst['op'] = op
        if definition:
            ninst['dest'] = definition
        if inst[0] == 'const':
            ninst['value'] = args
        else:
            nargs = []
            for arg_idx in inst[1]:
                if isinstance(arg_idx, int):
                    nargs.append(table[arg_idx][1])
                else:
                    # If the lv_map was not an index into the LVN table, then
                    # this variable must not be defined in this basic block, so
                    # just refer to it by the name
                    nargs.append(arg_idx)
            ninst['args'] = nargs

        if types[i]:
            ninst['type'] = types[i]

        new_instrs.append(ninst)

    return new_instrs


def insert_constant_result(inst, result):
    del inst[:]
    inst.append('const')
    inst.append(str(result))


def fold_constants(inst, table):
    # If all of the arguments to an op are statically known, fold the computation
    # into a constant load
    args = []
    for idx in inst[1]:
        # Argument is not defined by an instruction in this scope, and so is not
        # known staticaly for folding
        if isinstance(idx, str):
            continue

        arg, _ = table[idx]
        op, const = arg

        # Can't constant fold if an argument isn't constant
        if op != 'const':
            # We might still be able to fold! If this is an 'and' and one of the
            # arguments is false, we know the result is false even if we don't
            # know the other value. Similar argument for 'or' and True, addition
            # and 0, multiplication and zero or one, etc.
            continue

        args.append(const)

    opkind = inst[0]
    if opkind == 'and':
        if len(args) == 2:
            result = bool(args[0]) and bool(args[1])
        elif len(args) == 1 and args[0] == False:
            result = False
        else:
            return
        insert_constant_result(inst, result)

    if opkind == 'or':
        if len(args) == 2:
            result = bool(args[0]) or bool(args[1])
        elif len(args) == 1 and args[0] == True:
            result = True
        else:
            return
        insert_constant_result(inst, result)

    if opkind == 'not' and len(args) == 1:
        insert_constant_result(inst, not bool(args[0]))


def lvn_bb(bb: BasicBlock):
    # The principal data structure here will be a table of values and their
    # canonical locations. The way we will represent a value will be to have a
    # tuple of (op, args...), where the args will be indices into the LVN table.
    # For auxiliary purposes, we also keep a map from local variables to rows in
    # the LVN table. This map is the compilation context.
    table = []
    types = []
    lv_map = {}

    for inst in bb.instructions:
        definition = inst.get('dest')
        uses = inst.get('args')
        op = inst.get('op')

        if 'label' in inst:
            table.append(['label', inst['label']])
            types.append(None)
            continue

        if op == 'const':
            new_instruction = [op, inst['value']]
            table.append([new_instruction, definition])
            lv_map[definition] = len(table) - 1
            types.append(inst.get('type'))
            continue

        # Copy propagation
        if op == 'id':
            lv_map[definition] = lv_map[uses[0]]
            continue

        new_args = []
        if uses:
            for arg in uses:
                if arg not in lv_map:
                    # This variable has not been defined in this basic block, so
                    # map it specially to a string, not an index in the table
                    lv_map[arg] = arg

                new_args.append(lv_map[arg])

        # Cannonicalize arguments of commutative ops
        if is_commutative(op):
            new_args.sort(key=cmp_to_key(compare_args))

        new_inst = [op, new_args]
        fold_constants(new_inst, table)

        table_idx = get_index(new_inst, table)
        if table_idx >= 0:
            # Already in the table, so just map the value
            lv_map[definition] = table_idx
        else:
            table.append([new_inst, definition])
            types.append(inst.get('type'))
            lv_map[definition] = len(table) - 1

    ninstrs = convert_table_to_instructions(table, types)
    bb.instructions = ninstrs


def lvn(cfg: CFG):
    for bb in cfg.basic_blocks:
        lvn_bb(bb)


def lvn_and_dce(cfg):
    lvn(cfg)
    while tdce(cfg):
        lvn(cfg)


if __name__ == '__main__':
    functions = load_functions_from_stdin()
    cfg = CFG(functions)
    print(cfg)
    lvn(cfg)
    print(cfg)
