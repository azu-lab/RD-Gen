import random
from typing import Generator, Tuple

import networkx as nx

from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError, InfeasibleConfigError
from .dag_builder_base import DAGBuilderBase


class FanInFanOutBuilder(DAGBuilderBase):
    """Fan-in/fan-out class."""

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self._max_out = (
            max(self._config.out_degree)
            if isinstance(self._config.out_degree, list)
            else self._config.out_degree
        )
        self._max_in = (
            max(self._config.in_degree)
            if isinstance(self._config.in_degree, list)
            else self._config.in_degree
        )

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
        number_of_entry_nodes = Util.get_option_min(config.number_of_entry_nodes)
        number_of_exit_nodes = Util.get_option_min(config.number_of_exit_nodes) or 1
        number_of_nodes = Util.get_option_max(config.number_of_nodes)
        if number_of_entry_nodes + number_of_exit_nodes > number_of_nodes:  # type: ignore
            raise InfeasibleConfigError(
                "'Number of source nodes' + 'Number of exit nodes' > 'Number of nodes'"
            )

    def build(self) -> Generator:
        """Build DAG using fan-in/fan-out method.

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
            num_build_fail = 0

            # Determine number_of_nodes (Loop finish condition)
            num_nodes = Util.random_choice(self._config.number_of_nodes)
            num_exit = self._config.number_of_exit_nodes
            if num_exit:
                num_exit = Util.random_choice(num_exit)
                num_nodes -= num_exit

            # Initialize dag
            num_entry = Util.random_choice(self._config.number_of_entry_nodes)
            G = self._init_dag(num_entry)

            while G.number_of_nodes() != num_nodes:
                if Util.true_or_false():
                    # Fan-out
                    max_diff_node_i, diff = self._search_max_diff_node(G)
                    num_add = random.randint(1, diff)
                    add_node_i_list = [G.number_of_nodes() + i for i in range(num_add)]
                    nx.add_star(G, [max_diff_node_i] + add_node_i_list)

                else:
                    # Fan-in
                    num_sources = random.randint(1, self._max_in)
                    nodes = list(G.nodes())
                    random.shuffle(nodes)
                    sources = []
                    for node_i in nodes:
                        if G.out_degree(node_i) < self._max_out:
                            sources.append(node_i)
                            if len(sources) == num_sources:
                                break

                    add_node_i = G.number_of_nodes()
                    G.add_node(add_node_i)
                    for source_node_i in sources:
                        G.add_edge(source_node_i, add_node_i)

                # Check build fail
                if G.number_of_nodes() > num_nodes:
                    num_build_fail += 1
                    if num_build_fail == self._max_try:
                        msg = (
                            "A DAG satisfying 'Number of nodes' could not be built "
                            f"in {self._max_try} tries."
                        )
                        raise BuildFailedError(msg)
                    else:
                        G = self._init_dag(num_entry)  # reset

            # Add exit nodes (Optional)
            if num_exit:
                self._force_create_exit_nodes(G, num_exit)

            # Ensure weakly connected (Optional)
            if self._config.ensure_weakly_connected:
                self._ensure_weakly_connected(G, True, bool(num_exit))

            yield G

    def _search_max_diff_node(self, G: nx.DiGraph) -> Tuple[int, int]:
        """Search max difference node.

        Find the node with the biggest difference
        between its out-degree and max value of 'out-degree' parameter.

        Returns
        -------
        Tuple[int, int]
            - Index of node with the biggest difference
            - Difference size

        """
        min_out_i = Util.get_min_out_node(G, G.nodes)
        max_diff = self._max_out - G.out_degree(min_out_i)

        return min_out_i, max_diff

    def _init_dag(self, num_entry: int) -> nx.DiGraph:
        G = nx.DiGraph()
        for _ in range(num_entry):
            G.add_node(G.number_of_nodes())

        return G
