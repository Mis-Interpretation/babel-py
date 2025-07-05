# Screenshot Debug Mode Usage Guide

## Screenshot Debug Functionality

The screenshot service now includes debug mode that saves screenshots as image files for troubleshooting and verification.

## How to Enable Debug Mode

### Option 1: Command Line Flag
```bash
python terminal_input.py --debug
# or
python terminal_input.py -d
```

### Option 2: Programmatically
```python
from screenshot_service import ScreenshotService

service = ScreenshotService()
service.enable_debug(True)  # Enable debug mode
service.enable_debug(False) # Disable debug mode
```

## What Debug Mode Does

- **Saves screenshots** to `debug_screenshots/` folder
- **Timestamped filenames** with format: `primary_monitor_YYYYMMDD_HHMMSS_fff.jpg`
- **Console output** showing file paths when screenshots are saved
- **Quality setting** of 85% for debug files

## Debug Files

Screenshots are saved with descriptive prefixes:
- `primary_monitor_*.jpg` - Primary monitor captures
- `monitor_1_*.jpg` - Specific monitor captures
- `monitor_2_*.jpg` - etc.

## Example Output

```
Debug mode enabled. Screenshots will be saved to: debug_screenshots
📸 Capturing screenshot...
Debug: Primary monitor screenshot saved to debug_screenshots\primary_monitor_20250704_220127_680.jpg
⏳ Sending message with screenshot...
```

## Folder Structure

```
babel-py/
├── debug_screenshots/
│   ├── primary_monitor_20250704_220127_680.jpg
│   ├── monitor_1_20250704_220127_744.jpg
│   └── ...
├── screenshot_service.py
├── terminal_input.py
└── ...
```

## Clean Up

Debug images are not automatically deleted. To clean up:
```bash
# Windows
del debug_screenshots\*.jpg

# Linux/Mac
rm debug_screenshots/*.jpg
```

## Performance Impact

Debug mode has minimal performance impact:
- Screenshots are saved asynchronously
- File I/O doesn't block the main chat flow
- Only affects local file system, not network transmission 