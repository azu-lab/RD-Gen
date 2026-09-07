import re
from typing import List, Union

from schema import Optional, Or, Regex, Schema

from ..common import Util
from ..exceptions import InfeasibleConfigError
from .combo_generator import ComboGenerator


class ConfigValidator:
    """Config validator class."""

    base_schema = Schema(
        {
            Regex("Seed", flags=re.I): int,
            Regex("Number of DAGs", flags=re.I): int,
            Regex("Graph structure", flags=re.I): {
                Regex("Generation method", flags=re.I): Or(
                    Regex("Fan-in/Fan-out", flags=re.I),
                    Regex(r"G\(n,[ ]*p\)", flags=re.I),
                    Regex("Chain-based", flags=re.I),
                ),
                Optional(Regex("Number of nodes", flags=re.I)): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
            },
            Regex("Properties", flags=re.I): {
                Optional(Regex("Execution time", flags=re.I)): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Optional(Regex("Communication time", flags=re.I)): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Optional(Regex("CCR", flags=re.I)): Or(
                    {Regex("Fixed", flags=re.I): float},
                    {Regex("Random", flags=re.I): Or([float], str)},
                    {Regex("Combination", flags=re.I): Or([float], str)},
                ),
                Optional(Regex("End-to-end deadline", flags=re.I)): {
                    Regex("Ratio of deadline to critical path", flags=re.I): Or(
                        {Regex("Fixed", flags=re.I): float},
                        {Regex("Random", flags=re.I): Or([float], str)},
                        {Regex("Combination", flags=re.I): Or([float], str)},
                    )
                },
                Optional(Regex("Multi-rate", flags=re.I)): {
                    Regex("Periodic type", flags=re.I): Or(
                        Regex("^All$", flags=re.I),
                        Regex("^IO$", flags=re.I),
                        Regex("^Entry$", flags=re.I),
                        Regex("^Chain$", flags=re.I),
                        Regex("^DAG$", flags=re.I),
                    ),
                    Regex("Period", flags=re.I): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Source node period", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Sink node period", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Offset", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Total utilization", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): float},
                        {Regex("Random", flags=re.I): Or([float], str)},
                        {Regex("Combination", flags=re.I): Or([float], str)},
                    ),
                    Optional(Regex("Maximum utilization", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): float},
                        {Regex("Random", flags=re.I): Or([float], str)},
                        {Regex("Combination", flags=re.I): Or([float], str)},
                    ),
                },
                Optional(Regex("Additional properties", flags=re.I)): {
                    Optional(Regex("Node properties", flags=re.I)): {
                        str: Or(
                            {Regex("Fixed", flags=re.I): Or(float, int)},
                            {Regex("Random", flags=re.I): Or([float], [int], str)},
                            {Regex("Combination", flags=re.I): Or([float], [int], str)},
                        )
                    },
                    Optional(Regex("Edge properties", flags=re.I)): {
                        str: Or(
                            {Regex("Fixed", flags=re.I): Or(float, int)},
                            {Regex("Random", flags=re.I): Or([float], [int], str)},
                            {Regex("Combination", flags=re.I): Or([float], [int], str)},
                        )
                    },
                },
            },
            Regex("Output formats", flags=re.I): {
                Regex("Naming of combination directory", flags=re.I): Or(
                    Regex("Abbreviation", flags=re.I),
                    Regex("Full spell", flags=re.I),
                    Regex("Index of combination", flags=re.I),
                ),
                Regex("DAG", flags=re.I): {
                    Optional(Regex("YAML", flags=re.I)): bool,
                    Optional(Regex("JSON", flags=re.I)): bool,
                    Optional(Regex("XML", flags=re.I)): bool,
                    Optional(Regex("DOT", flags=re.I)): bool,
                },
                Optional(Regex("Figure", flags=re.I)): {
                    Optional(Regex("Draw legend", flags=re.I)): bool,
                    Optional(Regex("PNG", flags=re.I)): bool,
                    Optional(Regex("SVG", flags=re.I)): bool,
                    Optional(Regex("EPS", flags=re.I)): bool,
                    Optional(Regex("PDF", flags=re.I)): bool,
                },
            },
        },
        ignore_extra_keys=True,
    )

    fifo_gnp_common_schema = Schema(
        {
            Regex("Graph structure", flags=re.I): {
                Regex("Number of source nodes", flags=re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Regex("Number of sink nodes", flags=re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Optional(Regex("Ensure weakly connected", flags=re.I)): bool,
            }
        },
        ignore_extra_keys=True,
    )

    fan_in_fan_out_schema = Schema(
        {
            Regex("Graph structure", flags=re.I): {
                Regex("In-degree", flags=re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Regex("Out-degree", flags=re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
            }
        },
        ignore_extra_keys=True,
    )

    g_n_p_schema = Schema(
        {
            Regex("Graph structure", flags=re.I): {
                Regex("Probability of edge existence", re.I): Or(
                    {Regex("Fixed", flags=re.I): float},
                    {Regex("Random", flags=re.I): Or([float], str)},
                    {Regex("Combination", flags=re.I): Or([float], str)},
                )
            }
        },
        ignore_extra_keys=True,
    )

    branching_schema = Schema(
        {
            Regex("Graph structure", flags=re.I): {
                Optional(Regex("Branching", flags=re.I)): {
                    Regex("Probability of branching", flags=re.I): Or(
                        {Regex("Fixed", flags=re.I): float},
                        {Regex("Random", flags=re.I): Or([float], str)},
                        {Regex("Combination", flags=re.I): Or([float], str)},
                    ),
                    Regex("Maximum nesting depth", flags=re.I): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Regex("Maximum branches", flags=re.I): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Minimum branches", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Regex("Firing", flags=re.I): Or(
                        Regex("^deterministic$", flags=re.I),
                        Regex("^probabilistic$", flags=re.I),
                    ),
                    Regex("Probability distribution", flags=re.I): Or(
                        Regex("^dirichlet$", flags=re.I),
                        Regex("^uniform-normalize$", flags=re.I),
                    ),
                    Optional(Regex("Dirichlet alpha", flags=re.I)): Or(float, int),
                    Optional(Regex("Sub-chain length", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Optional(Regex("Accounting", flags=re.I)): Or(
                        Regex("^all$", flags=re.I),
                        Regex("^expected$", flags=re.I),
                        Regex("^max-branch$", flags=re.I),
                    ),
                }
            }
        },
        ignore_extra_keys=True,
    )

    chain_based_schema = Schema(
        {
            Regex("Graph structure", flags=re.I): {
                Regex("Number of chains", re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Regex("Main sequence length", re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Regex("Number of sub sequences", re.I): Or(
                    {Regex("Fixed", flags=re.I): int},
                    {Regex("Random", flags=re.I): Or([int], str)},
                    {Regex("Combination", flags=re.I): Or([int], str)},
                ),
                Optional(Regex("Vertically link chains", re.I)): {
                    Regex("Number of source nodes", re.I): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Regex("Main sequence tail", re.I): bool,
                    Regex("Sub sequence tail", re.I): bool,
                },
                Optional(Regex("Merge chains", re.I)): {
                    Regex("Number of sink nodes", re.I): Or(
                        {Regex("Fixed", flags=re.I): int},
                        {Regex("Random", flags=re.I): Or([int], str)},
                        {Regex("Combination", flags=re.I): Or([int], str)},
                    ),
                    Regex("Middle of chain", re.I): bool,
                    Regex("Sink node", re.I): bool,
                },
            }
        },
        ignore_extra_keys=True,
    )

    def __init__(self, config_raw: dict) -> None:
        self._config_raw = config_raw

    def validate(self) -> None:
        """Validate config.

        Check the entered configurations according to the schema.
        For detail, see https://www.andrewvillazon.com/validate-yaml-python-schema/.

        """
        self.base_schema.validate(self._config_raw)
        gm = self._config_raw["Graph structure"]["Generation method"]
        if Util.ambiguous_equals(gm, "fan-in/fan-out"):
            self.fifo_gnp_common_schema.validate(self._config_raw)
            self.fan_in_fan_out_schema.validate(self._config_raw)
            self.branching_schema.validate(self._config_raw)
        elif Util.ambiguous_equals(gm, "g(n, p)"):
            self.fifo_gnp_common_schema.validate(self._config_raw)
            self.g_n_p_schema.validate(self._config_raw)
            self.branching_schema.validate(self._config_raw)
        elif Util.ambiguous_equals(gm, "chain-based"):
            self.chain_based_schema.validate(self._config_raw)
            self.branching_schema.validate(self._config_raw)
        self._validate_semantics()

    def _validate_semantics(self) -> None:
        """Reject parameter combinations the schema alone cannot express.

        Raises
        ------
        InfeasibleConfigError
            Branching combined with 'Periodic type' All/IO (timer-driven nodes
            would appear inside branching constructs), 'Maximum branches' < 2,
            'Minimum branches' < 2 or above 'Maximum branches',
            'Probability of branching' outside [0, 1], 'Maximum nesting depth' < 0,
            'Accounting: expected' with deterministic firing, 'Periodic type'
            Chain without the Chain-based method, or 'CCR' without a base quantity.
        """
        gm = self._config_raw["Graph structure"]["Generation method"]
        branching = self._config_raw["Graph structure"].get("Branching")
        properties = self._config_raw["Properties"]
        multi_rate = properties.get("Multi-rate")
        if properties.get("CCR") and not (
            properties.get("Execution time") or properties.get("Communication time")
        ):
            raise InfeasibleConfigError(
                "'CCR' requires 'Execution time' or 'Communication time' to derive the other."
            )
        periodic_type = multi_rate.get("Periodic type") if multi_rate else None
        if periodic_type and Util.ambiguous_equals(periodic_type, "chain") and not (
            Util.ambiguous_equals(gm, "chain-based")
        ):
            raise InfeasibleConfigError(
                "'Periodic type: Chain' requires 'Generation method: Chain-based'."
            )
        if not branching:
            return
        if periodic_type and (
            Util.ambiguous_equals(periodic_type, "all") or Util.ambiguous_equals(periodic_type, "io")
        ):
            raise InfeasibleConfigError(
                "'Branching' cannot be combined with 'Periodic type' All or IO "
                "(timer-driven nodes must stay outside branching constructs). "
                "Use Entry, DAG, or Chain."
            )
        if min(self._option_values(branching["Maximum branches"])) < 2:
            raise InfeasibleConfigError("'Maximum branches' must be at least 2.")
        if "Minimum branches" in branching:
            minimum = self._option_values(branching["Minimum branches"])
            if min(minimum) < 2:
                raise InfeasibleConfigError("'Minimum branches' must be at least 2.")
            if max(minimum) > min(self._option_values(branching["Maximum branches"])):
                raise InfeasibleConfigError(
                    "'Minimum branches' must not exceed 'Maximum branches'."
                )
        if min(self._option_values(branching["Maximum nesting depth"])) < 0:
            raise InfeasibleConfigError("'Maximum nesting depth' must be non-negative.")
        p_b = self._option_values(branching["Probability of branching"])
        if min(p_b) < 0.0 or max(p_b) > 1.0:
            raise InfeasibleConfigError("'Probability of branching' must be within [0, 1].")
        accounting = branching.get("Accounting", "all")
        if Util.ambiguous_equals(accounting, "expected") and not Util.ambiguous_equals(
            branching["Firing"], "probabilistic"
        ):
            raise InfeasibleConfigError(
                "'Accounting: expected' requires 'Firing: probabilistic'."
            )

    @staticmethod
    def _option_values(option: dict) -> List[Union[int, float]]:
        """All values a Fixed / Random / Combination option can take."""
        value = list(option.values())[0]
        if isinstance(value, str):
            return ComboGenerator._convert_tuple_to_list(value)
        if isinstance(value, list):
            return value
        return [value]
