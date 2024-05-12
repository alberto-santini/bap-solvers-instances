from .instance import Instance
from typing import Union
from gurobipy import Model, tupledict, Var, GRB
from datetime import datetime
from os import path
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import json

class RPSolver:
    instance: Instance
    output_folder: str
    grb_timelimit: float

    m: Model
    u: tupledict
    v: tupledict
    c: tupledict
    sigma: tupledict
    delta: tupledict
    makespan: Var

    u_lb: dict
    u_ub: dict
    c_lb: dict
    v_ub: dict

    start_ti: datetime

    ij: list

    def __init__(self, instance: Union[str, Instance], output_folder: str, **kwargs):
        if type(instance) is Instance:
            self.instance = instance
        elif type(instance) is str:
            self.instance = Instance(instance_file=instance)
        else:
            raise TypeError(f"Type not supported for instance: {type(instance)}")
        
        self.output_folder = output_folder

        self.start_ti = datetime.now()
        self.__compute_bounds()
        self.__build_model()

        self.grb_timelimit = kwargs.get('grb_timelimit', 3600.0)

    def __compute_bounds(self) -> None:
        self.u_lb = dict()
        self.u_ub = dict()
        self.c_lb = dict()
        self.v_ub = dict()

        for i in self.instance.ships:
            self.u_lb[i] = self.instance.arrival_time[i]
            self.u_ub[i] = self.instance.n_periods - self.instance.processing_time[i] + 1
            self.c_lb[i] = self.instance.arrival_time[i] + self.instance.processing_time[i] - 1
            self.v_ub[i] = self.instance.n_berths - self.instance.ship_length_in_n_berths(i)

    def __build_model(self) -> None:
        if self.instance.n_periods is not None:
            M = self.instance.n_periods
        else:
            M = max(self.c_lb.values()) * 1.5

        self.ij = [(i, j) for i in self.instance.ships for j in self.instance.ships if i != j]

        self.m = Model()
        self.u = self.m.addVars(self.instance.ships, vtype=GRB.INTEGER, lb=self.u_lb, ub=self.u_ub, name='u')
        self.v = self.m.addVars(self.instance.ships, vtype=GRB.INTEGER, lb=0, ub=self.v_ub, name='v')
        self.c = self.m.addVars(self.instance.ships, vtype=GRB.CONTINUOUS, lb=self.c_lb, ub=GRB.INFINITY, name='c')
        self.makespan = self.m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=GRB.INFINITY, obj=1, name='makespan')
        self.sigma = self.m.addVars(self.ij, vtype=GRB.BINARY, name='sigma')
        self.delta = self.m.addVars(self.ij, vtype=GRB.BINARY, name='delta')

        self.m.addConstrs((
            self.makespan >= self.c[i] for i in self.instance.ships
        ), name='set_makespan')
        self.m.addConstrs((
            self.c[i] == self.u[i] + self.instance.processing_time[i] - 1 for i in self.instance.ships
        ), name='set_c')

        self.m.addConstrs((
            self.u[j] >= self.u[i] + self.instance.processing_time[i] + (self.sigma[i,j] - 1) * M
            for i, j in self.ij
        ), name='u_sigma_no_overlap')

        self.m.addConstrs((
            self.v[j] >= self.v[i] + self.instance.ship_length_in_n_berths(i) + (self.delta[i,j] - 1) * self.instance.n_berths
            for i, j in self.ij
        ), name='v_delta_no_overlap')

        self.m.addConstrs((
            self.sigma[i,j] + self.sigma[j,i] + self.delta[i,j] + self.delta[j,i] >= 1
            for i, j in self.ij
        ), name='sigma_delta_at_least_one')

        self.m.addConstrs((
            self.sigma[i,j] + self.sigma[j,i] <= 1
            for i, j in self.ij
        ), name='sigma_at_most_one')

        self.m.addConstrs((
            self.delta[i,j] + self.delta[j,i] <= 1
            for i, j in self.ij
        ), name='delta_at_most_one')

    def load_initial(self, initial_file: str, fix: bool = False) -> None:
        with open(initial_file) as f:
            init = json.load(f)

        for data in init['ships']:
            i = data['data_ship_id']
            j = self.instance.rightmost_berth_containing_position(data['mooring_position'])
            t = data['mooring_time']

            if fix:
                self.u[i].LB = self.u[i].UB = t
                self.v[i].LB = self.v[i].UB = j
            else:
                self.u[i].Start = t
                self.v[i].Start = j

    def solve(self, compute_iis: bool = False) -> None:
        basename = path.splitext(path.basename(self.instance.instance_file))[0]
        self.m.setParam(GRB.Param.TimeLimit, self.grb_timelimit)
        self.m.setParam(GRB.Param.Threads, 1)
        self.m.optimize()

        end_ti = datetime.now()
        elapsed_time = (end_ti - self.start_ti).total_seconds()

        if self.m.SolCount > 0:
            ### TMP ###
            # print(f"Variables value:")
            # for i in self.instance.ships:
            #     print(f"u[{i}] = {self.u[i].X:3.1f}, v[{i}] = {self.v[i].X:3.1f}, c[{i}] = {self.c[i].X:3.1f}")
            # for i, j in self.ij:
            #     if self.sigma[i,j].X > 0.5:
            #         print(f"x[{i},{j}] = 1")
            #     if self.delta[i,j].X > 0.5:
            #         print(f"y[{i},{j}] = 1")
            ### /TMP ###

            results = dict(
                feasbile=True,
                makespan=self.m.ObjVal,
                dual_bound=self.m.ObjBound,
                solve_time=self.m.Runtime,
                total_time=elapsed_time,
                ships=list()
            )

            for i in self.instance.ships:
                mooring_berth = int(self.v[i].X)
                results['ships'].append(dict(
                    data_ship_id=i,
                    data_arrival_time=self.instance.arrival_time[i],
                    data_handling_time=self.instance.processing_time[i],
                    data_ship_length=self.instance.ship_length[i],
                    data_ship_length_in_berths=self.instance.ship_length_in_n_berths(i),
                    mooring_time=int(self.u[i].X),
                    completion_time=int(self.u[i].X) + self.instance.processing_time[i] - 1,
                    mooring_position=self.instance.berth_start(mooring_berth),
                    mooring_berth=mooring_berth
                ))
        elif self.m.Status != GRB.INFEASIBLE:
            results = dict(
                feasible=True,
                makespan=None,
                dual_bound=self.m.ObjBound,
                solve_time=self.m.Runtime,
                total_time=elapsed_time,
                ships=None
            )
        else:
            print('Infeasible model (RP)')
            self.instance.print()

            if compute_iis:
                self.m.computeIIS()
                model_file = 'infeas-' + basename + '-rpmodel.lp'
                ilp_file = 'infeas-' + basename + '-rpiis.ilp'

                self.m.write(model_file)
                self.m.write(ilp_file)

                print(f"Infeasible model. Model written to {model_file}. IIS written to {ilp_file}.")

            results = dict(
                feasible=False,
                makespan=None,
                dual_bound=None,
                solve_time=self.m.Runtime,
                total_time=elapsed_time,
                ships=None
            )

        results_file = self.output_folder + '/results-' + basename + '-rpsolver.json'

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def print_variables(self) -> None:
        fig, ax = plt.subplots(figsize=(10,10))

        min_y, max_y = 9999, 0

        for idx, i in enumerate(self.instance.ships):
            j = self.v[i].X
            t = self.u[i].X

            ax.scatter([j], [t], label=f"Ship {i}. Variables (v,u).", color=f"C{idx}", s=100, edgecolor='red')
            ax.add_patch(Rectangle(xy=(j,t), width=self.instance.ship_length_in_n_berths(i), height=self.instance.processing_time[i], facecolor='none', edgecolor=f"C{idx}"))
            ax.axhline(y=self.instance.arrival_time[i], color=f"C{idx}", linestyle=':', alpha=0.75, label=f"Ship {i}. Arrival time.")

            end_t = t + self.instance.processing_time[i] - 1

            if t < min_y:
                min_y = int(t)
            if end_t > max_y:
                max_y = int(end_t)

        ax.legend(loc='upper right', bbox_to_anchor=(1.3,1))
        ax.set_xticks(range(self.instance.n_berths + 1))
        ax.set_yticks(range(min_y, max_y + 2))
        ax.xaxis.grid(which='major', color='black', linestyle='--', alpha=0.05)
        ax.yaxis.grid(which='major', color='black', linestyle='--', alpha=0.05)
        ax.set_axisbelow(True)

        basename = path.splitext(path.basename(self.instance.instance_file))[0]
        fig.savefig(self.output_folder + '/variables-' + basename + '-rpsolver.png', bbox_inches='tight', dpi=96)