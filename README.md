# ICD 11 API Requests library 

Forked from [Python-samples](https://github.com/ICD-API/Python-samples)

Client for requesting the [ICD REST API](https://icd.who.int/icdapi/)


Usage: 
- get a client id and secret from [ICD API Access Keys](https://icd.who.int/icdapi/Account/AccessKey)
- add your CLIENT_ID and CLIENT_SECRET to a .env file (see env.sample for reference)
- make an instance of Api class:

```python
from icd_11_api import Api
api = Api()
```
- use the api class to make requests: 
  - request a specific entity: 
  ```python
  api.get_entity(entity_id=455013390)
  ```
  - search for entities: 
  ```python
  api.search_entities(search_string="condition")
  ```
