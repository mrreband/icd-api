"""
crawl all icd10 codes, from the chapters recursively down to leaf nodes
note: a locally deployed instance of the WHO ICD API does not contain ICD10 endpoints,
      so this needs to run against their public API.
      as such, be considerate and use throttling
"""
import os
import json
from typing import List

import urllib3

from dotenv import load_dotenv, find_dotenv
from icd_api import Api

load_dotenv(find_dotenv())
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
output_folder = os.path.join(os.path.dirname(__file__), "output", "icd10")


def get_root_codes(api):
    """
    Get the root icd 10 code and its children
    """
    print(f"get_root_codes")
    root_uri = "release/10/2019"
    root_data = api.get_uri(root_uri)
    target_folder = os.path.join(output_folder, "depth 01")
    if os.path.exists(target_folder):
        print(f"{target_folder} already exists")
        return

    for child in root_data["child"]:
        child_data = api.get_url(child)
        child_id = child_data["@id"].split("/")[-1]
        target_file_path = f"{target_folder}/{child_id}.json"
        if not os.path.exists(target_file_path):
            child_data_items = api.get_icd10_codes(child, [])
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            with open(target_file_path, "w") as file:
                json_data = json.dumps(child_data_items, indent=4)
                file.write(json_data)


def get_files(root_folder, targets: list) -> List[str]:
    """
    :return: get results of os.walk as a list of file paths
    :rtype: List[str]
    """
    local_targets = list(os.walk(root_folder))
    for local_target in local_targets:
        root_dir, _, local_files = local_target
        local_file_paths = [os.path.join(root_dir, file) for file in local_files]
        targets.extend(local_file_paths)
    return targets


def get_next_depth(api: Api, depth: int):
    """
    traverse existing json files, get all of their children, and write them as separate json files
    only make requests if the target json file does not exist.
    """
    if depth == 1:
        get_root_codes(api=api)
        return

    print(f"get_next_depth - {depth}")
    parent_depth_folder = os.path.join(output_folder, f"depth 0{depth - 1}")
    target_depth_folder = os.path.join(output_folder, f"depth 0{depth}")

    for file_path in get_files(parent_depth_folder, []):
        with open(file_path, "r", encoding="utf8") as input_file:
            text = input_file.read()
            json_data = json.loads(text)
            if isinstance(json_data, dict):
                json_data = [json_data]
            for root_data in json_data:
                for child in root_data.get("child", []):
                    child_id = child.split("/")[-1]
                    target_file_path = f"{target_depth_folder}/{child_id}.json"
                    test = f"{parent_depth_folder}/{child_id}.json"
                    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                    if not os.path.exists(target_file_path) and not os.path.exists(test):
                        child_data_items = api.get_icd10_codes(child, [])
                        with open(target_file_path, "w") as output_file:
                            json_data = json.dumps(child_data_items, indent=4)
                            output_file.write(json_data)


def get_all_icd10_codes():
    """
    get all icd 10 codes, starting at the top and building downward
    """
    api = Api()
    for i in range(1, 6):
        get_next_depth(api, depth=i)


def merge_json_files():
    """
    concatenate json files
    """
    for i in range(1, 6):
        depth = f"depth 0{i}"
        source_depth_folder = os.path.join(output_folder, str(depth))
        print(f"processing {source_depth_folder}")
        targets = os.walk(source_depth_folder)
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

        target_json_path = os.path.join(output_folder, f"icd10 who api - depth {depth}.json")
        with open(target_json_path, "w") as output_file:
            output_data = json.dumps(codes, indent=4)
            output_file.write(output_data)


def normalize_json():
    print("normalize_json")
    file_paths = dict((i, os.path.join(output_folder, f"icd10 who api - depth 0{i}.json")) for i in range(1, 6))
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
    target_csv_path = os.path.join(output_folder, "icd10 who api.csv")
    with open(target_csv_path, "w", encoding="utf8") as output_file:
        output_file.write("Parent|Code|Depth|ClassKind|Description\n")
        output_file.writelines(results)


if __name__ == '__main__':
    get_all_icd10_codes()
    merge_json_files()
    normalize_json()
