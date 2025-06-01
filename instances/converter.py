from pathlib import Path
from glob import glob
from random import randint
from dataclasses import dataclass
from typing import List
from os.path import basename, splitext
import json


@dataclass
class Instance:
    n_ships: int
    n_berths: int
    n_periods: int
    ship_length: List[int]
    ship_arrival: List[int]
    ship_handling: List[int]

    def to_dict(self) -> dict:
        return vars(self)


def read_lr_instance(file: str) -> Instance:
    with open(file) as f:
        n_ships = int(f.readline().strip())
        n_berths = int(f.readline().strip())
        n_periods = 600
        ship_length = [randint(1, 3) for _ in range(n_ships)]
        ship_arrival = [int(x.strip()) - 1 for x in f.readline().strip().split(' ')]
        ship_handling = list()

        for _ in range(n_ships):
            ht = map(int, f.readline().strip().split(' '))
            ht = [h for h in ht if h < 1000] # There are some 99999 values in the files

            if len(ht) > 0:
                ship_handling.append(ht[0])
            else:
                ship_handling.append(36)

        return Instance(n_ships=n_ships, n_berths=n_berths, n_periods=n_periods,
                        ship_length=ship_length, ship_arrival=ship_arrival, ship_handling=ship_handling)


if __name__ == '__main__':
    Path('./Santini').mkdir(exist_ok=True)

    for inst in glob('Lalla_Ruiz_Original/*.txt'):
        name = splitext(basename(inst))[0]
        new_name = f"Santini/{name}.json"
        inst = read_lr_instance(file=inst)

        with open(new_name, mode='w') as f:
            json.dump(inst.to_dict(), f, indent=2)
