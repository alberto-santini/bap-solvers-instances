## Solvers and Instances for the Berth Allocation Problem

This repository contains code and instances relative to the manuscript ``A Note on Solving the Decision Version of the Berth Allocation Problem via Selective Graph Coloring''.

### Models implemented

The solvers are in folder `solvers/bap`.
They are implemented in Python using Gurobi.
The four models that are implemented are:

* The *Relative Position* and *Position Assignment* formulations presented in the following paper: Y. Guan and R. K. Cheung, “The berth allocation problem: models and
solution methods,” OR Spectrum, vol. 26, pp. 75–92, 2004.
* The *Sequence-variables* and *Time Index* formulations presented in the following paper: A. Ernst, C. Oguz, G. Singh, and G. Taherkhani, “Mathematical models
for the berth allocation problem in dry bulk terminals,” Journal of Scheduling, vol. 20, pp. 459–473, 2017.

### Instances

The instances used are a subset of the [Ernst instances](https://andreas-ernst.github.io/Mathprog-ORlib/info/readmeBAP.html).
They are in folder `instances`, in their original `.csv` format.

### Citation

You can solve this repository via Zenodo:

```bib
@misc{bap_github,
    title={Solvers and Instances for the Berth Allocation Problem},
    author={Santini, Alberto},
    date={2024-05-12},
    howpublished={Github repository},
    doi={???},
    url={https://github.com/alberto-santini/bap-solvers-instances/}
}
```

### License

The code in folder `solvers` is provided under the GNU General Public License v3.
See the `LICENSE` file.