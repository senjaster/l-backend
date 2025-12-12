I need a python rest service to serve the database described by @ddl.sql

# Application design
Generally, this app should not handle any business logic. Entire app is a remote repository for mobile app, so it should transparently serve data from the database.

There should be 3 layers
1) Repository layer. It should use pugsql to read and write tables.
2) Domain models should be defined using pydantic.
3) FastAPI should serve models over the http.

Use same pydantic models both for fastapi and for repos. I know that it's a violation of SRP principle, but it's ok for such a simple service

# API

0) REST api
1) Each aggregate should be served on a separate endpoint, they should not be nested.
2) There should be GET, PUT and DELETE operations 
 - GET /aggregate/{id}
 - PUT /aggregate/{id} - replace or create entire aggregate. May logically delete child entities. It should not internally delete and insert all aggregate rows, it should do updates.
 - DELETE /aggregate/{id} - logically delete entire aggregate
 3) There should be some custom methods:
 - POST /plant/{id}/locked
 - POST /plant/{id}/unlocked

 You may read ddd-aggregates.md for general domain knowlege, but you should not try to implement business rules. ddl.sql contains actual database structure, and  ddd-aggreagates.md maight be outdated a bit. 
