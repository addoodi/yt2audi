"""Test script to verify foundation components."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("YT2Audi v2.0 - Foundation Test")
print("=" * 60)

# Test 1: Import core modules
print("\n[1/5] Testing imports...")
try:
    import yt2audi
    from yt2audi.models import Profile, EncoderType, Job
    from yt2audi.config import load_profile, list_available_profiles
    from yt2audi.exceptions import YT2AudiError, ConfigError
    print("[OK] All imports successful")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Check version
print(f"\n[2/5] Checking version...")
print(f"[OK] YT2Audi version: {yt2audi.__version__}")

# Test 3: Load profile from TOML
print(f"\n[3/5] Testing profile loading...")
try:
    profile_path = Path("configs/profiles/audi_q5_mmi.toml")
    if not profile_path.exists():
        print(f"[FAIL] Profile not found: {profile_path}")
    else:
        profile = Profile.from_toml_file(profile_path)
        print(f"[OK] Loaded profile: {profile.profile.name}")
        print(f"  - Max resolution: {profile.video.max_width}x{profile.video.max_height}")
        print(f"  - Video codec: {profile.video.codec}")
        print(f"  - Audio bitrate: {profile.audio.bitrate_kbps}kbps")
        print(f"  - Max file size: {profile.output.max_file_size_gb}GB")
        print(f"  - On size exceed: {profile.output.on_size_exceed.value}")
except Exception as e:
    print(f"[FAIL] Profile loading failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test Pydantic validation
print(f"\n[4/5] Testing Pydantic validation...")
try:
    # This should fail - max_width must be >= 1
    from yt2audi.models import VideoConfig
    try:
        invalid_config = VideoConfig(max_width=0)
        print("[FAIL] Validation didn't catch invalid max_width")
    except Exception:
        print("[OK] Validation correctly rejected invalid max_width=0")

    # This should succeed
    valid_config = VideoConfig(max_width=1280, max_height=720)
    print(f"[OK] Valid config accepted: {valid_config.max_width}x{valid_config.max_height}")
except Exception as e:
    print(f"[FAIL] Validation test failed: {e}")

# Test 5: Test GPU detection (if dependencies available)
print(f"\n[5/5] Testing GPU detection...")
try:
    from yt2audi.core.gpu_detector import detect_available_gpus, select_best_encoder

    gpus = detect_available_gpus()
    print(f"[OK] GPU detection ran successfully")
    print(f"  - GPUs found: {len(gpus)}")
    for gpu in gpus:
        print(f"    * {gpu.vendor.value}: {gpu.name}")

    # Try to select encoder
    encoder = select_best_encoder([
        EncoderType.NVENC_H264,
        EncoderType.AMF_H264,
        EncoderType.QSV_H264,
        EncoderType.LIBX264,
    ])
    print(f"  - Selected encoder: {encoder.value}")

except ImportError as e:
    print(f"[WARN] GPU detection skipped (missing dependencies): {e}")
except Exception as e:
    print(f"[FAIL] GPU detection failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Foundation test complete!")
print("=" * 60)
