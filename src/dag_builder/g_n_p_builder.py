import random
from logging import getLogger
from typing import Generator

import networkx as nx

from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError, InfeasibleConfigError
from .dag_builder_base import DAGBuilderBase

logger = getLogger(__name__)


class GNPBuilder(DAGBuilderBase):
    """G(n, p) class."""

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _validate_config(self, config: Config):
        """Validate config.

        Parameters
        ----------
        config : Config
            Inputted config.

        Raises
        ------
        InfeasibleConfigError
            An infeasible parameter was entered.

        """
        number_of_entry_nodes = Util.get_option_min(config.number_of_entry_nodes) or 1
        number_of_exit_nodes = Util.get_option_min(config.number_of_exit_nodes) or 1
        number_of_nodes = Util.get_option_max(config.number_of_nodes)
        if number_of_entry_nodes + number_of_exit_nodes > number_of_nodes:  # type: ignore
            raise InfeasibleConfigError(
                "'Number of entry nodes' + 'Number of exit nodes' > 'Number of nodes'"
            )

        if Util.get_option_max(config.probability_of_edge) > 1.0:  # type: ignore
            logger.warning("'Probability of edge' > 1.0")

    def build(self) -> Generator[nx.DiGraph, None, None]:
        """Build DAG using G(n, p) method.

        See https://hal.archives-ouvertes.fr/hal-00471255/file/ggen.pdf.

        Yields
        ------
        Generator
            DAG generator.

        Raises
        ------
        BuildFailedError
            The number of build failures exceeded the maximum number of attempts.

        """
        for _ in range(self._config.number_of_dags):
            for try_i in range(1, self._max_try + 1):
                # Determine number_of_nodes
                num_nodes = Util.random_choice(self._config.number_of_nodes)
                num_entry = self._config.number_of_entry_nodes
                if num_entry:
                    num_entry = Util.random_choice(num_entry)
                    num_nodes -= num_entry
                num_exit = self._config.number_of_exit_nodes
                if num_exit:
                    num_exit = Util.random_choice(num_exit)
                    num_nodes -= num_exit

                # Initialize DAG
                G = nx.DiGraph()
                for i in range(num_nodes):
                    G.add_node(G.number_of_nodes())

                # Add edge
                prob_edge = Util.random_choice(self._config.probability_of_edge)
                for i in range(num_nodes):
                    for j in range(num_nodes):
                        if random.randint(1, 100) < prob_edge * 100 and i < j:
                            G.add_edge(i, j)

                # Add entry nodes (Optional)
                if num_entry:
                    self._force_create_entry_nodes(G, num_entry)

                # Add exit nodes (Optional)
                if num_exit:
                    self._force_create_exit_nodes(G, num_exit)

                # Ensure weakly connected (Optional)
                if self._config.ensure_weakly_connected:
                    try:
                        self._ensure_weakly_connected(G, bool(num_entry), bool(num_exit))
                        break
                    except BuildFailedError:
                        if try_i == self._max_try:
                            raise BuildFailedError(
                                f"A DAG could not be built in {self._max_try} tries."
                            )
                        continue

            yield G
