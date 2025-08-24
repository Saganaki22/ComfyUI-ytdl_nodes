# 🎧 ComfyUI YTDL Nodes

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-green?logo=youtube)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-critical?logo=ffmpeg)
![ComfyUI](https://img.shields.io/badge/ComfyUI-compatible-orange)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Custom [ComfyUI](https://github.com/comfyanonymous/ComfyUI) nodes for downloading, converting, and previewing audio/video from YouTube and other supported sites using **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**.  
Easily fetch high-quality media, auto-convert to your preferred formats, and preview files directly inside ComfyUI.

<img width="1876" height="588" alt="image" src="https://github.com/user-attachments/assets/6eb4aa9f-e67e-4afb-b5e2-c692faaa6f19" />


---

## ✨ Features

- 📥 **Download Media** – Supports **YouTube** and 1,000+ other platforms via [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- 🎵 **Audio Conversion** – Convert audio to `mp3`, `wav`, `flac`, `m4a`, or `ogg`.
- 📂 **Custom Output Paths** – Choose your own storage folder within ComfyUI.
- 🍪 **Cookie & Browser Support** – Use stored browser cookies to bypass restrictions.
- 📑 **Playlist Support** – Optionally download entire playlists or just individual videos.
- 🚀 **Optimized Download Speeds** – Auto-handles retries, anti-bot headers, and connection stability.
- 🔊 **Built-in Audio Preview** – Listen to downloaded audio directly within ComfyUI.
- 🛠️ **Automatic Dependency Management** – Installs dependencies on first run.

---

## 📦 Installation

### 1. Clone the repository
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Saganaki22/ComfyUI-ytdl_nodes.git
```

### 2. Install dependencies
The nodes will **auto-install requirements** on the first launch, but you can also manually install them:
```bash
pip install -r requirements.txt
```

---

## 📌 Requirements

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (latest)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://ffmpeg.org/download.html) *(required for audio conversion)*
- Python 3.9+ recommended

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
Download videos or extract audio:
- Choose **audio-only** or full video.
- Pick output format (`mp3`, `wav`, etc.`).
- Supports custom filenames and storage paths.
- Cookie + browser-based authentication supported.
- Playlist downloading enabled.

#### **3. YTDL Preview Audio**  
Preview downloaded audio directly in ComfyUI:
- Built-in audio player display.
- Shows file name, size, duration, channels, and format.
- Supports navigating between multiple downloaded files.

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
│   ├── YTDL_Simple.json
│   ├── YTDL_Advanced.json
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
- If the auto-installer fails, manually run:
  ```bash
  pip install yt-dlp ffmpeg-python
  ```

---

### 🚀 Ready to use in ComfyUI!

With these nodes, you can seamlessly integrate **media downloading and audio previewing** into your ComfyUI pipelines.
