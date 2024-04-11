from dataclasses import dataclass

from icd_api.icd_entity import ICDEntity
from icd_api.icd_util import get_params_dicts

search_keys = ["error", "errorMessage", "resultChopped", "wordSuggestionsChopped", "guessType", "uniqueSearchId",
               "words", "destinationEntities"]


@dataclass
class SearchResult:
    error: bool
    error_message: str
    result_chopped: bool
    word_suggestions_chopped: bool
    guess_type: int
    unique_search_id: str
    words: list
    destination_entities: list
    other: dict

    @classmethod
    def from_api(cls, **params):
        # create ICDEntity objects out of destinationEntities
        de_dicts = params.pop("destinationEntities")
        for de_dict in de_dicts:
            de_dict["@id"] = de_dict["id"]
        destination_entities = [ICDEntity.from_api(entity_id=de["id"], response_data=de) for de in de_dicts]
        params["destinationEntities"] = destination_entities

        params, other = get_params_dicts(response_data=params, known_keys=search_keys)
        return cls(**params, other=other)
