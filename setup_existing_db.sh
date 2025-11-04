#!/bin/bash

# Quick Setup Script for Existing Database
# Use this when you have an existing short_urls table with account_id column

set -e  # Exit on error

echo "🚀 URL Shortener - Quick Setup for Existing Database"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Step 1: Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Please create .env file with your database credentials:"
    echo ""
    echo "DATABASE_URL=postgresql://user:password@host:5432/database"
    echo ""
    read -p "Press Enter after you've created the .env file..."
fi

# Step 2: Activate virtual environment or check Python
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Step 3: Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Step 4: Check database connection
echo "🔍 Checking database connection..."
python manage.py check --database default

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your DATABASE_URL in .env"
    exit 1
fi

echo "✅ Database connection successful!"
echo ""

# Step 5: Ask about the account_id column
echo "⚠️  IMPORTANT: Database Migration Required"
echo "=========================================="
echo ""
echo "Your existing 'short_urls' table has an 'account_id' column that needs to be removed."
echo ""
echo "Choose your migration method:"
echo "1) Manual SQL (Recommended - via Supabase UI or SQL Editor)"
echo "2) Let me show you the SQL to run manually"
echo "3) Skip (I'll do it later)"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📋 Instructions for Supabase UI:"
        echo "================================"
        echo "1. Open Supabase → Table Editor → short_urls"
        echo "2. Click on the 'account_id' column"
        echo "3. Click 'Delete Column'"
        echo "4. Confirm the deletion"
        echo ""
        read -p "Press Enter after you've deleted the column..."
        
        echo ""
        echo "🔄 Marking migration as complete..."
        python manage.py migrate url_shortener --fake
        ;;
    2)
        echo ""
        echo "📋 Run this SQL in Supabase SQL Editor:"
        echo "========================================"
        echo ""
        cat << 'EOF'
-- Drop foreign key constraint
ALTER TABLE short_urls 
DROP CONSTRAINT IF EXISTS short_urls_account_id_fkey;

-- Drop old indexes
DROP INDEX IF EXISTS short_urls_account_id_4ecf26_idx;
DROP INDEX IF EXISTS short_urls_account_idx;

-- Drop the account_id column
ALTER TABLE short_urls 
DROP COLUMN IF EXISTS account_id;

-- Create new index for performance
CREATE INDEX IF NOT EXISTS short_urls_created_idx 
ON short_urls (created_at DESC);
EOF
        echo ""
        echo "========================================"
        echo ""
        read -p "Press Enter after you've run the SQL..."
        
        echo ""
        echo "🔄 Marking migration as complete..."
        python manage.py migrate url_shortener --fake
        ;;
    3)
        echo ""
        echo "⏭️  Skipping migration for now."
        echo "⚠️  Remember to remove the account_id column before using the app!"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

# Step 6: Create logs directory
echo ""
echo "📁 Creating logs directory..."
mkdir -p logs

# Step 7: Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Step 8: Test the setup
echo ""
echo "🧪 Testing the setup..."
python manage.py check

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "1. Start the server: python manage.py runserver 8001"
echo "2. Visit admin: http://localhost:8001/admin/"
echo "3. Visit API docs: http://localhost:8001/api/docs/"
echo "4. Test API: curl -X POST http://localhost:8001/api/shorten/ -H 'Content-Type: application/json' -d '{\"original_url\": \"https://example.com\"}'"
echo ""
echo "🎉 Happy URL shortening!"
