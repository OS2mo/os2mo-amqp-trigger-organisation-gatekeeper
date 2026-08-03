import pytest

# TODO(#70974): two tests are needed for the integration test pipeline to work,
#   these will be replaced by actual tests soon


@pytest.mark.integration
async def test_dummy_1():
    assert True


@pytest.mark.integration
async def test_dummy_2():
    assert True
