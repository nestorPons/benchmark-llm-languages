# Ensure the data directory exists
mkdir -p data

# Initialize the database schema
sqlite3 data/items.db < data/schema.sql