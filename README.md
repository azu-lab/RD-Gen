# RD-Gen
<p align="center">
  <img src="https://user-images.githubusercontent.com/55824710/208731888-be3e320a-4148-46cc-983c-f8ee6fe27b9d.png" width="350px">
</p>
<p align="center">
  <img src="https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat">
  <img src="https://img.shields.io/badge/-Github-black.svg?logo=github&style=flat"><img src="https://img.shields.io/badge/-pytest passing-gleen.svg">
</p>

## About
**RD-Gen** (random DAG generator considering multi-rate applications for reproducible scheduling evaluation) is a tool for researchers targeting DAGs.
RD-Gen makes the following contributions:
- RD-Gen **extends existing random DAG construction methods**, Fan-in/Fan-out [1] and G(n, p) [2] methods, to meet researchersâ€™ requirements.
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

## Documents
- [wiki](https://github.com/azu-lab/RD-Gen/wiki)
- [API list (for developer)](https://azu-lab.github.io/RD-Gen/)

## References
- [1] R. P. Dick, D. L. Rhodes, and W. Wolf. TGFF: task graphs for free. In Proc. of Workshop on CODES/CASHE, 1998.
- [2] Daniel Cordeiro, Gregory Mounie, Swann Perarnau, Denis Trystram, Jean-Marc Vincent, and Frederic Wagner. Random graph generation for scheduling simulations. In Proc. of SIMUTools, 2010.
