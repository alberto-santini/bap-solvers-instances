from __future__ import annotations
from os import path
from typing import List, Dict, Optional
from math import ceil, floor


class Instance:
    instance_file: str
    n_ships: int
    n_berths: int
    n_periods: int
    ships: List[int]
    berths: List[int]
    arrival_time: Dict[int, int]
    ship_length: Dict[int, float]
    processing_time: Dict[int, int]
    berth_length: Dict[int, float]
    quay_lenght: int
    time_horizon: List[int]


    def __init__(self, instance_file: Optional[str]):
        if instance_file is not None:
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
        if path.splitext(self.instance_file)[-1] == '.csv':
            self.__read_csv_instance()
        else:
            raise RuntimeError(f"File format not recognised for {self.instance_file}")
        
    def __read_csv_instance(self)-> None:
        with open(self.instance_file) as f:
            self.n_ships = int(f.readline().split(',')[1])
            self.ships = list(range(self.n_ships))

            skip = f.readline()
            assert 'Begin' in skip

            skip = f.readline()
            assert 'End' in skip

            processing_time = [int(x) for x in f.readline().split(',')[1:]]
            ship_length = [float(x) for x in f.readline().split(',')[1:]]
            arrival_time = [int(x) for x in f.readline().split(',')[1:]]
            self.quay_length = 3
            self.n_berths = 12
            self.berths = list(range(self.n_berths))
            berth_length = [0.25] * 12

            def list_to_dict(l: list) -> dict:
                return {i: x for i, x in enumerate(l)}

            self.processing_time = list_to_dict(processing_time)
            self.ship_length = list_to_dict(ship_length)
            self.arrival_time = list_to_dict(arrival_time)
            self.berth_length = list_to_dict(berth_length)

            max_ah = max([a + h for a, h in zip(self.arrival_time, self.processing_time)])
            self.n_periods = self.__csv_instance_n_periods()
            self.n_periods = max(self.n_periods, max_ah)
            self.time_horizon = list(range(self.n_periods))

    def __csv_instance_n_periods(self) -> int:
        # I need to enlarge the time horizon stated in the Ernest paper, because
        # there are instances that are not feasible otherwise.
        # The reason is that the time horizon in the paper refers to the processing
        # start time of the last ship, not the completion time.

        if self.n_ships < 32:
            n_periods = 168
        else:
            n_periods = 336
        
        n_periods = int(n_periods * 1.25)
            
        return n_periods

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

    def berth_start(self, berth: int) -> float:
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

    def discretise_time_conservative(self, granularity: int) -> Instance:
        new = Instance(instance_file=None)
        new.n_ships = self.n_ships
        new.n_berths = self.n_berths
        new.n_periods = int(floor(self.n_periods / granularity))
        new.ships = self.ships.copy()
        new.berths = self.berths.copy()
        new.arrival_time = {i: int(ceil(arr / granularity)) for i, arr in self.arrival_time.items()}
        new.ship_length = self.ship_length.copy()
        new.processing_time = {i: int(ceil(pro / granularity)) for i, pro in self.processing_time.items()}
        new.berth_length = self.berth_length.copy()
        new.quay_lenght = self.quay_lenght
        new.time_horizon = list(range(new.n_periods))
        new.instance_file = self.instance_file + f" - Granularity: {granularity}"

        return new
    
    def discretise_time_aggressive(self, granularity: int) -> Instance:
        new = Instance(instance_file=None)
        new.n_ships = self.n_ships
        new.n_berths = self.n_berths
        new.n_periods = int(ceil(self.n_periods / granularity))
        new.ships = self.ships.copy()
        new.berths = self.berths.copy()
        new.arrival_time = {i: int(floor(arr / granularity)) for i, arr in self.arrival_time.items()}
        new.ship_length = self.ship_length.copy()
        new.processing_time = {i: int(floor(pro / granularity)) for i, pro in self.processing_time.items()}
        new.berth_length = self.berth_length.copy()
        new.quay_lenght = self.quay_lenght
        new.time_horizon = list(range(new.n_periods))
        new.instance_file = self.instance_file + f" - Granularity: {granularity}"

        return new