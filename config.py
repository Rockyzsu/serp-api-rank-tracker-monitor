# Keyword Monitoring Configuration

# SerpApi Configuration
SERPAPI_KEY = ""

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/"
# For MongoDB Atlas, use:
# MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
DATABASE_NAME = "serpapi_monitor"

# Monitoring Configuration
INTERVAL_MINUTES = 60  # Check every 60 minutes
RUN_IMMEDIATELY = True  # Run first check immediately when starting

# Keywords to monitor
KEYWORDS = [
    "Private Crawler Cloud",
    "Private Proxy IP",
    "AI-Get"
]

# Domains to track
DOMAINS = [
    "dataget.ai",
    "dataget.com"
]

# Search Parameters
SEARCH_PARAMS = {
    "google_domain": "google.com",
    "gl": "us",
    "hl": "en",
    "location": "United States"
}

# Data Retention
DELETE_OLD_RECORDS_DAYS = 90  # Delete records older than 90 days
