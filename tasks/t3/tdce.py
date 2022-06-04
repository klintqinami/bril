from tasks.t2.cfg import *


# Trivial dead code elimination for a basic block. This is only a single
# iteration. Multiple iterations may be needed if deletion of an instruction
# reveals another candidate for deletion. Looks through all of the instructions
# for instructions that write to a variable that isn't used.
def tdce_bb_iter(cfg: CFG, bb: BasicBlock):
    # Set of variables that have no use since write
    candidates = {}
    delete = []
    for inst in bb.instructions:
        uses = inst.get('args')
        # All the arguments to this instruction are now used, so cannot be
        # candidates for deletion
        if uses:
            for v in uses:
                if v in candidates:
                    del candidates[v]

        dest = inst.get('dest')
        if dest in candidates:
            # Writing to a variable again before it was ever used, so the
            # previous instruction that wrote to it can be safely deleted
            delete.append(candidates[dest])

        # Only remove instructions that write to a variable, as other
        # instructions are assumed to have side effects (like print)
        if dest:
            candidates[dest] = inst

    # Reached the end of this basic block and still have some candidates left
    # over. If this basic block jumps somewhere else, then we cannot delete
    # these without analyzing their uses in the successors of this basic block.
    if cfg.end_of_function(bb):
        for c in candidates:
            delete.append(candidates[c])

    for inst in delete:
        bb.instructions.remove(inst)

    return len(delete) != 0


def tdce_bb(cfg: CFG, bb: BasicBlock):
    # Iterate to a fixed point
    while tdce_bb_iter(cfg, bb):
        continue


def tdce(cfg: CFG):
    for bb in cfg.basic_blocks:
        tdce_bb(cfg, bb)


if __name__ == '__main__':
    functions = load_functions_from_stdin()
    cfg = CFG(functions)
    print(cfg)
    tdce(cfg)
    print(cfg)
