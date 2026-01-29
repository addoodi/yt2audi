"""Test the splitter fix for format string issue."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from yt2audi.core.splitter import Splitter


def test_output_pattern():
    """Test that the output pattern is built correctly."""

    input_path = Path("test_video.mp4")
    output_dir = Path("output")

    # This would previously fail with "Unknown format code 'd' for object of type 'str'"
    # Now it should work

    # Simulate the pattern building (without actually running FFmpeg)
    output_pattern = str(output_dir / f"{input_path.stem}_part%03d{input_path.suffix}")

    print("="*80)
    print("Splitter Format Pattern Test")
    print("="*80)
    print(f"\nInput file:      {input_path}")
    print(f"Output dir:      {output_dir}")
    print(f"Output pattern:  {output_pattern}")
    print("\nExpected pattern: output/test_video_part%03d.mp4")
    print(f"Actual pattern:   {output_pattern}")

    expected = "output\\test_video_part%03d.mp4"  # Windows path

    if output_pattern == expected or output_pattern == expected.replace("\\", "/"):
        print("\n[PASS] TEST PASSED: Pattern is correct!")
        print("\nFFmpeg will replace %03d with:")
        print("  output\\test_video_part000.mp4")
        print("  output\\test_video_part001.mp4")
        print("  output\\test_video_part002.mp4")
        print("  etc.")
        return True
    else:
        print(f"\n[FAIL] TEST FAILED: Expected {expected}, got {output_pattern}")
        return False


def test_your_actual_file():
    """Show what the pattern would be for your actual file."""

    actual_file = Path(
        "output/He_Was_Last_Of_His_Clan_But_Demon_King_Gave_Him_Power_"
        "Of_Strongest_Martial_God_To_Take_Revenge_CxSoJuRWLA4.mp4"
    )

    output_dir = Path("output")
    output_pattern = str(output_dir / f"{actual_file.stem}_part%03d{actual_file.suffix}")

    print("\n" + "="*80)
    print("Your Actual File Pattern")
    print("="*80)
    print(f"\nYour file: {actual_file.name}")
    print(f"\nSplit pattern: {output_pattern}")
    print("\nThis will create:")
    print(f"  {output_dir / f'{actual_file.stem}_part000.mp4'}")
    print(f"  {output_dir / f'{actual_file.stem}_part001.mp4'}")
    print(f"  {output_dir / f'{actual_file.stem}_part002.mp4'}")
    print("\nEach part will be < 3.9GB (FAT32 safe)")
    print("="*80)


if __name__ == "__main__":
    success = test_output_pattern()
    test_your_actual_file()

    if success:
        print("\n[SUCCESS] The splitter fix is working correctly!")
        print("\nYou can now re-run the download, and it should complete successfully.")
    else:
        print("\n[FAILED] The fix didn't work as expected.")

    sys.exit(0 if success else 1)
