import csv
import json
from typing import Optional


def load_json(file_path: str) -> dict:
    """
    read a json file into a dict

    :param file_path: path to the json file
    :return: dictionary from json.loads
    """
    with open(file_path, "r") as file:
        json_data = json.loads(file.read())
        return json_data


def get_all_keys(data: list[dict]):
    keys = list(set(key for item_dict in data for key in list(item_dict.keys())))
    return keys


def write_csv(data: list, file_path: str, columns: Optional[list] = None):
    if columns is None:
        columns = get_all_keys(data=data)

    output = ['"' + '","'.join(columns) + '"\n']
    for item in data:
        row = '"' + '","'.join([str(item.get(col, "")) for col in columns]) + '"\n'
        output.append(row)
    with open(file_path, "w", encoding="utf8") as output_file:
        output_file.writelines(output)


def load_csv(file_path: str) -> list:
    """
    load a csv into a list
    """
    entities = []
    with open(file_path, "r", encoding="utf8") as file:
        reader = csv.reader(file, delimiter=',')
        headers = next(reader, None)
        if headers is None:
            return entities

        headers[0] = headers[0].lstrip("\ufeff")

        for line in reader:
            values = line
            entity = dict(zip(headers, values))
            entities.append(entity)
    return entities


def write_json(data, file_path: str, indent: int = 4):
    with open(file_path, "w", encoding="utf8") as file:
        file.write(json.dumps(data, indent=indent))
