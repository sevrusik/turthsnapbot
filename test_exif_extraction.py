#!/usr/bin/env python3
"""
Test EXIF extraction for TruthSnapBot
Tests GPS, Device info, and other metadata extraction
"""
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fraudlens'))

from PIL import Image
from backend.integrations.metadata import MetadataAnalyzer

async def test_exif_extraction(image_path: str):
    """Test EXIF extraction on an image file"""
    print(f"\n{'='*80}")
    print(f"Testing EXIF extraction: {image_path}")
    print(f"{'='*80}\n")

    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: File not found: {image_path}")
        return

    # Read image bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print(f"✅ Read {len(image_bytes):,} bytes\n")

    # Test with PIL directly (modern method)
    print("1️⃣ Testing PIL getexif() method:")
    print("-" * 80)
    try:
        img = Image.open(image_path)
        exif = img.getexif()

        if exif:
            print(f"✅ Found {len(exif)} EXIF tags")

            # Print some key tags
            from PIL.ExifTags import TAGS
            for tag_id, value in list(exif.items())[:10]:
                tag = TAGS.get(tag_id, tag_id)
                print(f"  • {tag} ({tag_id}): {str(value)[:100]}")

            # Check for GPS
            if 34853 in exif:
                print(f"\n  📍 GPS IFD found (tag 34853)")
                gps_ifd = exif.get(34853)
                print(f"     GPS data type: {type(gps_ifd)}")
                if hasattr(gps_ifd, 'items'):
                    print(f"     GPS tags: {len(gps_ifd)} items")
                elif hasattr(gps_ifd, 'keys'):
                    print(f"     GPS tags: {len(list(gps_ifd.keys()))} keys")
            else:
                print(f"\n  ⚠️  No GPS IFD found")
        else:
            print("❌ No EXIF data found")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test with MetadataAnalyzer
    print(f"\n2️⃣ Testing MetadataAnalyzer.analyze():")
    print("-" * 80)
    try:
        analyzer = MetadataAnalyzer()
        result = await analyzer.analyze(image_bytes)

        print(f"✅ Analysis complete")
        print(f"\n📊 Results:")
        print(f"  • Format: {result.get('format')}")
        print(f"  • Size: {result.get('size')}")
        print(f"  • Mode: {result.get('mode')}")
        print(f"  • EXIF tags: {len(result.get('exif', {}))}")
        print(f"  • Manipulation detected: {result.get('manipulation_detected')}")
        print(f"  • Anomalies: {len(result.get('anomalies', []))}")

        if result.get('exif'):
            print(f"\n  📝 Key EXIF fields:")
            key_fields = ['Make', 'Model', 'Software', 'DateTime', 'DateTimeOriginal']
            for field in key_fields:
                if field in result['exif']:
                    print(f"     • {field}: {result['exif'][field]}")

        if result.get('gps'):
            print(f"\n  📍 GPS Coordinates:")
            gps = result['gps']
            print(f"     • Latitude: {gps.get('latitude'):.6f}")
            print(f"     • Longitude: {gps.get('longitude'):.6f}")
            if 'altitude' in gps:
                print(f"     • Altitude: {gps.get('altitude'):.2f}m")
        else:
            print(f"\n  ⚠️  No GPS coordinates found")

        if result.get('anomalies'):
            print(f"\n  🚨 Anomalies:")
            for anomaly in result['anomalies']:
                print(f"     • {anomaly}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*80}\n")

async def main():
    """Test multiple image files"""
    # Test with provided test images
    test_images = [
        "/Volumes/KINGSTON/Projects/FraudLensAI/test_data/test_original.jpg",
        "/Volumes/KINGSTON/Projects/FraudLensAI/test_data/test_similar.jpg",
        "/Volumes/KINGSTON/Projects/FraudLensAI/test_data/test_different.jpg",
    ]

    print("\n" + "="*80)
    print("EXIF EXTRACTION TEST SUITE")
    print("="*80)

    # Test each image
    for image_path in test_images:
        await test_exif_extraction(image_path)

    # Allow custom image path
    if len(sys.argv) > 1:
        custom_path = sys.argv[1]
        await test_exif_extraction(custom_path)

    print("\n✅ All tests complete!\n")

if __name__ == "__main__":
    asyncio.run(main())
