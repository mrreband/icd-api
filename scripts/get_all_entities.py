import json
import os

from dotenv import load_dotenv, find_dotenv
from icd_api.icd_api import Api

load_dotenv(find_dotenv())

api = Api.from_environment()
api.get_linearization("mms", "2024-01")


data_folder = os.path.join(os.path.dirname(__file__), "data")
entities_folder = os.path.join(data_folder, "entities")
os.makedirs(entities_folder, exist_ok=True)

root_entity_id = "448895267"  # highest level ICD Entity 448895267  # smaller entity for testing: 1301318821; 1208497819
root_ids = {"455013390": "stem_codes_455013390.json", "1920852714": "x_codes_1920852714.json"}


def get_entities_recurse(entities: list,
                         entity_id: str,
                         nested_output: bool,
                         exclude_duplicates: bool = False):
    """
    get everything for an entity:
    """
    icd_entity = api.get_entity(entity_id=entity_id)

    if nested_output:
        icd_entity.child_entities = []

    if exclude_duplicates:
        existing = [e for e in entities if e.entity_id == entity_id]
        if existing:
            # we already processed this entity and by extension its children
            return entities

    entities.append(icd_entity)

    for child_id in icd_entity.child_ids:
        existing = next(iter([e for e in entities if e.entity_id == child_id]), None)
        if existing is None:
            if nested_output:
                recurse_child_entities = icd_entity.child_entities
            else:
                recurse_child_entities = entities
            get_entities_recurse(entities=recurse_child_entities,
                                 entity_id=child_id,
                                 nested_output=nested_output,
                                 exclude_duplicates=exclude_duplicates)
    return entities


def get_all_entities():
    # build the same treeview that's on the side panel here:
    # https://icd.who.int/dev11/f/en#/http%3a%2f%2fid.who.int%2ficd%2fentity%1920852714
    # split up stem codes from extension codes
    # this takes a while if the root node is high up enough
    # if you can run against your own local instance, it's much faster
    # write each chapter to its own file
    for child_id, target_file_name in root_ids.items():
        target_file_path = os.path.join(entities_folder, target_file_name)
        if not os.path.exists(target_file_path):
            print(f"get_all_entities - {child_id}")
            grandchild_entities = get_entities_recurse(
                entities=[],
                entity_id=child_id,
                nested_output=False,
                exclude_duplicates=True
            )

            with open(target_file_path, "w") as file:
                data = json.dumps(grandchild_entities, default=lambda x: x.to_dict(), indent=4)
                file.write(data)
        else:
            print(f"get_all_entities - {child_id}.json already exists")


def dedupe_entities(entities: list):
    """
    get_ancestors tries to remove duplicates but sometimes two recurson paths have the same entity,
    and they don't know about each other
    """
    distinct_ids = set(e["entity_id"] for e in entities)
    if len(distinct_ids) == len(entities):
        print("bypassing dedupe_entities - no dupes found")
        return entities

    print("dedupe_entities")
    deduped = []
    for idx, entity in enumerate(entities):
        if idx % 1000 == 0:
            print(f"dedupe_entities - {idx}")
        if entity["entity_id"] not in [e["entity_id"] for e in deduped]:
            deduped.append(entity)
    return deduped


def load_entities() -> dict or None:
    entities = {}
    for k, v in root_ids.items():
        file_path = os.path.join(entities_folder, v)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf8") as file:
                cached_data = json.loads(file.read())
                if cached_data is None:
                    return None
                entities[k] = cached_data
    return entities


def get_flattened_entity_ids() -> list[dict]:
    entities_dicts = load_entities()
    entities = []
    for k, v in entities_dicts.items():
        existing_ids = [e["entity_id"] for e in entities]
        new_entities = [e for e in v if e["entity_id"] not in existing_ids]
        entities.extend(new_entities)
    return entities


def get_distinct_entity_ids() -> list[str]:
    eids_path = os.path.join(data_folder, "entity_ids.txt")
    if os.path.exists(eids_path):
        with open(eids_path, "r", encoding="utf8") as eids_file:
            eids = eids_file.readlines()
            eids = [eid.rstrip("\n") for eid in eids]
            return eids

    entities_dicts = get_flattened_entity_ids()
    entity_ids = [e["entity_id"] for e in entities_dicts]

    with open(eids_path, "w", encoding="utf8") as target_file:
        target_file.writelines([f"{eid}\n" for eid in entity_ids])

    return entity_ids


if __name__ == '__main__':
    # # to populate ancestors json files (one json per top-level entity)
    # get_all_entities()

    # # to load existing ancestors into one json file (may include duplicates)
    eids = get_distinct_entity_ids()
    print(len(eids))
