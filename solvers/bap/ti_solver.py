from .instance import Instance
from typing import Union, List, Dict
from gurobipy import Model, tupledict, Var, GRB
from datetime import datetime
from os import path
import json


class TISolver:
    instance: Instance
    output_folder: str
    grb_timelimit: float

    T: int
    time: List[int]

    m: Model
    x: tupledict
    I: tupledict
    s: tupledict
    c: tupledict
    y: tupledict
    q: tupledict
    makespan: Var

    s_lb: Dict[int, int]
    s_ub: Dict[int, int]
    c_lb: Dict[int, int]
    y_ub: Dict[int, int]

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

    def __compute_bounds(self):
        if self.instance.n_periods is not None:
            self.T = self.instance.n_periods
        else:
            self.T = int(max(
                [a + h for a, h in zip(self.instance.arrival_time, self.instance.processing_time)]
            ) * 1.5)
        
        self.time = list(range(self.T))

        self.s_lb = {
            i: self.instance.arrival_time[i] for i in self.instance.ships
        }

        self.s_ub = {
            i: self.T - self.instance.processing_time[i] for i in self.instance.ships
        }

        self.c_lb = {
            i: self.instance.arrival_time[i] + self.instance.processing_time[i] - 1 for i in self.instance.ships
        }

        self.y_ub = {
            i: self.instance.n_berths - self.instance.ship_length_in_n_berths(i) for i in self.instance.ships
        }

    def __build_model(self):
        M = 1e4
        T = self.instance.n_periods
        diff_ships = [(i1, i2) for i1 in self.instance.ships for i2 in self.instance.ships if i1 != i2]

        self.m = Model()
        self.x = self.m.addVars(diff_ships, vtype=GRB.BINARY, name='x')
        self.I = self.m.addVars(diff_ships, vtype=GRB.BINARY, name='I')
        self.s = self.m.addVars(self.instance.ships, vtype=GRB.INTEGER, lb=self.s_lb, ub=self.s_ub, name='s')
        self.c = self.m.addVars(self.instance.ships, vtype=GRB.CONTINUOUS, lb=self.c_lb, ub=self.T, name='c')
        self.y = self.m.addVars(self.instance.ships, vtype=GRB.INTEGER, lb=0, ub=self.y_ub, name='y')
        self.q = self.m.addVars(self.instance.ships, self.instance.time_horizon, vtype=GRB.BINARY, name='q')
        self.makespan = self.m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=self.T, obj=1, name='makespan')

        for i in self.instance.ships:
            self.q[i, T-1].LB = 1

        self.m.addConstrs((
            self.makespan >= self.c[i] for i in self.instance.ships
        ), name='set_makespan')

        self.m.addConstrs((
            self.c[i] == self.s[i] + self.instance.processing_time[i] - 1
            for i in self.instance.ships
        ), name='set_c')

        self.m.addConstrs((
            self.x[i1, i2] + self.x[i2, i1] + self.I[i1, i2] + self.I[i2, i1] == 1
            for i1, i2 in diff_ships
        ), name='max_one_x_I')

        self.m.addConstrs((
            self.s[i2] >= self.c[i1] + 1 - M * (1 - self.x[i1,i2])
            for i1, i2 in diff_ships
        ), name='link_sc_x')

        self.m.addConstrs((
            self.y[i2] >= self.instance.ship_length_in_n_berths(i1) * self.I[i1,i2] +\
                self.y[i1] -\
                (self.instance.n_berths - self.instance.ship_length_in_n_berths(i1)) * (1 - self.I[i1, i2])
            for i1, i2 in diff_ships
        ), name='link_y_I')

        self.m.addConstrs((
            self.c[i] == sum(
                t * (self.q[i, t+1] - self.q[i,t])
                for t in range(self.instance.arrival_time[i] + self.instance.processing_time[i] - 1, T - 1)
            ) for i in self.instance.ships
        ), name='link_c_q')

        self.m.addConstrs((
            self.q[i,t+1] >= self.q[i,t]
            for i in self.instance.ships
            for t in range(T - 1)
        ), name='nondecreasing_q')

        self.m.addConstrs((
            sum(
                self.instance.ship_length_in_n_berths(i) * \
                (self.q[i, t + self.instance.processing_time[i]] - self.q[i,t])
                for i in self.instance.ships
                if t + self.instance.processing_time[i] < self.instance.n_periods
            ) <= self.instance.n_berths
            for t in self.instance.time_horizon
        ), name='ships_fit_in_quay')

    def load_initial(self, initial_file: str, fix: bool = False) -> None:
        with open(initial_file) as f:
            init = json.load(f)

        for data in init['ships']:
            i = data['data_ship_id']
            if fix:
                self.s[i].LB = self.s[i].UB = data['mooring_time']
                self.y[i].LB = self.y[i].UB = data['mooring_berth']
            else:
                self.s[i].Start = data['mooring_time']
                self.y[i].Start = data['mooring_berth']

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
                ships = list()
            )

            for i in self.instance.ships:
                mooring_berth = int(self.y[i].X)
                results['ships'].append(dict(
                    data_ship_id=i,
                    data_arrival_time=self.instance.arrival_time[i],
                    data_handling_time=self.instance.processing_time[i],
                    data_ship_length=self.instance.ship_length[i],
                    data_ship_length_in_berths=self.instance.ship_length_in_n_berths(i),
                    mooring_time=int(self.s[i].X),
                    completion_time=int(self.c[i].X),
                    mooring_position=self.instance.berth_start(mooring_berth),
                    mooring_berth=mooring_berth
                ))
        elif self.m.Status != GRB.INFEASIBLE:
            results = dict(
                feasible=True,
                makespan=None,
                dual_bound=self.m.ObjBound,
                solve_time=self.m.RunTime,
                total_time=elapsed_time,
                ships=None
            )
        else:
            if compute_iis:
                self.m.computeIIS()
                model_file = 'infeas-' + basename + '-smodel.lp'
                ilp_file = 'infeas-' + basename + '-smodel.ilp'

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

        results_file = self.output_folder + '/results-' + basename + '-tisolver.json'

        with open(results_file, mode='w') as f:
            json.dump(results, f, indent=2)
