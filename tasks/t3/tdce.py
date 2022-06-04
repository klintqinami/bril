from tasks.t2.cfg import *


def tdce():
    return


if __name__ == '__main__':
    functions = load_functions_from_stdin()
    cfg = CFG(functions)
    print(cfg)