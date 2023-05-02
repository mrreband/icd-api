import csv
import json


def load_json(file_path: str) -> dict:
    """
    read a json file into a dict

    :param file_name: path to the json file
    :return: dictionary from json.loads
    """
    with open(file_path, "r") as file:
        json_data = json.loads(file.read())
        return json_data


def write_csv(data: list, file_path: str):
    columns = list(data[0].keys())
    output = [",".join(columns) + "\n"]
    for item in data:
        row = ",".join([str(item.get(col, "")) for col in columns]) + "\n"
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
        headers[0] = headers[0].lstrip("\ufeff")

        for line in reader:
            values = line
            entity = dict(zip(headers, values))
            entities.append(entity)
    return entities


def write_json(data, file_path, indent: int or None = 4):
    with open(file_path, "w", encoding="utf8") as file:
        file.write(json.dumps(data, indent=indent))
