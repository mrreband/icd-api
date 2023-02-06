import json
import os

import pytest as pytest
from dotenv import load_dotenv, find_dotenv

from icd_api import Api

load_dotenv(find_dotenv())


@pytest.fixture
def api():
    _api = Api()
    _api.set_linearization("mms")
    return _api


def test_get_all_children(api):
    root_entity_id = 1301318821  # higher up: 1920852714  # lower down: 1301318821
    all_entities = api.get_ancestors(root_entity_id)
    parent_folder = os.path.dirname(__file__)
    target_file_path = os.path.join(parent_folder, f"output/{root_entity_id}_children.json")
    with open(target_file_path, "w") as file:
        data = json.dumps(all_entities, indent=4)
        file.write(data)

    assert all_entities

def test_get_entity(api):
    entity = api.get_entity(1920852714)
    assert entity

    for child in entity["child"]:
        print(child)


def test_search_entities(api):
    search_results = api.search_entities(search_string="diabetes")
    assert search_results


def test_set_linearization(api):
    # are there any valid linearizations besides 'mms'?
    linearization_name = "mms"
    linearization = api.set_linearization(linearization_name=linearization_name)
    assert linearization


def test_get_entity_linearization(api):
    linearization_name = "mms"
    linearization = api.get_entity_linearization(entity_id=1630407678, linearization_name=linearization_name)
    assert linearization


def test_get_code_icd_10(api):
    code = api.get_code(icd_version=10, code="M54.5")
    assert code["@context"]
    assert code["@id"]
    assert code["title"]
    assert code["latestRelease"]
    assert code["release"]


def test_get_code_icd_11(api):
    code = api.get_code(icd_version=11, code="ME84.2")
    assert code["@context"]
    assert code["@id"]
    assert code["code"]
    assert code["stemId"]


def test_lookup(api):
    foundation_uri = "http://id.who.int/icd/entity/1435254666"
    results = api.lookup(foundation_uri=foundation_uri)
    assert results["@context"]
    assert results["@id"]
    assert results["parent"]
    assert results["browserUrl"]
    assert results["code"]
    assert results["classKind"]
    assert results["title"]
    assert results["relatedEntitiesInPerinatalChapter"]
    assert results["indexTerm"]


def test_search_linearization(api):
    results = api.search_linearization(search_string="diabetes")
    assert results


if __name__ == '__main__':
    pytest.main(["test_icd_api.py"])
