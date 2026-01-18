#!/usr/bin/env python3
"""
FFT Detailed Profiling
"""
import time
import asyncio
import sys
from PIL import Image
import io
import numpy as np

sys.path.insert(0, '/app/backend')
from integrations.fft_detector import FFTDetector

async def profile_detailed():
    # Create test image
    img = Image.new('RGB', (1024, 1024), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()

    detector = FFTDetector()

    # Warm up
    await detector.analyze(img_bytes)

    # Profile one iteration in detail
    print("Profiling single iteration...")

    import io as io_module
    from scipy import fft

    t0 = time.time()

    # Step 1: Load image
    t1 = time.time()
    img = Image.open(io_module.BytesIO(img_bytes))
    t2 = time.time()
    print(f"1. Image.open: {(t2-t1)*1000:.2f}ms")

    # Step 2: Resize check
    t1 = time.time()
    if max(img.size) > 2048:
        if img.width > img.height:
            new_width = 2048
            new_height = int(img.height * (2048 / img.width))
        else:
            new_height = 2048
            new_width = int(img.width * (2048 / img.height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    t2 = time.time()
    print(f"2. Resize check: {(t2-t1)*1000:.2f}ms")

    # Step 3: Convert to array
    t1 = time.time()
    img_array = np.array(img.convert('RGB'))
    t2 = time.time()
    print(f"3. Convert to RGB array: {(t2-t1)*1000:.2f}ms")

    # Step 4: Grayscale
    t1 = time.time()
    gray = np.mean(img_array, axis=2)
    t2 = time.time()
    print(f"4. Convert to grayscale: {(t2-t1)*1000:.2f}ms")

    # Step 5: FFT computation
    t1 = time.time()
    f = fft.fft2(gray)
    t2 = time.time()
    print(f"5. FFT2 computation: {(t2-t1)*1000:.2f}ms")

    # Step 6: FFT shift
    t1 = time.time()
    fshift = fft.fftshift(f)
    t2 = time.time()
    print(f"6. FFT shift: {(t2-t1)*1000:.2f}ms")

    # Step 7: Magnitude spectrum
    t1 = time.time()
    magnitude_spectrum = np.abs(fshift)
    t2 = time.time()
    print(f"7. Magnitude spectrum: {(t2-t1)*1000:.2f}ms")

    # Step 8: Power spectrum
    t1 = time.time()
    power_spectrum = magnitude_spectrum ** 2
    t2 = time.time()
    print(f"8. Power spectrum: {(t2-t1)*1000:.2f}ms")

    # Step 9: Geometric arrays
    t1 = time.time()
    h, w = magnitude_spectrum.shape
    center_h, center_w = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - center_w)**2 + (y - center_h)**2)
    t2 = time.time()
    print(f"9. Geometric arrays: {(t2-t1)*1000:.2f}ms")

    # Step 10: Check 1 - JPEG artifacts
    t1 = time.time()
    jpeg_score = detector._check_jpeg_artifacts_optimized(magnitude_spectrum, center_h, center_w)
    t2 = time.time()
    print(f"10. JPEG artifacts check: {(t2-t1)*1000:.2f}ms")

    # Step 11: Check 2 - High frequency
    t1 = time.time()
    hf_score = detector._check_high_frequency_optimized(magnitude_spectrum, dist, center_h, center_w)
    t2 = time.time()
    print(f"11. High-frequency check: {(t2-t1)*1000:.2f}ms")

    # Step 12: Check 3 - Power spectrum
    t1 = time.time()
    spectrum_score = detector._check_power_spectrum_optimized(power_spectrum, dist, center_h, center_w)
    t2 = time.time()
    print(f"12. Power spectrum check: {(t2-t1)*1000:.2f}ms")

    # Step 13: Check 4 - Periodic patterns
    t1 = time.time()
    periodic_score = detector._check_periodic_patterns_optimized(magnitude_spectrum, center_h, center_w)
    t2 = time.time()
    print(f"13. Periodic patterns check: {(t2-t1)*1000:.2f}ms")

    total = time.time() - t0
    print(f"\nTOTAL: {total*1000:.2f}ms")

    # Now run full benchmark
    print("\n" + "="*50)
    print("Running full benchmark (10 iterations)...")
    start = time.time()
    for i in range(10):
        result = await detector.analyze(img_bytes)
    end = time.time()

    total_time = end - start
    avg_time = total_time / 10

    print(f"\nTotal time: {total_time:.2f}s")
    print(f"Average per image: {avg_time:.3f}s")
    print(f"Images per second: {1/avg_time:.2f}")

if __name__ == "__main__":
    asyncio.run(profile_detailed())
