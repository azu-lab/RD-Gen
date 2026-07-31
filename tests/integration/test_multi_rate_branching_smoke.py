import os
import shutil
import subprocess
import tempfile

import pytest
import yaml

RDGEN_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

YAML_BODY = """\
Seed: 1
Number of DAGs: 3

Graph structure:
  Generation method: "Chain-based"
  Number of chains: { Fixed: 2 }
  Main sequence length: { Fixed: 4 }
  Number of sub sequences: { Fixed: 0 }
  Branching:
    Probability of branching: { Fixed: 0.4 }
    Maximum nesting depth: { Fixed: 1 }
    Maximum branches: { Fixed: 3 }
    Firing: probabilistic
    Probability distribution: uniform-normalize

Properties:
  Multi-rate:
    Periodic type: 'Entry'
    Period:
      Random: [10000, 20000]
    Source node period:
      Fixed: 100
    Total utilization:
      Fixed: 2.0
    Maximum utilization:
      Fixed: 1.0

Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
"""


def test_multi_rate_chain_with_branching_completes(tmp_path):
    cfg_path = tmp_path / "smoke.yaml"
    cfg_path.write_text(YAML_BODY)
    dest = tmp_path / "out"
    subprocess.run(
        ["python", "run_generator.py", "-c", str(cfg_path), "-d", str(dest)],
        cwd=RDGEN_ROOT, check=True,
    )
    found = False
    for root, _, files in os.walk(dest):
        for fn in files:
            if fn.endswith(".yaml") and fn != "combination_log.yaml":
                found = True
                with open(os.path.join(root, fn)) as f:
                    d = yaml.safe_load(f)
                # Must include at least one v_ent node
                node_types = [n.get("node_type", "regular") for n in d["nodes"]]
                assert "v_ent" in node_types
    assert found
