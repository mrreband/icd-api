"""
crawl all icd10 codes, from the chapters recursively down to leaf nodes
note: a locally deployed instance of the WHO ICD API does not contain ICD10 endpoints,
      so this needs to run against their public API.
      as such, be considerate and use throttling
"""
import os
import json

from dotenv import load_dotenv, find_dotenv
from icd_api import Api

load_dotenv(find_dotenv())


def get_root_codes(api):
    root_uri = "release/10/2019"
    root_data = api.get_uri(root_uri)
    target_folder = f"output/ICD10/depth 01"
    os.makedirs(target_folder, exist_ok=True)

    for child in root_data["child"]:
        child_data = api.get_url(child)
        child_id = child_data["@id"].split("/")[-1]
        target_file_path = f"{target_folder}/{child_id}.json"
        if not os.path.exists(target_file_path):
            child_data_items = api.get_url_recurse(child, [])
            with open(target_file_path, "w") as file:
                json_data = json.dumps(child_data_items, indent=4)
                file.write(json_data)


def get_files(root_folder, targets: list):
    local_targets = list(os.walk(root_folder))
    for local_target in local_targets:
        root_dir, _, local_files = local_target
        local_file_paths = [os.path.join(root_dir, file) for file in local_files]
        targets.extend(local_file_paths)

    return targets


def get_next_depth(api: Api, depth: int):
    """
    traverse existing json files, get all of their children, and write them as separate json files
    """
    if depth == 1:
        get_root_codes(api=api)
        return

    root_folder = f"../tests/output/ICD10/depth 0{depth - 1}"
    output_folder = f"../tests/output/ICD10/depth 0{depth}"
    os.makedirs(output_folder, exist_ok=True)
    for file_path in get_files(root_folder, []):
        with open(file_path, "r", encoding="utf8") as input_file:
            text = input_file.read()
            json_data = json.loads(text)
            if isinstance(json_data, dict):
                json_data = [json_data]
            for root_data in json_data:
                for child in root_data.get("child", []):
                    child_id = child.split("/")[-1]
                    target_file_path = f"{output_folder}/{child_id}.json"
                    test = f"{root_folder}/{child_id}.json"
                    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                    if not os.path.exists(target_file_path) and not os.path.exists(test):
                        child_data_items = api.get_url_recurse(child, [])
                        with open(target_file_path, "w") as output_file:
                            json_data = json.dumps(child_data_items, indent=4)
                            output_file.write(json_data)


def merge_json_files():
    """
    concatenate json files
    """
    for i in range(1, 6):
        depth = f"depth 0{i}"
        root_folder = f"../tests/output/ICD10/{depth}"
        print(f"processing {root_folder}")
        targets = os.walk(root_folder)
        codes = {}
        for _, folder_paths, file_names in targets:
            for file_name in file_names:
                file_path = os.path.join(_, file_name)
                with open(file_path, "r", encoding="utf8") as file:
                    json_data = json.loads(file.read())
                    if isinstance(json_data, dict):
                        json_data = [json_data]
                    for json_code in json_data:
                        code_url = json_code["@id"]
                        code_id = code_url.split("/")[-1]
                        codes[code_id] = json_code

        with open(f"../tests/output/icd10 who api - {depth}.json", "w") as output_file:
            output_data = json.dumps(codes, indent=4)
            output_file.write(output_data)


def normalize_json():
    print("normalize_json")
    file_paths = {
        1: "../tests/output/icd10 who api - depth 01.json",
        2: "../tests/output/icd10 who api - depth 02.json",
        3: "../tests/output/icd10 who api - depth 03.json",
        4: "../tests/output/icd10 who api - depth 04.json",
        5: "../tests/output/icd10 who api - depth 05.json",
    }
    results = []
    for depth, file_path in file_paths.items():
        with open(file_path, "r", encoding="utf8") as file:
            data = json.loads(file.read())
            for code, detail in data.items():
                class_kind = detail["classKind"]
                parent = detail["parent"][0].split("/")[-1]
                title = detail["title"]
                description = title["@value"]
                results.append(f"{parent}|{code}|{depth}|{class_kind}|{description}\n")

    results.sort()
    output_path = "../tests/output/icd10 who api.csv"
    with open(output_path, "w", encoding="utf8") as output_file:
        output_file.write("Parent|Code|Depth|ClassKind|Description\n")
        output_file.writelines(results)


if __name__ == '__main__':
    # api = Api()
    # get_next_depth(api=api, depth=5)
    merge_json_files()
    normalize_json()
