import argparse

from bap.instance import Instance
from bap.pa_solver import PASolver
from bap.rp_solver import RPSolver
from bap.s_solver import SSolver
from bap.ti_solver import TISolver

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='main',
        description='Main solver programme for multiple BAP models'
    )

    parser.add_argument(
        '-i', '--instance', action='store', help='Path to the instance file')
    parser.add_argument(
        '-m', '--model', action='store', help='Model to use',
        choices=('pa', 'rp', 's', 'ti'))
    parser.add_argument(
        '-t', '--truncate', action='store', type=int,
        help='Truncate instance to the first n ships')
    parser.add_argument(
        '-x', '--cut', action='store', type=str,
        help='Comma-separated list of ship indices to retain')
    parser.add_argument(
        '-s', '--starting-solution', action='store', type=str,
        help='File containing a starting solution')
    parser.add_argument(
        '-f', '--fix-starting', action='store_true',
        help='If the flag is given, the starting solution is fied rather than used as a hint')
    parser.add_argument(
        '-z', '--compute-iis', action='store_true',
        help='If the flag is given and the model is unfeasible, compute the IIS')
    parser.add_argument(
        '-p', '--print', action='store_true',
        help='If the flag is given, print instance data')
    parser.add_argument(
        '-o', '--output-folder', action='store', type=str,
        help='Output folder', default='results')
    
    args = parser.parse_args()
    
    i = Instance(instance_file=args.instance)

    if args.truncate is not None:
        i.truncate(n_ships=args.truncate)

    if args.cut is not None:
        ships = [int(i) for i in args.cut.split(',')]
        i.reduce(ships=ships)

    if args.print is not None and args.print:
        i.print()

    if args.model == 'pa':
        m = PASolver(instance=i, output_folder=args.output_folder)
    elif args.model == 'rp':
        m = RPSolver(instance=i, output_folder=args.output_folder)
    elif args.model == 's':
        m = SSolver(instance=i, output_folder=args.output_folder)
    elif args.model == 'ti':
        m = TISolver(instance=i, output_folder=args.output_folder)
    else:
        raise NotImplementedError(f"Model {args.model} not recognised")
    
    if args.starting_solution is not None:
        fix = (args.fix_starting is not None) and args.fix_starting
        print(f"Using a starting solution. Fix = {fix}.")
        m.load_initial(initial_file=args.starting_solution, fix=fix)
    
    m.solve(compute_iis=args.compute_iis)