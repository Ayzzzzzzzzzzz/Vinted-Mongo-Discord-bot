from pymongo import MongoClient, DESCENDING
from datetime import datetime
from loguru import logger as log
import re

# MongoDB connection settings
MONGO_HOST = "192.168.178.120"
MONGO_PORT = 27017
MONGO_USER = "admin"
MONGO_PASSWORD = "1345"
MONGO_DB = "Vinted"
MAX_ITEMS = 50

class Database:
    _instance = None
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance
    
    def connect(self):
        try:
            self.client = MongoClient(
                host=MONGO_HOST,
                port=MONGO_PORT,
                username=MONGO_USER,
                password=MONGO_PASSWORD
            )
            self.db = self.client[MONGO_DB]
            log.info("Connected to MongoDB successfully")
        except Exception as e:
            log.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def sanitize_collection_name(self, channel_name: str) -> str:
        """Convert channel name to valid MongoDB collection name"""
        # Remove invalid characters and limit length
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(channel_name))
        return f"channel_{sanitized[:50]}"  # Prefix with channel_ and limit length
    
    def create_channel_collection(self, channel_id: str):
        """Create a new collection for a channel if it doesn't exist"""
        collection_name = self.sanitize_collection_name(channel_id)
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
        return collection_name
    
    def cleanup_collection(self, collection_name):
        """Maintain collection size limit by removing oldest items"""
        collection = self.db[collection_name]
        count = collection.count_documents({})
        if count > MAX_ITEMS:
            # Find and delete oldest items
            to_delete = count - MAX_ITEMS
            oldest = collection.find().sort('timestamp', DESCENDING).skip(MAX_ITEMS)
            ids_to_delete = [doc['_id'] for doc in oldest]
            collection.delete_many({'_id': {'$in': ids_to_delete}})
            log.info(f"Cleaned up {to_delete} old items from {collection_name}")

    def insert_subscription(self, url, channel_id):
        collection = self.db['subscriptions']
        collection_name = self.create_channel_collection(channel_id)
        subscription = {
            'url': url,
            'channel_id': channel_id,
            'collection_name': collection_name,
            'last_sync': -1,
            'timestamp': datetime.now()
        }
        result = collection.insert_one(subscription)
        return result.inserted_id

    def get_subscriptions(self):
        return list(self.db['subscriptions'].find())

    def update_last_sync(self, subscription_id, timestamp):
        self.db['subscriptions'].update_one(
            {'_id': subscription_id},
            {'$set': {'last_sync': timestamp}}
        )

    def delete_subscription(self, subscription_id):
        return self.db['subscriptions'].delete_one({'_id': subscription_id})

    def insert_item(self, item_data, channel_id):
        collection_name = self.sanitize_collection_name(channel_id)
        collection = self.db[collection_name]
        # Ensure we have the required fields
        if 'id' not in item_data:
            raise ValueError("Item data missing required 'id' field")
        item_data['timestamp'] = datetime.now()
        item_data['item_id'] = item_data['id']
        collection.insert_one(item_data)
        self.cleanup_collection(collection_name)

    def item_exists(self, item_id, channel_id):
        collection_name = self.sanitize_collection_name(channel_id)
        return self.db[collection_name].find_one({'item_id': str(item_id)}) is not None
