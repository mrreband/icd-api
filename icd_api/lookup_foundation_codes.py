import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv, find_dotenv
from icd_api import Api

load_dotenv(find_dotenv())

api = Api()
api.set_linearization("mms")


mms_parent_counters = {True: 0, False: 0}

def get_entity_id(uri):
    return uri.split("/")[-1]


def get_foundation_uri(entity_id):
    return f"http://id.who.int/icd/entity/{entity_id}"


@dataclass
class Entity:
    parent_id: str
    parent_label: str
    entity_id: str
    entity_label: str
    parent_count: int
    child_count: int
    true_mms_parent_id: str
    parent_code: str = None
    mms_code: str = None

    @property
    def node_color(self):
        if self.mms_code:
            return "blue"
        return "black"

    @property
    def node_filled(self):
        if self.child_count > 0:
            return "empty"
        return "filled"

    @property
    def node(self):
        return f"{self.node_filled} {self.node_color} circle"


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
    #  - if child is a category with a code in mms --> filled in blue circle
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
        mms_parent_id = get_entity_id(child_lookup["parent"][0])  # todo: can there be multiple?

        if mms_parent_id != entity_id:
            parent_foundation_uri = get_foundation_uri(mms_parent_id)
            parent = api.lookup(parent_foundation_uri)
        else:
            parent = entity
        true_parents[child_name] = parent

    print(true_parents)
    return true_parents


def get_parents(entity_id):
    uri = get_foundation_uri(entity_id=entity_id)
    entity = api.get_entity(entity_id=entity_id)
    lookup_results = api.lookup(foundation_uri=uri)
    entity_parents = entity.get("parent", [])
    lookup_parents = lookup_results.get("parent", [])
    print(entity_parents, lookup_parents)


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


def write_json(data, file_path):
    print(f"write_json -  {file_path}")
    with open(file_path, "w", encoding="utf8") as file:
        file.write(json.dumps(data, indent=4))


def get_leaf_node_lookups(entity_ids):
    print("get_leaf_node_lookups")
    lookups = []
    for entity_id in entity_ids:
        entity_uri = get_foundation_uri(entity_id)
        entity = api.lookup(foundation_uri=entity_uri)
        lookups.append(entity)

    file_path = os.path.join(os.path.dirname(__file__), "output", "leaf_node_lookups.json")
    write_json(data=lookups, file_path=file_path)
    return lookups


def get_all_entity_ids():
    csv_path = r"C:\Users\mr\source\repos\icd-api\output\entities.csv"
    with open(csv_path, "r", encoding="utf8") as csv_file:
        entities = csv_file.readlines()[1:]
        return [int(e.split(",")[0]) for e in entities]


def get_all_entities():
    print("get_all_entities")
    entities = []

    entity_ids = get_all_entity_ids()
    for entity_id in entity_ids:
        entity = api.get_entity(entity_id=entity_id)
        entities.append(entity)

    file_path = os.path.join(os.path.dirname(__file__), "output", "all_entities.json")
    write_json(data=entities, file_path=file_path)
    return entities


def get_leaf_node_entities(entity_ids):
    print("get_leaf_node_entities")
    entities = []
    for entity_id in entity_ids:
        entity = api.get_entity(entity_id=entity_id)
        entities.append(entity)

    file_path = os.path.join(os.path.dirname(__file__), "output", "leaf_node_entities.json")
    write_json(data=entities, file_path=file_path)
    return entities


def get_mms_parent(entity_id):
    """
    Get the parent entity for an entity.

    :return: mms parent entity_id
    :rtype: str
    """
    leaf_node_uri = get_foundation_uri(entity_id=entity_id)

    # api.get_entity returns foundation entity, which may have multiple parents
    leaf_node_entity = api.get_entity(entity_id=entity_id)

    # api.lookup returns the entity within mms linearization, which should have only one parent
    # however it may return 404
    leaf_node_lookup = api.lookup(leaf_node_uri)

    if leaf_node_lookup is None:
        # # this just means the entity is not in mms
        # # so it won't have a parent in mms
        return None

    entity_parent_foundation_uris = leaf_node_entity["parent"]
    true_parent_mms_uri = leaf_node_lookup["parent"][0]
    entity_parent_ids = [get_entity_id(uri) for uri in entity_parent_foundation_uris]
    true_parent_mms_id = get_entity_id(true_parent_mms_uri)
    mms_parent_counters[true_parent_mms_id not in entity_parent_ids] += 1
    # if true_parent_mms_id not in entity_parent_ids:
    #     raise ValueError(f"true parent mms id not in foundation ids for {leaf_node_id}")

    return true_parent_mms_id


def get_mms_parents(leaf_node_ids):
    """
    get mms parent entity_id for each leaf_node_id

    :return: dictionary with key = leaf node id, value = mms parent entity id
    :rtype: dict
    """
    true_parents = dict()
    for leaf_node_id in leaf_node_ids:
        true_parents[leaf_node_id] = get_mms_parent(entity_id=leaf_node_id)
    return true_parents


def load_leaf_nodes():
    icdapi_folder = os.path.dirname(os.path.dirname(__file__))
    output_folder = os.path.join(icdapi_folder, "output")
    leaf_nodes_path = os.path.join(output_folder, "leaf_nodes.json")
    with open(leaf_nodes_path, "r", encoding="utf8") as leaf_nodes_file:
        return json.loads(leaf_nodes_file.read())


if __name__ == '__main__':
    # leaf_nodes = load_leaf_nodes()
    # get_leaf_node_lookups(entity_ids=leaf_nodes)
    # get_leaf_node_entities(entity_ids=leaf_nodes)
    get_all_entities()

    # true_parents = get_mms_parents(leaf_node_ids=leaf_nodes)
    # print(true_parents)

    # get_children(entity_id="2008663041")
    # get_asphyxia_children_details()
