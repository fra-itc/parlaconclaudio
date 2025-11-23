# Assets Directory

This directory contains application assets for the Electron app.

## Required Icons

For production builds, you need to provide the following icon files:

### Windows
- `icon.ico` - Windows icon file (256x256 or multiple sizes)

### macOS
- `icon.icns` - macOS icon file (512x512@2x)

### Linux
- `icon.png` - PNG icon file (512x512 recommended)

### System Tray
- `tray-icon.png` - Small icon for system tray (16x16 or 32x32)

## Placeholder Icons

For development, you can use placeholder icons. The application will use a default empty icon if these files are not found.

## Icon Generation Tools

- **electron-icon-maker**: Generate all required icon formats from a single PNG
- **png2icons**: Convert PNG to ICO and ICNS formats
- **Photoshop/GIMP**: Manual icon creation

## Recommended Icon Sizes

- Base PNG: 1024x1024 (for best quality across all platforms)
- Tray Icon: 32x32 (will be scaled down by the OS)
