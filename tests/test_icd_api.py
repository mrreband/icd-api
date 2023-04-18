import json
import os

import pytest as pytest
from dotenv import load_dotenv, find_dotenv

from icd_api import Api, Entity

load_dotenv(find_dotenv())


@pytest.fixture
def api():
    _api = Api()
    _api.set_linearization("mms")
    return _api


def test_api(api):
    api.set_linearization("mms")
    assert api


def test_get_all_children(api):
    root_entity_id = "1301318821"  # higher up: 1920852714  # lower down: 1301318821
    all_entities = api.get_ancestors(root_entity_id)
    parent_folder = os.path.dirname(__file__)
    target_file_path = os.path.join(parent_folder, f"output/{root_entity_id}_children.json")
    with open(target_file_path, "w") as file:
        data = json.dumps(all_entities, default=lambda e: e.__dict__, indent=4)
        file.write(data)

    assert all_entities


def test_get_entity(api):
    entity = api.get_entity("1920852714")
    assert entity

    for child in entity.child_ids:
        print(child)


def test_get_entity_full(api):
    entity = api.get_entity_full("2008663041")
    assert entity

    for child in entity.indirect_children_ids:
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
    if os.getenv("CLIENT_ID") and os.getenv("CLIENT_SECRET"):
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
    entity = api.lookup(foundation_uri=foundation_uri)
    assert isinstance(entity, Entity)
    assert entity.request_type == "lookup"


def test_search_linearization(api):
    results = api.search_linearization(search_string="diabetes")
    assert results


def test_missing_entities():
    """these were missing from the entities output by Api.get_ancestors - check that the api returns 404 for each"""
    api = Api()
    api.set_linearization("mms")
    entity_ids = [1000664379, 1029251439, 1059449428, 1076215290, 1076641430, 1104895717, 1110925902, 1117344084,
                  1130046240, 1147241349, 1219708494, 1233380430, 1249767098, 1252104698, 1252530838, 1274104313,
                  1278087668, 1295619984, 1314209579, 1324098793, 1329167995, 1367002461, 137053351, 1377008485,
                  1379451626, 1386056187, 1429696590, 1447062984, 1450351129, 1471542998, 1488283014, 1488428775,
                  1531867635, 1542941233, 1576332228, 1606080290, 1627131462, 1688071994, 1708364937, 1712884804,
                  1737130163, 1742405136, 1759348926, 1780130598, 1785833770, 1815255902,
                  1857550376, 1873479241, 1892211281, 1896371070, 1901778594, 1908537217, 1918241818, 1952938548,
                  1970407217, 1976940353, 1978089630, 2007596156, 2021399300, 2027662198, 2072376338, 2110178918,
                  2136477741, 2137712626, 21381775, 244158019, 2753503, 296673756, 298183636, 305626317, 309514703,
                  33641403, 341642327, 344029973, 353229912, 353597412, 383282991, 38874374, 404581329, 420567170,
                  457723064, 462864539, 480312815, 512470411, 523854074, 562274788, 564430212, 583544121, 604042066,
                  616163476, 623633507, 627880448, 63119863, 640597431, 641502186, 645959339, 658701543, 678919564,
                  691174964, 730763934, 748187240, 749377975, 749808774, 761201319, 775180288, 799425295, 823901578,
                  832593195, 832742988, 841741921, 844739135, 858244402, 862523453, 936674819, 944000127, 964894896,
                  967467614, 990165161, 992936232]
    for entity_id in entity_ids:
        test = api.get_entity(entity_id)
        assert test is None


if __name__ == '__main__':
    pytest.main(["test_icd_api.py"])
