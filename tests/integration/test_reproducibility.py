"""Same YAML + same seed must give bit-identical output across processes.

Each configuration is generated twice in separate interpreters with different
PYTHONHASHSEED values, so any dependence on hash-based iteration order or on an
unseeded second RNG shows up as a hash mismatch.
"""
import hashlib
import os
import subprocess
import sys

import pytest

RDGEN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CHAIN_VERTICAL_LINK = """\
Seed: 3
Number of DAGs: 8

Graph structure:
  Generation method: "Chain-based"
  Number of chains: { Random: [3, 4] }
  Main sequence length: { Random: [3, 4, 5] }
  Number of sub sequences: { Random: [1, 2] }
  Vertically link chains:
    Number of source nodes: { Fixed: 2 }
    Main sequence tail: True
    Sub sequence tail: True
  Merge chains:
    Number of sink nodes: { Fixed: 1 }
    Middle of chain: False
    Sink node: True

Properties:
  Multi-rate:
    Periodic type: 'Chain'
    Period: { Random: [10000, 20000, 30000] }
    Source node period: { Random: [50, 100] }
    Total utilization: { Fixed: 2.0 }
    Maximum utilization: { Fixed: 1.0 }

Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
    DOT: True
"""

GNP_DIRICHLET_DAG_TYPE = """\
Seed: 4
Number of DAGs: 4

Graph structure:
  Generation method: "G(n, p)"
  Number of nodes: { Fixed: 15 }
  Number of source nodes: { Fixed: 1 }
  Number of sink nodes: { Fixed: 1 }
  Probability of edge existence: { Fixed: 0.3 }
  Ensure weakly connected: True
  Branching:
    Probability of branching: { Combination: [0.2, 0.5] }
    Maximum nesting depth: { Fixed: 2 }
    Maximum branches: { Fixed: 3 }
    Firing: probabilistic
    Probability distribution: dirichlet
    Accounting: expected

Properties:
  Multi-rate:
    Periodic type: DAG
    Period: { Random: [1000, 2000] }
    Total utilization: { Fixed: 0.5 }

Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
"""

CHAIN_BRANCHING_CHAIN_TYPE = """\
Seed: 5
Number of DAGs: 4

Graph structure:
  Generation method: "Chain-based"
  Number of chains: { Fixed: 3 }
  Main sequence length: { Fixed: 4 }
  Number of sub sequences: { Fixed: 1 }
  Vertically link chains:
    Number of source nodes: { Fixed: 2 }
    Main sequence tail: True
    Sub sequence tail: True
  Branching:
    Probability of branching: { Fixed: 0.5 }
    Maximum nesting depth: { Fixed: 2 }
    Maximum branches: { Fixed: 2 }
    Sub-chain length: { Random: [1, 2] }
    Firing: deterministic
    Probability distribution: uniform-normalize
    Accounting: max-branch

Properties:
  Multi-rate:
    Periodic type: 'Chain'
    Period: { Fixed: 100000 }
    Total utilization: { Fixed: 1.5 }

Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
"""


def _generate(cfg_path, dest, hash_seed):
    env = dict(os.environ, PYTHONHASHSEED=str(hash_seed))
    subprocess.run(
        [sys.executable, "run_generator.py", "-c", str(cfg_path), "-d", str(dest)],
        cwd=RDGEN_ROOT, check=True, timeout=300, env=env,
    )
    digests = {}
    for root, _, files in os.walk(dest):
        for fn in files:
            path = os.path.join(root, fn)
            with open(path, "rb") as f:
                digests[os.path.relpath(path, dest)] = hashlib.sha256(f.read()).hexdigest()
    return digests


@pytest.mark.parametrize("body", [CHAIN_VERTICAL_LINK, GNP_DIRICHLET_DAG_TYPE,
                                  CHAIN_BRANCHING_CHAIN_TYPE],
                         ids=["chain-vertical-link", "gnp-dirichlet-dag-type",
                              "chain-branching-chain-type"])
def test_bit_identical_output_across_processes(tmp_path, body):
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(body)
    first = _generate(cfg_path, tmp_path / "run1", hash_seed=1)
    second = _generate(cfg_path, tmp_path / "run2", hash_seed=2)
    assert any(name.endswith(".yaml") and "dag_" in name for name in first)
    assert first == second
