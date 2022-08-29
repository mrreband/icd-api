import pytest as pytest

from icd_11_api import Api


@pytest.fixture
def api():
    return Api()


def test_get_entity(api):
    entity = api.get_entity(455013390)
    assert entity

    for child in entity["child"]:
        print(child)


def test_search_entities(api):
    search_results = api.search_entities(search_string="diabetes")
    assert search_results


if __name__ == '__main__':
    pytest.main(["test_icd_11_api.py"])
