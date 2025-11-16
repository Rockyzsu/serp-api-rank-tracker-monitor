# Domain Keyword Monitoring

这个项目扩展了 SerpApi Python 客户端，添加了定时监控域名关键词排名变化并保存到 MongoDB 的功能。

## 功能特性

- 🔍 定时监控指定关键词的搜索排名
- 💾 自动保存排名数据到 MongoDB
- 📊 跟踪排名变化历史
- 🔔 检测排名变化并通知
- ⏰ 可配置的检查间隔
- 📈 查看历史排名趋势

## 安装依赖

```bash
# 安装 SerpApi 客户端
pip install -e .

# 安装监控功能所需依赖
pip install -r requirements_monitor.txt
```

## MongoDB 设置

### 选项 1: 本地 MongoDB

安装并启动 MongoDB:

```bash
# Windows
# 下载并安装 MongoDB Community Server
# 启动服务: net start MongoDB

# macOS
brew install mongodb-community
brew services start mongodb-community

# Linux (Ubuntu)
sudo apt-get install mongodb
sudo systemctl start mongodb
```

### 选项 2: MongoDB Atlas (云服务)

1. 访问 [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. 创建免费集群
3. 获取连接字符串
4. 在 `config.py` 中更新 `MONGODB_URI`

## 配置

编辑 `config.py` 文件配置监控参数:

```python
# SerpApi API Key
SERPAPI_KEY = "your_api_key_here"

# MongoDB 连接
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "serpapi_monitor"

# 监控间隔 (分钟)
INTERVAL_MINUTES = 60

# 要监控的关键词
KEYWORDS = [
    "Private Crawler Cloud",
    "Private Proxy IP",
    "AI-Get"
]

# 要跟踪的域名
DOMAINS = [
    "dataget.ai",
    "dataget.com"
]

# 搜索参数
SEARCH_PARAMS = {
    "google_domain": "google.com",
    "gl": "us",
    "hl": "en",
    "location": "United States"
}
```

## 使用方法

### 1. 启动持续监控

```bash
python keyword_monitor.py
```

这将启动监控服务，按配置的间隔定期检查关键词排名。按 Ctrl+C 停止。

### 2. 运行单次检查

```bash
python keyword_monitor.py --once
```

运行一次检查后退出，适合用于测试或 cron 任务。

### 3. 查看历史数据

```bash
python keyword_monitor.py --history
```

显示所有监控关键词的历史排名数据。

### 4. 帮助信息

```bash
python keyword_monitor.py --help
```

## 代码示例

### 基础使用

```python
from monitor import MongoDBHandler, KeywordMonitor
import config

# 初始化 MongoDB
db = MongoDBHandler(config.MONGODB_URI, config.DATABASE_NAME)

# 创建监控器
monitor = KeywordMonitor(
    api_key=config.SERPAPI_KEY,
    mongodb_handler=db,
    interval_minutes=60
)

# 配置监控
monitor.configure(
    keywords=["Python programming", "Web scraping"],
    domains=["example.com", "example.org"],
    google_domain="google.com",
    gl="us",
    hl="en"
)

# 运行单次检查
monitor.run_once()

# 或启动持续监控
monitor.start()
```

### 监听排名变化

```python
def on_ranking_change(change_info):
    print(f"关键词 '{change_info['keyword']}' 排名变化:")
    print(f"  {change_info['previous_position']} → {change_info['current_position']}")
    
    # 可以在这里添加通知逻辑
    # 例如: 发送邮件、Slack 消息等

monitor.on_change(on_ranking_change)
monitor.start()
```

### 查询历史数据

```python
# 获取特定关键词的历史排名
history = db.get_ranking_history("Python programming", "example.com", limit=50)

for record in history:
    print(f"{record['timestamp']}: Position {record['position']}")

# 获取最新排名
latest = db.get_latest_ranking("Python programming", "example.com")
print(f"当前排名: {latest['position']}")

# 获取最近 24 小时的变化
changes = db.get_ranking_changes("Python programming", "example.com", hours=24)
```

## MongoDB 数据结构

每条记录包含以下字段:

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

## 数据维护

### 清理旧数据

```python
# 删除 90 天前的记录
db.delete_old_records(days=90)
```

### 查看所有监控的关键词和域名

```python
keywords = db.get_all_keywords()
domains = db.get_all_domains()
```

## 注意事项

1. **API 配额**: SerpApi 有请求限制，请合理设置检查间隔
2. **MongoDB 存储**: 定期清理旧数据以控制数据库大小
3. **错误处理**: 监控器会自动处理错误并继续运行
4. **并发限制**: 每次检查后会有 1 秒延迟，避免触发速率限制

## 高级配置

### 设置为系统服务 (Linux)

创建 systemd 服务文件 `/etc/systemd/system/keyword-monitor.service`:

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

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl start keyword-monitor
sudo systemctl enable keyword-monitor
```

### 使用 Cron 定时任务

```bash
# 每小时运行一次
0 * * * * cd /path/to/serpapi-python && python keyword_monitor.py --once
```

## 故障排除

### MongoDB 连接失败

- 确保 MongoDB 服务正在运行
- 检查连接字符串是否正确
- 验证网络连接和防火墙设置

### API 错误

- 验证 SerpApi API Key 是否有效
- 检查 API 配额是否用尽
- 确认搜索参数格式正确

## 许可证

与主项目相同的许可证。
