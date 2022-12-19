import random

import pytest

from src.property_setter.property_setter_base import PropertySetterBase


class TestPropertySetterBase:
    @pytest.mark.parametrize("sum", list(range(1, 30)))
    def test_grouping_normal(self, sum):
        if sum == 1:
            num_groups = 1
        else:
            num_groups = random.randint(1, sum)

        grouping = PropertySetterBase._grouping(sum, num_groups)
        assert len(grouping) == num_groups
        after_sum = 0
        for v in grouping:
            assert isinstance(v, int)
            assert v >= 1
            after_sum += v
        assert after_sum == sum

    def test_grouping_infeasible(self):
        assert not PropertySetterBase._grouping(1, 10)
