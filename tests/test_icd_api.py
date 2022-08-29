import pytest as pytest
from dotenv import load_dotenv, find_dotenv

from icd_api import Api

load_dotenv(find_dotenv())


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
    linearization = api.get_linearisation(linearisation_name=linearization_name)
    assert linearization


def test_get_entity_linearization(api):
    linearization_name = "mms"
    linearization = api.get_entity_linearization(entity_id=1630407678, linearisation_name=linearization_name)
    assert linearization


def test_get_code(api):
    code = api.get_code(icd_version=10, code="M54.5")
    assert code


if __name__ == '__main__':
    pytest.main(["test_icd_api.py"])
