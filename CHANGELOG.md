Changelog
=========

19.08
-----

* A new resource has been added to list contacts from the `conference` backend

  * GET `/0.1/backends/conference/sources/<source_uuid>/contacts`


19.07
-----

* The `personal` service and backend now uses the global `db_uri`. The `db_uri` field is no longer
  part of the body of a personal source
* The `phonebook` service and backend now uses the global `db_uri`. The `db_uri` field is no longer
  part of the body of a phonebook source
* A new resource has been added to configure `conference` backends

  * POST `/0.1/backends/conference/sources`
  * GET `/0.1/backends/conference/sources`
  * GET `/0.1/backends/conference/sources/<source_uuid>`
  * DELETE `/0.1/backends/conference/sources/<source_uuid>`
  * PUT `/0.1/backends/conference/sources/<source_uuid>`


19.06
-----

* A new resource has been added to config lookup `profiles`

  * GET `/0.1/profiles`
  * POST `/0.1/profiles`
  * DELETE `/0.1/profiles/<profile_uuid>`
  * GET `/0.1/profiles/<profile_uuid>`
  * PUT `/0.1/profiles/<profile_uuid>`


19.05
-----

* When performing `GET /directories/lookup/{profile}`, the backend type of every contact is now returned

* A new resource has been added to configure `displays`


  * POST `/0.1/displays`
  * GET `/0.1/displays`
  * DELETE `/0.1/displays/<display_uuid>`
  * GET `/0.1/displays/<display_uuid>`
  * PUT `/0.1/displays/<display_uuid>`


19.03
-----

* A new resource has been added to configure `csv_ws` backends

  * POST `/0.1/backends/csv_ws/sources`
  * GET `/0.1/backends/csv_ws/sources`
  * GET `/0.1/backends/csv_ws/sources/<source_uuid>`
  * DELETE `/0.1/backends/csv_ws/sources/<source_uuid>`
  * PUT `/0.1/backends/csv_ws/sources/<source_uuid>`

* A new resource has been added to configure `csv` backends

  * POST `/0.1/backends/csv/sources`
  * GET `/0.1/backends/csv/sources`
  * GET `/0.1/backends/csv/sources/<source_uuid>`
  * DELETE `/0.1/backends/csv/sources/<source_uuid>`
  * PUT `/0.1/backends/csv/sources/<source_uuid>`

* A new resource has been added to configure `ldap` backends

  * POST `/0.1/backends/ldap/sources`
  * GET `/0.1/backends/ldap/sources`
  * GET `/0.1/backends/ldap/sources/<source_uuid>`
  * DELETE `/0.1/backends/ldap/sources/<source_uuid>`
  * PUT `/0.1/backends/ldap/sources/<source_uuid>`

* A new resource has been added to configure `personal` backends

  * POST `/0.1/backends/personal/sources`
  * GET `/0.1/backends/personal/sources`
  * GET `/0.1/backends/personal/sources/<source_uuid>`
  * DELETE `/0.1/backends/personal/sources/<source_uuid>`
  * PUT `/0.1/backends/personal/sources/<source_uuid>`


19.02
-----

* A new resource has been added to list configured and loaded back-ends

  * GET `/0.1/backends`

* The phonebook API will now return a 404 when the tenant in the URL does not exist

  * POST `/0.1/tenants/<tenant_name>/phonebooks'
  * GET `/0.1/tenants/<tenant_name>/phonebooks'
  * DELETE `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>'
  * GET `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>'
  * PUT `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>'
  * POST `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/contacts/import'
  * POST `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/contacts'
  * GET `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/contacts'
  * DELETE `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/<phonebook_id>/contacts/<contact_id>'
  * GET `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/<phonebook_id>/contacts/<contact_id>'
  * PUT `/0.1/tenants/<tenant_name>/phonebooks/<phonebook_id>/<phonebook_id>/contacts/<contact_id>'

* A new resource has been added to configure `phonebook` backends

  * POST `/0.1/backends/phonebook/sources`
  * GET `/0.1/backends/phonebook/sources`
  * GET `/0.1/backends/phonebook/sources/<source_uuid>`
  * DELETE `/0.1/backends/phonebook/sources/<source_uuid>`
  * PUT `/0.1/backends/phonebook/sources/<source_uuid>`

* A new resource has been added to configure `wazo` backends

  * POST `/0.1/backends/wazo/sources`
  * GET `/0.1/backends/wazo/sources`
  * GET `/0.1/backends/wazo/sources/<source_uuid>`
  * DELETE `/0.1/backends/wazo/sources/<source_uuid>`
  * PUT `/0.1/backends/wazo/sources/<source_uuid>`


16.16
-----

* A new resource has been added to fetch the current configuration of xivo-dird

    * GET `/0.1/config`


16.14
-----

* The `phonebook` backend has been removed in favor of the `dird_phonebook` backend.


16.12
-----

* Added phonebook imports

  * POST `0.1/tenants/<tenant>/phonebooks/<phonebook_id>/contacts/import`


16.11
-----

* Added a new internal phonebook with a CRUD interface
* Added a new backend to do lookups in the new phonebook


15.20
-----

* The ldap plugins `ldap_network_timeout` default value has been incremented from 0.1 to 0.3 seconds


15.19
-----

* Added the `voicemail` type in :ref:`dird-integration-views` configuration
* Removed reverse endpoints in REST API:

  * GET `/0.1/directories/reverse/<profile>/me`


15.18
-----

* Added reverse endpoints in REST API:

  * GET `/0.1/directories/reverse/<profile>/<xivo_user_uuid>`
  * GET `/0.1/directories/reverse/<profile>/me`


15.17
-----

* Added directories endpoints in REST API:

  * GET `/0.1/directories/input/<profile>/aastra`
  * GET `/0.1/directories/lookup/<profile>/aastra`
  * GET `/0.1/directories/input/<profile>/polycom`
  * GET `/0.1/directories/lookup/<profile>/polycom`
  * GET `/0.1/directories/input/<profile>/snom`
  * GET `/0.1/directories/lookup/<profile>/snom`
  * GET `/0.1/directories/lookup/<profile>/thomson`
  * GET `/0.1/directories/lookup/<profile>/yealink`


15.16
-----

* Added more cisco endpoints in REST API:

  * GET `/0.1/directories/input/<profile>/cisco`
* Endpoint `/0.1/directories/lookup/<profile>/cisco` accepts a new `limit` and `offset` query string arguments.


15.15
-----

* Added cisco endpoints in REST API:

  * GET `/0.1/directories/menu/<profile>/cisco`
  * GET `/0.1/directories/lookup/<profile>/cisco`


15.14
-----

* Added more personal contacts endpoints in REST API:

  * GET `/0.1/personal/<contact_id>`
  * PUT `/0.1/personal/<contact_id>`
  * POST `/0.1/personal/import`
  * DELETE `/0.1/personal`

* Endpoint `/0.1/personal` accepts a new `format` query string argument.


15.13
-----

* Added personal contacts endpoints in REST API:

  * GET `/0.1/directories/personal/<profile>`
  * GET `/0.1/personal`
  * POST `/0.1/personal`
  * DELETE `/0.1/personal/<contact_id>`

* Signature of backend method `list()` has a new argument `args`
* Argument `args` for backend methods `list()` and `search()` has a new key `token_infos`
* Argument `args` for backend method `load()` has a new key `main_config`
* Methods `__call__()` and `lookup()` of service plugin `lookup` take a new `token_infos`
  argument


15.12
-----

* Added authentication on all REST API endpoints
* Service plugins receive the whole configuration, rather than only their own section
