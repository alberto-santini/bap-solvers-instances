from .instance import Instance
from typing import Union
from gurobipy import Model, tupledict, Var, GRB
from os import path
from datetime import datetime
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import json

class PASolver:
    instance: Instance
    output_folder: str
    grb_timelimit: float

    time: list
    m: Model
    x: tupledict
    y: tupledict
    c: tupledict
    makespan: Var

    c_lb: dict
    x_ijt: list
    y_ijt: list

    start_ti: datetime

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
        self.c_lb = dict()

        for i in self.instance.ships:
            self.c_lb[i] = self.instance.arrival_time[i] + self.instance.processing_time[i] - 1

    def __build_model(self) -> None:
        if self.instance.n_periods is not None:
            T = self.instance.n_periods            
        else:
            T = int(max(self.c_lb.values()) * 1.5)

        M = 1e4
        self.time = range(T)

        self.x_ijt = [
            (i, j, t)
            for i in self.instance.ships
            for j in self.instance.berths
            for t in self.time if t >= self.instance.arrival_time[i]
        ]

        self.y_ijt = [
            (i, j, t)
            for i in self.instance.ships
            for j in self.instance.berths if self.instance.berth_start(j) + self.instance.ship_length[i] <= self.instance.quay_length
            for t in self.time if t >= self.instance.arrival_time[i] and t <= T - self.instance.processing_time[i] + 1
        ]

        self.m = Model()
        self.x = self.m.addVars(self.x_ijt, vtype=GRB.BINARY, name='x')
        self.y = self.m.addVars(self.y_ijt, vtype=GRB.BINARY, name='y')
        self.c = self.m.addVars(self.instance.ships, vtype=GRB.CONTINUOUS, lb=self.c_lb, ub=GRB.INFINITY, name='c')
        self.makespan = self.m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=GRB.INFINITY, obj=1, name='makespan')

        self.m.addConstrs((
            self.makespan >= self.c[i] for i in self.instance.ships
        ), name='set_makespan')
        
        self.m.addConstrs((
            self.c[i] == self.instance.processing_time[i] + \
            sum(
                sum(
                    t * self.y[i,j,t]
                    for t in range(self.instance.arrival_time[i], T - self.instance.processing_time[i] + 2)
                    if (i, j, t) in self.y_ijt
                )
                for j in self.instance.berths
                if self.instance.berth_start(j) + self.instance.ship_length[i] <= self.instance.quay_length
            ) - 1
            for i in self.instance.ships
        ), name='set_c')

        self.m.addConstrs((
            self.y.sum(i, '*', '*') == 1
            for i in self.instance.ships
        ), name='each_ship_one_berth')

        self.m.addConstrs((
            sum(
                sum(
                    self.x[i,m,n]
                    for n in range(t, T)
                    if n < t + self.instance.processing_time[i] and (i,m,n) in self.x_ijt
                )
                for m in range(j, self.instance.n_berths)
                if m < j + self.instance.ship_length_in_n_berths(i)
            ) >=
            self.instance.processing_time[i] * self.instance.ship_length_in_n_berths(i) + \
            (self.y[i,j,t] - 1) * M
            for i in self.instance.ships
            for j in self.instance.berths
            for t in self.time if t >= self.instance.arrival_time[i]
            if (i,j,t) in self.y_ijt
        ), name='link_x_y')

        self.m.addConstrs((
            self.x.sum('*', j, t) <= 1
            for j in self.instance.berths
            for t in self.time
        ), name='no_overlap')

    def load_initial(self, initial_file: str, fix: bool = False) -> None:
        with open(initial_file) as f:
            init = json.load(f)

        for data in init['ships']:
            i = data['data_ship_id']
            j = self.instance.rightmost_berth_containing_position(data['mooring_position'])
            t = data['mooring_time']

            if (i,j,t) in self.y_ijt:
                if fix:
                    self.y[i,j,t].LB = self.y[i,j,t].UB = 1
                else:
                    self.y[i,j,t].Start = 1

    def solve(self, compute_iis: bool = False) -> None:
        basename = path.splitext(path.basename(self.instance.instance_file))[0]
        self.m.setParam(GRB.Param.TimeLimit, self.grb_timelimit)
        self.m.setParam(GRB.Param.Threads, 1)
        self.m.optimize()

        end_ti = datetime.now()
        elapsed_time = (end_ti - self.start_ti).total_seconds()

        if self.m.SolCount > 0:
            results = dict(
                feasible=True,
                makespan=self.m.ObjVal,
                dual_bound=self.m.ObjBound,
                solve_time=self.m.Runtime,
                total_time=elapsed_time,
                ships=list()
            )

            for i in self.instance.ships:
                for j in self.instance.berths:
                    found = False
                    for t in self.time:
                        if (i,j,t) not in self.y_ijt:
                            continue

                        if self.y[i,j,t].X > 0.5:
                            results['ships'].append(dict(
                                data_ship_id=i,
                                data_arrival_time=self.instance.arrival_time[i],
                                data_handling_time=self.instance.processing_time[i],
                                data_ship_length=self.instance.ship_length[i],
                                data_ship_length_in_berths=self.instance.ship_length_in_n_berths(i),
                                mooring_time=t,
                                completion_time=t + self.instance.processing_time[i] - 1,
                                mooring_position=self.instance.berth_start(j),
                                mooring_berth=j
                            ))
                            found = True
                            break
                    if found:
                        break
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
            print('Infeasible model (PA)')
            self.instance.print()

            if compute_iis:
                self.m.computeIIS()
                model_file = 'infeas-' + basename + '-pamodel.lp'
                ilp_file = 'infeas-' + basename + '-paiis.ilp'

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

        results_file = self.output_folder + '/results-' + basename + '-pasolver.json'

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def print_variables(self) -> None:
        fig, ax = plt.subplots(figsize=(10,10))

        min_y, max_y = 9999, 0

        for idx, i in enumerate(self.instance.ships):
            x_xs, x_ys = list(), list()
            y_xs, y_ys = list(), list()

            for j in self.instance.berths:
                for t in self.instance.time_horizon:
                    if (i,j,t) in self.x_ijt:
                        if self.x[i,j,t].X > 0.5:
                            x_xs.append(j)
                            x_ys.append(t)

                            if t < min_y:
                                min_y = t
                            if t > max_y:
                                max_y = t
                    if (i,j,t) in self.y_ijt:
                        if self.y[i,j,t].X > 0.5:
                            y_xs.append(j)
                            y_ys.append(t)

                            if t < min_y:
                                min_y = t
                            if t > max_y:
                                max_y = t
            
            ax.scatter(x_xs, x_ys, label=f"Ship {i}. Variables x.", color=f"C{idx}")
            ax.scatter(y_xs, y_ys, label=f"Ship {i}. Variables y.", color=f"C{idx}", s=100, edgecolor='red')
            ax.add_patch(Rectangle(xy=(y_xs[0], y_ys[0]), width=self.instance.ship_length_in_n_berths(i), height=self.instance.processing_time[i], facecolor='none', edgecolor=f"C{idx}"))
            ax.axhline(y=self.instance.arrival_time[i], color=f"C{idx}", linestyle=':', alpha=0.75, label=f"Ship {i}. Arrival time.")
        
        ax.legend(loc='upper right', bbox_to_anchor=(1.275,1))
        ax.set_xticks(self.instance.berths)
        ax.set_yticks(range(min_y, max_y + 2))
        ax.xaxis.grid(which='major', color='black', linestyle='--', alpha=0.05)
        ax.yaxis.grid(which='major', color='black', linestyle='--', alpha=0.05)
        ax.set_axisbelow(True)

        basename = path.splitext(path.basename(self.instance.instance_file))[0]
        fig.savefig(self.output_folder + '/variables-' + basename + '-pasolver.png', bbox_inches='tight', dpi=96)