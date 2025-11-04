# Migration Guide: Removing Account Relationship

This guide explains how to migrate your existing URL shortener database to remove the account/client foreign key relationship.

## What Changed

The URL shortener is now a **fully standalone public service** with:
- ✅ No client/account model required
- ✅ No authentication needed (public API like bit.ly)
- ✅ Automatic domain detection from request
- ✅ Simplified database schema

## Database Changes

The `short_urls` table will have the following column removed:
- `account_id` (foreign key to accounts/clients table)

And the following index removed:
- Index on `(account_id, created_at)`

A new index will be created:
- Index on `(created_at)` for better query performance

## Migration Steps

### Option 1: Using Django Migration (Recommended)

If you have Django access to the database:

```bash
# 1. Pull the latest code
git pull

# 2. Run the migration
python manage.py migrate url_shortener 0002_remove_account_relationship

# 3. Verify the migration
python manage.py showmigrations url_shortener
```

### Option 2: Manual SQL (Supabase UI or psql)

If you prefer to remove the column manually via Supabase UI or SQL:

```sql
-- Step 1: Drop the foreign key constraint
ALTER TABLE short_urls 
DROP CONSTRAINT IF EXISTS short_urls_account_id_fkey;

-- Step 2: Drop the column
ALTER TABLE short_urls 
DROP COLUMN IF EXISTS account_id;

-- Step 3: Drop the old index
DROP INDEX IF EXISTS short_urls_account_id_idx;

-- Step 4: Create new index for performance
CREATE INDEX IF NOT EXISTS short_urls_created_at_idx 
ON short_urls (created_at DESC);
```

**Then mark the migration as applied:**

```bash
python manage.py migrate url_shortener 0002_remove_account_relationship --fake
```

### Option 3: Fresh Database

If you're starting fresh or can recreate the database:

```bash
# 1. Drop existing tables (BE CAREFUL - THIS DELETES DATA!)
python manage.py migrate url_shortener zero

# 2. Run all migrations from scratch
python manage.py migrate
```

## Verification

After migration, verify everything works:

### 1. Check Database Schema

```sql
-- Verify account_id column is gone
\d short_urls

-- Or in PostgreSQL:
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'short_urls';
```

You should NOT see `account_id` in the columns.

### 2. Test the API

```bash
# Create a short URL
curl -X POST http://localhost:8001/api/shorten/ \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/long-url",
    "title": "Test Link"
  }'

# Should return:
# {
#   "status": "success",
#   "data": {
#     "id": 1,
#     "short_code": "abc123",
#     "full_short_url": "http://localhost:8001/abc123",
#     ...
#   }
# }

# Test redirect
curl -I http://localhost:8001/abc123/
# Should return 302 redirect
```

### 3. Check Admin Interface

Visit http://localhost:8001/admin/url_shortener/shorturl/

You should see URLs listed without any client/account reference.

## Rollback (If Needed)

If you need to rollback the migration:

```bash
# Rollback the migration
python manage.py migrate url_shortener 0001_initial
```

Note: This will fail if you manually dropped the column. In that case, you'll need to manually recreate the column:

```sql
ALTER TABLE short_urls 
ADD COLUMN account_id INTEGER;

-- Recreate the foreign key if needed
ALTER TABLE short_urls 
ADD CONSTRAINT short_urls_account_id_fkey 
FOREIGN KEY (account_id) REFERENCES accounts(id);
```

## Post-Migration

After successful migration:

1. **Update your API clients** - Remove any account/client authentication logic
2. **Monitor usage** - Check logs for any errors related to missing account_id
3. **Test all endpoints**:
   - POST `/api/shorten/` - Create short URL
   - GET `/{short_code}/` - Redirect
   - GET `/api/urls/` - List URLs for domain
   - GET `/api/stats/{short_code}/` - Get statistics
   - PATCH `/api/urls/{short_code}/` - Update URL
   - DELETE `/api/urls/{short_code}/` - Delete URL

## Troubleshooting

### Error: "column account_id does not exist"

This means the migration completed successfully! The column has been removed as intended.

### Error: "constraint short_urls_account_id_fkey does not exist"

This is normal if the constraint was already dropped or didn't exist. The migration will continue.

### Error: Model errors in admin

Clear your Python cache:

```bash
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

Then restart the server.

## Need Help?

- Check the logs: `tail -f logs/django.log`
- Verify database connection in `.env`
- Ensure migrations table exists: `SELECT * FROM django_migrations WHERE app='url_shortener';`

## Production Deployment

For production deployments:

1. **Backup your database first!**
   ```bash
   pg_dump -h hostname -U username dbname > backup_$(date +%Y%m%d).sql
   ```

2. **Test in staging environment first**

3. **Run migration during low-traffic period**

4. **Monitor logs after deployment**
   ```bash
   tail -f logs/django.log
   ```

5. **Have rollback plan ready**
