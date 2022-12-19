import random
from typing import Generator, List, Optional

import networkx as nx

from ..common import Util
from ..config import Config
from ..exceptions import BuildFailedError, InfeasibleConfigError
from .dag_builder_base import DAGBuilderBase


class Chain(nx.DiGraph):
    """Chain class."""

    def __init__(self, start_idx: int) -> None:
        """Constructor.

        Parameters
        ----------
        start_idx : int
            Index of chain head.

        """
        super().__init__()
        self.start_idx: int = start_idx
        self.end_idx: int
        self.main_tail: int

    @property
    def head(self) -> int:
        return self.start_idx

    @property
    def sub_sequence_tails(self) -> List[int]:
        tails = Util.get_exit_nodes(self)
        tails.remove(self.main_tail)
        return tails

    def build_chain(
        self,
        main_sequence_length: int,
        number_of_sub_sequence: Optional[int] = None,
    ) -> None:
        """Build chain.

        Build the chain so that the main sequence is the longest.

        Parameters
        ----------
        main_sequence_length : int
            Main sequence length
        number_of_sub_sequence : Optional[int], optional
            Number of sub sequence, by default None

        """

        def create_sequence(start_idx: int, len_sequence: int) -> None:
            self.add_node(start_idx)
            for i in range(start_idx, start_idx + len_sequence - 1):
                self.add_edge(i, i + 1)

        # Build main sequence
        main_seq_i = [i for i in range(self.start_idx, self.start_idx + main_sequence_length)]
        self.main_tail = self.end_idx = main_seq_i[-1]
        create_sequence(self.start_idx, main_sequence_length)

        # Build sub sequence (Optional)
        if number_of_sub_sequence:
            for _ in range(number_of_sub_sequence):
                src_i = random.choice(main_seq_i[:-1])
                sub_seq_len = main_sequence_length - main_seq_i.index(src_i) - 1
                sub_seq_start_idx = self.end_idx + 1
                create_sequence(sub_seq_start_idx, sub_seq_len)
                self.add_edge(src_i, sub_seq_start_idx)
                self.end_idx = sub_seq_start_idx + sub_seq_len - 1


class ChainBasedDAG(nx.DiGraph):
    """Chain-based DAG class."""

    def __init__(self, chains: List[Chain]) -> None:
        super().__init__()
        self._chains = chains
        for chain in self._chains:
            self.add_nodes_from(chain.nodes)
            self.add_edges_from(chain.edges)

    def vertically_link_chains(
        self, number_of_entry_nodes: int, link_main_tail: bool, link_sub_tail: bool
    ) -> None:
        """Vertically link chains.

        Parameters
        ----------
        number_of_entry_nodes : int
            Number of entry nodes.
        link_main_tail : bool
            Allow link in main sequence tails.
        link_sub_tail : bool
            Allow link in sub sequence tails.

        """
        # Determine source option
        src_chains = set(random.sample(self._chains, number_of_entry_nodes))
        src_option = []
        for chain in src_chains:
            if link_main_tail:
                src_option.append(chain.main_tail)
            if link_sub_tail:
                src_option += chain.sub_sequence_tails

        # Determine targets
        tgt_chains = set(self._chains) - src_chains
        targets = [chain.head for chain in tgt_chains]

        # Add edges
        for tgt_i in targets:
            src_i = Util.get_min_out_node(self, src_option)
            self.add_edge(src_i, tgt_i)

    def merge_chains(
        self, number_of_exit_nodes: int, merge_middle: bool, merge_exit: bool
    ) -> None:
        """Merge chains.

        Parameters
        ----------
        number_of_exit_nodes : int
            Number of exit nodes.
        merge_middle : bool
            Allow merge to middle nodes.
        merge_exit : bool
            Allow merge to exit nodes.

        Raises
        ------
        BuildFailedError
            No merging is possible.

        """
        selected_exits = set(random.sample(Util.get_exit_nodes(self), number_of_exit_nodes))
        sources = set(Util.get_exit_nodes(self)) - set(selected_exits)

        # Determine target option
        tgt_option = set(self.nodes()) - set(Util.get_entry_nodes(self)) - sources
        if not merge_exit:
            tgt_option -= selected_exits
        if not merge_middle:
            tgt_option = selected_exits

        # Add edges
        for src_i in sources:
            _tgt_option = tgt_option - nx.ancestors(self, src_i)
            if not _tgt_option:
                raise BuildFailedError("No merging is possible.")
            tgt_i = Util.get_min_in_node(self, _tgt_option)
            self.add_edge(src_i, tgt_i)


class ChainBasedBuilder(DAGBuilderBase):
    """Chain-based class."""

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
        main_sequence_length = config.main_sequence_length
        number_of_sub_sequences = config.number_of_sub_sequences
        if main_sequence_length == 1 and number_of_sub_sequences:
            raise InfeasibleConfigError(
                "Since the length of 'Main sequence length' is 1, "
                "the sub-sequence cannot be built."
            )

        if config.vertically_link_chains:
            main_sequence_tail = config.main_sequence_tail
            sub_sequence_tail = config.sub_sequence_tail
            if main_sequence_tail is False and sub_sequence_tail is False:
                raise InfeasibleConfigError(
                    "Either 'Main sequence tail' or 'Sub sequence tail' must be set to True."
                )

            number_of_chains = config.number_of_chains
            number_of_entry_nodes = config.number_of_entry_nodes
            if number_of_chains < number_of_entry_nodes:
                raise InfeasibleConfigError("'Number of chains' < 'Number of entry nodes.'")

        if config.merge_chains:
            middle_of_chain = config.middle_of_chain
            exit_node = config.exit_node
            if middle_of_chain is False and exit_node is False:
                raise InfeasibleConfigError(
                    "Either 'Middle of chain' or 'Exit node' must be set to True."
                )

            number_of_chains = config.number_of_chains
            number_of_exit_nodes = config.number_of_exit_nodes
            if number_of_chains * number_of_sub_sequences < number_of_exit_nodes:
                raise InfeasibleConfigError(
                    "'Number of chains' * 'Number of sub sequence' < 'Number of exit nodes.'"
                )

    def build(self) -> Generator[nx.DiGraph, None, None]:
        """Build DAG using chain-based method.

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
                # Build each chain
                chains: List[Chain] = []
                start_idx = 0
                for _ in range(self._config.number_of_chains):
                    chain = Chain(start_idx)
                    main_sequence_length = Util.random_choice(self._config.main_sequence_length)
                    number_of_sub_sequence = (
                        Util.random_choice(self._config.number_of_sub_sequences)
                        if self._config.number_of_sub_sequences
                        else None
                    )
                    chain.build_chain(main_sequence_length, number_of_sub_sequence)
                    chains.append(chain)
                    start_idx = chain.end_idx + 1

                # Create chain-based DAG
                chain_based_dag = ChainBasedDAG(chains)

                # Vertically link chains (optional)
                if self._config.vertically_link_chains:
                    chain_based_dag.vertically_link_chains(
                        Util.random_choice(self._config.number_of_entry_nodes),
                        self._config.main_sequence_tail,
                        self._config.sub_sequence_tail,
                    )

                # Merge chains (optional)
                if self._config.merge_chains:
                    try:
                        chain_based_dag.merge_chains(
                            Util.random_choice(self._config.number_of_exit_nodes),
                            self._config.middle_of_chain,
                            self._config.exit_node,
                        )
                        break
                    except BuildFailedError:
                        if try_i == self._max_try:
                            raise BuildFailedError(
                                f"A DAG could not be built in {self._max_try} tries."
                            )
                        continue

            yield chain_based_dag
