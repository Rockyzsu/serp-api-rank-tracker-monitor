"""
MongoDB handler for storing keyword ranking data
"""

from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure


class MongoDBHandler:
    """Handle MongoDB operations for keyword monitoring"""
    
    def __init__(self, connection_string: str, database_name: str = "serpapi_monitor"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name to use
        """
        try:
            self.client = MongoClient(connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            self.collection = self.db['keyword_rankings']
            self._create_indexes()
            print(f"Successfully connected to MongoDB: {database_name}")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        # Compound index for efficient querying
        self.collection.create_index([
            ("keyword", 1),
            ("domain", 1),
            ("timestamp", DESCENDING)
        ])
        self.collection.create_index([("timestamp", DESCENDING)])
    
    def save_ranking(self, keyword: str, domain: str, ranking_data: Dict):
        """
        Save keyword ranking data to MongoDB
        
        Args:
            keyword: Search keyword
            domain: Domain name
            ranking_data: Dictionary containing ranking information
        """
        document = {
            "keyword": keyword,
            "domain": domain,
            "timestamp": datetime.now(),
            "position": ranking_data.get("position"),
            "link": ranking_data.get("link"),
            "title": ranking_data.get("title"),
            "snippet": ranking_data.get("snippet"),
            "found": ranking_data.get("found", False),
            "total_results": ranking_data.get("total_results"),
            "search_params": ranking_data.get("search_params", {})
        }
        
        result = self.collection.insert_one(document)
        print(f"Saved record for '{keyword}' + '{domain}': {result.inserted_id}")
        return result.inserted_id
    
    def get_ranking_history(self, keyword: str, domain: str, limit: int = 100) -> List[Dict]:
        """
        Get ranking history for a keyword and domain
        
        Args:
            keyword: Search keyword
            domain: Domain name
            limit: Maximum number of records to return
            
        Returns:
            List of ranking records
        """
        cursor = self.collection.find(
            {"keyword": keyword, "domain": domain}
        ).sort("timestamp", DESCENDING).limit(limit)
        
        return list(cursor)
    
    def get_latest_ranking(self, keyword: str, domain: str) -> Optional[Dict]:
        """
        Get the latest ranking for a keyword and domain
        
        Args:
            keyword: Search keyword
            domain: Domain name
            
        Returns:
            Latest ranking record or None
        """
        return self.collection.find_one(
            {"keyword": keyword, "domain": domain},
            sort=[("timestamp", DESCENDING)]
        )
    
    def get_ranking_changes(self, keyword: str, domain: str, hours: int = 24) -> List[Dict]:
        """
        Get ranking changes within specified hours
        
        Args:
            keyword: Search keyword
            domain: Domain name
            hours: Number of hours to look back
            
        Returns:
            List of ranking records within the time period
        """
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor = self.collection.find({
            "keyword": keyword,
            "domain": domain,
            "timestamp": {"$gte": cutoff_time}
        }).sort("timestamp", DESCENDING)
        
        return list(cursor)
    
    def get_all_keywords(self) -> List[str]:
        """Get all unique keywords in the database"""
        return self.collection.distinct("keyword")
    
    def get_all_domains(self) -> List[str]:
        """Get all unique domains in the database"""
        return self.collection.distinct("domain")
    
    def delete_old_records(self, days: int = 90):
        """
        Delete records older than specified days
        
        Args:
            days: Number of days to keep
        """
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=days)
        
        result = self.collection.delete_many({"timestamp": {"$lt": cutoff_time}})
        print(f"Deleted {result.deleted_count} old records")
        return result.deleted_count
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
