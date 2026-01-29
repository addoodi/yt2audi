# Audi Q5 (2019) Supported Media & Specifications

## 1. General Media Support

*Applies to Jukebox, SD card reader, and USB storage device connections.*

### Supported Hardware & Storage

| **Media Type**                 | **Specifications**                                                                                                                                                                                        |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SD Memory Cards**            | SD, SDHC, SDXC, MMC with capacity up to **128 GB**                                                                                                                                                        |
| **DVD Drive**                  | • Audio CDs (up to 80 min) with CD text (artist, album, song)  <br>• CD-ROMs up to 700 MB  <br>• DVD $\pm$ R/RW  <br>• DVD video & DVD audio (compatible tracks)                                          |
| **Audi Music Interface (USB)** | • Mobile devices (e.g., iPod, MTP players)  <br>• USB storage devices ("USB Device Subclass 1 and 6", USB 2.0)  <br>• USB sticks, USB MP3 players (Plug-and-Play), external flash drives, and hard drives |

### File Systems & Structure

| **Feature**                  | **Details**                                               |
| ---------------------------- | --------------------------------------------------------- |
| **Memory Card File Systems** | exFAT, FAT, FAT32, NTFS                                   |
| **USB Storage File Systems** | FAT, FAT32, NTFS                                          |
| **CD/DVD File Systems**      | ISO9660, Joliet, UDF                                      |
| **Partitions**               | Max **2** partitions per USB connection (primary/logical) |

### Supported File Formats (Audio & Video)

| **Format / Codec**        | **File Extensions**                     | **Notes**                                          |
| ------------------------- | --------------------------------------- | -------------------------------------------------- |
| **MPEG 1/2 Layer 3**      | `.mp3`                                  |                                                    |
| **Windows Media Audio**   | `.wma`, `.asf`                          | Versions 9 and 10. *Voice format 9 not supported*. |
| **MPEG 2/4**              | `.m4a`, `.m4b`, `.aac`                  |                                                    |
| **FLAC**                  | `.flac`                                 |                                                    |
| **MPEG 1/2 Video**        | `.mpg`, `.mpeg`, `.avi`                 |                                                    |
| **MPEG 4 Video**          | `.mp4`, `.m4v`, `.mov`                  | ISO MPEG4; MPEG4 AVC (H.264)                       |
| **Windows Media Video 9** | `.wmv`, `.asf`                          |                                                    |
| **Playlists**             | `.M3U`, `.PLS`, `.WPL`, `.M3U8`, `.ASX` |                                                    |

### Performance Characteristics & Limits

| **Category**               | **Limit**                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Audio Quality**          | Max **320 kbit/s** and **48 kHz** sampling frequency                                                        |
| **Video Quality**          | Max **2,000 kbit/s** bitrate  <br>Max resolution **720** $\times$ **576 px**  <br>Max frame rate **25 fps** |
| **Metadata (Album Cover)** | GIF, JPG, PNG up to **800** $\times$ **800 px**                                                             |

### File Quantity Limits

- **DVD Drive:** Max 1,000 files per medium.

- **Jukebox:** Approx. 10 GB capacity; max 3,000 files can be imported.

- **USB/SD Cards:** Max 10,000 files per medium; max 1,000 files per playlist/directory.

## 2. CD Drive Specifications

*Applies specifically to vehicles equipped with a CD drive.*

| **Feature**                 | **Details**                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Supported Media**         | Audio CDs (up to 80 min with CD text), CD-ROMs (up to 700 MB)                                        |
| **File Systems**            | ISO9660, Joliet, UDF                                                                                 |
| **Supported Audio Formats** | • MP3 (MPEG 1/2 Layer 3)  <br>• WMA (Windows Media Audio 9/10)  <br>• AAC/M4A (MPEG 2/4)  <br>• FLAC |
| **Extensions**              | `.mp3`, `.wma`, `.m4a`, `.m4b`, `.aac`, `.flac`                                                      |
| **Quality Limits**          | Max **320 kbit/s**, **48 kHz** sampling frequency                                                    |
| **File Limit**              | Max **1,000 files** per medium                                                                       |

## 3. Important Tips & Notes

- **MP3 Compression:** Audi recommends a bit rate of at least **160 kbit/s**.

- **Variable Bit Rate (VBR):** The remaining play time display may differ for VBR files.

- **WMA Voice:** Windows Media Audio 9 *Voice* format is **not** supported.

- **Text Display:** Special characters (e.g., in ID3 tags) may not display correctly depending on the system language.

- **MTP Players:** Some functions (rating tracks, video playback) are not supported. Battery must be above 5% for playback.

## 4. Troubleshooting Guide

| **Problem**                                     | **Solution/Explanation**                                                                   |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Mobile device not supported (AMI/Bluetooth)** | Check manual or `www.audiusa.com/bluetooth` for supported devices.                         |
| **Volume too high/low (AMI/AUX)**               | Adjust mobile device volume to approx. **70%** of max output.                              |
| **Mobile device not recognized**                | Ensure battery is sufficient (mobile devices may not playback if battery < 5%).            |
| **Malfunctions during playback (iPod/iPhone)**  | If Bluetooth audio is on, switch it off. Reset Media settings to factory default.          |
| **Changed content not displayed**               | Reset, or before disconnecting/connecting, mute the device or switch audio sources.        |
| **Static on AUX connection**                    | Mute or switch to a different audio source before connecting/disconnecting the cable.      |
| **Audio interference (Bluetooth/Wi-Fi)**        | Only use one interface at a time. Close third-party music apps; use the integrated player. |
| **Jukebox tracks grayed out**                   | When importing playlists, the actual files must also be imported.                          |
| **Jukebox imported tracks missing**             | Files may not be supported. Only copy supported files.                                     |
| **Online media connection failed**              | Ensure "MMI connection" switch is ON in the myAudi app.                                    |
| **Wi-Fi hotspot disconnects**                   | Turn off network optimization functions on the Wi-Fi device.                               |
| **AMI playback not possible**                   | Ensure USB mode **MTP** is selected on the mobile device.                                  |
