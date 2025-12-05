#!/bin/bash
# Complete clean rebuild script for Plasmo extension

echo "🧹 Cleaning Plasmo extension build cache..."

# Stop any running dev servers
echo "Stopping dev servers..."
pkill -f "plasmo dev" 2>/dev/null || echo "No plasmo process running"

# Wait a moment for processes to stop
sleep 2

# Remove all build artifacts and caches
echo "Removing build artifacts..."
rm -rf .plasmo
rm -rf node_modules/.cache
rm -rf .parcel-cache
rm -rf build
rm -rf dist
rm -rf .plasmo-temp

# Optional: Clear npm cache (uncomment if needed)
# npm cache clean --force

echo "✅ Cache cleared!"
echo ""
echo "Now run: npm run dev"










