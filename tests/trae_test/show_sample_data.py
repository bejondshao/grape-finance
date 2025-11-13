import sys
import os
import asyncio
from pprint import pprint

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.mongodb_service import MongoDBService

async def show_sample_data():
    try:
        mongo = MongoDBService()
        # Try to find data from a sample collection
        collections = await mongo.db.list_collection_names()
        stock_collections = [c for c in collections if c.startswith('stock_') and c != 'stock_info']
        
        if stock_collections:
            sample_collection = stock_collections[0]
            print(f"Showing sample data from collection: {sample_collection}")
            data = await mongo.find(sample_collection, {}, limit=1)
            pprint(data)
        else:
            print("No stock collections found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(show_sample_data())