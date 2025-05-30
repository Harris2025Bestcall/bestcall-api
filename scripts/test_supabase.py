from supabase import create_client
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Fetch environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug print
print("🔗 Supabase URL:", SUPABASE_URL)
print("🔑 Supabase Key starts with:", SUPABASE_KEY[:10])

# Connect to Supabase
try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = client.table("inventory").select("*").limit(1).execute()
    print("✅ Connection successful. Sample inventory data:")
    print(response.data)
except Exception as e:
    print("❌ Connection failed:")
    print(e)
