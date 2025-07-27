# Apollonia Logging Convention

## Emoji Prefix System

All logging messages in the Apollonia system use emoji prefixes to provide visual categorization and
quick identification of log types. This improves readability and helps developers quickly scan logs
for relevant information.

## Emoji Categories and Usage

### System Lifecycle

- 🚀 **Starting/Launching** - System or service startup
- 🛑 **Stopping/Shutdown** - Clean shutdown operations
- 👋 **Goodbye** - Final shutdown message
- ⚡ **Signal Received** - Signal handling (SIGINT, SIGTERM)
- ⌨️ **User Interrupt** - Keyboard interrupt (Ctrl+C)
- 💥 **Fatal Error** - Unrecoverable errors causing shutdown

### Connection & Network

- 🔌 **Connecting/Disconnecting** - Database, AMQP, or service connections
- 📡 **Network Operations** - API calls, message queue operations
- 🌐 **HTTP/API** - REST or GraphQL operations
- 📤 **Publishing/Sending** - Outgoing messages or data
- 📥 **Receiving/Consuming** - Incoming messages or data

### File Operations

- 📁 **Directory Operations** - Directory watching, creation, scanning
- 📂 **Subdirectory Operations** - Recursive directory operations
- 📄 **File Operations** - File reading, writing, processing
- 👁️ **Watching/Monitoring** - File system watching
- ⏭️ **Skipping** - Skipping files or operations

### Processing & Analysis

- 🔍 **Processing/Analyzing** - General processing operations
- 🎵 **Audio Processing** - Audio file detection and analysis
- 🎬 **Video Processing** - Video file detection and analysis
- 🖼️ **Image Processing** - Image file operations
- 🧠 **ML/AI Operations** - Machine learning model operations
- 🤖 **Model Management** - Model loading, initialization

### Status & Progress

- ✅ **Success/Complete** - Successful operations
- ❌ **Error/Failure** - Operation failures
- ⚠️ **Warning** - Non-critical issues
- 🚨 **Critical Error** - Critical errors requiring attention
- 📊 **Metrics/Stats** - Performance metrics or statistics
- 🔄 **In Progress/Loading** - Ongoing operations

### Data & Storage

- 💾 **Database Operations** - Database queries, updates
- 📦 **Package/Archive** - Compressed files, model packages
- 🗑️ **Deletion/Cleanup** - Removing old data or files
- 🧹 **Cleanup Operations** - General cleanup tasks
- 💼 **Batch Operations** - Batch processing

### Authentication & Security

- 🔐 **Authentication** - Login, token operations
- 🔑 **Authorization** - Permission checks
- 🛡️ **Security** - Security-related operations
- 👤 **User Operations** - User-specific actions

### Development & Debug

- 🐛 **Debug Information** - Debug-level logging
- 🔧 **Configuration** - Configuration loading or changes
- 📝 **Logging/Audit** - Audit trail or logging metadata
- 💡 **Info/Notice** - General information

## Implementation Guidelines

### Log Level Mapping

```python
# Debug - Detailed information for debugging
logger.debug("🐛 Detailed debug info: %s", details)

# Info - General informational messages
logger.info("✅ Operation completed successfully")

# Warning - Warning messages
logger.warning("⚠️ Deprecated feature used: %s", feature)

# Error - Error messages
logger.error("❌ Failed to connect to database: %s", error)

# Critical - Critical errors
logger.critical("🚨 System failure: %s", error)

# Exception - Exception with traceback
logger.exception("💥 Unhandled exception occurred")
```

### Composite Messages

For operations with multiple stages, use appropriate emoji for each stage:

```python
logger.info("🔌 Connecting to database...")
logger.info("✅ Database connection established")
logger.info("🔄 Processing data...")
logger.info("✅ Data processing complete")
```

### Contextual Usage

Choose emoji based on the context and operation type:

- Use 🎵 for audio-specific operations
- Use 🎬 for video-specific operations
- Use 🧠 for ML/AI operations
- Use 📡 for network/messaging operations

### Consistency Rules

1. Always place emoji at the beginning of the message
1. Follow emoji with a space before the message
1. Use consistent emoji for similar operations across the codebase
1. Prefer specific emoji over generic ones when applicable
1. Limit to one primary emoji per log message

## Examples

### Service Startup

```python
logger.info("🚀 Starting Apollonia API service...")
logger.info("🔌 Connecting to PostgreSQL database")
logger.info("📡 Initializing Redis cache")
logger.info("✅ All systems ready")
```

### File Processing

```python
logger.info("🎵 Audio file detected: %s", filename)
logger.info("🔍 Processing audio file...")
logger.info("🧠 Running ML analysis...")
logger.info("✅ Audio processing complete")
```

### Error Handling

```python
logger.error("❌ Failed to load model: %s", model_name)
logger.exception("💥 Critical error in processing pipeline")
logger.warning("⚠️ Falling back to CPU processing")
```

### Cleanup Operations

```python
logger.info("🧹 Starting cleanup process...")
logger.info("🗑️ Removing temporary files")
logger.info("📦 Archiving old logs")
logger.info("✅ Cleanup complete")
```

## Benefits

1. **Visual Scanning** - Quickly identify log types by emoji
1. **Categorization** - Group related operations visually
1. **Consistency** - Standardized logging across all services
1. **Developer Experience** - More enjoyable log reading
1. **Pattern Recognition** - Easily spot patterns in logs

## Migration Notes

When updating existing logging statements:

1. Identify the operation type
1. Choose the most appropriate emoji from the categories above
1. Add emoji prefix to the message
1. Ensure consistency with similar operations
1. Test that logging output remains readable
