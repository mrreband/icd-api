import os
import json
from collections import defaultdict
from dotenv import load_dotenv, find_dotenv

from icd_api import Api

load_dotenv(find_dotenv())

icdapi_folder = os.path.dirname(os.path.dirname(__file__))
output_folder = os.path.join(icdapi_folder, "output")
root_entity_path = os.path.join(output_folder, "root_entity.json")
children_csv_path = os.path.join(output_folder, "children.json")
parents_csv_path = os.path.join(output_folder, "parents.json")
filtered_output_path = os.path.join(output_folder, "children_with_multiple_parents.json")
root_entity_id = 448895267


def get_aggregates(file_path: str):
    with open(file_path, "r", encoding="utf8") as file:
        detail = file.readlines()
        detail = [c.strip("\n").split(",") for c in detail]
        detail = [{"key": c[0], "value": c[1]} for c in detail]

        aggregates = defaultdict(lambda: 0)
        for item in detail:
            aggregates[item["value"]] += 1
    return aggregates


def get_children_with_multiple_parents(entities: list, results: list):
    for entity in entities:
        if entity["parent_count"] > 0:
            results.append(entity)
            return get_children_with_multiple_parents(entities=entity.get("child_entities", []), results=results)
    write_json(data=results, file_path=filtered_output_path)
    return results


def load_all():
    data = dict()
    with open(r"C:\Users\mr\source\repos\icd-api\output\root_entity.json", "r", encoding="utf8") as file:
        data["entities"] = json.loads(file.read())
    data["children"] = get_aggregates(file_path=r"C:\Users\mr\source\repos\icd-api\output\children.csv")
    data["parents"] = get_aggregates(file_path=r"C:\Users\mr\source\repos\icd-api\output\parents.csv")
    return data


def get_counts(entities, parents):
    for entity in entities:
        entity["child_count"] = len(entity.get("child_entities", []))
        entity["parent_count"] = parents.get(str(entity["entity_id"]), 0)
        get_counts(entities=entity.get("child_entities", []), parents=parents)

    write_json(data=entities, file_path=os.path.join(output_folder, "all_entities.json"))
    return entities


def write_json(data, file_path):
    with open(file_path, "w", encoding="utf8") as file:
        file.write(json.dumps(data, indent=4))


def get_leaf_nodes():
    api = Api()
    leaf_nodes = api.get_leaf_nodes(entity_id=root_entity_id)
    leaf_node_path = os.path.join(output_folder, "leaf_nodes.json")
    write_json(data=leaf_nodes, file_path=leaf_node_path)
    print(len(leaf_nodes))


if __name__ == '__main__':
    # data = load_all()
    # get_counts(entities=data["entities"], parents=data["parents"])
    # get_children_with_multiple_parents(entities=data["entities"], results=[])
    # print(data)
    get_leaf_nodes()