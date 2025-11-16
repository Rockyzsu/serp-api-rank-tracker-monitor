"""
Keyword monitoring scheduler with periodic checks
"""

import time
from datetime import datetime
from typing import List, Dict, Callable, Optional
from threading import Thread, Event
from serpapi import GoogleSearch
from .db import MongoDBHandler


class KeywordMonitor:
    """Monitor keyword rankings on a schedule"""
    
    def __init__(
        self,
        api_key: str,
        mongodb_handler: MongoDBHandler,
        interval_minutes: int = 60
    ):
        """
        Initialize keyword monitor
        
        Args:
            api_key: SerpApi API key
            mongodb_handler: MongoDB handler instance
            interval_minutes: Monitoring interval in minutes
        """
        self.api_key = api_key
        self.db = mongodb_handler
        self.interval_minutes = interval_minutes
        self.keywords = []
        self.domains = []
        self.search_params = {}
        self.running = False
        self.thread = None
        self.stop_event = Event()
        self.on_change_callback: Optional[Callable] = None
    
    def configure(
        self,
        keywords: List[str],
        domains: List[str],
        **search_params
    ):
        """
        Configure monitoring parameters
        
        Args:
            keywords: List of keywords to monitor
            domains: List of domains to track
            **search_params: Additional search parameters (google_domain, gl, hl, location, etc.)
        """
        self.keywords = keywords
        self.domains = domains
        
        # Default search parameters
        self.search_params = {
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "location": "United States",
            **search_params
        }
        
        print(f"Configured monitor: {len(keywords)} keywords, {len(domains)} domains")
        print(f"Interval: {self.interval_minutes} minutes")
    
    def search_keyword(self, keyword: str) -> Dict:
        """
        Search for a keyword using SerpApi
        
        Args:
            keyword: Search keyword
            
        Returns:
            Search results dictionary
        """
        params = {
            "api_key": self.api_key,
            "q": keyword,
            **self.search_params
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            print(f"Error searching for '{keyword}': {e}")
            return {}
    
    def check_domain_ranking(self, keyword: str, domain: str) -> Dict:
        """
        Check ranking for a specific keyword and domain
        
        Args:
            keyword: Search keyword
            domain: Domain to check
            
        Returns:
            Ranking data dictionary
        """
        print(f"Checking: '{keyword}' for domain '{domain}'")
        
        results = self.search_keyword(keyword)
        
        if not results or 'organic_results' not in results:
            return {
                "found": False,
                "position": None,
                "link": None,
                "title": None,
                "snippet": None,
                "total_results": results.get('search_information', {}).get('total_results'),
                "search_params": self.search_params
            }
        
        # Search for domain in organic results
        for result in results['organic_results']:
            if 'link' in result and domain in result['link']:
                ranking_data = {
                    "found": True,
                    "position": result.get('position'),
                    "link": result.get('link'),
                    "title": result.get('title'),
                    "snippet": result.get('snippet'),
                    "total_results": results.get('search_information', {}).get('total_results'),
                    "search_params": self.search_params
                }
                print(f"  ✓ Found at position {result.get('position')}: {result.get('link')}")
                return ranking_data
        
        print(f"  ✗ Domain '{domain}' not found in results")
        return {
            "found": False,
            "position": None,
            "link": None,
            "title": None,
            "snippet": None,
            "total_results": results.get('search_information', {}).get('total_results'),
            "search_params": self.search_params
        }
    
    def check_all(self):
        """Check all configured keyword-domain combinations"""
        print(f"\n{'='*60}")
        print(f"Starting monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        for keyword in self.keywords:
            for domain in self.domains:
                ranking_data = self.check_domain_ranking(keyword, domain)
                
                # Save to MongoDB
                self.db.save_ranking(keyword, domain, ranking_data)
                
                # Check for changes
                self._check_changes(keyword, domain, ranking_data)
                
                # Small delay to avoid rate limiting
                time.sleep(1)
        
        print(f"{'='*60}")
        print(f"Monitoring cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
    
    def _check_changes(self, keyword: str, domain: str, current_data: Dict):
        """
        Check if ranking has changed and trigger callback
        
        Args:
            keyword: Search keyword
            domain: Domain name
            current_data: Current ranking data
        """
        history = self.db.get_ranking_history(keyword, domain, limit=2)
        
        if len(history) >= 2:
            previous = history[1]  # Second latest (first is the one just inserted)
            current_pos = current_data.get('position')
            previous_pos = previous.get('position')
            
            if current_pos != previous_pos:
                change_info = {
                    "keyword": keyword,
                    "domain": domain,
                    "previous_position": previous_pos,
                    "current_position": current_pos,
                    "timestamp": datetime.now()
                }
                print(f"  📊 Ranking changed: {previous_pos} → {current_pos}")
                
                if self.on_change_callback:
                    self.on_change_callback(change_info)
    
    def on_change(self, callback: Callable):
        """
        Register callback for ranking changes
        
        Args:
            callback: Function to call when ranking changes
        """
        self.on_change_callback = callback
    
    def _monitor_loop(self):
        """Internal monitoring loop"""
        while not self.stop_event.is_set():
            try:
                self.check_all()
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            
            # Wait for next interval or stop event
            self.stop_event.wait(self.interval_minutes * 60)
    
    def start(self, run_immediately: bool = True):
        """
        Start monitoring in background thread
        
        Args:
            run_immediately: If True, run first check immediately
        """
        if self.running:
            print("Monitor is already running")
            return
        
        if not self.keywords or not self.domains:
            raise ValueError("Please configure keywords and domains first")
        
        self.running = True
        self.stop_event.clear()
        
        if run_immediately:
            print("Running initial check...")
            self.check_all()
        
        # Start background thread
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"Monitor started. Will check every {self.interval_minutes} minutes.")
    
    def stop(self):
        """Stop monitoring"""
        if not self.running:
            print("Monitor is not running")
            return
        
        print("Stopping monitor...")
        self.running = False
        self.stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("Monitor stopped")
    
    def run_once(self):
        """Run a single monitoring check"""
        self.check_all()
