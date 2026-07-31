#!/bin/bash

# Configuration
ICON_SIZE="40x40"
ICON_COLOR="#ae8593" # Mixed Pink and Green
SVG_DIR="./svg"
PNG_DIR="./png"
OUTPUT_DIR="./xpm"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "✨ CCE Icons Builder"
echo "-----------------------"
echo "Target Color: $ICON_COLOR"

# Check for ImageMagick
if ! command -v magick &> /dev/null; then
    echo "❌ Error: ImageMagick (magick) is not installed."
    exit 1
fi

count=0

# Convert SVGs
for svg in "$SVG_DIR"/*.svg; do
    [ -e "$svg" ] || continue
    filename=$(basename -- "$svg")
    name="${filename%.*}"
    output="$OUTPUT_DIR/$name.xpm"
    echo "🎨 Converting & Coloring: $filename -> $name.xpm"
    # -fill + -colorize 100% applies the color while preserving alpha
    magick -background none "$svg" -fill "$ICON_COLOR" -colorize 100% -resize "$ICON_SIZE" "$output"
    ((count++))
done

# Convert PNGs
for png in "$PNG_DIR"/*.png; do
    [ -e "$png" ] || continue
    filename=$(basename -- "$png")
    name="${filename%.*}"
    output="$OUTPUT_DIR/$name.xpm"
    echo "🎨 Converting & Coloring: $filename -> $name.xpm"
    magick -background none "$png" -fill "$ICON_COLOR" -colorize 100% -resize "$ICON_SIZE" "$output"
    ((count++))
done

if [ "$count" -eq 0 ]; then
    echo "📭 No source files found."
else
    echo "-----------------------"
    echo "✅ Successfully converted $count icons to $OUTPUT_DIR"
fi
