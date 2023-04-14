"""
What could assist me is a spreadsheet listing the ICD categories that have the following URI as their parent.
(uris are in a list in __main__)
The results should be displayed on individual sheets.
"""

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv, find_dotenv

import openpyxl
from openpyxl.styles import Font, Color
from openpyxl.styles.colors import BLUE

from icd_api import Api

load_dotenv(find_dotenv())

api = Api()
api.set_linearization("mms")

output_folder = os.path.join(os.path.dirname(__file__), "output")
target_path = os.path.join(output_folder, "child_categories_for_kathy.xlsx")
os.makedirs(output_folder, exist_ok=True)


@dataclass
class FoundationEntity:
    foundation_uri: str
    title: str
    synonyms: list = None
    exclusions: list = None
    children: list = None

    @property
    def entity_id(self):
        return int(self.foundation_uri.split("/")[-1])

    def __repr__(self):
        return f"{self.entity_id}: {self.title} ({len(self.children)} children)"


def write_xlsx(foundation_entities: list, target_path: str):
    """
    write all data to excel - each list of child entities should be on a separate worksheet
    """

    def set_hyperlink(cell):
        """
        create a hyperlink for a foundation entity
        """
        entity_id = cell.value
        uri = f'https://icd.who.int/dev11/f/en#/http%3a%2f%2fid.who.int%2ficd%2fentity%2f{entity_id}?view=V231H3'
        hyperlink = openpyxl.worksheet.hyperlink.Hyperlink(ref=uri, target=uri)
        cell.hyperlink = hyperlink

        font = Font(color=Color(BLUE), underline='single')
        cell.font = font

    # new workbook
    workbook = openpyxl.Workbook()

    for foundation_entity in foundation_entities:
        # new worksheet
        worksheet = workbook.create_sheet(str(foundation_entity.entity_id))

        # Add headers
        headers = ['depth', 'foundation_uri', 'title', 'child_uri', 'child_mms_code', 'child_title']
        worksheet.append(headers)

        # add a row per child entity
        for item in foundation_entity.children:
            row = [
                item["depth"],
                item["parent_id"],
                item["parent_title"],
                item["entity_id"],
                item["code"],
                item["title"]
            ]
            worksheet.append(row)

        # bold the titles
        bold = Font(bold=True)
        for cell in worksheet[1]:
            cell.font = bold

        # auto size columns
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length

        # convert entity ids to hyperlinks
        for idx, row in enumerate(worksheet.rows):
            if idx > 0:  # skip header
                set_hyperlink(cell=row[1])
                set_hyperlink(cell=row[3])
                worksheet.column_dimensions["A"].width = 6
                worksheet.column_dimensions["B"].width = 14
                worksheet.column_dimensions["D"].width = 14
                worksheet.column_dimensions["E"].width = 15

    workbook.remove(workbook["Sheet"])
    workbook.save(target_path)


def get_en_label(entity: dict, key_name: str):
    return entity[key_name]["@value"]


def get_en_labels(entity: dict, key_name: str):
    label_dicts = entity.get(key_name, [])
    labels = [l["label"]["@value"] for l in label_dicts]
    return labels


def get_entity_children(foundation_entity: FoundationEntity,
                        child_uris: list,
                        child_entities: list,
                        depth: int):
    """
    get all children for the provided foundation entity;
    call recursively for children of children
    """
    if child_entities is None:
        child_entities = []

    for child_uri in child_uris:
        child_id = child_uri.split("/")[-1]
        child_entity = api.get_entity(entity_id=child_id)
        child_lookup = api.lookup(foundation_uri=child_uri) or dict()
        child_code = child_lookup.get("code", "")
        code_exists = any([child_code == ce.get("code", "") for ce in child_entities])

        if child_entity is not None and child_lookup is not None:
            child_entity_dict = {
                "parent_id": foundation_entity.entity_id,
                "parent_title": foundation_entity.title,
                "depth": depth,
                "entity_id": child_id,
                "uri": child_entity["@id"],
                "title": child_entity["title"]["@value"],
                "code": child_code if not code_exists else "",
                "synonyms": get_en_labels(child_entity, "synonym"),
                "exclusions": get_en_labels(child_entity, "exclusion"),
            }

            child_foundation_entity = FoundationEntity(foundation_uri=child_uri,
                                                       title=child_entity_dict["title"],
                                                       synonyms=child_entity_dict["synonyms"],
                                                       exclusions=child_entity_dict["exclusions"],
                                                       children=[])

            child_entities.append(child_entity_dict)

            # these child_uris are specific to mms -- convert them to foundation uris
            grandchild_mms_uris = child_lookup.get("child", [])
            grandchild_entity_ids = [uri.split("/")[-1] for uri in grandchild_mms_uris]
            grandchild_foundation_uris = [f"http://id.who.int/icd/entity/{e}" for e in grandchild_entity_ids]

            grandchild_lookup_uris = child_entity.get("child", [])
            grandchild_foundation_uris.extend(grandchild_lookup_uris)
            grandchild_foundation_uris = list(set(grandchild_foundation_uris))

            get_entity_children(foundation_entity=child_foundation_entity,
                                child_uris=grandchild_foundation_uris,
                                child_entities=child_entities,
                                depth=depth + 1)

    return child_entities


def get_foundation_entities(foundation_uris: list) -> List[FoundationEntity]:
    """
    :return: list of foundation entities with all ancestors
    :rtype: List[FoundationEntity]
    """
    entities = []
    foundation_entities = []
    for foundation_uri in foundation_uris:
        entity_id = int(foundation_uri.split("/")[-1])
        entity = api.get_entity(entity_id=entity_id)
        if entity is not None:
            foundation_entity = FoundationEntity(foundation_uri=foundation_uri,
                                                 title=get_en_label(entity, "title"),
                                                 synonyms=get_en_labels(entity, "synonym"),
                                                 exclusions=get_en_labels(entity, "exclusion"))

            entities.append(foundation_entity)

            child_uris = entity.get("child", [])
            foundation_entity.children = get_entity_children(foundation_entity=foundation_entity,
                                                             child_uris=child_uris,
                                                             child_entities=[],
                                                             depth=1)

            foundation_entities.append(foundation_entity)
        else:
            print(f"{entity_id} DNE")

    return foundation_entities


if __name__ == '__main__':
    foundation_uris = [
        "http://id.who.int/icd/entity/1319316338",
        "http://id.who.int/icd/entity/1003660192",
        "http://id.who.int/icd/entity/1144140024",
        "http://id.who.int/icd/entity/1948641708",
        "http://id.who.int/icd/entity/343867322",
        "http://id.who.int/icd/entity/438849334",
        "http://id.who.int/icd/entity/1144088229",
        "http://id.who.int/icd/entity/1943119179",
        "http://id.who.int/icd/entity/778231924",
        "http://id.who.int/icd/entity/856558301",
        "http://id.who.int/icd/entity/849490973 ",
    ]
    foundation_entities = get_foundation_entities(foundation_uris=foundation_uris)

    write_xlsx(foundation_entities=foundation_entities, target_path=target_path)
