# NiftyPool Enhanced Telegram Group Joiner

An advanced Python application for automatically joining Telegram groups with sophisticated error handling, beautiful UI, and comprehensive logging. Built with modern Python practices and async/await patterns.

## ✨ Features

### Core Functionality
- **Automated Group Joining**: Join multiple Telegram groups with configurable intervals
- **Smart Rate Limiting**: Intelligent delay randomization to avoid detection
- **Batch & Interactive Modes**: CLI arguments for automation or interactive UI
- **Resume Capability**: Continue from where you left off after interruptions

### Enhanced UI/UX
- **Beautiful Rich UI**: Modern terminal interface with progress bars and tables
- **Real-time Progress**: Live updates during group joining process
- **Detailed Results**: Comprehensive success/failure reporting with statistics
- **Color-coded Status**: Visual feedback for all operations

### Advanced Error Handling
- **Flood Protection**: Automatic handling of rate limiting
- **Comprehensive Error Types**: Specific handling for all Telegram API errors
- **Graceful Degradation**: Continues operation despite individual failures
- **Detailed Logging**: Complete audit trail with timestamps

### Account Management
- **Multi-Account Support**: Save and manage multiple Telegram accounts
- **Secure Credential Storage**: Encrypted storage of API credentials
- **Session Management**: Automatic session handling and persistence
- **Account Switching**: Easy switching between different accounts

### Data Management
- **Results Export**: Save joining results in JSON format
- **Statistics Tracking**: Track success rates and performance metrics
- **Link Validation**: Automatic validation of Telegram group links
- **Template Generation**: Auto-create template files for easy setup

## 🚀 Installation

1. **Clone the repository**:
```bash
git clone https://github.com/HarshDhaka69/NiftyJoiner.git
cd niftypool-enhanced
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Get Telegram API credentials**:
   - Visit https://my.telegram.org/
   - Log in with your phone number
   - Go to 'API Development Tools'
   - Create a new application
   - Copy the API_ID and API_HASH

4. **Create your links file**:
```bash
# The application will create a template links.txt file automatically
# Add your group links, one per line:
https://t.me/group1
https://t.me/group2
https://t.me/joinchat/XXXXXXXXXX
```

## 📖 Usage

### Interactive Mode (Recommended)
```bash
python joiner.py
```

This launches the full interactive interface with:
- Account management
- Real-time progress tracking
- Result visualization
- Settings configuration

### Batch Mode (Automation)
```bash
# Basic batch mode
python joiner.py --batch-mode --session mysession

# With custom settings
python joiner.py --batch-mode --session mysession --interval 3.0 --links-file mylinks.txt

# Disable randomization for consistent intervals
python joiner.py --batch-mode --session mysession --no-randomize
```

### Command Line Options
```bash
Options:
  -s, --session TEXT      Session name to use
  -i, --interval FLOAT    Base interval in minutes (default: 5.0)
  -f, --links-file TEXT   File containing group links (default: links.txt)
  --no-randomize          Disable interval randomization
  --batch-mode            Run in batch mode (non-interactive)
  --help                  Show this message and exit
```

## 🏗️ Project Structure

```
niftypool-enhanced/
├── joiner.py              # Main application
├── requirements.txt       # Dependencies
├── links.txt             # Group links (auto-generated template)
├── config/               # Configuration files
│   ├── credentials.json  # Saved API credentials
│   └── settings.json     # Application settings
├── logs/                 # Log files
│   └── niftypool_*.log   # Timestamped log files
├── results/              # Join results
│   └── join_results_*.json # Timestamped result files
└── *.session            # Telegram session files
```

## 🔧 Configuration

### Credential Management
- API credentials are automatically saved after first login
- Multiple accounts can be managed simultaneously
- Secure JSON storage with timestamp tracking

### Settings Options
- Base join interval (minutes)
- Randomization settings
- Default file paths
- Logging levels

### Links File Format
```txt
# Comments start with #
# Add one group link per line

# Public groups
https://t.me/publicgroup1
https://t.me/publicgroup2

# Private groups (invite links)
https://t.me/joinchat/XXXXXXXXXX
https://t.me/joinchat/YYYYYYYYYY
```

## 📊 Features in Detail

### Error Handling
The application handles all common Telegram API errors:

| Error Type | Handling |
|------------|----------|
| `FloodWaitError` | Automatic retry with proper delay |
| `UserAlreadyParticipantError` | Marked as successful (already joined) |
| `InviteHashExpiredError` | Marked as failed with clear message |
| `UserBannedInChannelError` | Marked as failed, continues with next |
| `ChannelPrivateError` | Marked as failed (invalid link) |
| `SessionPasswordNeededError` | Prompts for 2FA password |

### Progress Tracking
- Real-time progress bars
- Current operation status
- Estimated time remaining
- Success/failure counters

### Results Export
Results are saved in JSON format with detailed information:
```json
{
  "link": "https://t.me/example",
  "success": true,
  "error": null,
  "group_name": "Example Group",
  "member_count": 1234,
  "join_time": "2024-01-01T12:00:00"
}
```

## 🔒 Security Features

- **No Plain Text Storage**: API credentials are stored securely
- **Session Management**: Proper session handling prevents unauthorized access
- **Rate Limiting**: Built-in protection against API abuse
- **Error Isolation**: Failed operations don't affect others

## 🎯 Best Practices

### Recommended Settings
- **Base Interval**: 5-10 minutes for safety
- **Randomization**: Always enabled (default)
- **Batch Size**: Process 10-20 groups per session
- **Monitoring**: Check logs regularly for issues

### Avoiding Detection
- Use realistic intervals (5+ minutes)
- Enable randomization
- Don't join too many groups in one session
- Use different accounts for different purposes

## 🐛 Troubleshooting

### Common Issues

**Login Failed**
```bash
# Check your API credentials
# Ensure phone number includes country code
# Verify 2FA password if enabled
```

**Rate Limiting**
```bash
# The application handles this automatically
# Wait for the specified time before retrying
# Consider increasing base interval
```

**Group Join Failures**
```bash
# Check if links are valid
# Verify you're not banned from groups
# Ensure account has necessary permissions
```

### Debug Mode
Enable detailed logging by setting the log level:
```python
logging.getLogger("NiftyPool").setLevel(logging.DEBUG)
```

## 📈 Performance

### Optimization Tips
- Use SSD storage for session files
- Enable uvloop on Linux/macOS for better async performance
- Monitor memory usage with large link lists
- Use batch mode for automated operations

### Resource Usage
- **Memory**: ~50MB base + ~1MB per 100 groups
- **CPU**: Minimal (mostly I/O bound)
- **Network**: Depends on API calls and file downloads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black joiner.py

# Type checking
mypy joiner.py
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original NiftyPool concept
- Telethon library for Telegram API
- Rich library for beautiful terminal UI
- Click for CLI interface

## 📞 Support

For support and questions:
- Telegram: @ItsHarshX
- GitHub Issues: [Create an issue](https://github.com/yourusername/niftypool-enhanced/issues)

## 📋 Changelog

### Version 2.0.0 (Enhanced)
- ✨ Complete rewrite with modern Python practices
- 🎨 Beautiful Rich UI with progress tracking
- 🔧 CLI arguments for automation
- 📊 Comprehensive error handling
- 💾 Results export and statistics
- 🔒 Enhanced security features
- 📈 Performance optimizations

### Version 1.0.0 (Original)
- Basic group joining functionality
- Simple colorama-based UI
- Basic error handling
- Credential storage

## 🔮 Roadmap

- [ ] Web interface
- [ ] API rate limiting dashboard
- [ ] Group analytics
- [ ] Scheduled joining
- [ ] Proxy support
- [ ] Multi-threading optimization
- [ ] Database integration
- [ ] Cloud deployment options