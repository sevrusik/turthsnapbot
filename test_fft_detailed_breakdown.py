#!/usr/bin/env python3
"""
Detailed FFT Performance Breakdown
Shows exactly where time is spent and why
"""
import time
import asyncio
import sys
from PIL import Image
import io
import numpy as np

sys.path.insert(0, '/app/backend')
from integrations.fft_detector import FFTDetector

def profile_single_image():
    """Profile a single image analysis in extreme detail"""

    # Create test image
    img = Image.new('RGB', (1024, 1024), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()

    print("="*70)
    print("DETAILED FFT PERFORMANCE BREAKDOWN")
    print("="*70)
    print(f"Image size: 1024x1024 pixels = {1024*1024:,} pixels")
    print(f"Image bytes: {len(img_bytes):,} bytes")
    print("="*70)

    # Manual breakdown
    import io as io_module
    from scipy import fft

    times = {}

    # Step 1: Image loading and decoding
    t1 = time.perf_counter()
    img = Image.open(io_module.BytesIO(img_bytes))
    t2 = time.perf_counter()
    times['1_image_open'] = (t2-t1)*1000

    # Step 2: RGB conversion
    t1 = time.perf_counter()
    img_array = np.array(img.convert('RGB'))
    t2 = time.perf_counter()
    times['2_rgb_conversion'] = (t2-t1)*1000
    print(f"Array shape: {img_array.shape} = {img_array.size:,} values")
    print(f"Array memory: {img_array.nbytes:,} bytes ({img_array.nbytes/1024/1024:.2f} MB)")

    # Step 3: Grayscale conversion
    t1 = time.perf_counter()
    gray = np.mean(img_array, axis=2)
    t2 = time.perf_counter()
    times['3_grayscale'] = (t2-t1)*1000
    print(f"Grayscale shape: {gray.shape} = {gray.size:,} values")
    print(f"Grayscale memory: {gray.nbytes:,} bytes ({gray.nbytes/1024/1024:.2f} MB)")

    # Step 4: FFT2 computation (THE MAIN OPERATION)
    t1 = time.perf_counter()
    f = fft.fft2(gray)
    t2 = time.perf_counter()
    times['4_fft2_compute'] = (t2-t1)*1000
    print(f"FFT output shape: {f.shape} (complex128)")
    print(f"FFT memory: {f.nbytes:,} bytes ({f.nbytes/1024/1024:.2f} MB)")

    # Step 5: FFT shift
    t1 = time.perf_counter()
    fshift = fft.fftshift(f)
    t2 = time.perf_counter()
    times['5_fft_shift'] = (t2-t1)*1000

    # Step 6: Magnitude spectrum
    t1 = time.perf_counter()
    magnitude_spectrum = np.abs(fshift)
    t2 = time.perf_counter()
    times['6_magnitude'] = (t2-t1)*1000
    print(f"Magnitude shape: {magnitude_spectrum.shape}")
    print(f"Magnitude memory: {magnitude_spectrum.nbytes:,} bytes ({magnitude_spectrum.nbytes/1024/1024:.2f} MB)")

    # Step 7: Power spectrum
    t1 = time.perf_counter()
    power_spectrum = magnitude_spectrum ** 2
    t2 = time.perf_counter()
    times['7_power_spectrum'] = (t2-t1)*1000

    # Step 8: Geometric arrays
    h, w = magnitude_spectrum.shape
    center_h, center_w = h // 2, w // 2
    t1 = time.perf_counter()
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - center_w)**2 + (y - center_h)**2)
    t2 = time.perf_counter()
    times['8_geometric_arrays'] = (t2-t1)*1000

    # Step 9-12: The four checks
    detector = FFTDetector()

    t1 = time.perf_counter()
    _ = detector._check_jpeg_artifacts_optimized(magnitude_spectrum, center_h, center_w)
    t2 = time.perf_counter()
    times['9_jpeg_artifacts'] = (t2-t1)*1000

    t1 = time.perf_counter()
    _ = detector._check_high_frequency_optimized(magnitude_spectrum, dist, center_h, center_w)
    t2 = time.perf_counter()
    times['10_high_frequency'] = (t2-t1)*1000

    t1 = time.perf_counter()
    _ = detector._check_power_spectrum_optimized(power_spectrum, dist, center_h, center_w)
    t2 = time.perf_counter()
    times['11_power_spectrum_check'] = (t2-t1)*1000

    t1 = time.perf_counter()
    _ = detector._check_periodic_patterns_optimized(magnitude_spectrum, center_h, center_w)
    t2 = time.perf_counter()
    times['12_periodic_patterns'] = (t2-t1)*1000

    print("\n" + "="*70)
    print("TIME BREAKDOWN (milliseconds)")
    print("="*70)

    total_time = 0
    for step, ms in times.items():
        print(f"{step:30s}: {ms:6.2f}ms ({ms/sum(times.values())*100:5.1f}%)")
        total_time += ms

    print("-"*70)
    print(f"{'TOTAL':30s}: {total_time:6.2f}ms (100.0%)")
    print("="*70)

    # Theoretical calculations
    print("\nTHEORETICAL ANALYSIS:")
    print("="*70)

    # FFT complexity
    n = 1024 * 1024
    fft_ops = n * np.log2(n)
    print(f"FFT size: {1024}x{1024} = {n:,} points")
    print(f"FFT complexity: O(N log N) = {n:,} × log₂({n:,}) = {fft_ops:,.0f} operations")
    print(f"FFT time: {times['4_fft2_compute']:.2f}ms")
    print(f"Operations per ms: {fft_ops/times['4_fft2_compute']:,.0f}")

    # Memory bandwidth
    rgb_size = img_array.nbytes
    gray_size = gray.nbytes
    fft_size = f.nbytes
    total_memory = rgb_size + gray_size + fft_size + magnitude_spectrum.nbytes + power_spectrum.nbytes

    print(f"\nTotal memory moved: {total_memory:,} bytes ({total_memory/1024/1024:.2f} MB)")
    print(f"Memory bandwidth: {total_memory/total_time:.2f} MB/ms = {total_memory/total_time*1000/1024:.2f} MB/s")

    print("\n" + "="*70)
    print("WHY THIS SPEED?")
    print("="*70)
    print(f"1. FFT is O(N log N), not O(N²) - highly optimized FFTW library")
    print(f"2. NumPy/SciPy use vectorized C/Fortran code (not Python loops)")
    print(f"3. Single FFT computation (was 4x before optimization)")
    print(f"4. Avoided expensive scipy.ndimage.maximum_filter")
    print(f"5. Vectorized operations: np.bincount, boolean masks, etc.")
    print(f"6. CPU can process {fft_ops/times['4_fft2_compute']/1e6:.1f}M FFT ops/sec")

    print("\n" + "="*70)
    print(f"RESULT: {1000/total_time:.1f} images/second")
    print("="*70)

async def main():
    profile_single_image()

    # Verify with actual detector
    print("\n" + "="*70)
    print("VERIFICATION WITH ACTUAL DETECTOR")
    print("="*70)

    img = Image.new('RGB', (1024, 1024), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()

    detector = FFTDetector()

    # Run 20 iterations
    times = []
    for i in range(20):
        t1 = time.perf_counter()
        await detector.analyze(img_bytes)
        t2 = time.perf_counter()
        times.append((t2-t1)*1000)

    times = np.array(times)
    print(f"20 iterations:")
    print(f"  Mean: {np.mean(times):.2f}ms")
    print(f"  Std:  {np.std(times):.2f}ms")
    print(f"  Min:  {np.min(times):.2f}ms")
    print(f"  Max:  {np.max(times):.2f}ms")
    print(f"  Throughput: {1000/np.mean(times):.1f} images/second")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
