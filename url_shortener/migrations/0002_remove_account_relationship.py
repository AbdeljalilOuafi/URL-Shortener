# Generated migration to remove account_id foreign key from short_urls table
# This makes the URL shortener truly standalone with no client/account dependencies

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('url_shortener', '0001_initial'),
    ]

    operations = [
        # Drop the foreign key constraint first
        migrations.RunSQL(
            sql="""
                ALTER TABLE short_urls 
                DROP CONSTRAINT IF EXISTS short_urls_account_id_fkey;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Drop the account_id column
        migrations.RunSQL(
            sql="""
                ALTER TABLE short_urls 
                DROP COLUMN IF EXISTS account_id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Drop the index on account_id if it exists
        migrations.RunSQL(
            sql="""
                DROP INDEX IF EXISTS short_urls_account_id_idx;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Optionally, update the index that was on (account_id, created_at) to just (created_at)
        # This may already exist or may need to be recreated
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS short_urls_created_at_idx 
                ON short_urls (created_at DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS short_urls_created_at_idx;
            """,
        ),
    ]
