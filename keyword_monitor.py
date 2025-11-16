#!/usr/bin/env python3
"""
Domain Keyword Monitoring Script

This script monitors keyword rankings for specified domains and saves
the results to MongoDB. It runs periodically based on the configured interval.

Usage:
    python keyword_monitor.py                    # Start monitoring
    python keyword_monitor.py --once             # Run once and exit
    python keyword_monitor.py --history          # View ranking history
"""

import sys
import signal
from datetime import datetime
from monitor import MongoDBHandler, KeywordMonitor
import config


def ranking_change_handler(change_info):
    """Handle ranking changes"""
    print(f"\n🔔 RANKING CHANGE DETECTED!")
    print(f"   Keyword: {change_info['keyword']}")
    print(f"   Domain: {change_info['domain']}")
    print(f"   Change: {change_info['previous_position']} → {change_info['current_position']}")
    print(f"   Time: {change_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")


def show_ranking_history(db: MongoDBHandler):
    """Display ranking history for all monitored keywords"""
    print("\n" + "="*80)
    print("RANKING HISTORY")
    print("="*80)
    
    for keyword in config.KEYWORDS:
        for domain in config.DOMAINS:
            print(f"\nKeyword: '{keyword}' | Domain: '{domain}'")
            print("-" * 80)
            
            history = db.get_ranking_history(keyword, domain, limit=10)
            
            if not history:
                print("  No data available")
                continue
            
            for i, record in enumerate(history, 1):
                timestamp = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                if record['found']:
                    print(f"  {i}. [{timestamp}] Position: {record['position']} | {record['link']}")
                else:
                    print(f"  {i}. [{timestamp}] Not found in results")
    
    print("\n" + "="*80 + "\n")


def run_monitor():
    """Run the keyword monitor"""
    print("\n" + "="*80)
    print("DOMAIN KEYWORD MONITORING")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Monitoring {len(config.KEYWORDS)} keywords across {len(config.DOMAINS)} domains")
    print(f"Check interval: {config.INTERVAL_MINUTES} minutes")
    print("="*80 + "\n")
    
    # Initialize MongoDB handler
    try:
        db = MongoDBHandler(config.MONGODB_URI, config.DATABASE_NAME)
    except ConnectionError as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\nPlease ensure MongoDB is running and the connection string is correct.")
        print(f"Current connection string: {config.MONGODB_URI}")
        sys.exit(1)
    
    # Initialize monitor
    monitor = KeywordMonitor(
        api_key=config.SERPAPI_KEY,
        mongodb_handler=db,
        interval_minutes=config.INTERVAL_MINUTES
    )
    
    # Configure monitoring
    monitor.configure(
        keywords=config.KEYWORDS,
        domains=config.DOMAINS,
        **config.SEARCH_PARAMS
    )
    
    # Register change handler
    monitor.on_change(ranking_change_handler)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nReceived interrupt signal. Stopping monitor...")
        monitor.stop()
        db.close()
        print("Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start monitoring
    try:
        monitor.start(run_immediately=config.RUN_IMMEDIATELY)
        
        # Keep main thread alive
        print("\nMonitor is running. Press Ctrl+C to stop.\n")
        while True:
            signal.pause()
    except Exception as e:
        print(f"❌ Error: {e}")
        monitor.stop()
        db.close()
        sys.exit(1)


def run_once():
    """Run monitoring check once and exit"""
    print("\n" + "="*80)
    print("RUNNING SINGLE CHECK")
    print("="*80 + "\n")
    
    try:
        db = MongoDBHandler(config.MONGODB_URI, config.DATABASE_NAME)
    except ConnectionError as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    monitor = KeywordMonitor(
        api_key=config.SERPAPI_KEY,
        mongodb_handler=db,
        interval_minutes=config.INTERVAL_MINUTES
    )
    
    monitor.configure(
        keywords=config.KEYWORDS,
        domains=config.DOMAINS,
        **config.SEARCH_PARAMS
    )
    
    monitor.run_once()
    db.close()
    print("\n✅ Check completed!\n")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            run_once()
        elif sys.argv[1] == '--history':
            try:
                db = MongoDBHandler(config.MONGODB_URI, config.DATABASE_NAME)
                show_ranking_history(db)
                db.close()
            except ConnectionError as e:
                print(f"❌ Failed to connect to MongoDB: {e}")
                sys.exit(1)
        elif sys.argv[1] in ['-h', '--help']:
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        run_monitor()


if __name__ == "__main__":
    main()
