## Instances, Best Known Solutions and Models for a Berth Allocation Problem

This repository contains instances, solutions, and models for a Berth Allocation Problem with the following characteristics:

* Temporal aspect: dynamic (not all ships are available at the beginning of the time horizon).
* Spatial aspect: hybrid (some ship occupies more than one berth).
* Handling aspect: fixed (the ship handling time depends on the ship but not on the assigned berth).
* Objective function: minimising the total completion time.

This variant of the problem is denoted as `hyb|dyn|fix|max(comp)` in the notation introuced in: Bierwirth, Christian and Frank Meisel (2015). “A follow-up survey of berth allocation and quay crane scheduling problems in container terminals”. In: European Journal of Operational Research 244, pp. 675–689.

### Instances

The instances were created starting from data made available by the [Port of Barcelona](https://opendata.portdebarcelona.cat/), Spain.
We used data relative to quays 24B (APM Terminals) and 36A (Barcelona Europe South Terminal) and describing container ship movements during 2024.
Instances are in folder `instances/hyb_dyn_fix_max-comp`.
The file name is `bcn_<quay>_<startweek>.json`, where `<quay>` is either 24B or 36A and `<startweek>` refers to the first week of the year 2024 included in the data.
To avoid inconsistencies with ships starting service in 2023 and ending it in 2024 or starting in 2024 and ending in 2025, we do not use the first and last week of the year and `<startweek>` goes from 2 to 50.

The instances are in Json format, with the following structure:

* `n_ships`: number of ships arriving over the time horizon.
* `n_berths`: number of available berths.
* `n_periods`: number of periods in the time horizon. Solvers might not use this information. It is expressed in the same unit of measure as the arrival and handling times.
* `berth_len`: an array with one entry per berth. It is the berth length, expressed in the same unit of measure as the ship length (see below).
* `arrival_time`: an array with one entry per ship. It is the ship arrival time, expressed in the same unit of measure as the time horizon length (see above) and the handling times (see below).
* `handling_time`: an array with one entry per ship. It is the ship handling time, i.e., the time necessary for loading and unloading operations. It is expressed in the same unit of measure as the time horizon length and the arrival time (see above).
* `ship_len`: an array with one entry per ship. It is the ship length, expressed in the same unit of measure as the berth length (see above).

This format can be extended for other Berth Allocation Problems.

* Attribute `handling_time` can be turned into a two-dimensional array indexed by ship and berth, containing the ship's handling time when mooring with the leftmost end at the given berth.
* One can use an additional attribute `ship_importance` if ships should have different priorities when it comes to berthing.

### Utilities

We provide code to read the instances for both `C++` and `Python`, respectively in folders `src/cpp` and `src/python`.
You can use this code in your repository to jump straight to the algorithm development phase, without worring about the "boring" data reading part.
For example, the following C++ code reads an instance.

```cpp
#include "Instance.h"

int main() {
    using namespace bap;
    const auto instance = Instance{"/path/to/bcn_36A_6.json"};
}
```

### Models implemented

The solvers are in folder `solvers/bap`.
They are implemented in Python using Gurobi.
The four models that are implemented are:

* The *Relative Position* and *Position Assignment* formulations presented in the following paper: Y. Guan and R. K. Cheung, “The berth allocation problem: models and
solution methods,” OR Spectrum, vol. 26, pp. 75–92, 2004.
* The *Sequence-variables* and *Time Index* formulations presented in the following paper: A. Ernst, C. Oguz, G. Singh, and G. Taherkhani, “Mathematical models
for the berth allocation problem in dry bulk terminals,” Journal of Scheduling, vol. 20, pp. 459–473, 2017.

### Citation

You can solve this repository via Zenodo:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11180306.svg)](https://doi.org/10.5281/zenodo.11180306)

```bib
@misc{bap_github,
    title={Instances, Best Known Solutions and Models for a Berth Allocation Problem},
    author={Santini, Alberto},
    date={2024-05-12},
    howpublished={Github repository},
    doi={10.5281/zenodo.11180306},
    url={https://github.com/alberto-santini/bap-solvers-instances/}
}
```

### License

The code in folder `solvers` is provided under the GNU General Public License v3.
See the `LICENSE` file.
