import copy
import os
import re
import subprocess
import sys

import pytest
import yaml

SAMPLE_CONFIGS = [
    "sample_config/chain_based/sample_chain_based.yaml",
    "sample_config/g_n_p/sample_g_n_p.yaml",
    "sample_config/fan_in_fan_out/sample_fan_in_fan_out.yaml",
]

RDGEN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _reduce(cfg):
    """Recursively replace any {Combination: [...]} / {Combination: "(a,b,c)"}
    with {Fixed: first_value}. Cap Number of DAGs to 2."""
    if isinstance(cfg, dict):
        new = {}
        for k, v in cfg.items():
            if isinstance(v, dict) and "Combination" in v:
                items = v["Combination"]
                if isinstance(items, list) and items:
                    new[k] = {"Fixed": items[0]}
                elif isinstance(items, str):
                    # parse e.g. "(5.0, 6.5, 0.1)" or "(2, 7, 1)" -> first
                    m = re.search(r"-?\d+(?:\.\d+)?", items)
                    if m:
                        val = m.group(0)
                        new[k] = {"Fixed": float(val) if "." in val else int(val)}
                    else:
                        new[k] = v
                else:
                    new[k] = v
            elif isinstance(v, dict) and "Random" in v:
                items = v["Random"]
                if isinstance(items, list) and items:
                    new[k] = {"Fixed": items[0]}
                elif isinstance(items, str):
                    m = re.search(r"-?\d+(?:\.\d+)?", items)
                    if m:
                        val = m.group(0)
                        new[k] = {"Fixed": float(val) if "." in val else int(val)}
                    else:
                        new[k] = v
                else:
                    new[k] = v
            else:
                new[k] = _reduce(v)
        return new
    if isinstance(cfg, list):
        return [_reduce(x) for x in cfg]
    return cfg


@pytest.mark.parametrize("config", SAMPLE_CONFIGS)
def test_existing_sample_pipeline(config, tmp_path):
    """Smoke: each existing sample YAML still drives the generation pipeline
    without errors after Branching feature was added. Combination/Random
    parameters are reduced to fixed values, and Number of DAGs is capped at
    2, to keep wall time bounded."""
    with open(os.path.join(RDGEN_ROOT, config)) as f:
        raw = yaml.safe_load(f)
    reduced = _reduce(copy.deepcopy(raw))
    reduced["Number of DAGs"] = 2
    cfg_path = tmp_path / "reduced.yaml"
    cfg_path.write_text(yaml.safe_dump(reduced))
    dest = tmp_path / "out"
    subprocess.run(
        [sys.executable, "run_generator.py", "-c", str(cfg_path), "-d", str(dest)],
        cwd=RDGEN_ROOT, check=True, timeout=60,
    )
    found = False
    for root, _, files in os.walk(dest):
        for fn in files:
            if fn.endswith(".yaml") and fn != "combination_log.yaml":
                found = True
    assert found, f"No DAGs produced for {config}"
