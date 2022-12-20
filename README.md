# Random_DAG_Generator

## About
A random DAG generator considering multi-rate applications for reproducible scheduling evaluation (**RD-Gen**) is a tool for researchers targeting DAGs.
RD-Gen makes the following contributions:
- RD-Gen **extends existing random DAG construction methods**, Fan-in/Fan-out [1] and G(n, p) [2] methods, to meet researchers’ requirements.
- RD-Gen proposes a new **Chain-based method** to flexibly construct state-of-the-art chain-based multi-rate DAGs.
- RD-Gen reduces implementation effort through the **automatic setting of complex parameters** and **batch generation of random DAG sets**.

## Setup flow
```bash
$ git clone https://github.com/atsushi421/Random_DAG_Generator.git
$ cd Random_DAG_Generator
$ ./setup.bash
```

## Quick start
Sample config files can be used without modification.

### Chain-based method
- `python3 run_generator.py -c ./sample_config/chain_based/sample_chain_based.yaml`

### Fan-in/Fan-out method
- `python3 run_generator.py -c ./sample_config/fan_in_fan_out/sample_fan_in_fan_out.yaml`

### G(n, p) method
- `python3 run_generator.py -c ./sample_config/g_n_p/sample_g_n_p.yaml`

## Documents
[See wiki](https://github.com/azu-lab/RD-Gen/wiki).

## References
- [1] R. P. Dick, D. L. Rhodes, and W. Wolf. TGFF: task graphs for free. In Proc. of Workshop on CODES/CASHE, 1998.
- [2] Daniel Cordeiro, Gregory Mounie, Swann Perarnau, Denis Trystram, Jean-Marc Vincent, and Frederic Wagner. Random graph generation for scheduling simulations. In Proc. of SIMUTools, 2010.
