# Domain Keyword Monitoring

This project extends the SerpApi Python client by adding scheduled monitoring of domain keyword rankings and saving results to MongoDB.

## Features

- 🔍 Scheduled monitoring of specified keywords’ search rankings
- 💾 Automatically saves ranking data to MongoDB
- 📊 Tracks ranking change history
- 🔔 Detects ranking changes and supports notifications
- ⏰ Configurable check interval
- 📈 View historical ranking trends

## Installation

```bash
# Install the SerpApi client (editable)
pip install -e .

# Install dependencies for the monitoring module
pip install -r requirements_monitor.txt
```

## MongoDB Setup

### Option 1: Local MongoDB

Install and start MongoDB:

```bash
# Windows
# Download and install MongoDB Community Server
# Start service: net start MongoDB

# macOS
brew install mongodb-community
brew services start mongodb-community

# Linux (Ubuntu)
sudo apt-get install mongodb
sudo systemctl start mongodb
```

### Option 2: MongoDB Atlas (Cloud)

1. Visit https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get the connection string
4. Update `MONGODB_URI` in `config.py`

## Configuration

Edit the `config.py` file to configure monitoring parameters:

```python
# SerpApi API Key
SERPAPI_KEY = "your_api_key_here"

# MongoDB connection
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "serpapi_monitor"

# Monitoring interval (minutes)
INTERVAL_MINUTES = 60

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

# Search parameters
SEARCH_PARAMS = {
    "google_domain": "google.com",
    "gl": "us",
    "hl": "en",
    "location": "United States"
}
```

## Usage

### 1. Start continuous monitoring

```bash
python keyword_monitor.py
```

This starts the monitoring service and checks rankings at the configured interval. Press Ctrl+C to stop.

### 2. Run a single check

```bash
python keyword_monitor.py --once
```

Runs a single check and exits; useful for testing or cron jobs.

### 3. View historical data

```bash
python keyword_monitor.py --history
```

Displays historical ranking data for all monitored keywords.

### 4. Help

```bash
python keyword_monitor.py --help
```

## Code Examples

### Basic usage

```python
from monitor import MongoDBHandler, KeywordMonitor
import config

# Initialize MongoDB
db = MongoDBHandler(config.MONGODB_URI, config.DATABASE_NAME)

# Create the monitor
monitor = KeywordMonitor(
    api_key=config.SERPAPI_KEY,
    mongodb_handler=db,
    interval_minutes=60
)

# Configure monitoring
monitor.configure(
    keywords=["Python programming", "Web scraping"],
    domains=["example.com", "example.org"],
    google_domain="google.com",
    gl="us",
    hl="en"
)

# Run a single check
monitor.run_once()

# Or start continuous monitoring
monitor.start()
```

### Listen for ranking changes

```python
def on_ranking_change(change_info):
    print(f"Keyword '{change_info['keyword']}' ranking changed:")
    print(f"  {change_info['previous_position']} → {change_info['current_position']}")
    
    # Add your notification logic here
    # e.g., send an email or a Slack message

monitor.on_change(on_ranking_change)
monitor.start()
```

### Query historical data

```python
# Get historical rankings for a specific keyword/domain
history = db.get_ranking_history("Python programming", "example.com", limit=50)

for record in history:
    print(f"{record['timestamp']}: Position {record['position']}")

# Get the latest ranking
latest = db.get_latest_ranking("Python programming", "example.com")
print(f"Current position: {latest['position']}")

# Get changes in the last 24 hours
changes = db.get_ranking_changes("Python programming", "example.com", hours=24)
```

## MongoDB Data Model

Each record contains the following fields:

```json
{
  "keyword": "Python programming",
  "domain": "example.com",
  "timestamp": "2025-11-16T10:30:00",
  "position": 5,
  "link": "https://example.com/python",
  "title": "Python Programming Guide",
  "snippet": "Learn Python programming...",
  "found": true,
  "total_results": 1500000,
  "search_params": {
    "google_domain": "google.com",
    "gl": "us",
    "hl": "en"
  }
}
```

## Data Maintenance

### Cleanup old data

```python
# Delete records older than 90 days
db.delete_old_records(days=90)
```

### List all monitored keywords and domains

```python
keywords = db.get_all_keywords()
domains = db.get_all_domains()
```

## Notes

1. API quota: SerpApi has request limits; set the interval appropriately
2. MongoDB storage: Regularly clean up old data to control DB size
3. Error handling: The monitor handles errors and keeps running
4. Concurrency/rate limits: Adds a 1-second delay after each check to avoid rate limits

## Advanced

### Run as a system service (Linux)

Create a systemd service file at `/etc/systemd/system/keyword-monitor.service`:

```ini
[Unit]
Description=Keyword Ranking Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/serpapi-python
ExecStart=/usr/bin/python3 keyword_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start keyword-monitor
sudo systemctl enable keyword-monitor
```

### Use Cron for scheduling

```bash
# Run every hour
0 * * * * cd /path/to/serpapi-python && python keyword_monitor.py --once
```

## Troubleshooting

### MongoDB connection failure

- Ensure the MongoDB service is running
- Check that the connection string is correct
- Verify network connectivity and firewall settings

### API errors

- Verify the SerpApi API key is valid
- Check whether you have exceeded your API quota
- Ensure search parameters are formatted correctly

## License

Same license as the main project.
