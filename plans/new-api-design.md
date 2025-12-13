New principles for aggregates with GUID ids

GET /aggregate/all - provides list of all ids. It won't be used, just for the sake of completenes
GET /aggregate/by_id/{id} - get specific aggregate
GET /aggregate/by_plant_id/{plant_id} - get all aggregates for a plant. 
 - Response is {"items": [list of aggregates]}
PUT /aggregate?force=false - create or replace aggregate. The following rules apply
    - If force=false (default value): 
      - If aggreagate already exists, then "server_modified_at" should match value in the database. Reject otherwise with 409 error. Provide error message with conflict explanstion
      - ignore server_modified_at for new instances
      - if server_modified_at match and there are "extra" child entities (matched by id) on server, reject 409 and throw error. Provide error message with conflict explanstion
    - if force=true:
      - ignore server_modified_at
      - mark "extra" child entities on server as deleted
    - In any case server_modified_at should be updated during update/insert
    - Put should never "steal" child entities from other aggreagate. By "stealing" I mean changing parent_entity_id of existing child row.
no DELETE method since all deletes are logical
