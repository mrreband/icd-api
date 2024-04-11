from dataclasses import dataclass

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
        params, other = get_params_dicts(response_data=params, known_keys=search_keys)
        return cls(**params, other=other)
