"""
Simple test for OCR watermark detection through FraudLens API

Usage:
    python test_ocr_simple.py
"""
import asyncio
import sys
from pathlib import Path

# Test using FraudLens API directly
sys.path.insert(0, "/Volumes/KINGSTON/Projects/FraudLensAI")

from backend.integrations.content_credentials import ContentCredentialsDetector
from backend.integrations.visual_watermark_detector import VisualWatermarkDetector


async def test_visual_watermark_direct(image_path: str):
    """Test visual watermark detector directly"""
    print(f"\n🧪 Testing Visual Watermark Detector")
    print("=" * 80)

    detector = VisualWatermarkDetector()

    result = detector.detect_watermark(image_path)

    print(f"✅ Visual Watermark Detection Result:")
    print(f"   Has Watermark: {result['has_watermark']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Type: {result.get('watermark_type', 'N/A')}")
    print(f"   Method: {result.get('method', 'N/A')}")

    if result.get('text_found'):
        print(f"   Text Found: '{result['text_found']}'")

    if result.get('location'):
        print(f"   Location: {result['location']}")

    print("=" * 80)

    return result


async def test_content_credentials(image_path: str):
    """Test content credentials detector (includes visual watermark)"""
    print(f"\n🧪 Testing Content Credentials Detector")
    print("=" * 80)

    detector = ContentCredentialsDetector()

    result = await detector.detect_credentials(image_path)

    print(f"✅ Content Credentials Result:")
    print(f"   Has Credentials: {result['has_credentials']}")
    print(f"   Is AI Generated: {result.get('is_ai_generated', False)}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Generator: {result.get('generator', 'N/A')}")
    print(f"   Method: {result.get('method', 'N/A')}")

    if result.get('text_found'):
        print(f"   OCR Text: '{result['text_found']}'")

    if result.get('location'):
        print(f"   Location: {result['location']}")

    print("=" * 80)

    return result


async def main():
    """Main test"""
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_simple.py <image_path>")
        print("\nExample:")
        print("  python test_ocr_simple.py /path/to/gemini_image.png")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"❌ Error: Image not found: {image_path}")
        sys.exit(1)

    print(f"\n📸 Testing OCR Watermark Detection")
    print(f"Image: {image_path}")

    # Test 1: Visual watermark detector directly
    await test_visual_watermark_direct(image_path)

    # Test 2: Content credentials (includes visual watermark)
    await test_content_credentials(image_path)

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
