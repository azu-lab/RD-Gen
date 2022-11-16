# import re

import yaml

from src.config import Config

# from schema import Optional, Or, Regex, Schema, SchemaError


class ConfigLoader():
    def __init__(
        self,
        config_path: str
    ) -> None:
        with open(config_path, "r") as f:
            self._cfg_raw = yaml.safe_load(f)
        # self._validate()

    def load(self) -> Config:
        return Config(self._cfg_raw)

#     def _validate(self) -> None:
#         try:
#             base_schema.validate(self._cfg_raw)
#             gm = self._cfg_raw["Graph structure"]["Generation method"]
#             if gm.lower() == "fan-in/fan-out":
#                 fifo_gnp_common_schema.validate(self._cfg_raw)
#                 fan_in_fan_out_schema.validate(self._cfg_raw)
#             elif gm.lower() == "g(n, p)":
#                 fifo_gnp_common_schema.validate(self._cfg_raw)
#                 g_n_p_schema.validate(self._cfg_raw)
#             elif gm.lower() == "chain-based":
#                 chain_based_schema.validate(self._cfg_raw)
#         except SchemaError as se:
#             raise se


# base_schema = Schema({
#     Regex("Seed", flags=re.I): int,
#     Regex("Number of DAGs", flags=re.I): int,

#     Regex("Graph structure", flags=re.I): {
#         Regex("Generation method", flags=re.I): Or(
#             Regex("Fan-in/Fan-out", flags=re.I),
#             Regex(r"G\(n,[ ]*p\)", flags=re.I),
#             Regex("Chain-based", flags=re.I)
#         ),
#         Optional(Regex("Number of nodes", flags=re.I)): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         )
#     },

#     Regex("Properties", flags=re.I): {
#         Optional(Regex("Execution time", flags=re.I)): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Optional(Regex("Communication time", flags=re.I)): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Optional(Regex("End-to-end deadline", flags=re.I)): {
#             Regex("Ratio of deadline to critical path", flags=re.I): Or(
#                 {Regex("Fixed", flags=re.I): float},
#                 {Regex("Random", flags=re.I): Or([float], str)},
#                 {Regex("Combination", flags=re.I): Or([float], str)}
#             )
#         },
#         Optional(Regex("Multi-rate", flags=re.I)): {
#             Regex("Periodic type", flags=re.I): Or(
#                 Regex("All", flags=re.I),
#                 Regex("IO", flags=re.I),
#                 Regex("Entry", flags=re.I),
#                 Regex("Chain", flags=re.I)
#             ),
#             Regex("Period", flags=re.I): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Optional(Regex("Entry node period", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Optional(Regex("Exit node period", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Optional(Regex("Offset", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Optional(Regex("Total utilization", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): float},
#                 {Regex("Random", flags=re.I): Or([float], str)},
#                 {Regex("Combination", flags=re.I): Or([float], str)}
#             ),
#             Optional(Regex("Maximum utilization", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): float},
#                 {Regex("Random", flags=re.I): Or([float], str)},
#                 {Regex("Combination", flags=re.I): Or([float], str)}
#             ),
#             Optional(Regex("CCR", flags=re.I)): Or(
#                 {Regex("Fixed", flags=re.I): float},
#                 {Regex("Random", flags=re.I): Or([float], str)},
#                 {Regex("Combination", flags=re.I): Or([float], str)}
#             )
#         },
#         Optional(Regex("Additional properties", flags=re.I)): {
#             Optional(Regex("Node properties", flags=re.I)): {
#                 str: Or(
#                     {Regex("Fixed", flags=re.I): Or(float, int)},
#                     {Regex("Random", flags=re.I): Or(
#                         [float], [int], str
#                     )},
#                     {Regex("Combination", flags=re.I): Or(
#                         [float], [int], str
#                     )}
#                 )
#             },
#             Optional(Regex("Edge properties", flags=re.I)): {
#                 str: Or(
#                     {Regex("Fixed", flags=re.I): Or(float, int)},
#                     {Regex("Random", flags=re.I): Or(
#                         [float], [int], str
#                     )},
#                     {Regex("Combination", flags=re.I): Or(
#                         [float], [int], str
#                     )}
#                 )
#             },
#         }
#     },

#     Regex("Output formats", flags=re.I): {
#         Regex("Naming of combination directory", flags=re.I): Or(
#             Regex("Abbreviation", flags=re.I),
#             Regex("Full spell", flags=re.I),
#             Regex("Index of combination", flags=re.I)
#         ),
#         Regex("DAG", flags=re.I): {
#             Optional(Regex("YAML", flags=re.I)): bool,
#             Optional(Regex("JSON", flags=re.I)): bool,
#             Optional(Regex("XML", flags=re.I)): bool,
#             Optional(Regex("DOT", flags=re.I)): bool
#         },
#         Regex("Figure", flags=re.I): {
#             Optional(Regex("Draw legend", flags=re.I)): bool,
#             Optional(Regex("PNG", flags=re.I)): bool,
#             Optional(Regex("SVG", flags=re.I)): bool,
#             Optional(Regex("EPS", flags=re.I)): bool,
#             Optional(Regex("PDF", flags=re.I)): bool
#         }
#     }
# }, ignore_extra_keys=True)

# fifo_gnp_common_schema = Schema({
#     Regex("Graph structure", flags=re.I): {
#         Regex("Number of entry nodes", flags=re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Regex("Number of exit nodes", flags=re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Optional(Regex("Ensure weakly connected", flags=re.I)): bool
#     }
# }, ignore_extra_keys=True)

# fan_in_fan_out_schema = Schema({
#     Regex("Graph structure", flags=re.I): {
#         Regex("In-degree", flags=re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Regex("Out-degree", flags=re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         )
#     }
# }, ignore_extra_keys=True)

# g_n_p_schema = Schema({
#     Regex("Graph structure", flags=re.I): {
#         Regex("Probability of edge", re.I): Or(
#             {Regex("Fixed", flags=re.I): float},
#             {Regex("Random", flags=re.I): Or([float], str)},
#             {Regex("Combination", flags=re.I): Or([float], str)}
#         )
#     }
# }, ignore_extra_keys=True)

# chain_based_schema = Schema({
#     Regex("Graph structure", flags=re.I): {
#         Regex("Number of chains", re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Regex("Main sequence length", re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Regex("Number of sub sequences", re.I): Or(
#             {Regex("Fixed", flags=re.I): int},
#             {Regex("Random", flags=re.I): Or([int], str)},
#             {Regex("Combination", flags=re.I): Or([int], str)}
#         ),
#         Optional(Regex("Vertically link chains", re.I)): {
#             Regex("Number of entry nodes", re.I): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Regex("Main sequence tail", re.I): bool,
#             Regex("Sub sequence tail", re.I): bool,
#         },
#         Optional(Regex("Merge chains", re.I)): {
#             Regex("Number of exit nodes", re.I): Or(
#                 {Regex("Fixed", flags=re.I): int},
#                 {Regex("Random", flags=re.I): Or([int], str)},
#                 {Regex("Combination", flags=re.I): Or([int], str)}
#             ),
#             Regex("Middle of chain", re.I): bool,
#             Regex("Exit node", re.I): bool,
#         }
#     }
# }, ignore_extra_keys=True)
