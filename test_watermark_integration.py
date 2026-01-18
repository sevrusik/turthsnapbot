"""
Test Watermark Detection Integration

Tests the integration of FraudLens OCR watermark detection with TruthSnapBot.

Usage:
    python test_watermark_integration.py <image_path>
"""
import asyncio
import sys
from pathlib import Path

# Add TruthSnapBot to path
sys.path.insert(0, str(Path(__file__).parent / "truthsnap-bot" / "app"))

from services.fraudlens_client import FraudLensClient
from fraudlens.backend.integrations.watermark_detector import WatermarkDetector


async def test_watermark_detection(image_path: str):
    """
    Test full watermark detection pipeline
    """
    print(f"\n🧪 Testing watermark detection for: {image_path}")
    print("=" * 80)

    # Read image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print(f"✅ Image loaded: {len(image_bytes)} bytes\n")

    # STEP 1: Call FraudLens API
    print("📡 STEP 1: Calling FraudLens API...")
    client = FraudLensClient()

    try:
        result = await client.verify_photo(
            image_bytes=image_bytes,
            detail_level="detailed",
            preserve_exif=True
        )

        print(f"✅ FraudLens API Response:")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Watermark Detected: {result.get('watermark_detected', False)}")
        print(f"   Processing Time: {result.get('processing_time_ms', 0)}ms")

        if result.get('watermark_analysis'):
            wa = result['watermark_analysis']
            print(f"\n🔍 Watermark Analysis:")
            print(f"   Type: {wa.get('type', 'N/A')}")
            print(f"   Confidence: {wa.get('confidence', 0):.2%}")
            print(f"   Method: {wa.get('method', 'N/A')}")

            if wa.get('text_found'):
                print(f"   Text Found: '{wa.get('text_found')}'")

            if wa.get('location'):
                print(f"   Location: {wa.get('location')}")

            if wa.get('metadata'):
                print(f"   Metadata: {wa.get('metadata')}")

    except Exception as e:
        print(f"❌ FraudLens API Error: {e}")
        await client.close()
        return

    # STEP 2: Extract watermark info using WatermarkDetector
    print(f"\n📦 STEP 2: Extracting watermark info via WatermarkDetector...")
    detector = WatermarkDetector()

    watermark_info = await detector.detect(
        image_bytes=image_bytes,
        fraudlens_result=result  # Pass FraudLens result
    )

    print(f"✅ Watermark Info Extracted:")
    print(f"   Detected: {watermark_info['detected']}")
    print(f"   Type: {watermark_info['type']}")
    print(f"   Confidence: {watermark_info['confidence']:.2%}")

    if watermark_info.get('text_found'):
        print(f"   Text Found: '{watermark_info['text_found']}'")

    if watermark_info.get('location'):
        print(f"   Location: {watermark_info['location']}")

    if watermark_info.get('method'):
        print(f"   Detection Method: {watermark_info['method']}")

    # STEP 3: Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")

    if watermark_info['detected']:
        print(f"✅ AI Watermark DETECTED via {watermark_info.get('method', 'unknown method')}")
        print(f"   Generator: {watermark_info['type']}")
        print(f"   Confidence: {watermark_info['confidence']:.2%}")

        if watermark_info.get('text_found'):
            print(f"   OCR Text: '{watermark_info['text_found']}'")

    else:
        print("❌ No AI watermark detected")
        print("   This could mean:")
        print("   - Image is a real photo")
        print("   - AI generator doesn't add watermarks")
        print("   - Watermark was removed")

    print("=" * 80)

    await client.close()


async def test_multiple_images(image_paths: list):
    """
    Test watermark detection on multiple images
    """
    print(f"\n🧪 Testing {len(image_paths)} images...")

    for i, image_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] {image_path}")
        await test_watermark_detection(image_path)
        print("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_watermark_integration.py <image_path> [<image_path2> ...]")
        print("\nExample:")
        print("  python test_watermark_integration.py test_data/gemini_generated.jpg")
        print("  python test_watermark_integration.py test_data/*.jpg")
        sys.exit(1)

    image_paths = sys.argv[1:]

    if len(image_paths) == 1:
        asyncio.run(test_watermark_detection(image_paths[0]))
    else:
        asyncio.run(test_multiple_images(image_paths))
