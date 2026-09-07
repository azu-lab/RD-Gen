import os
import subprocess
import sys

import pytest
import yaml
from networkx.readwrite import json_graph

from src.branching_structure import BranchingStructure
from src.common import Util

RDGEN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CHAIN_STRUCTURE = """\
Graph structure:
  Generation method: "Chain-based"
  Number of chains: { Fixed: 3 }
  Main sequence length: { Fixed: 4 }
  Number of sub sequences: { Fixed: 1 }
  Vertically link chains:
    Number of source nodes: { Fixed: 2 }
    Main sequence tail: True
    Sub sequence tail: True
  Merge chains:
    Number of sink nodes: { Fixed: 1 }
    Middle of chain: False
    Sink node: True
  Branching:
    Probability of branching: { Fixed: 0.4 }
    Maximum nesting depth: { Fixed: 1 }
    Maximum branches: { Fixed: 3 }
    Sub-chain length: { Fixed: 2 }
    Firing: probabilistic
    Probability distribution: uniform-normalize
    Accounting: max-branch
"""

GNP_STRUCTURE = """\
Graph structure:
  Generation method: "G(n, p)"
  Number of nodes: { Fixed: 12 }
  Number of source nodes: { Fixed: 1 }
  Number of sink nodes: { Fixed: 1 }
  Probability of edge existence: { Fixed: 0.3 }
  Ensure weakly connected: True
  Branching:
    Probability of branching: { Fixed: 0.4 }
    Maximum nesting depth: { Fixed: 2 }
    Maximum branches: { Fixed: 3 }
    Firing: probabilistic
    Probability distribution: dirichlet
    Accounting: max-branch
"""

OUTPUT = """\
Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
"""


def _multi_rate(periodic_type):
    return f"""\
Properties:
  Multi-rate:
    Periodic type: '{periodic_type}'
    Period: { {"Fixed": 100000} }
    Total utilization: { {"Fixed": 1.0} }
"""


def _run(tmp_path, body):
    cfg_path = tmp_path / "smoke.yaml"
    cfg_path.write_text("Seed: 1\nNumber of DAGs: 3\n\n" + body)
    dest = tmp_path / "out"
    subprocess.run(
        [sys.executable, "run_generator.py", "-c", str(cfg_path), "-d", str(dest)],
        cwd=RDGEN_ROOT, check=True, timeout=120,
    )
    dags = []
    for root, _, files in os.walk(dest):
        for fn in sorted(files):
            if fn.startswith("dag_") and fn.endswith(".yaml"):
                with open(os.path.join(root, fn)) as f:
                    dags.append(json_graph.node_link_graph(
                        yaml.safe_load(f), directed=True, multigraph=False, edges="links"))
    with open(os.path.join(dest, "DAGs", "generation_stats.yaml")) as f:
        stats = yaml.safe_load(f)
    return dags, stats


def test_entry_type_with_branching(tmp_path):
    dags, stats = _run(tmp_path, CHAIN_STRUCTURE + _multi_rate("Entry") + OUTPUT)
    assert stats == {"requested": 3, "exported": 3, "discarded": 0,
                     "augmentation_retries_total": 0, "augmentation_retries_max": 0}
    assert len(dags) == 3
    assert any(a.get("node_type") == "v_ent" for g in dags for _, a in g.nodes(data=True))
    for g in dags:
        for n in Util.get_source_nodes(g):
            assert g.nodes[n]["node_type"] == "regular" and "period" in g.nodes[n]


def test_chain_type_with_branching(tmp_path):
    """Periodic type Chain on an augmented chain-based DAG (crashed before)."""
    dags, _ = _run(tmp_path, CHAIN_STRUCTURE + _multi_rate("Chain") + OUTPUT)
    assert len(dags) == 3
    for g in dags:
        assert all("chain_id" in a for _, a in g.nodes(data=True))
        chains = Util.chains(g)
        assert len(chains) == 3
        heads = [Util.chain_head(g, nodes) for nodes in chains.values()]
        assert sorted(n for n, a in g.nodes(data=True) if "period" in a) == sorted(heads)
        s = BranchingStructure(g)
        for uid in s.units:  # a construct never straddles two chains
            body = set().union(*s.bodies[uid].values()) | {s.vent[uid], s.vext[uid]}
            assert len({g.nodes[n]["chain_id"] for n in body}) == 1
        total = sum(
            s.aggregate({n: g.nodes[n]["execution_time"] for n in nodes}, "max-branch")
            / g.nodes[Util.chain_head(g, nodes)]["period"]
            for nodes in chains.values()
        )
        assert abs(total - 1.0) <= 0.01


def test_dag_type_with_branching(tmp_path):
    dags, _ = _run(tmp_path, GNP_STRUCTURE + _multi_rate("DAG") + OUTPUT)
    assert len(dags) == 3
    for g in dags:
        assert g.graph["period"] == 100000
        timer_nodes = [n for n, a in g.nodes(data=True) if "period" in a]
        assert sorted(timer_nodes) == sorted(Util.get_source_nodes(g))
        execs = {n: a["execution_time"] for n, a in g.nodes(data=True)}
        assert abs(BranchingStructure(g).aggregate(execs, "max-branch") / 100000 - 1.0) <= 0.01
        for n, a in g.nodes(data=True):
            assert 0.0 < a["marginal_prob"] <= 1.0


@pytest.mark.parametrize("periodic_type", ["All", "IO"])
def test_all_and_io_types_are_rejected_with_branching(tmp_path, periodic_type):
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text("Seed: 1\nNumber of DAGs: 1\n\n" + GNP_STRUCTURE
                        + _multi_rate(periodic_type) + OUTPUT)
    proc = subprocess.run(
        [sys.executable, "run_generator.py", "-c", str(cfg_path), "-d", str(tmp_path / "out")],
        cwd=RDGEN_ROOT, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode != 0
    assert "All or IO" in proc.stderr
