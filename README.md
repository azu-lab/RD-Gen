# Random_DAG_Generator

## Setup flow
Clone this repository to your own workspace.
```
git clone https://github.com/atsushi421/Random_DAG_Generator.git
cd Random_DAG_Generator
./setup.bash
```

## Uninstall flow
```
./uninstall.bash  # if you want to remove installed packages.
cd ../
rm -rf Random_DAG_Generator
```

## Quick start
Sample config files can be used without modification.

### Chain-based method
- `bash run_generator.bash -c ./sample_config/chain_based/sample_chain_based.yaml`

### Fan-in/Fan-out method
- `bash run_generator.bash -c ./sample_config/fan_in_fan_out/sample_fan_in_fan_out.yaml`

### G(n, p) method
- `bash run_generator.bash -c ./sample_config/g_n_p/sample_g_n_p.yaml`

## Documents
https://azu-lab.github.io/RD-Gen/
