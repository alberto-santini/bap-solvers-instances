from os import path
from typing import List
from math import ceil
from typing import Optional

NEED_LONGER_TH_FILE = '../instances/longer_th.txt'

class Instance:
    instance_file: str
    n_ships: int
    n_berths: int
    n_periods: Optional[int]
    ships: list
    berths: list
    arrival_time: dict
    ship_length: dict
    processing_time: dict
    berth_length: dict
    quay_lenght: int
    time_horizon: Optional[list]

    def __init__(self, instance_file: str):
        if not path.exists(instance_file):
            if '.csv' not in instance_file:
                instance_file += '.csv'
            if 'instances/' not in instance_file:
                instance_file = f"../instances/source_ernst/{instance_file}"

            if not path.exists(instance_file):
                raise FileNotFoundError(f"Instance file not found: {instance_file}")
        
        self.instance_file = instance_file
        self.__read_instance()

    def __read_instance(self) -> None:
        if path.splitext(self.instance_file)[-1] == '.txt':
            self.__read_txt_instance()
        elif path.splitext(self.instance_file)[-1] == '.csv':
            self.__read_csv_instance()
        else:
            raise RuntimeError(f"File format not recognised for {self.instance_file}")
        
    def __read_csv_instance(self)-> None:
        with open(self.instance_file) as f:
            self.n_ships = int(f.readline().split(',')[1])
            self.ships = range(self.n_ships)

            skip = f.readline()
            assert 'Begin' in skip

            skip = f.readline()
            assert 'End' in skip

            self.processing_time = [int(x) for x in f.readline().split(',')[1:]]
            self.ship_length = [float(x) for x in f.readline().split(',')[1:]]
            self.arrival_time = [int(x) for x in f.readline().split(',')[1:]]
            self.quay_length = 3
            self.n_berths = 12
            self.berths = range(self.n_berths)
            self.berth_length = [0.25] * 12

            def list_to_dict(l: list) -> dict:
                return {i: x for i, x in enumerate(l)}

            self.processing_time = list_to_dict(self.processing_time)
            self.ship_length = list_to_dict(self.ship_length)
            self.arrival_time = list_to_dict(self.arrival_time)
            self.berth_length = list_to_dict(self.berth_length)

            max_ah = max([a + h for a, h in zip(self.arrival_time, self.processing_time)])
            self.n_periods = self.__csv_instance_n_periods()
            self.n_periods = max(self.n_periods, max_ah)
            self.time_horizon = range(self.n_periods)

    def __csv_instance_n_periods(self) -> int:
        # I need to enlarge the time horizon stated in the Ernest paper, because
        # there are instances that are not feasible otherwise.
        # + 16 for 168 time instants
        # + 32 for 336 time instants

        if self.n_ships < 32:
            n_periods = 168 + 16 # Some instances are infeasible with 168
        else:
            n_periods = 336 + 32 # Some instances are infeasible with 336

        # Even with the above adjustments, some instances need more time.
        # The reason is that the time horizon in the paper refers to the processing
        # start time of the last ship, not the completion time.
        
        if path.exists(NEED_LONGER_TH_FILE):
            with open(NEED_LONGER_TH_FILE) as f:
                instances = f.readlines()

            if any([instance in self.instance_file for instance in instances]):
                n_periods = int(n_periods * 1.25)
            
        return n_periods

    def __read_txt_instance(self) -> None:
        with open(self.instance_file) as f:
            self.n_ships = int(f.readline())
            self.ships = list(range(self.n_ships))

            self.arrival_time = dict()
            self.ship_length = dict()
            self.processing_time = dict()

            for i in self.ships:
                _, at, l, pt, _, _ = f.readline().split()
                self.arrival_time[i] = int(at)
                self.ship_length[i] = int(l)
                self.processing_time[i] = int(pt)

            self.n_berths = int(f.readline())
            self.berths = list(range(self.n_berths))
            blengths = [int(l) for l in f.readline().split()]

            assert len(blengths) == self.n_berths

            self.berth_length = dict()

            for j in self.berths:
                self.berth_length[j] = blengths[j]

            self.quay_lenght = sum(blengths)
            self.n_periods = None
            self.time_horizon = None

    def truncate(self, n_ships: int) -> None:
        self.reduce(list(range(n_ships)))

    def reduce(self, ships: List[int]) -> None:
        if any(i not in self.ships for i in ships):
            raise ValueError('All indices must be valid ship indices when using reduce')

        self.ships = ships
        self.arrival_time = {ship: at for ship, at in self.arrival_time.items() if ship in self.ships}
        self.ship_length = {ship: sl for ship, sl in self.ship_length.items() if ship in self.ships}
        self.processing_time = {ship: pt for ship, pt in self.processing_time.items() if ship in self.ships}
        self.n_ships = len(self.ships)

    def berth_start(self, berth: int) -> int:
        return sum(self.berth_length[i] for i in range(berth))
    
    def rightmost_berth_containing_position(self, pos: float) -> int:
        for i in self.berths:
            if self.berth_start(i) > pos:
                assert i > 0
                return i - 1
        else:
            raise RuntimeError(f"Cannot find rightmost berth for position {pos}")
    
    def ship_length_in_n_berths(self, ship: int) -> int:
        assert all(x == self.berth_length[0] for x in self.berth_length.values()), \
            f"To measure a ship length in terms of the number of berths it occupies, all berths must be of the same length."
        
        return int(ceil(self.ship_length[ship] / self.berth_length[0]))
    
    def print(self) -> None:
        print(f"Number of ships: {self.n_ships}")
        print(f"Number of berths: {self.n_berths}")
        
        if self.n_periods is not None:
            print(f"Number of periods: {self.n_periods}\n")

        for i in self.ships:
            print(f"=== Ship {i} ===")
            print(f"\tArrival time = {self.arrival_time[i]}")
            print(f"\tLength = {self.ship_length[i]} ({self.ship_length_in_n_berths(i)} berths)")
            print(f"\tHandling time = {self.processing_time[i]}")