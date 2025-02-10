# Solvers and Instances for the Berth Allocation Problem

This repository contains code and instances relative to the manuscript ``Solving the Decision Version of the Berth Allocation Problem via Selective Graph Coloring''.

## Algorithms

### Proposed algorithm

The solver presented in the paper and based on the Selective Graph Colouring Problem is in folder `bap_sgcp`.
It is coded in `C++` and relies on four external libraries:

* The SGCP solver [alberto-santini/selective-graph-colouring](https://github.com/).
* The maximum-weight independent set solver [heldstephan/exactcolors](https://github.com/heldstephan/exactcolors).
* The [Cplex](https://www.ibm.com/products/ilog-cplex-optimization-studio) solver.
* The [Gurobi](https://www.gurobi.com/) solver.

### Other formulations

Solvers for other five formulations are in folder `solvers/bap`.
They are implemented in Python using Gurobi.
The five implemented models are:

* The *Relative Position* and *Position Assignment* formulations presented in the following paper: Y. Guan and R. K. Cheung, "The berth allocation problem: models and solution methods", OR Spectrum, vol. 26, pp. 75–92, 2004.
* The *Sequence-variables* and *Time Index* formulations presented in the following paper: A. Ernst, C. Oguz, G. Singh, and G. Taherkhani, "Mathematical models for the berth allocation problem in dry bulk terminals", Journal of Scheduling, vol. 20, pp. 459–473, 2017.
* The *Generalised Set Partitioning Problem* formulation presented in the following thesis: C. G. Christensen and Holst C. T., "Allokering af kajplads i containerhavne", Thesis number Imm-m.sc.-2008-37, MA thesis, Danish Technical University, 2018.

### Instances

The instances are a modified version of those introduced in the following paper: E. Lalla-Ruiz, B. Melián-Batista, and J. M. Moreno-Vega. "Artificial intelligence hybrid heuristic based on tabu search for the dynamic berth allocation problem", Engineering Applications of Artificial Intelligence, vol. 25(6), pp. 1132–1141, 2012.

They have been adapted by adding different ship lengths because, in the original version, all ships occupied exactly one berth.
The format has also been changed to `json`.
The original instances are in folder [instances/Lalla_Ruiz_Original](instances/Lalla_Ruiz_Original/) and the new instances are in folder [instances/Santini](instances/Santini/).

### Citation

You can cite this repository via Zenodo:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11180306.svg)](https://doi.org/10.5281/zenodo.11180306)

```bib
@misc{bap_github,
    title={Solvers and Instances for the Berth Allocation Problem},
    author={Santini, Alberto},
    date={2024-05-12},
    howpublished={Github repository},
    doi={10.5281/zenodo.11180306},
    url={https://github.com/alberto-santini/bap-solvers-instances/}
}
```

### License

The code in folders `bap_sgcp` and `solvers` is provided under the GNU General Public License v3.
See the `LICENSE` file.
