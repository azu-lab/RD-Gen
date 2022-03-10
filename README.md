# Random_DAG_Generator

## Setup flow
Clone this repository to your own workspace.
```
git clone git@github.com:atsushi421/Random_DAG_Generator.git
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
### Normal mode
- Modify Random_DAG_Generator/config/normal/sample_normal_config.yaml
  - Random_DAG_Generator can be executed without any changes.
- `bash run_generator.bash --config_yaml_name sample_normal_config.yaml`

### Chain mode
- Modify Random_DAG_Generator/config/chain/sample_chain_config.yaml
  - Random_DAG_Generator can be executed without any changes.
- `bash run_generator.bash -c --config_yaml_name sample_chain_config.yaml`
