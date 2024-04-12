import re


def get_entity_id(uri: str):
    return uri.split("/")[-1]


def get_foundation_uri(entity_id: str):
    return f"http://id.who.int/icd/entity/{entity_id}"


def get_linearization_uri(entity_id: str, linearization_name: str):
    return f"http://id.who.int/icd/release/11/beta/{linearization_name}/{entity_id}"


def get_mms_uri(entity_id: str):
    return get_linearization_uri(entity_id=entity_id, linearization_name="mms")


def camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def get_params_dicts(response_data: dict, known_keys: list):
    camel_params = dict((k, v) for k, v in response_data.items() if k in known_keys)
    snake_params = dict((camel_to_snake(k), v) for k, v in camel_params.items())

    camel_other = dict((k, v) for k, v in response_data.items() if k not in known_keys)
    snake_other = dict((camel_to_snake(k), v) for k, v in camel_other.items())
    return snake_params, snake_other


def get_value(value: dict) -> str:
    """extract just the text of a label, e.g.
    title = { "@language": "en", "@value": "Central nervous system" }
    result = process_labels (title)
    assert result == "Central nervous system"
    """
    return value["@value"]


def process_labels(labels: list, language: str = "en") -> list[str]:
    """extract the text all labels, in the specified language"""
    return [get_value(label) for label in labels if label["@language"] == language]


def process_inclusions(inclusions) -> list[dict[str, str]]:
    """extract the label and foundation reference"""
    return [{"label": value["label"]["@value"], "foundationReference": value.get("foundationReference", None)}
            for value in inclusions]


def process_fcr(exclusions) -> list[dict[str, str]]:
    """extract the label, foundation reference, linearization reference - both refs have the same entity id"""
    return [{"label": value["label"]["@value"],
             "foundationReference": value.get("foundationReference", None),
             "linearizationReference": value.get("linearizationReference", None)}
            for value in exclusions]


def flatten_labels(obj: dict):
    for label_field in obj.keys():
        if isinstance(obj[label_field], dict):
            if "@language" in obj[label_field].keys() and "@value" in obj[label_field].keys():
                obj[label_field] = get_value(obj[label_field])
        elif isinstance(obj[label_field], list):
            for item in obj[label_field]:
                if isinstance(item, dict) and "label" in item.keys():
                    item["label"] = get_value(item["label"])
    return obj
