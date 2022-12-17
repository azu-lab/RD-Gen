from src.common import Util


class TestUtil:
    def test_ambiguous_equals_s_upper(self):
        assert Util.ambiguous_equals("APPLE", "apple")

    def test_ambiguous_equals_space(self):
        assert Util.ambiguous_equals("ap ple", "apple")
