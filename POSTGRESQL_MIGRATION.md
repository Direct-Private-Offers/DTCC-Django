# PostgreSQL Migration Guide

This document summarizes the changes made to migrate from SQLite to PostgreSQL.

## Changes Made

### 1. Database Configuration (`backend/config/settings.py`)
- **Before**: Defaulted to SQLite if `DATABASE_URL` was not set
- **After**: `DATABASE_URL` is now **required** - application will not start without it
- Added PostgreSQL-specific optimizations:
  - Connection pooling (max age: 600 seconds)
  - Connection health checks
  - Statement timeout: 30 seconds
  - Connection timeout: 10 seconds

### 2. Documentation Updates
- **README.md**: Updated to require PostgreSQL setup
- **docs/env-setup.md**: Updated to show PostgreSQL as required
- **docs/postgresql-setup.md**: New comprehensive PostgreSQL setup guide

### 3. No Code Changes Required
- All models use Django's ORM which is database-agnostic
- `JSONField` is supported in both SQLite and PostgreSQL
- No SQLite-specific queries or features were used

## Migration Steps

### For New Installations
1. Install PostgreSQL (see `docs/postgresql-setup.md`)
2. Create database: `createdb dtcc_sto_db`
3. Set `DATABASE_URL` in `.env` file
4. Run migrations: `python manage.py migrate`

### For Existing SQLite Installations
If you have existing data in SQLite that needs to be migrated:

1. **Export data from SQLite:**
   ```bash
   python manage.py dumpdata > data.json
   ```

2. **Set up PostgreSQL:**
   ```bash
   createdb dtcc_sto_db
   # Set DATABASE_URL in .env
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Import data:**
   ```bash
   python manage.py loaddata data.json
   ```

## Environment Variable

**Required:**
```bash
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

**With SSL (production):**
```bash
DATABASE_URL=postgres://user:password@host:5432/dbname?sslmode=require
```

## Benefits of PostgreSQL

1. **Better Performance**: Optimized for production workloads
2. **Concurrent Access**: Better handling of multiple connections
3. **Advanced Features**: JSONB, full-text search, advanced indexing
4. **Production Ready**: Standard for production Django applications
5. **Scalability**: Better support for large datasets

## Verification

After migration, verify the setup:

```bash
# Check database connection
python manage.py dbshell

# In PostgreSQL shell:
\dt  # List tables
\q   # Exit

# Check Django can connect
python manage.py check --database default
```

## Troubleshooting

See `docs/postgresql-setup.md` for detailed troubleshooting guide.

## Notes

- `psycopg2-binary` is already in `requirements.txt`
- All existing migrations are compatible with PostgreSQL
- No model changes were required
- JSONField works identically in PostgreSQL (uses JSONB)

