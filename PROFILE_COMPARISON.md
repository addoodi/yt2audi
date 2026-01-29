# YT2Audi Profile Comparison Guide

## Why Files Get Larger During Conversion

### The AV1 vs H.264 Problem

Modern YouTube videos often use **AV1 codec** (highly efficient):
- AV1 achieves same quality at 40-50% smaller file sizes than H.264
- Your Audi MMI only supports H.264 (older, less efficient)
- Converting AV1 → H.264 while maintaining quality = **LARGER files**

**Example (your 24-hour video):**
- Downloaded (AV1): 3.5GB @ 0.35 Mbps
- Converted (H.264): 9.5GB @ 0.90 Mbps
- **File grew 2.7x** to maintain the same visual quality

---

## Available Profiles

### 1. Audi Q5 MMI (Default)

**Best for:** Normal videos (< 2 hours), high quality

```toml
quality_cq = 24          # Good quality
max_bitrate_mbps = "auto" # Matches input
audio_bitrate = 128kbps   # Full quality audio
```

**Expected file sizes (H.264 output):**
- 10 min video: ~150-250 MB
- 30 min video: ~450-750 MB
- 1 hour video: ~900 MB - 1.5 GB
- 2 hour video: ~1.8 - 3 GB
- 4 hour video: ~3.6 - 6 GB (needs splitting)

**Pros:**
- Best quality
- Good for short-medium videos

**Cons:**
- Large files for long videos
- May need splitting frequently

---

### 2. Audi Q5 Long Videos (NEW!)

**Best for:** Long videos (> 2 hours), podcasts, lectures, background content

```toml
quality_cq = 28          # Lower quality = smaller files
max_bitrate_mbps = 0.8   # Hard limit on bitrate
audio_bitrate = 96kbps   # Slightly lower audio
```

**Expected file sizes (H.264 output):**
- 10 min video: ~60-100 MB
- 30 min video: ~180-300 MB
- 1 hour video: ~360-600 MB
- 2 hour video: ~720 MB - 1.2 GB
- 4 hour video: ~1.4 - 2.4 GB
- **24 hour video: ~7.5 GB** (splits into 2 parts)

**Pros:**
- Much smaller files (50-60% smaller than default)
- Less splitting needed
- Still good quality for most content
- Perfect for long-form content

**Cons:**
- Slightly lower quality (but still very watchable)
- Not ideal for high-detail content (sports, action movies)

---

## Quality Comparison

### CQ (Constant Quality) Scale

| CQ Value | Quality | Use Case | File Size (relative) |
|----------|---------|----------|----------------------|
| 18 | Excellent | Movies, high-detail | 150% |
| 20 | Very Good | Movies, TV shows | 130% |
| **24** | **Good** | **Default (general use)** | **100%** |
| 26 | Acceptable | Long videos, podcasts | 75% |
| **28** | **Fair** | **Long videos, lectures** | **60%** |
| 30 | Low | Very long content | 50% |
| 32+ | Poor | Not recommended | <50% |

---

## Bitrate Limits

### Understanding max_bitrate_mbps

| Setting | Result | 1hr Video Size | 24hr Video Size |
|---------|--------|----------------|-----------------|
| `"auto"` | Matches input | ~1.5 GB | ~9.5 GB |
| `1.2` | High quality | ~540 MB | ~12.9 GB |
| `1.0` | Good quality | ~450 MB | ~10.8 GB |
| `0.8` | Acceptable | ~360 MB | ~8.6 GB |
| `0.6` | Low quality | ~270 MB | ~6.5 GB |
| `0.4` | Very low | ~180 MB | ~4.3 GB |

---

## Real-World Scenarios

### Scenario 1: Your 24-hour Video

**With Default Profile (audi_q5_mmi):**
- Input: 3.5 GB (AV1, highly compressed)
- Output: 9.5 GB (H.264, preserving quality)
- Result: Needs splitting into 3 parts

**With Long Videos Profile (audi_q5_long_videos):**
- Input: 3.5 GB (AV1)
- Output: ~7.5 GB (H.264, bitrate limited)
- Result: Splits into 2 parts (cleaner)

**Recommendation:** Use `audi_q5_long_videos` profile

---

### Scenario 2: 90-minute Movie

**With Default Profile:**
- Output: ~2.2 GB
- Result: Single file, no splitting needed
- Quality: Excellent

**With Long Videos Profile:**
- Output: ~1.3 GB
- Result: Single file
- Quality: Very good (indistinguishable for most viewers)

**Recommendation:** Use default `audi_q5_mmi` for best quality

---

### Scenario 3: 4-hour Road Trip Podcast

**With Default Profile:**
- Output: ~5.5 GB
- Result: Splits into 2 parts
- Quality: Excellent (but wasted on audio content)

**With Long Videos Profile:**
- Output: ~3.3 GB
- Result: Single file (no splitting!)
- Quality: Perfect for podcast/talk content

**Recommendation:** Definitely use `audi_q5_long_videos`

---

## How to Choose

### Use **Default Profile** (`audi_q5_mmi`) when:
- Video is < 2 hours
- High visual detail matters (movies, sports, gaming)
- You have plenty of USB storage
- Quality > file size

### Use **Long Videos Profile** (`audi_q5_long_videos`) when:
- Video is > 2 hours
- Content is talking heads, podcasts, lectures
- You want smaller files
- You're okay with slightly lower quality
- You want to minimize file splitting

---

## Switching Profiles

### In Interactive Menu:

```
Select profile:
  [1] Audi Q5 MMI (Default - balanced quality)
  [2] Audi Q5 Long Videos (For videos >2hrs, smaller files)
  [3] Custom profile

Profile choice (1-3): 2
```

### Via Command Line:

```bash
# Default profile
python -m yt2audi download "URL" --profile audi_q5_mmi

# Long videos profile
python -m yt2audi download "URL" --profile audi_q5_long_videos
```

---

## Custom Adjustments

Want to create your own custom settings? Edit the profile file:

```bash
# Copy existing profile
cp configs/profiles/audi_q5_mmi.toml configs/profiles/my_custom.toml

# Edit settings
notepad configs/profiles/my_custom.toml
```

**Key settings to adjust:**

```toml
[video]
quality_cq = 26              # Lower = better quality, higher = smaller files
max_bitrate_mbps = 0.9       # Limit maximum bitrate

[audio]
bitrate_kbps = 96            # Lower for smaller files (96-128 typical)

[output]
max_file_size_gb = 3.9       # FAT32 limit
on_size_exceed = "split"     # or "compress" to force smaller single file
```

---

## FAQ

**Q: Why does AV1 → H.264 conversion make files LARGER?**

A: AV1 is much more efficient. To keep the same visual quality in H.264, you need more data. Think of it like translating a compressed ZIP file back to uncompressed files.

---

**Q: Can I keep the AV1 file instead of converting?**

A: Unfortunately, no. Your Audi MMI only supports H.264, not AV1. Conversion is required for compatibility.

---

**Q: What if I don't care about quality for long videos?**

A: Use the Long Videos profile, or create a custom profile with:
- `quality_cq = 30` (very small files)
- `max_bitrate_mbps = 0.5` (aggressive compression)
- `audio_bitrate = 64` (minimum for acceptable audio)

---

**Q: How can I reduce file size even more?**

A: Three options:
1. Lower resolution: Set `max_height = 480` (but Audi screen is 540p)
2. Lower quality: Set `quality_cq = 30` or higher
3. Set bitrate limit: `max_bitrate_mbps = 0.5` or lower

---

**Q: Will lower quality look bad on my Audi screen?**

A: Probably not! The Audi screen is small (540p max), and you're watching while driving. Most people can't tell the difference between CQ 24 and CQ 28 on a car screen.

---

## Conclusion

For your 24-hour video, I **strongly recommend** using the **Long Videos profile**:

```
Profile choice (1-3): 2
```

This will:
- Reduce file size by ~20-30%
- Result in only 2 parts instead of 3
- Still maintain good visual quality
- Perfect for long-form content

---

*Last Updated: 2025-12-25*
