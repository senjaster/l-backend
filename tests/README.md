# Test Configuration

## Database Setup for Tests

The tests use Flyway migrations to set up the database schema. This requires a database user with schema management permissions.

### Environment Variables

Create a `.env.test` file in the project root with the following content:

```bash
# Flyway migration credentials (user with schema management permissions)
FLYWAY_URL=jdbc:postgresql://localhost:5432/postgres
FLYWAY_USER=l_app_admin
FLYWAY_PASSWORD=your_actual_password_here
```

**Note:** The `.env.test` file is separate from `.env` to keep test-specific configuration isolated from production settings.

### Required Permissions

The Flyway user (`l_app_admin`) needs the following permissions:

```sql
-- Grant schema creation and management permissions
GRANT CREATE ON DATABASE postgres TO l_app_admin;
GRANT ALL PRIVILEGES ON SCHEMA lesiv TO l_app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA lesiv TO l_app_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA lesiv TO l_app_admin;

-- Allow creating and managing the flyway_schema_history table
ALTER DEFAULT PRIVILEGES IN SCHEMA lesiv GRANT ALL ON TABLES TO l_app_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA lesiv GRANT ALL ON SEQUENCES TO l_app_admin;
```

### Running Tests

Once the environment variables are set and the user has proper permissions:

```bash
source .venv/bin/activate
pytest tests/
```

The test suite will automatically:
1. Run Flyway migrations to set up the schema
2. Populate dictionary data (sticker types, defect types, equipment types, facility templates)
3. Execute all tests
