from dotenv import load_dotenv
import os

print("🔍 Testing environment variable loading...")

# Load .env file
load_dotenv()

# Check DATABASE_URL
db_url = os.environ.get('DATABASE_URL')
if db_url:
    print(f"✅ DATABASE_URL found: {db_url[:50]}...")
else:
    print("❌ DATABASE_URL not found")

# Check current directory
print(f"📁 Current directory: {os.getcwd()}")
print(f"📋 .env file exists: {os.path.exists('.env')}")

# List environment variables that start with 'DATABASE'
db_vars = {k: v for k, v in os.environ.items() if k.startswith('DATABASE')}
print(f"🗃️  Database-related env vars: {list(db_vars.keys())}")
