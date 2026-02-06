set -o allexport
. ./.env
set +o allexport

psql -c "DROP SCHEMA lesiv CASCADE"
psql -f ddl.sql
psql -f perm.sql
psql -f perm_test.sql
psql -f init_db.sql
psql -f facility_templates.sql
