#!/bin/bash
# Fix Plasmo build issues by clearing all caches

echo "🧹 Cleaning Plasmo build cache..."

# Remove Plasmo build directory
rm -rf .plasmo

# Remove node_modules cache
rm -rf node_modules/.cache

# Remove Parcel cache
rm -rf .parcel-cache

# Remove any build artifacts
rm -rf build
rm -rf dist

echo "✅ Cache cleared!"
echo ""
echo "Now run: npm run dev"










