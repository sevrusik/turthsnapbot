#!/usr/bin/env python3
"""
Test EXIF Extraction on Server
Run this on the server to verify PyExifTool works

Usage:
    python3 test_exif_on_server.py /path/to/image.jpg
"""
import sys
import os

def test_exiftool_import():
    """Test if PyExifTool can be imported"""
    print("\n" + "="*70)
    print("1️⃣ Testing PyExifTool Import")
    print("="*70)

    try:
        from exiftool import ExifToolHelper
        print("✅ ExifToolHelper imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ExifToolHelper: {e}")
        print("\nInstall with: pip3 install PyExifTool==0.5.6")
        return False


def test_exiftool_cli():
    """Test if exiftool CLI is available"""
    print("\n" + "="*70)
    print("2️⃣ Testing ExifTool CLI")
    print("="*70)

    import subprocess
    try:
        result = subprocess.run(['exiftool', '-ver'],
                              capture_output=True, text=True, check=True)
        print(f"✅ ExifTool CLI version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ exiftool command not found")
        print("\nInstall with: apt install exiftool")
        return False
    except Exception as e:
        print(f"❌ Error running exiftool: {e}")
        return False


def test_extraction(image_path: str):
    """Test EXIF extraction from a real image"""
    print("\n" + "="*70)
    print(f"3️⃣ Testing EXIF Extraction: {image_path}")
    print("="*70)

    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return False

    try:
        from exiftool import ExifToolHelper

        with ExifToolHelper() as et:
            metadata = et.get_metadata(image_path)

            if not metadata:
                print("❌ No metadata extracted")
                return False

            result = metadata[0]
            print(f"✅ Extracted {len(result)} EXIF fields\n")

            # Check for critical fields
            critical_fields = [
                ('MakerNotes:RunTimeFlags', 'Apple Runtime Token'),
                ('EXIF:SerialNumber', 'Camera Serial'),
                ('EXIF:Make', 'Camera Make'),
                ('EXIF:Model', 'Camera Model'),
                ('GPS:GPSLatitude', 'GPS Latitude'),
                ('XMP:CreatorTool', 'Creator Tool'),
            ]

            print("🔍 Critical Fields Check:")
            found_count = 0
            for field, description in critical_fields:
                value = result.get(field)
                if value:
                    print(f"  ✅ {description:25s}: {str(value)[:50]}")
                    found_count += 1
                else:
                    print(f"  ❌ {description:25s}: NOT FOUND")

            print(f"\nFound {found_count}/{len(critical_fields)} critical fields")

            # Show all categories
            print("\n📦 Available Categories:")
            categories = {}
            for key in result.keys():
                if ':' in key:
                    cat = key.split(':')[0]
                    categories[cat] = categories.get(cat, 0) + 1

            for cat, count in sorted(categories.items()):
                print(f"  • {cat:20s}: {count:3d} fields")

            return True

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_validator():
    """Test MetadataValidator integration"""
    print("\n" + "="*70)
    print("4️⃣ Testing MetadataValidator Integration")
    print("="*70)

    try:
        # Try to import from fraudlens structure
        sys.path.insert(0, '/opt/truthsnap-ecosystem/fraudlens')
        sys.path.insert(0, '/opt/truthsnap-ecosystem/api')

        from backend.integrations.metadata_validator import MetadataValidator
        print("✅ MetadataValidator imported successfully")

        # Check if _extract_exiftool method exists
        validator = MetadataValidator()
        if hasattr(validator, '_extract_exiftool'):
            print("✅ _extract_exiftool method found")
        else:
            print("❌ _extract_exiftool method not found")

        return True

    except ImportError as e:
        print(f"❌ Failed to import MetadataValidator: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("🔍 TruthSnap EXIF Extraction Test Suite")
    print("="*70)

    # Test 1: Import
    import_ok = test_exiftool_import()
    if not import_ok:
        print("\n❌ FAILED: Cannot proceed without PyExifTool")
        sys.exit(1)

    # Test 2: CLI
    cli_ok = test_exiftool_cli()

    # Test 3: Extract from image
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        extraction_ok = test_extraction(image_path)
    else:
        print("\n⚠️  No image provided for extraction test")
        print("Usage: python3 test_exif_on_server.py /path/to/image.jpg")
        extraction_ok = None

    # Test 4: MetadataValidator
    validator_ok = test_metadata_validator()

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"  PyExifTool Import:     {'✅ PASS' if import_ok else '❌ FAIL'}")
    print(f"  ExifTool CLI:          {'✅ PASS' if cli_ok else '❌ FAIL'}")
    print(f"  Extraction Test:       {'✅ PASS' if extraction_ok else '⚠️ SKIP' if extraction_ok is None else '❌ FAIL'}")
    print(f"  MetadataValidator:     {'✅ PASS' if validator_ok else '❌ FAIL'}")
    print("="*70)

    if import_ok and cli_ok and (extraction_ok or extraction_ok is None) and validator_ok:
        print("\n✅ All tests passed! EXIF extraction should work.")
        print("\nNext steps:")
        print("  1. Restart services: systemctl restart fraudlens truthsnap-bot")
        print("  2. Send a document (not photo) to the bot")
        print("  3. Check logs: journalctl -u fraudlens -f | grep -E 'exiftool|EXIF|RunTime'")
    else:
        print("\n❌ Some tests failed. Check errors above.")


if __name__ == '__main__':
    main()
