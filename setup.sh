#!/bin/bash
# Setup script for URL Shortener

set -e

echo "🚀 Setting up URL Shortener..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env .env.example 2>/dev/null || echo "SECRET_KEY=change-me-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1" > .env
    echo "📝 Please edit .env file with your configuration"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Create superuser prompt
echo ""
echo "👤 Create superuser account? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver 8001"
echo ""
echo "Admin interface: http://localhost:8001/admin/"
echo "API docs: http://localhost:8001/api/docs/"
echo ""
