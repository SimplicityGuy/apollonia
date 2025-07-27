# Emoji Logging Quick Reference

## Common Emoji Usage in Apollonia

### System Lifecycle

- 🚀 **Starting**: Service/system startup
- 🛑 **Stopping**: Service shutdown
- 👋 **Goodbye**: Final shutdown message
- ⚡ **Signal**: Signal handling (SIGINT/SIGTERM)
- ⌨️ **Interrupt**: User keyboard interrupt
- 💥 **Fatal**: Fatal errors/exceptions

### Connections

- 🔌 **Connect/Disconnect**: Database, AMQP, service connections
- 📡 **Network**: Exchange declarations, network operations
- 📤 **Publish**: Publishing messages/data
- 📥 **Consume**: Consuming messages/data

### File Operations

- 📁 **Directory**: Directory operations
- 📄 **File**: File operations
- 👁️ **Watch**: File system monitoring
- 🔍 **Process**: Processing/analyzing files
- ⏭️ **Skip**: Skipping non-relevant files

### Media Processing

- 🎵 **Audio**: Audio file operations
- 🎬 **Video**: Video file operations
- 🖼️ **Image**: Image file operations
- 🧠 **ML/AI**: Machine learning operations
- 🤖 **Model**: Model loading/management

### Status

- ✅ **Success**: Successful operations
- ❌ **Error**: Failed operations
- ⚠️ **Warning**: Warnings
- 🚨 **Critical**: Critical errors
- 📊 **Metrics**: Statistics/metrics
- 🔄 **Progress**: In-progress operations

### Data Operations

- 💾 **Database/Cache**: Database or cache operations
- 📦 **Package**: Model packages, archives
- 🗑️ **Delete**: Deletion operations
- 🧹 **Cleanup**: Cleanup operations
- 💼 **Batch**: Batch processing

### API Operations

- 🌐 **HTTP/API**: API operations
- 🔐 **Auth**: Authentication operations
- 🔑 **Permission**: Authorization checks
- 🚫 **Denied**: Access denied/failed auth
- 📚 **Resource**: Resource operations (catalogs, etc.)
- ➕ **Create**: Creating new resources
- ✏️ **Update**: Updating resources
- 💡 **Info**: General information

### Development

- 🐛 **Debug**: Debug-level logging
- 🔧 **Config**: Configuration operations
- 📝 **Log**: Logging metadata

## Usage Examples

### Service Startup

```python
logger.info("🚀 Starting Apollonia API...")
logger.info("🔌 Connecting to PostgreSQL database")
logger.info("📡 Initializing Redis cache")
logger.info("✅ All systems ready")
```

### File Processing

```python
logger.info("🎵 Audio file detected: music.mp3")
logger.info("🔍 Processing audio file...")
logger.info("🧠 Running ML analysis...")
logger.info("✅ Audio processing complete")
```

### Error Handling

```python
logger.error("❌ Failed to connect to database")
logger.warning("⚠️ Falling back to cached data")
logger.exception("💥 Fatal error in processing pipeline")
```

### API Operations

```python
logger.info("🔐 User logged in: john_doe")
logger.info("📚 Creating new catalog: My Music")
logger.info("📤 Uploading file: song.mp3")
logger.info("✅ Upload complete")
```

## Service-Specific Patterns

### Ingestor

- Uses 👁️ for file watching
- Uses 📤 for publishing events
- Uses 🔍 for processing events

### Analyzer

- Uses 🎵/🎬 for media type identification
- Uses 🧠 for ML operations
- Uses 📤 for publishing results

### Populator

- Uses 📥 for consuming messages
- Uses 💾 for database operations
- Uses ✅ for successful imports

### API

- Uses 🔐 for authentication
- Uses 📚 for catalog operations
- Uses 💾 for cache hits/misses
- Uses ✅/❌ for operation results

## Implementation Notes

1. **Consistency**: Always use the same emoji for similar operations across services
1. **Placement**: Emoji should be the first character in the log message
1. **Spacing**: Always add a space after the emoji
1. **Context**: Choose emoji based on the operation context
1. **Fallback**: If no specific emoji fits, use 💡 for info level

## Benefits

- **Visual Scanning**: Quickly identify log entry types
- **Pattern Recognition**: Spot issues and successes at a glance
- **Categorization**: Group related operations visually
- **Developer Experience**: More enjoyable log reading
- **Consistency**: Standardized logging across all services
