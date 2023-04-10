from dotenv import load_dotenv, find_dotenv
from icd_api import Api

load_dotenv(find_dotenv())

api = Api()
api.set_linearization("mms")


def get_entity_id(uri):
    return uri.split("/")[-1]


def get_foundation_uri(entity_id):
    return f"http://id.who.int/icd/entity/{entity_id}"


def get_children(entity_id):
    """
    get all foundation children of an entity,
    along with the MMS parent of each, which may or may not be the provided entity

    :param entity_id: id of the entity to traverse
    :return:the true mms parents of each child entity of the provided entity
    :rtype: dict
    """
    # todo: results should include the following (some are nullable)
    #  - parent_id, parent_label, parent_code, child_id, child_label, child_code, candidate_parent_count, true_parent
    #  - if parent is not the true parent --> gray line in lineage
    #  - if parent is the true parent --> blue line in lineage
    #  - if child is a chapter or block or parent category --> empty blue circle
    #  - if child is a caetgory with a code in mms --> filled in blue circle
    #  - if child doesn't have a code in mms --> empty black circle
    entity = api.get_entity(entity_id=entity_id)
    child_foundation_uris = entity["child"]
    true_parents = dict()
    for child_foundation_uri in child_foundation_uris:
        # get info about the child entity
        child_id = get_entity_id(uri=child_foundation_uri)
        child_entity = api.get_entity(entity_id=child_id)
        child_name = child_entity["title"]["@value"]

        # use api.lookup to get info about the child's true mms parent(s)
        child_lookup = api.lookup(child_foundation_uri)
        mms_parent_id = get_entity_id(child_lookup["parent"][0])

        if mms_parent_id != entity_id:
            parent_foundation_uri = get_foundation_uri(mms_parent_id)  # todo: can there be multiple?
            parent = api.lookup(parent_foundation_uri)
        else:
            parent = entity
        true_parents[child_name] = parent

    print(true_parents)
    return true_parents


def get_asphyxia_children_details():
    """
    hard-coded version of get_children() - uses the example described by MP
    """
    entity_ids = dict(asphyxia="2008663041",
                      hypoxia="474887737",
                      anoxia="1211091398",
                      birth_asphyxia="848321559",
                      intrauterine_hypoxia="1474007427")
    entity_names = dict((v, k) for k, v in entity_ids.items())
    foundation_uris = dict((k, get_foundation_uri(v)) for k, v in entity_ids.items())
    lookup_results = dict((k, api.lookup(v)) for k, v in foundation_uris.items())

    for k, v in lookup_results.items():
        v["parent_ids"] = [p.split("/")[-1] for p in v["parent"]]
        v["parent_names"] = [entity_names.get(p, None) for p in v["parent_ids"]]
        v["parent_lookup"] = []
        for parent_id, parent_name in zip(v["parent_ids"], v["parent_names"]):
            if parent_name is None:
                parent_foundation_uri = get_foundation_uri(parent_id)
                parent = api.lookup(parent_foundation_uri)
                v["parent_lookup"].append(parent)
            else:
                v["parent_lookup"].append(lookup_results[parent_name])

    print(lookup_results)
    return lookup_results


if __name__ == '__main__':
    get_children(entity_id="2008663041")
    # get_asphyxia_children_details()

