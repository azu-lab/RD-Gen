import copy
import decimal
import itertools
from typing import Dict, Generator, List, Tuple, Union

import numpy as np

from ..common import Util
from .abbreviation import TO_ABB
from .config import Config


class ComboGenerator:
    """ComboGenerator class."""

    def __init__(self, config_raw: dict) -> None:
        self._combo_params: List[str] = []
        self._combo_values: List[Union[List[int], List[float]]] = []
        self._search_combo_and_format_tuple(config_raw["Graph structure"])
        self._search_combo_and_format_tuple(config_raw["Properties"])
        self._config = Config(config_raw)

    def get_num_combos(self) -> int:
        """Get number of combinations.

        Returns
        -------
        int
            Number of combinations.
        """
        num_combos = len(self._combo_values[0])
        if len(self._combo_values) == 1:
            return num_combos

        for v in self._combo_values[1:]:
            num_combos *= len(v)

        return num_combos

    def get_combo_iter(self) -> Generator[Tuple[str, dict, Config], None, None]:
        """Get iterator for combinations.

        Yields
        ------
        Generator[Tuple[str, dict, Config], None, None]
            (combo_dir_name, combo_log, combo_config)
            - combo_dir_name:
                Directory name where the generated DAG set is stored.
            - combo_log:
                Dictionary containing parameter names and chosen values
                for which 'Combination' is specified.
            - combo_config:
                Configuration in which the chosen value is stored
                for the parameter specified as 'Combination'.

        """
        for i, combo in enumerate(itertools.product(*self._combo_values)):
            combo_dir_name = self._create_combo_dir_name(combo, i)  # type: ignore
            combo_log = {}
            combo_config = copy.deepcopy(self._config)
            for k, v in zip(self._combo_params, combo):
                combo_log[k] = v
                combo_config.update_param_value(k, {"Fixed": v})
            combo_config.optimize()
            combo_config.set_random_seed()

            yield (combo_dir_name, combo_log, combo_config)

    def _create_combo_dir_name(
        self,
        combo: Tuple[Union[int, float]],
        index: int,
    ) -> str:
        combo_dir_name: str = ""
        naming = self._config.naming_of_combination_directory
        if Util.ambiguous_equals(naming, "Full spell"):
            for param, value in zip(self._combo_params, combo):
                param_str_list = param.split(" ")
                param_str_list = [s.capitalize() for s in param_str_list]
                if combo_dir_name:
                    combo_dir_name += f'_{"".join(param_str_list)}_{value}'
                else:
                    combo_dir_name = f'{"".join(param_str_list)}_{value}'

        elif Util.ambiguous_equals(naming, "Abbreviation"):
            for param, value in zip(self._combo_params, combo):
                try:
                    param = TO_ABB[param.lower()]
                except KeyError:  # Additional parameter
                    param = param
                if combo_dir_name:
                    combo_dir_name += f"_{param}_{value}"
                else:
                    combo_dir_name = f"{param}_{value}"

        elif Util.ambiguous_equals(naming, "Index of combination"):
            combo_dir_name = f"Combination_{index+1}"

        else:
            raise NotImplementedError

        return combo_dir_name

    @staticmethod
    def _convert_tuple_to_list(tuple_str: str) -> Union[List[int], List[float]]:
        tuple_str = tuple_str.replace("(", "")
        tuple_str = tuple_str.replace(")", "")
        tuple_str = tuple_str.replace(" ", "")

        args: Dict[str, float] = {}
        for i, arg in enumerate(tuple_str.split(",")):
            if i == 0 or "start" in arg:
                args["start"] = float(arg.replace("start=", ""))
            elif i == 1 or "stop" in arg:
                args["stop"] = float(arg.replace("stop=", ""))
            elif i == 2 or "step" in arg:
                args["step"] = float(arg.replace("step=", ""))

        if args["start"].is_integer() and args["stop"].is_integer() and args["step"].is_integer():
            # int case
            converted = list(range(int(args["start"]), int(args["stop"]), int(args["step"])))
            if (args["stop"] - args["start"]) % args["step"] == 0:
                converted.append(int(args["stop"]))
        else:
            # float case
            def get_num_decimal_places(n: float) -> int:
                ctx = decimal.Context()
                d = ctx.create_decimal(repr(n))
                return len(format(d, "f").split(".")[1])

            m = max(
                get_num_decimal_places(args["start"]),
                get_num_decimal_places(args["stop"]),
                get_num_decimal_places(args["step"]),
            )
            converted = [round(n, m) for n in np.arange(**args)]  # type: ignore
            if ((args["stop"] * (10**m)) - (args["start"]) * (10**m)) % (
                args["step"] * (10**m)
            ) < 10**-10:
                converted.append(args["stop"])  # type: ignore

        return converted

    def _search_combo_and_format_tuple(self, param_dict: dict) -> None:
        for k, v in param_dict.items():
            if isinstance(v, dict):
                if "Combination" in v.keys():
                    self._combo_params.append(k)
                    if isinstance(v["Combination"], str):
                        v["Combination"] = self._convert_tuple_to_list(v["Combination"])  # format
                    self._combo_values.append(v["Combination"])
                elif "Random" in v.keys() and isinstance(v["Random"], str):
                    v["Random"] = self._convert_tuple_to_list(v["Random"])
                else:
                    self._search_combo_and_format_tuple(v)
