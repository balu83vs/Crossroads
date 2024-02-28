import pytest
from contextlib import nullcontext as does_not_raise


from not_assyncio_way.main import AvtoTrafficLight, Camera

@pytest.fixture
def lights():
    test_light = AvtoTrafficLight(1, Camera(), False)
    return test_light


pytest.mark.usefixtures("lights")
class TestAvtoTrafficLight:

    def test_initial_states(self, lights):
        assert lights.get_state() == 'RED'


    @pytest.mark.parametrize (
            "color, result, expectation",
            [('RED', 'RED', does_not_raise()),
            ('YELLOW', 'YELLOW', does_not_raise()),
            ('GREEN', 'GREEN', does_not_raise()),
            (1, 'RED', pytest.raises(TypeError)),
            (1.5, 'RED', pytest.raises(TypeError))]
    )
    def test_set_states(self, color, result, expectation, lights):
        with expectation:
            lights.set_state(color)
            assert lights.get_state() == result