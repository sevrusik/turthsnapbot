#!/usr/bin/env python3
"""
FFT Performance Benchmark
"""
import time
import asyncio
import sys
from PIL import Image
import io

sys.path.insert(0, '/app/backend')
from integrations.fft_detector import FFTDetector

async def benchmark():
    # Create test image
    img = Image.new('RGB', (1024, 1024), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()

    detector = FFTDetector()

    # Warm up
    print("Warming up...")
    await detector.analyze(img_bytes)

    # Benchmark
    print("Running benchmark (10 iterations)...")
    start = time.time()
    for i in range(10):
        result = await detector.analyze(img_bytes)
        print(f"  Iteration {i+1}/10 complete")
    end = time.time()

    total_time = end - start
    avg_time = total_time / 10

    print(f"\n{'='*50}")
    print(f"RESULTS:")
    print(f"{'='*50}")
    print(f"Total time for 10 iterations: {total_time:.2f}s")
    print(f"Average per image: {avg_time:.3f}s")
    print(f"Images per second: {1/avg_time:.2f}")
    print(f"Sample FFT score: {result['fft_score']:.3f}")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(benchmark())
