#!/usr/bin/env python3
"""Generate one RD-Gen config per u_norm bin for the theory-vs-reality study
(see awkernel/applications/rd_gen_to_dags/examples/theory_vs_reality.rs's own
module doc for the full design).

Unlike my_chain_theory_pool.yaml's single shared pool (where m is derived
per resampled trial as ceil(U_Sigma/u_norm), independent of any real core
count), this study fixes REAL_CORES to the target machine's actual DAG-pool
core count and instead varies u_norm on the *generation* side: each bin's
"Whole-DAG utilization" range is centered on

    per_dag_utilization = u_norm * REAL_CORES / DAGS_PER_SET

so a plain random draw of DAGS_PER_SET DAGs from that bin's own pool already
lands close to the target u_norm, with no rejection sampling or post-hoc
rescaling of C/T needed.

REAL_CORES=14 is the confirmed 2026-09-24 measurement on the current real
machine (16 CPUs, HT disabled via smt_disable -> 15 worker cores, minus 1
regular-pool-reserved core per awkernel_async_lib::scheduler::pool::
is_dag_pool_core's num_cpu()-2 split).

Usage: python3 gen_theory_vs_reality_bins.py
Writes one YAML per bin next to this script, named u_norm_<value>.yaml.
"""

from pathlib import Path

REAL_CORES = 14
DAGS_PER_SET = 8
U_NORM_MIN = 0.10
U_NORM_MAX = 1.00
U_NORM_STEP = 0.05

# 'Constrained' (D ~ Uniform(L, T]) or 'Implicit' (D = T): both keep D tied
# to the fixed period T below by construction, which is what makes this
# study's generation-time utilization targeting (anchored on that same fixed
# T) survive into admission -- see TEMPLATE's own comment for the
# 'Arbitrary'+override_period scheme this replaced (2026-09-24) and why it
# broke that targeting.
#
# 'Arbitrary' (D = L * ratio, independent of T) also works -- verified
# empirically 2026-09-24: T is set by 'Multi-rate' (a separate Properties
# section from 'End-to-end deadline'), so it's untouched either way, and the
# per-bin median utilization tracked its target under 'Arbitrary' just as
# well as under 'Constrained'. The one real pitfall: RD-Gen's "Ratio of
# deadline to critical path: Random: [a, b]" is NOT a continuous range --
# `Util.random_choice` (src/common/util.py) treats a list as a *discrete*
# `random.choice`, unlike "Whole-DAG utilization"'s own continuous sampling
# -- so `[1.0, 3.33]` picks *exactly* 1.0 or 3.33, 50/50, never anything
# between. Worse, a ratio of exactly 1.0 sets `D = L` exactly, making
# `min_dedicated_cores()`'s `D - L` denominator 0 -- every such DAG then
# comes back `Infeasible` regardless of anything else, not merely "light"
# (confirmed: an `Random: [1.0, 3.33]` bin produced zero heavy DAGs, all
# `light`/`infeasible`). ARBITRARY_RATIO_CHOICES below is deliberately a
# longer discrete list, none of them 1.0, to approximate a spread without
# hitting that trap.
DEADLINE_MODE = "Constrained"  # 'Constrained' | 'Implicit' | 'Arbitrary'
ARBITRARY_RATIO_CHOICES = [1.2, 1.5, 1.8, 2.1, 2.5, 3.0, 3.33]
# Half-width of each bin's "Whole-DAG utilization" range, in per-DAG
# utilization units, *derived* from the other constants above (not a fixed
# number) so it stays correctly scaled if REAL_CORES/DAGS_PER_SET/
# U_NORM_STEP ever change: two adjacent bins' centers are
# U_NORM_STEP*REAL_CORES/DAGS_PER_SET apart in per-DAG-utilization terms, and
# DELTA_FRACTION_OF_STEP (< 0.5) is how much of that gap each bin's own
# half-width may occupy before adjacent bins' ranges would start to overlap.
# 0.3 leaves comfortable headroom while still giving each bin some internal
# utilization diversity (not a single repeated value). At the
# REAL_CORES=14/DAGS_PER_SET=8/U_NORM_STEP=0.05 this was tuned against, this
# resolves to ~0.026 (close to the earlier hand-picked 0.02).
DELTA_FRACTION_OF_STEP = 0.3
DELTA = DELTA_FRACTION_OF_STEP * U_NORM_STEP * REAL_CORES / DAGS_PER_SET
POOL_SIZE_PER_BIN = 300

TEMPLATE = """Seed: {seed}
# Per-u_norm-bin pool for the theory-vs-reality study (see
# gen_theory_vs_reality_bins.py, which generated this file -- do not hand-edit,
# regenerate instead). u_norm={u_norm:.2f}, REAL_CORES={real_cores},
# DAGS_PER_SET={dags_per_set}: centers this bin's per-DAG "Whole-DAG
# utilization" on u_norm*REAL_CORES/DAGS_PER_SET = {center:.4f}.
#
# Deadline mode: {deadline_mode} -- NOT 'Arbitrary'+override_deadline/
# override_period like acceptance_ratio.rs/my_chain_theory_pool.yaml (that
# scheme was tried first and rejected, 2026-09-24: its override_period
# discards RD-Gen's own period entirely and derives a new one from
# critical_path/beta instead, decorrelating utilization=C/period from this
# file's own generation-time C-vs-1000 targeting). See
# gen_theory_vs_reality_bins.py's own DEADLINE_MODE comment for how each of
# 'Constrained'/'Implicit'/'Arbitrary' keeps (or, for 'Arbitrary', doesn't
# need to keep) that targeting intact.
Number of DAGs: {pool_size}

Graph structure:
  Generation method: "Chain-based"
  Number of chains:
    Fixed: 1
  Main sequence length:
    Random: (5, 10, 1)
  Number of sub sequences:
    Random: (1, 3, 1)          # 幅を持たせるため多めに設定
  Merge chains:
    Number of sink nodes:
      Fixed: 1
    Middle of chain: False
    Sink node: True

Properties:
  Multi-rate:
    Periodic type: "Entry"
    Source node period:
      Fixed: 1000
    Whole-DAG utilization:
      Random: [{lo:.4f}, {hi:.4f}]
  End-to-end deadline:
{deadline_block}

Output formats:
  Naming of combination directory: "Abbreviation"
  DAG:
    YAML: True
    JSON: False
    XML: False
    DOT: False
  Figure:
    Draw legend: False
    PNG: False
    SVG: False
    EPS: False
    PDF: True
"""


def deadline_block():
    if DEADLINE_MODE in ("Constrained", "Implicit"):
        return f"    Deadline mode: '{DEADLINE_MODE}'"
    if DEADLINE_MODE == "Arbitrary":
        choices = ", ".join(str(v) for v in ARBITRARY_RATIO_CHOICES)
        return (
            "    Deadline mode: 'Arbitrary'\n"
            "    Ratio of deadline to critical path:\n"
            f"      Random: [{choices}]"
        )
    raise ValueError(f"DEADLINE_MODE must be 'Constrained'/'Implicit'/'Arbitrary', got {DEADLINE_MODE!r}")


def u_norm_values():
    n_steps = round((U_NORM_MAX - U_NORM_MIN) / U_NORM_STEP)
    return [round(U_NORM_MIN + i * U_NORM_STEP, 2) for i in range(n_steps + 1)]


def main():
    out_dir = Path(__file__).resolve().parent / "theory_vs_reality_bins"
    out_dir.mkdir(exist_ok=True)
    for seed, u_norm in enumerate(u_norm_values()):
        center = u_norm * REAL_CORES / DAGS_PER_SET
        lo = max(center - DELTA, 0.01)
        hi = center + DELTA
        content = TEMPLATE.format(
            seed=seed,
            u_norm=u_norm,
            real_cores=REAL_CORES,
            dags_per_set=DAGS_PER_SET,
            center=center,
            pool_size=POOL_SIZE_PER_BIN,
            lo=lo,
            hi=hi,
            deadline_mode=DEADLINE_MODE,
            deadline_block=deadline_block(),
        )
        out_path = out_dir / f"u_norm_{u_norm:.2f}.yaml"
        out_path.write_text(content)
        print(f"wrote {out_path} (center={center:.4f}, range=[{lo:.4f}, {hi:.4f}])")


if __name__ == "__main__":
    main()
