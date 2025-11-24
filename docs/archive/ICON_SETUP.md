# Extension Icon Setup

## Icons Created

Proper PNG icons have been created in the `assets/` directory:
- `icon32.png` - 32x32 pixels
- `icon64.png` - 64x64 pixels  
- `icon128.png` - 128x128 pixels
- `icon256.png` - 256x256 pixels
- `icon512.png` - 512x512 pixels

All icons are valid PNG images with an indigo background (#6366f1) and white "L" text.

## Verification

To verify icons are valid:
```bash
file assets/icon*.png
```

All should show: `PNG image data, [size] x [size], 8-bit/color RGB`

## Replacing Icons

To replace with custom icons:
1. Create PNG files with the same names
2. Ensure they are proper PNG format (not just renamed files)
3. Recommended: Use a design tool to create proper icons

## Plasmo Build

The build should now work correctly with these icons. If you see errors:
1. Ensure icons are valid PNG files
2. Check file permissions
3. Try: `rm -rf .plasmo build && npm run dev`


