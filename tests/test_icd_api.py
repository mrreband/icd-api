import pytest as pytest

from icd_api import Api


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


def test_get_linearization(api):
    # are there any valid linearisations besides 'mms'?
    linearization_name = "mms"
    linearization = api.get_linearization(linearisation_name=linearization_name)
    assert linearization
    for release_url in linearization["release"]:
        release_id = release_url.strip("/mms").split("/")[-1]
        release = api.get_linearization(linearisation_name=linearization_name, release_id=release_id)
        assert release


if __name__ == '__main__':
    pytest.main(["test_icd_api.py"])
