# ICD API Requests library

Forked from [Python-samples](https://github.com/ICD-API/Python-samples)

Client for working with data from the [WHO ICD REST API](https://icd.who.int/icdapi/)

---

## Usage:

- get a client id and secret from [ICD API Access Keys](https://icd.who.int/icdapi/Account/AccessKey)
- make an instance of Api:

```python
from icd_api import Api

# create an instance directly (change `your_client_id` and `your_client_secret`):
api = Api(base_url="https://id.who.int/icd",
          language="en",
          api_version="v2",
          linearization_name="mms",
          release_id="2024-01",
          token_endpoint="https://icdaccessmanagement.who.int/connect/token",
          client_id=your_client_id,
          client_secret=your_client_secret,
          cached_session_config={})

# alternatively, create an instance using environment variables
# add `your_client_id` and `your_client_secret` to a `.env` file
# (see env.sample for a complete reference)
api = Api.from_environment()

```
- use the api class to make requests:
  - get a foundation entity:
  ```python
  api.get_entity(entity_id="455013390")
  ```
  - lookup an entity in the linearization:
  ```python
  api.lookup(entity_id="1944385475")
  ```
  - search for entities:
  ```python
  api.search_entities(search_string="condition")
  ```

---

## Usage with a locally deployed instance:

- [ICD API Local Deployment](https://icd.who.int/docs/icd-api/ICDAPI-LocalDeployment/)
- Local deployments do not have authentication, so `client_id`, `client_secret`, and `token_endpoint` are not required

