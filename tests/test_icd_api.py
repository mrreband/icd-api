import os

import pytest as pytest
from dotenv import load_dotenv, find_dotenv

from icd_api import Api, ICDLookup

load_dotenv(find_dotenv())


@pytest.fixture(scope="session")
def api():
    _api = Api.from_environment()
    _api.set_linearization("mms", release_id="2023-01")
    return _api


def test_api(api):
    assert api
    assert api.current_release_id == "2023-01"


def test_set_linearization():
    # create a separate Api object so as to not contaminate the fixture
    test = Api.from_environment()
    linearization = test.set_linearization("mms", "2024-01")
    assert linearization
    assert test.current_release_id == "2024-01"


def test_get_all_children(api):
    root_entity_id = "1301318821"  # higher up: 1920852714  # lower down: 1301318821
    all_entities = api.get_ancestors(root_entity_id, entities=[])
    assert all_entities


def test_get_entity(api):
    entity = api.get_entity("1920852714")
    assert entity

    for child in entity.child_ids:
        print(child)


def test_get_linearization_entity(api):
    entity = api.get_linearization_entity(entity_id="1376721186")
    assert entity
    assert "136616595" not in entity.child_ids


def test_get_linearization_descendants(api):
    descendants = api.get_linearization_descendent_ids(entity_id="1376721186")
    assert descendants


def test_get_linearization_ancestors(api):
    ancestors = api.get_linearization_ancestor_ids(entity_id="1376721186")
    assert ancestors


def test_get_foundation_child_elsewhere(api):
    linearization_entity = api.get_linearization_entity(entity_id="1376721186")
    assert linearization_entity
    assert "136616595" in linearization_entity.foundation_child_elsewhere_ids


def test_get_entity_full(api):
    entity = api.get_entity_full("2008663041")
    assert entity.entity_id
    assert entity.lookup


def test_search_entities(api):
    search_results = api.search_entities(search_string="diabetes")
    assert search_results


def test_get_entity_linearization(api):
    linearization_name = "mms"
    linearization = api.get_entity_linearization_releases(entity_id=1630407678, linearization_name=linearization_name)
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
    assert isinstance(entity, ICDLookup)
    assert entity.request_type == "lookup"


def test_lookup_residual(api):
    foundation_uri = "http://id.who.int/icd/entity/1008196289"
    entity = api.lookup(foundation_uri=foundation_uri)
    assert isinstance(entity, ICDLookup)
    assert entity.is_residual
    assert entity.residual == "unspecified"


def test_search_linearization(api):
    results = api.search_linearization(search_string="diabetes")
    assert results


def test_get_residual(api):
    results = api.get_residual_codes(entity_id="515117475")
    assert results["Y"]["code"] == "1A09.Y"
    assert results["Z"]["code"] == "1A09.Z"

    results = api.get_residual_codes(entity_id="78422942")
    assert results["Y"] is None
    assert results["Z"]["code"] == "1A11.Z"

    results = api.get_residual_codes(entity_id="1777228366")
    assert results["Y"]["code"] == "1A36.1Y"
    assert results["Z"] is None


def test_missing_entities(api):
    """these were missing from the entities output by Api.get_ancestors - check that the api returns 404 for each"""
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


def test_cache_nocache():
    # api with no cache
    os.environ["ICDAPI_REQUESTS_CACHE_NAME"] = ""
    _api = Api.from_environment()
    assert _api.use_cache is False

    # api with cache
    os.environ["ICDAPI_REQUESTS_CACHE_NAME"] = "sure why not"
    _api = Api.from_environment()
    assert _api.use_cache is True

    # cleanup (del bc it has a lock on the sqlite file)
    del _api
    if os.path.exists("sure why not.sqlite"):
        os.remove("sure why not.sqlite")


if __name__ == '__main__':
    pytest.main(["test_icd_api.py"])
