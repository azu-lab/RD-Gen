import re

from schema import Optional, Or, Regex, Schema, SchemaError

from ..common import Util


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
                    Optional(Regex("Deadline mode", flags=re.I)): Or(
                        Regex("Implicit", flags=re.I),
                        Regex("Constrained", flags=re.I),
                        Regex("Arbitrary", flags=re.I),
                    ),
                    Optional(Regex("Ratio of deadline to critical path", flags=re.I)): Or(
                        {Regex("Fixed", flags=re.I): float},
                        {Regex("Random", flags=re.I): Or([float], str)},
                        {Regex("Combination", flags=re.I): Or([float], str)},
                    ),
                },
                Optional(Regex("Multi-rate", flags=re.I)): {
                    Regex("Periodic type", flags=re.I): Or(
                        Regex("All", flags=re.I),
                        Regex("IO", flags=re.I),
                        Regex("Entry", flags=re.I),
                        Regex("Chain", flags=re.I),
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
                    Optional(Regex("Auto-fit cycle", flags=re.I)): bool,
                    Optional(Regex("Whole-DAG utilization", flags=re.I)): Or(
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
                    Regex("Firing", flags=re.I): Or(
                        Regex("^deterministic$", flags=re.I),
                        Regex("^probabilistic$", flags=re.I),
                    ),
                    Regex("Probability distribution", flags=re.I): Or(
                        Regex("^dirichlet$", flags=re.I),
                        Regex("^uniform-normalize$", flags=re.I),
                    ),
                    Optional(Regex("Dirichlet alpha", flags=re.I)): Or(float, int),
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

        self._validate_deadline_mode()

    def _validate_deadline_mode(self) -> None:
        """Validate cross-field constraints for 'Deadline mode'.

        'Implicit' and 'Constrained' deadline modes need a single,
        well-defined period per DAG task to compare the deadline against,
        which only 'Multi-rate' with 'Periodic type: Entry' guarantees.
        'Arbitrary' (the default when 'Deadline mode' is omitted) instead
        requires 'Ratio of deadline to critical path', which is otherwise
        unused.

        """
        end_to_end_deadline = self._config_raw["Properties"].get("End-to-end deadline")
        if not end_to_end_deadline:
            return

        deadline_mode = end_to_end_deadline.get("Deadline mode", "Arbitrary")
        if Util.ambiguous_equals(deadline_mode, "Arbitrary"):
            if not end_to_end_deadline.get("Ratio of deadline to critical path"):
                raise SchemaError(
                    "'Ratio of deadline to critical path' is required "
                    "when 'Deadline mode' is 'Arbitrary' or omitted."
                )
            return

        multi_rate = self._config_raw["Properties"].get("Multi-rate")
        if not multi_rate:
            raise SchemaError(
                f"'Deadline mode: {deadline_mode}' requires 'Multi-rate' to be specified."
            )

        periodic_type = multi_rate.get("Periodic type")
        if not Util.ambiguous_equals(periodic_type, "Entry"):
            raise SchemaError(
                f"'Deadline mode: {deadline_mode}' requires 'Multi-rate.Periodic type' "
                f"to be 'Entry', but got '{periodic_type}'."
            )
