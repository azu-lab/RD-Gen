# RD-Gen
<p align="center">
  <img src="https://user-images.githubusercontent.com/55824710/208731888-be3e320a-4148-46cc-983c-f8ee6fe27b9d.png" width="300px">&emsp;&emsp;&emsp;&emsp;<img src="https://user-images.githubusercontent.com/55824710/228999914-af1f5be9-fffe-4b3b-b988-76379389f46b.png" width="420px">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat">
  <img src="https://img.shields.io/badge/-Github-black.svg?logo=github&style=flat"><img src="https://img.shields.io/badge/-pytest passing-gleen.svg">
</p>

## About
**RD-Gen** (random DAG generator considering multi-rate applications for reproducible scheduling evaluation) is a tool for researchers targeting DAGs.

The current release, [v2.0.0](https://github.com/azu-lab/RD-Gen/releases/tag/v2.0.0), is **RD-Gen+**, which extends RD-Gen with conditional (cDAG) and probabilistic (pDAG) branching DAGs through the `Branching` block described in [RD-Gen+ (branching augmentation)](#rd-gen-branching-augmentation). RD-Gen+ is described in the IEEE Access article listed under [Documents](#documents). The RD-Gen of ISORC 2023 remains available as release [v1.0.0](https://github.com/azu-lab/RD-Gen/releases/tag/v1.0.0).
RD-Gen makes the following contributions:
- RD-Gen **extends existing random DAG construction methods**, Fan-in/Fan-out [1] and G(n, p) [2] methods, to meet researchers’ requirements.
- RD-Gen proposes a new **Chain-based method** to flexibly construct state-of-the-art chain-based multi-rate DAGs.
- RD-Gen reduces implementation effort through the **automatic setting of complex parameters** and **batch generation of random DAG sets**.

## Setup flow
```bash
$ git clone https://github.com/azu-lab/RD-Gen.git
$ cd RD-Gen
$ ./setup.bash
```

## Quick start
Sample config files can be used without modification.

### Chain-based method
`$ python3 run_generator.py -c ./sample_config/chain_based/sample_chain_based.yaml`

### Fan-in/Fan-out method
`$ python3 run_generator.py -c ./sample_config/fan_in_fan_out/sample_fan_in_fan_out.yaml`

### G(n, p) method
`$ python3 run_generator.py -c ./sample_config/g_n_p/sample_g_n_p.yaml`

### Branching (cDAG / pDAG) methods
`$ python3 run_generator.py -c ./sample_config/branching/sample_cdag.yaml`

`$ python3 run_generator.py -c ./sample_config/branching/sample_pdag.yaml`

`$ python3 run_generator.py -c ./sample_config/branching/sample_chain_branching.yaml`

## RD-Gen+ (branching augmentation)
RD-Gen+ adds conditional (cDAG) and probabilistic (pDAG) branching constructs to any of the three construction methods through the `Branching` block of `Graph structure`:

| Parameter | Meaning |
|---|---|
| `Probability of branching` | Probability p_b that a regular node is replaced by a branching construct (source nodes, sink nodes and chain heads are never replaced). Drawn once per DAG when given as `Random`. |
| `Maximum nesting depth` | Nesting depth d_b of constructs (0 disables branching). |
| `Maximum branches` | Upper bound w_b >= 2 of the number of branches k ~ U{w_min, ..., w_b}. |
| `Minimum branches` | Lower bound w_min of the number of branches (default 2; set both bounds equal for a fixed k). |
| `Sub-chain length` | (Chain-based only) length of every branch body; default is the remaining chain length. |
| `Firing` | `deterministic` (cDAG) or `probabilistic` (pDAG: every `v_ent` out-edge carries `firing_prob`, every node `marginal_prob`). |
| `Probability distribution` | `dirichlet` (Dirichlet(alpha); uniform on the simplex for alpha = 1) or `uniform-normalize` (normalised U(0, 1), as in Zhao 2025). Both draw from the single seeded generator. |
| `Dirichlet alpha` | Concentration of the Dirichlet sampler (default 1.0). |
| `Accounting` | How total utilization, chain execution time and CCR aggregate over branches: `all` (every branch, default), `expected` (marginal-probability weighted), `max-branch` (heaviest branch of every construct, Zhao 2025 Eq. (10)). |

Entry and exit vertices of a construct are exported as nodes with `node_type` `v_ent` / `v_ext`, `branch_unit_id` and `execution_time` 0; the edges leaving `v_ent` carry `branch_id`. Every generated DAG is verified against the structural constraints of Melani 2015 and Zhao 2025 (acyclicity, proper nesting, no edge entering or leaving a branch body, dominance of `v_ent` and post-dominance of `v_ext`, firing probabilities summing to 1); an instance that fails 100 times is discarded and counted in `generation_stats.yaml`, and `augmentation_retries` is stored on every exported graph.

With branching, `Periodic type` must be `Entry`, `DAG` or `Chain`. `DAG` assigns one period to the whole DAG (graph attribute `period` and the source nodes) and scales the execution times so that the aggregate selected by `Accounting` equals `Total utilization` x period. Chain-based DAGs export `chain_id` on every node; nodes created by a replacement inherit it, so `Periodic type: Chain` also works on branch-augmented chains.

The emitted number of nodes grows with augmentation: `Number of nodes` is the host graph size, and each replacement removes one node and adds k (n_sub + 1) + 2 nodes (G(n, p) / Fan-in/Fan-out hosts, n_sub = max(2, |V| / (k (d_b - d + 1))) at depth d) or k L + 2 nodes (Chain-based hosts, L = `Sub-chain length`).

## Documents
- [wiki](https://github.com/azu-lab/RD-Gen/wiki)
- [API list (for developer)](https://azu-lab.github.io/RD-Gen/)
- RD-Gen+ (release v2.0.0) is presented in the following article:
  - A. Yano and T. Azumi, "RD-Gen+: A Random DAG Generator Unifying Multi-rate, Conditional, and Probabilistic DAGs for Reproducible Scheduling Evaluation", submitted to IEEE Access, 2026 (under review)

    <details>
    <summary>BibTeX</summary>

    ```bibtex
    @unpublished{RD-Gen-plus,
      title={{RD-Gen+}: A Random {DAG} Generator Unifying Multi-rate, Conditional, and Probabilistic {DAGs} for Reproducible Scheduling Evaluation},
      author={Atsushi, Yano and Takuya, Azumi},
      note={Submitted to IEEE Access},
      year={2026}
    }
    ```

    </details>
- RD-Gen (release v1.0.0) is presented in the following paper:
  - A. Yano and T. Azumi, "RD-Gen: Random DAG Generator Considering Multi-rate Applications for Reproducible Scheduling Evaluation", the 26th IEEE International Symposium on Real-Time Distributed Computing (ISORC), 2023
  
    <details>
    <summary>BibTeX</summary>

    ```bibtex
    @inproceedings{RD-Gen,
      title={{RD-Gen}: Random {DAG} Generator Considering Multi-rate Applications for Reproducible Scheduling Evaluation},
      author={Atsushi, Yano and Takuya, Azumi},
      booktitle={Proceedings of the 26th IEEE International Symposium on Real-Time Distributed Computing (ISORC)},
      year={2023},
      organization={IEEE}
    }
    ```

    </details>

## License
RD-Gen and RD-Gen+ are released under the [MIT License](LICENSE).

## References
- [1] R. P. Dick, D. L. Rhodes, and W. Wolf. TGFF: task graphs for free. In Proc. of Workshop on CODES/CASHE, 1998.
- [2] Daniel Cordeiro, Gregory Mounie, Swann Perarnau, Denis Trystram, Jean-Marc Vincent, and Frederic Wagner. Random graph generation for scheduling simulations. In Proc. of SIMUTools, 2010.
