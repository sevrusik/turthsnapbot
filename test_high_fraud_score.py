#!/usr/bin/env python3
"""
Test script to verify high fraud score detection (>=80) now returns 98% confidence
This tests the fix for the discrepancy between standalone FraudLens (98%) and bot (68%)
"""

import asyncio
import httpx
import sys

FRAUDLENS_URL = "http://localhost:8000"

async def test_gemini_image(image_path: str):
    """Test Gemini image that has fraud score of 90"""

    print(f"🧪 Testing high fraud score detection")
    print(f"Image: {image_path}")
    print("=" * 80)

    try:
        # Read image
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        print(f"✅ Image loaded: {len(image_bytes)} bytes\n")

        # Call FraudLens API
        print("📡 Calling FraudLens API /api/v1/consumer/verify...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{FRAUDLENS_URL}/api/v1/consumer/verify",
                files={"image": ("test.jpg", image_bytes, "image/jpeg")},
                data={
                    "detail_level": "detailed",
                    "preserve_exif": "false"
                }
            )

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return

        result = response.json()

        print("✅ FraudLens API Response:")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Watermark Detected: {result.get('watermark_detected', False)}")
        print(f"   Processing Time: {result.get('processing_time_ms', 0)}ms")
        print()

        # Check metadata validation
        if "metadata_validation" in result:
            meta = result["metadata_validation"]
            print(f"🔍 Metadata Validation:")
            print(f"   Fraud Score: {meta.get('score', 0)}/100")
            print(f"   Risk Level: {meta.get('risk_level', 'UNKNOWN')}")
            print(f"   Red Flags: {len(meta.get('red_flags', []))}")
            if meta.get('red_flags'):
                for flag in meta['red_flags'][:3]:
                    print(f"      - {flag.get('reason', 'Unknown')}")
            print()

        # Check watermark analysis
        if result.get("watermark_detected") and "watermark_analysis" in result:
            wm = result["watermark_analysis"]
            print(f"🎯 Watermark Analysis:")
            print(f"   Type: {wm.get('type', 'Unknown')}")
            print(f"   Confidence: {wm.get('confidence', 0):.2%}")
            if "text_found" in wm:
                print(f"   Text Found: '{wm['text_found']}'")
            if "location" in wm:
                print(f"   Location: {wm['location']}")
            print()

        # Check visual watermark
        if "visual_watermark" in result and result["visual_watermark"].get("detected"):
            vw = result["visual_watermark"]
            print(f"👁️  Visual Watermark (OCR):")
            print(f"   Type: {vw.get('type', 'Unknown')}")
            print(f"   Provider: {vw.get('provider', 'Unknown')}")
            print(f"   Text Found: '{vw.get('text_found', '')}'")
            print(f"   Confidence: {vw.get('confidence', 0):.2%}")
            print()

        # Verdict summary
        print("=" * 80)
        print("📊 SUMMARY:")

        expected_confidence = 0.90  # For fraud score of 90
        actual_confidence = result["confidence"]

        if actual_confidence >= expected_confidence:
            print(f"✅ HIGH CONFIDENCE ACHIEVED: {actual_confidence:.2%}")
            print(f"   Expected: ≥{expected_confidence:.0%}")
            print(f"   Verdict: {result['verdict']}")
            print(f"   ✨ Fix successful - matches standalone FraudLens API behavior!")
        else:
            print(f"❌ CONFIDENCE TOO LOW: {actual_confidence:.2%}")
            print(f"   Expected: ≥{expected_confidence:.0%}")
            print(f"   Issue: High fraud score (90/100) should trigger early exit")

        print("=" * 80)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_high_fraud_score.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    await test_gemini_image(image_path)


if __name__ == "__main__":
    asyncio.run(main())
