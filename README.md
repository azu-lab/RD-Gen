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

## Parameters in config file
![image](https://user-images.githubusercontent.com/55824710/205211293-b8d1232f-ca91-4b91-9f4d-52a009ccb703.png)
![image](https://user-images.githubusercontent.com/55824710/205211338-284b2550-ca2d-488b-a0f1-b34bcb2fd77d.png)
