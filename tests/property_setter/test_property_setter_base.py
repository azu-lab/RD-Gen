import pytest
from src.exceptions import InvalidArgumentError
from src.property_setter.property_setter_base import PropertySetterBase


class TestPropertySetterBase:

    def test_grouping_int_01(self):
        g = PropertySetterBase._grouping_int(10, 3)
        assert len(g) == 3
        sum = 0
        for v in g:
            sum += v
        assert sum == 10

    def test_grouping_int_02(self):
        with pytest.raises(InvalidArgumentError) as e:
            PropertySetterBase._grouping_int(10, 11)

        assert str(e.value) == '(sum_value/num_group) < 1.0'
