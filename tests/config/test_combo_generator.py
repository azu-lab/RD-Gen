from src.config import ComboGenerator, Config, abbreviation


def get_config_raw_base() -> dict:
    config_raw_base = {
        "Seed": 0,
        "Number of DAGs": 1,
        "Graph structure": {"Number of nodes": {"Combination": [1, 2]}},
        "Properties": {
            "End-to-end deadline": {
                "Ratio of deadline to critical path": {"Combination": "(3, 4, 1)"}
            }
        },
        "Output formats": {
            "Naming of combination directory": "Abbreviation",
            "DAG": {"YAML": True},
        },
    }
    return config_raw_base


class TestComboGenerator:
    def test_convert_tuple_to_list_exist_space(self):
        assert ComboGenerator._convert_tuple_to_list("(1, 2,1)") == [1, 2]

    def test_convert_tuple_to_list_exist_arg_names(self):
        assert ComboGenerator._convert_tuple_to_list("(start=1,stop=2, step=1)") == [1, 2]

    def test_convert_tuple_to_list_int(self):
        assert ComboGenerator._convert_tuple_to_list("(1, 1, 1)") == [1]
        assert ComboGenerator._convert_tuple_to_list("(1, 2, 1)") == [1, 2]
        assert ComboGenerator._convert_tuple_to_list("(1, 6, 2)") == [1, 3, 5]
        assert ComboGenerator._convert_tuple_to_list("(1, 7, 2)") == [1, 3, 5, 7]

    def test_convert_tuple_to_list_float(self):
        assert ComboGenerator._convert_tuple_to_list("(0.1, 0.1, 0.1)") == [0.1]
        assert ComboGenerator._convert_tuple_to_list("(0.1, 0.2, 0.1)") == [0.1, 0.2]
        assert ComboGenerator._convert_tuple_to_list("(0.1, 0.6, 0.2)") == [0.1, 0.3, 0.5]
        assert ComboGenerator._convert_tuple_to_list("(0.1, 0.7, 0.2)") == [0.1, 0.3, 0.5, 0.7]
        assert ComboGenerator._convert_tuple_to_list(
            "(0.00000000001, 0.00000000007, 0.00000000002)"
        ) == [0.00000000001, 0.00000000003, 0.00000000005, 0.00000000007]

    def test_get_num_combos(self):
        config_raw = get_config_raw_base()
        assert ComboGenerator(config_raw).get_num_combos() == 4

    def test_get_combo_iter_dir_name_abbreviation(self):
        config_raw = get_config_raw_base()
        config_raw["Output formats"]["Naming of combination directory"] = "Abbreviation"
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        dir_names = set()
        for dir_name, _, _ in combo_iter:
            dir_names.add(dir_name)

        assert dir_names == {
            f"{abbreviation.TO_ABB['number of nodes']}_1"
            f"_{abbreviation.TO_ABB['ratio of deadline to critical path']}_3",
            f"{abbreviation.TO_ABB['number of nodes']}_2"
            f"_{abbreviation.TO_ABB['ratio of deadline to critical path']}_3",
            f"{abbreviation.TO_ABB['number of nodes']}_1"
            f"_{abbreviation.TO_ABB['ratio of deadline to critical path']}_4",
            f"{abbreviation.TO_ABB['number of nodes']}_2"
            f"_{abbreviation.TO_ABB['ratio of deadline to critical path']}_4",
        }

    def test_get_combo_iter_dir_name_full_spell(self):
        config_raw = get_config_raw_base()
        config_raw["Output formats"]["Naming of combination directory"] = "Full spell"
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        dir_names = set()
        for dir_name, _, _ in combo_iter:
            dir_names.add(dir_name)

        assert dir_names == {
            "NumberOfNodes_1_RatioOfDeadlineToCriticalPath_3",
            "NumberOfNodes_2_RatioOfDeadlineToCriticalPath_3",
            "NumberOfNodes_1_RatioOfDeadlineToCriticalPath_4",
            "NumberOfNodes_2_RatioOfDeadlineToCriticalPath_4",
        }

    def test_get_combo_iter_dir_name_index_of_combination(self):
        config_raw = get_config_raw_base()
        config_raw["Output formats"]["Naming of combination directory"] = "Index of combination"
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        dir_names = set()
        for dir_name, _, _ in combo_iter:
            dir_names.add(dir_name)

        assert dir_names == {
            "Combination_1",
            "Combination_2",
            "Combination_3",
            "Combination_4",
        }

    def test_get_combo_iter_log(self):
        config_raw = get_config_raw_base()
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        for _, log, _ in combo_iter:
            assert log in [
                {"Number of nodes": 1, "Ratio of deadline to critical path": 3},
                {"Number of nodes": 2, "Ratio of deadline to critical path": 3},
                {"Number of nodes": 1, "Ratio of deadline to critical path": 4},
                {"Number of nodes": 2, "Ratio of deadline to critical path": 4},
            ]

    def test_get_combo_iter_config_normal(self):
        config_raw = get_config_raw_base()
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        configs = set()
        for _, _, config in combo_iter:
            assert isinstance(config, Config)
            assert config.number_of_nodes in [1, 2]
            assert config.ratio_of_deadline_to_critical_path in [3, 4]
            configs.add(config)

        assert len(configs) == 4

    def test_get_combo_iter_config_additional(self):
        config_raw = get_config_raw_base()
        config_raw["Properties"]["Additional properties"] = {
            "Node properties": {"New node": {"Combination": [1, 2, 3]}},
            "Edge properties": {"New edge": {"Combination": [4, 5]}},
        }
        combo_iter = ComboGenerator(config_raw).get_combo_iter()
        configs = set()
        for _, _, config in combo_iter:
            assert isinstance(config, Config)
            assert config.additional_properties["Node properties"]["New node"] in [1, 2, 3]
            assert config.additional_properties["Edge properties"]["New edge"] in [4, 5]
            configs.add(config)

        assert len(configs) == 24
