export PGHOST=127.0.0.1
export PGPORT=15432
export PGDATABASE=postgres
export PGUSER=l_app_admin
# export PGPASSWORD=''

psql -c "DROP SCHEMA lesiv CASCADE"
psql -f ddl.sql
psql -f perm.sql
psql -f perm_test.sql
psql -f init_db.sql
