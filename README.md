
# 🎧 ComfyUI YTDL Nodes

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-green?logo=youtube)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-critical?logo=ffmpeg)
![ComfyUI](https://img.shields.io/badge/ComfyUI-compatible-orange)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Custom [ComfyUI](https://github.com/comfyanonymous/ComfyUI) nodes for downloading, converting, and previewing audio/video from YouTube and other supported sites using **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**.  
Easily fetch high-quality media, auto-convert to your preferred formats, and preview files directly inside ComfyUI.

<img width="1583" height="971" alt="image_2025-08-25_18-43-06" src="https://github.com/user-attachments/assets/d3f5c34b-c4f0-49ae-8805-37e8730954d4" />


---

## 📝 Updates

### Version 1.0.6 - Latest Release
🎉 **Major Update:** This version introduces the new **YTDLPreview** node with enhanced media preview capabilities and significantly improved functionality.

#### **🎬 New Main Preview Node:**
- **YTDLPreview Node** – New unified preview node that handles both audio and video files
- **Replaces Audio-Only Preview** – YTDL Preview becomes the primary preview node (YTDLPreviewAudio is now legacy)
- **Smart Media Detection** – Automatically detects whether files are audio or video and displays appropriate metadata
- **Streamlined Outputs** – Clean AUDIO output + current_file_path STRING for connecting to other nodes
- **Visual File Navigation** – Easy browsing between multiple downloaded files with clear media type indicators

#### **🍪 Enhanced Cookie & Authentication System:**
- **Comprehensive Cookie Guide** – Complete setup instructions for all major browsers in README
- **Chromium Browser Support** – Detailed steps for Chrome, Edge, Brave cookie extraction using browser extensions
- **Firefox Auto-Extraction** – Seamless automatic cookie extraction for Firefox users
- **1080p+ Video Access** – Proper cookie setup enables high-quality video downloads (720p, 1080p, 4K)
- **Quality Restriction Warnings** – Clear explanation of YouTube's 480p limit for non-authenticated users

#### **⏂ Advanced Time Cropping & Quality Control:**
- **Fully Functional Time Cropping** – Extract specific video/audio segments with native yt-dlp integration
- **Precise Format Control** – Choose exact video format + resolution combinations (720p + mp4, 1080p + webm)
- **Enhanced Progress Tracking** – Real-time download progress with detailed console output
- **Better Error Handling** – Improved retry mechanisms and format fallback systems
- **FFmpeg Integration** – Seamless audio/video processing with proper parameter handling

#### **🔧 User Experience Improvements:**
- **Fixed Index Switching** – file_index parameter now properly triggers node re-execution when changed
- **Simplified Node Outputs** – Removed confusing video COMBO output (current_file_path STRING is sufficient)
- **Enhanced Input Validation** – Better time format support with colon separators (0:30 format)
- **Comprehensive Documentation** – All parameters, cookie setup, and troubleshooting moved to README
- **Legacy Node Deprecation** – Clear guidance to migrate from YTDLPreviewAudio to YTDLPreview

#### **🔄 Compatibility:**
- **Backward Compatible** – All existing workflows continue to work
- **Legacy Support** – Original YTDLPreviewAudio marked as legacy but fully functional
- **Stability Fixes** – Resolved ComfyUI crashes and integration issues

---

## ✨ Features

- 📥 **Download Media** – Supports **YouTube** and 1,000+ other platforms via [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- 🎵 **Audio Conversion** – Convert audio to `mp3`, `wav`, `flac`, `m4a`, or `ogg`.
- 🎬 **Enhanced Video Quality Selection** – Choose specific video formats (mp4, webm, mkv) with resolution control (720p, 1080p, etc.).
- ✂️ **Time Cropping** – Crop videos/audio to specific time ranges with FFmpeg integration.
- 📂 **Custom Output Paths** – Choose your own storage folder within ComfyUI.
- 🍪 **Cookie & Browser Support** – Use stored browser cookies to bypass restrictions.
- 📑 **Playlist Support** – Optionally download entire playlists or just individual videos.
- 🚀 **Optimized Download Speeds** – Auto-handles retries, anti-bot headers, and connection stability.
- 🔊 **Built-in Audio Preview** – Listen to downloaded audio directly within ComfyUI.
- 🛠️ **Automatic Dependency Management** – Validates dependencies on first run.

---

## 📦 Installation

### 1. Clone the repository
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Saganaki22/ComfyUI-ytdl_nodes.git
```

### 2. Dependencies
The nodes will **auto-validate requirements** on the first launch, but you can also manually install them:
```bash
pip install -r requirements.txt
```

---

## 📌 Requirements

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (latest)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/download.html) *(required for audio conversion and time cropping)*
- Python 3.9+ recommended

### Additional Requirements for YTDLPreview Node:
- `torch` + `torchaudio` *(usually included with ComfyUI)*
- `opencv-python` *(for video thumbnail extraction)*
- `Pillow` *(for image processing fallbacks)*

### Manual FFmpeg Installation

- **Windows:**  
  ```bash
  winget install ffmpeg
  ```
- **MacOS:**  
  ```bash
  brew install ffmpeg
  ```
- **Linux:**  
  ```bash
  sudo apt install ffmpeg
  ```

---

## 🛠️ Usage

Once installed, restart **ComfyUI**.  
You'll find the new nodes under **`audio/ytdl`** in the node search bar:

### Available Nodes

#### **1. YTDL Links Input**  
Input one or more video URLs (YouTube, SoundCloud, etc.).  
- Supports **multiple links** (one per line).
- Returns a list of valid URLs for downstream nodes.

#### **2. YTDL Downloader**
Download videos or extract audio with comprehensive options:
- Choose **audio-only** or full video with enhanced quality control.
- Pick output format (`mp3`, `wav`, etc.) and video formats (mp4, webm, mkv).
- **Time cropping** – Extract specific segments (e.g., 30s-2:30).
- Supports custom filenames and storage paths.
- Cookie + browser-based authentication supported.
- Playlist downloading enabled.
- **See detailed parameter guide below** for cookie setup and quality restrictions.

#### **3. YTDL Preview** ⭐ **NEW - Main Preview Node**
Enhanced preview node with streamlined outputs (replaces the old audio-only preview):
- **Audio + Media Support** – Preview both video and audio files with metadata display
- **Fixed Index Switching** – file_index properly triggers updates
- **Smart Detection** – Auto-detects media type and provides appropriate preview data
- **Clean Outputs** – Returns AUDIO data and current_file_path STRING for connecting to other nodes
- **Enhanced UI** – Clear tooltips and improved format input indicators
- **Visual File List** – Navigate between files with media type indicators
- **Use this node instead of the legacy audio preview**

#### **4. YTDL Preview Audio** ⚠️ **LEGACY - Use YTDL Preview Instead**
Original audio-only preview node (kept for backward compatibility):
- ⚠️ **DEPRECATED** – Use the new **YTDL Preview** node instead for better functionality
- Built-in audio player display.
- Shows file name, size, duration, channels, and format.
- Supports navigating between multiple downloaded files.
- **Will be removed in future versions**

---

## 📋 **YTDL Downloader - Complete Parameter Guide**

### **Core Settings**
- **`links`**: Connect from YTDL Links Input node
- **`output_folder`**: Where files are saved (relative to ComfyUI root)
- **`media_type`**: Choose "audio_only" or "video" downloads
- **`quality`**: Resolution/bitrate (higher = better quality, larger files)

### **Format Settings** 
- **`audio_format`**: Output format for audio-only downloads (mp3, wav, m4a, flac, ogg)
- **`video_format`**: Output format for video downloads (mp4, webm, mkv, best)

### **Time Cropping** ⏂
- **`enable_time_crop`**: Extract only part of the video/audio
- **`crop_start`**: Start time (e.g., "0:30" or "30")
- **`crop_end`**: End time (e.g., "5:00" or "300")
- Requires FFmpeg to be installed

### **Cookie Authentication** 🍪
- **`use_cookies`**: Enable for higher quality downloads (RECOMMENDED)
- **`browser_for_cookies`**: Choose your browser for cookie extraction
- **`cookie_file`**: Path to custom cookies.txt file

### **Advanced Options**
- **`download_playlist`**: Download entire playlist vs single video
- **`continue_on_error`**: Keep going if some videos fail
- **`custom_filename`**: Template for output filenames

---

## 🚨 **IMPORTANT NOTES**

### **YouTube Quality Restrictions**
> ⚠️ **YouTube limits video quality to 480p or lower for non-authenticated requests**
> 
> For **720p, 1080p, or higher quality**, you MUST use cookies!

### **Cookie Setup for Chromium Browsers** (Chrome, Edge, Brave)
> 🍪 **Chromium-based browsers require manual cookie export to download 1080p+ videos**
> 
> **Step-by-Step Instructions:**
> 1. **Install Cookie Extractor Extension**
>    - Install "[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)" extension
>    - Or search "cookies.txt" in your browser's extension store
>   
>      <img width="539" height="153" alt="image" src="https://github.com/user-attachments/assets/4ce7ce66-2e30-4313-96a8-51070e97b75b" />

> 
> 2. **Login to YouTube**
>    - Open YouTube in the same browser where you installed the extension
>    - **Log in to your YouTube account** (this is crucial for quality access)
> 
> 3. **Extract Cookies**
>    - Click the cookie extension icon while on YouTube
>    - Click "Export" or "Download cookies.txt"
>    - Save the `cookies.txt` file to a location you can remember
>   
>      <img width="492" height="216" alt="image_2025-08-25_18-55-37" src="https://github.com/user-attachments/assets/d1a68f38-384e-4950-beb0-fcee31dd177c" />

> 
> 4. **Configure YTDL Downloader Node**
>    - In ComfyUI, open the YTDL Downloader node
>    - Set `cookie_file` field to the full path of your exported `cookies.txt` file
>    - Example: `C:\Users\YourName\Downloads\cookies.txt`
>    - Set `browser_for_cookies` to "none" when using custom cookie file
>
>      <img width="575" height="46" alt="image_2025-08-25_18-55-00" src="https://github.com/user-attachments/assets/3c4e05e6-f8c6-4b7a-a468-f275f0f53993" />

> 
> 5. **Enjoy High Quality Downloads**
>    - You can now download videos up to **1080p, 1440p, and 4K quality**
>    - Without cookies, YouTube limits downloads to 480p maximum

### **Network Requirements**
> 🌐 **Disable VPN for best results**
> 
> VPNs can cause download failures or quality restrictions

### **Firefox Users**
> 🦊 **Firefox cookie extraction works automatically**
> 
> Set `browser_for_cookies = "firefox"` and `use_cookies = True`

---

## 💡 **Tips for Best Results**

1. **Always enable cookies** for quality downloads
2. **Use Firefox** if possible (better cookie support)  
3. **Disable VPN** during downloads
4. **Install FFmpeg** for time cropping features
5. **Choose appropriate quality** based on your needs

---

## 🛡️ Troubleshooting YouTube Errors

If you experience issues when downloading from **YouTube**:

### **1. Do NOT use a VPN**  
YouTube aggressively blocks suspicious traffic. Disable any VPNs before retrying.

### **2. Log in to YouTube in same your browser**  
Some restricted videos require authentication. Sign in to YouTube using the same browser you'll use for cookie extraction.

### **3. Use Browser Cookie Extraction (Firefox Recommended)**  
In the **YTDL Downloader** node, set **`browser_for_cookies`** → **`firefox`** *(recommended)*.  
- Firefox stores cookies in a readable format for yt-dlp.
- Chrome uses a secure database, which may fail to extract cookies.

### **4. Provide a Custom Cookie File**  
If browser extraction fails for chromium / Chrome, you can manually export cookies:
- Use a browser extension like [Get cookies.txt](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc).
- Paste the path to your `cookies.txt` file into the **`cookie_file`** input field in the YTDL Downloader node.

Even if you don't set up cookies, the downloader includes **graceful fallbacks**.

---

## 🔄 Graceful Fallbacks

The nodes have several built-in fail-safes to ensure downloads and previews succeed whenever possible:

| **Feature** | **Primary Method** | **Fallback(s)** |
|------------|---------------------|-----------------|
| **Authentication** | Browser cookie extraction | Custom cookie file → No cookies with retries |
| **Anti-bot Protection** | Normal yt-dlp request | Adds extra headers, retries, and randomized delays |
| **Playlist Handling** | Full playlist download | Falls back to first video if playlist mode is disabled |
| **File Detection** | Uses expected filename | Scans output folder & picks latest downloaded file |
| **Audio Conversion** | `torchaudio` loads audio | Falls back to `ffmpeg` to convert to `.wav` automatically |

These mechanisms ensure your downloads keep working even if YouTube changes its API or blocks certain requests.

---

## 📂 Folder Structure

```
ComfyUI-ytdl_nodes/
├── __init__.py
├── ytdl_nodes.py
├── requirements.txt
├── workflows
│   ├── YTDL_Audio.json
│   ├── YTDL_Video.json
└── README.md
```

---

## 🙌 Acknowledgments

This project uses:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** – for downloading and extracting media.
- **[ffmpeg](https://ffmpeg.org/)** – for audio/video conversion.
- **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** – for node-based AI workflows.

---

## 📝 License

This project is released under the **MIT License**.  
Feel free to use, modify, and distribute.

---

## 💡 Tips

- If yt-dlp fails to bypass restrictions, try **browser cookie extraction** (recommended).
- Always prefer **Firefox** for better compatibility.
- If dependency validation fails, manually run:
  ```bash
  pip install yt-dlp ffmpeg-python
  ```

---

### 🚀 Ready to use in ComfyUI!

With these nodes, you can seamlessly integrate **media downloading and audio previewing** into your ComfyUI pipelines.
