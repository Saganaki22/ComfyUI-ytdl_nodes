import os
import json
import subprocess
import sys
from typing import List, Tuple, Optional
import re
def ensure_yt_dlp():
    try:
        import yt_dlp
        return yt_dlp
    except ImportError:
        print("❌ yt-dlp not found! Please restart ComfyUI to auto-install dependencies.")
        raise ImportError("yt-dlp not available - restart ComfyUI to install requirements")
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
def install_ffmpeg_python():
    try:
        import ffmpeg
        return True
    except ImportError:
        try:
            print("📦 Ensuring ffmpeg-python availability...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ffmpeg-python", "--quiet"])
            print("✅ ffmpeg-python confirmed!")
            return True
        except Exception as e:
            print(f"⚠️ Could not install ffmpeg-python: {e}")
            return False
def parse_time_to_seconds(time_str: str) -> Optional[float]:
    
    if not time_str or time_str.strip() == "":
        return None
    time_str = time_str.strip()
    try:
        return float(time_str)
    except ValueError:
        pass
    time_parts = time_str.split(':')
    try:
        if len(time_parts) == 1:
            return float(time_parts[0])
        elif len(time_parts) == 2:
            return float(time_parts[0]) * 60 + float(time_parts[1])
        elif len(time_parts) == 3:
            return float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
        else:
            print(f"⚠️ Invalid time format: {time_str}")
            print(f"💡 Use formats like: 30 (seconds), 1:30 (MM:SS), or 1:30:45 (HH:MM:SS)")
            return None
    except ValueError:
        print(f"⚠️ Could not parse time: {time_str}")
        print(f"💡 Use formats like: 30 (seconds), 1:30 (MM:SS), or 1:30:45 (HH:MM:SS)")
        return None
class YTDLLinksInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "links": ("STRING", {
                    "multiline": True,
                    "default": "https://www.youtube.com/watch?v=example",
                    "placeholder": "Enter one or more links, each on a new line"
                }),
            }
        }
    RETURN_TYPES = ("YTDL_LINKS",)
    RETURN_NAMES = ("links",)
    FUNCTION = "process_links"
    CATEGORY = "audio/ytdl"
    def process_links(self, links: str):
        link_list = [link.strip() for link in links.split('\n') if link.strip()]
        valid_links = []
        for link in link_list:
            if link.startswith(('http://', 'https://', 'www.')):
                valid_links.append(link)
        return (valid_links,)
class YTDLDownloader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "links": ("YTDL_LINKS",),
                "output_folder": ("STRING", {
                    "default": "output/YTDL/",
                    "placeholder": "Will save to: ComfyUI/output/YTDL/"
                }),
                "media_type": (["audio_only", "video"], {"default": "audio_only"}),
                "audio_format": (["mp3", "wav", "m4a", "flac", "ogg"], {
                    "default": "mp3",
                    "tooltip": "🎵 AUDIO FORMAT - Only applies when media_type = 'audio_only'. Ignored for video downloads."
                }),
                "video_format": (["mp4", "webm", "mkv", "best"], {
                    "default": "mp4",
                    "tooltip": "🎬 VIDEO FORMAT - Only applies when media_type = 'video'. Ignored for audio-only downloads."
                }),
                "quality": (["best", "worst", "1080p", "720p", "480p", "360p", "320", "256", "192", "128"], {"default": "best"}),
                "enable_time_crop": ("BOOLEAN", {"default": False}),
                "crop_start": ("STRING", {
                    "default": "",
                    "placeholder": "Start time (0:30 or 30 seconds)"
                }),
                "crop_end": ("STRING", {
                    "default": "",
                    "placeholder": "End time (5:00 or 300 seconds)"
                }),
                "use_cookies": ("BOOLEAN", {"default": True}),
                "browser_for_cookies": (["chrome", "firefox", "edge", "safari", "brave", "none"], {"default": "firefox"}),
                "download_playlist": ("BOOLEAN", {"default": False}),
                "continue_on_error": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "custom_filename": ("STRING", {
                    "default": "%(title)s.%(ext)s",
                    "placeholder": "e.g., %(title)s.%(ext)s or %(uploader)s - %(title)s.%(ext)s"
                }),
                "cookie_file": ("STRING", {
                    "default": "",
                    "placeholder": "Path to cookies.txt file (optional)"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("downloaded_files", "download_info")
    FUNCTION = "download_media"
    CATEGORY = "audio/ytdl"
    OUTPUT_NODE = True
    def safe_extract_info(self, ydl, url, download=False, max_retries=3):
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt + 1}/{max_retries} for info extraction: {url}")
                return ydl.extract_info(url, download=download)
            except Exception as e:
                error_msg = str(e).lower()
                print(f"⚠️ Info extraction attempt {attempt + 1} failed for {url}: {str(e)}")
                retryable_errors = [
                    'timeout', 'connection', 'network', 'temporary',
                    'rate limit', 'too many requests', '429', '503', '502'
                ]
                is_retryable = any(err in error_msg for err in retryable_errors)
                if attempt < max_retries - 1 and is_retryable:
                    import time
                    wait_time = (attempt + 1) * 2
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    if not is_retryable:
                        print(f"❌ Non-retryable error, skipping retries: {str(e)}")
                    break
        return None
    def safe_download_single_video(self, ydl, video_info, progress_hook=None, max_retries=3):
        video_title = video_info.get('title', 'Unknown')
        video_url = video_info.get('webpage_url', video_info.get('url', 'Unknown'))
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"🔄 Download retry attempt {attempt + 1}/{max_retries} for: {video_title}")
                if progress_hook:
                    ydl.params['progress_hooks'] = [progress_hook]
                ydl.download([video_url])
                return True
            except Exception as e:
                error_msg = str(e).lower()
                print(f"⚠️ Download attempt {attempt + 1} failed for '{video_title}': {str(e)}")
                retryable_errors = [
                    'timeout', 'connection', 'network', 'temporary',
                    'rate limit', 'too many requests', '429', '503', '502',
                    'fragment', 'http error 5', 'server error'
                ]
                format_errors = [
                    'no video formats', 'format not available', 'requested format not available',
                    'no suitable format', 'format selection failed'
                ]
                is_retryable = any(err in error_msg for err in retryable_errors)
                is_format_error = any(err in error_msg for err in format_errors)
                if attempt < max_retries - 1:
                    if is_retryable:
                        import time
                        wait_time = (attempt + 1) * 3
                        print(f"⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    elif is_format_error and attempt == 0:
                        print("🔄 Format error detected, trying with fallback format options...")
                        original_format = ydl.params.get('format', 'best')
                        try:
                            ydl.params['format'] = 'best[ext=mp4]/best[ext=webm]/best'
                            ydl.download([video_url])
                            return True
                        except:
                            ydl.params['format'] = original_format
                        continue
                    else:
                        print(f"❌ Non-retryable error: {str(e)}")
                        break
                else:
                    print(f"❌ Max retries ({max_retries}) reached for: {video_title}")
                    break
        return False
    def download_media(self, links: List[str], output_folder: str, media_type: str,
                      audio_format: str, video_format: str, quality: str,
                      enable_time_crop: bool, crop_start: str, crop_end: str,
                      use_cookies: bool, browser_for_cookies: str,
                      download_playlist: bool, continue_on_error: bool,
                      custom_filename: str = "%(title)s.%(ext)s", cookie_file: str = ""):
        yt_dlp = ensure_yt_dlp()
        def update_progress(current_step, total_steps, status_message):
            if total_steps > 0:
                percent = (current_step / total_steps) * 100
                print(f"📊 [{percent:5.1f}%] {status_message}")
        def check_interrupted():
            
            try:
                import execution
                if hasattr(execution, 'ExecutionBlocker'):
                    pass
                return False
            except:
                return False
        total_links = len(links)
        total_steps = total_links * 3
        current_step = 0
        update_progress(current_step, total_steps, "Initializing YTDL downloader...")
        audio_only = media_type == "audio_only"
        need_ffmpeg = False
        if audio_only and audio_format != 'm4a':
            need_ffmpeg = True
        if enable_time_crop:
            need_ffmpeg = True
        ffmpeg_available = check_ffmpeg()
        if need_ffmpeg and not ffmpeg_available:
            print("=" * 60)
            print("⚠️ FFMPEG NOT FOUND!")
            if enable_time_crop:
                print("Time cropping requires ffmpeg for processing.")
            if audio_only and audio_format != 'm4a':
                print("Audio conversion requires ffmpeg.")
            print("Please install ffmpeg:")
            print("  Windows: winget install ffmpeg")
            print("  Mac:     brew install ffmpeg")
            print("  Linux:   sudo apt install ffmpeg")
            print("  Or download from: https://ffmpeg.org/download.html")
            print("=" * 60)
            if enable_time_crop:
                return ("", json.dumps({
                    "error": "Time cropping requires ffmpeg. Please install ffmpeg and try again.",
                    "downloads": []
                }))
        elif ffmpeg_available:
            install_ffmpeg_python()
        update_progress(current_step, total_steps, "Configuring download settings...")
        start_time = None
        end_time = None
        duration = None
        if enable_time_crop:
            start_time = parse_time_to_seconds(crop_start)
            end_time = parse_time_to_seconds(crop_end)
            if start_time is not None and end_time is not None:
                if end_time <= start_time:
                    print("⚠️ End time must be greater than start time. Ignoring time crop.")
                    enable_time_crop = False
                else:
                    duration = end_time - start_time
                    print(f"⏰ Time cropping enabled: {start_time}s to {end_time}s (duration: {duration}s)")
            elif start_time is not None and end_time is None:
                print(f"⏰ Time cropping enabled: from {start_time}s to end")
            elif start_time is None and end_time is not None:
                duration = end_time
                print(f"⏰ Time cropping enabled: first {end_time}s")
            else:
                print("⚠️ No valid crop times provided. Disabling time crop.")
                enable_time_crop = False
        if not output_folder or output_folder.strip() == "":
            output_folder = "output/YTDL/"
        output_folder = output_folder.rstrip('/\\')
        if not os.path.isabs(output_folder):
            comfyui_root = os.getcwd()
            abs_output_folder = os.path.join(comfyui_root, output_folder)
        else:
            abs_output_folder = output_folder
        os.makedirs(abs_output_folder, exist_ok=True)
        print(f"📁 Saving files to: {abs_output_folder}")
        if not custom_filename or custom_filename.strip() == "":
            custom_filename = "%(title)s.%(ext)s"
        if enable_time_crop:
            base_name = custom_filename.replace('.%(ext)s', '')
            crop_suffix = f"_crop_{start_time or 0}s"
            if end_time:
                crop_suffix += f"-{end_time}s"
            elif duration:
                crop_suffix += f"_{duration}s"
            custom_filename = f"{base_name}{crop_suffix}.%(ext)s"
        clean_filename = custom_filename.replace('/', '_').replace('\\', '_')
        full_output_template = os.path.join(abs_output_folder, clean_filename)
        downloaded_files = []
        download_info = []
        ydl_opts = {
            'outtmpl': full_output_template,
            'noplaylist': not download_playlist,
            'ignoreerrors': False,
            'no_warnings': False,
            'extract_flat': False,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 3,
            'file_access_retries': 3,
            'format_sort': ['hasaud', 'lang', 'quality', 'res', 'fps', 'hdr:12', 'codec:vp9.2', 'size', 'br', 'asr', 'proto'],
            'format_sort_force': False,
            'socket_timeout': 30,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'sleep_interval_requests': 0.5,
            'sleep_interval_subtitles': 1,
        }
        print("\n📋 DOWNLOAD CONFIGURATION")
        print("=" * 50)
        print(f"🎯 Media Type: {media_type}")
        if audio_only:
            print(f"🎵 Audio Format: {audio_format}")
        else:
            print(f"🎦 Video Format: {video_format}")
        print(f"📊 Quality: {quality}")
        if enable_time_crop:
            print(f"✂️ Time Crop: ENABLED")
            if start_time is not None:
                print(f"   ⏰ Start: {start_time}s")
            if end_time is not None:
                print(f"   ⏰ End: {end_time}s")
            if duration is not None:
                print(f"   ⏱️ Duration: {duration}s")
        else:
            print(f"✂️ Time Crop: DISABLED")
        if download_playlist:
            print("📋 Playlist mode: ENABLED - Will download available videos from playlists")
        else:
            print("📋 Playlist mode: DISABLED - Will download only single videos from playlist URLs")
        if continue_on_error:
            print("🛡️ Error handling: CONTINUE - Will skip unavailable videos and continue")
        else:
            print("🛡️ Error handling: STOP - Will stop on first error")
        print("=" * 50)
        if use_cookies:
            if cookie_file and os.path.exists(cookie_file):
                ydl_opts['cookiefile'] = cookie_file
                print(f"Using custom cookie file: {cookie_file}")
            elif browser_for_cookies != "none":
                try:
                    ydl_opts['cookiesfrombrowser'] = (browser_for_cookies,)
                    print(f"Attempting to extract cookies from {browser_for_cookies}")
                    test_ydl = yt_dlp.YoutubeDL({'quiet': True, 'cookiesfrombrowser': (browser_for_cookies,)})
                    try:
                        test_ydl.cookiejar
                        print("✅ Cookie extraction successful")
                    except Exception as cookie_error:
                        print(f"⚠️ Cookie extraction failed: {str(cookie_error)}")
                        print("💡 Trying without cookies...")
                        if 'cookiesfrombrowser' in ydl_opts:
                            del ydl_opts['cookiesfrombrowser']
                        ydl_opts.update({
                            'extractor_retries': 3,
                            'fragment_retries': 3,
                            'sleep_interval': 1,
                            'max_sleep_interval': 5,
                        })
                except Exception as e:
                    print(f"Cookie setup failed: {e}")
        ydl_opts.update({
            'sleep_interval_requests': 1,
            'sleep_interval_subtitles': 1,
            'extractor_retries': 3,
            'fragment_retries': 3,
        })
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        postprocessors = []
        if audio_only:
            if quality == "best":
                ydl_opts['format'] = (
                    'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio[ext=webm]/'
                    'bestaudio/best[height<=720]/best'
                )
            elif quality == "worst":
                ydl_opts['format'] = (
                    'worstaudio[ext=m4a]/worstaudio[ext=mp3]/worstaudio[ext=webm]/'
                    'worstaudio/worst'
                )
            elif quality.isdigit():
                ydl_opts['format'] = (
                    f'bestaudio[abr<={quality}][ext=m4a]/bestaudio[abr<={quality}][ext=mp3]/'
                    f'bestaudio[abr<={quality}]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/'
                    f'bestaudio/best[height<=720]/best'
                )
            else:
                ydl_opts['format'] = (
                    f'bestaudio[abr<={quality}][ext=m4a]/bestaudio[abr<={quality}][ext=mp3]/'
                    f'bestaudio[abr<={quality}]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/'
                    f'bestaudio/best[height<=720]/best'
                )
            if ffmpeg_available:
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': quality if quality.isdigit() else None,
                })
        else:
            if quality == "best":
                if video_format == "best":
                    ydl_opts['format'] = 'best[height>=1080]/best[height>=720]/best'
                else:
                    ydl_opts['format'] = (
                        f'best[height>=1080][ext={video_format}]/'
                        f'best[height>=720][ext={video_format}]/'
                        f'best[height>=1080][ext=mp4]/'
                        f'best[height>=720][ext=mp4]/'
                        f'best[ext={video_format}]/best[ext=mp4]/best'
                    )
            elif quality == "worst":
                ydl_opts['format'] = f'worst[ext={video_format}]/worst[ext=mp4]/worst'
            elif quality.endswith('p'):
                height = quality[:-1]
                if video_format == "best":
                    ydl_opts['format'] = (
                        f'best[height>={height}]/'
                        f'best[height={height}]/'
                        f'best[height<={height}]/'
                        f'best[height>=720]/best'
                    )
                else:
                    ydl_opts['format'] = (
                        f'best[height>={height}][ext={video_format}]/'
                        f'best[height={height}][ext={video_format}]/'
                        f'best[height<={height}][ext={video_format}]/'
                        f'best[height>={height}][ext=mp4]/'
                        f'best[height>=720][ext=mp4]/'
                        f'best[ext={video_format}]/best'
                    )
            else:
                if video_format == "best":
                    ydl_opts['format'] = 'best[height>=1080]/best[height>=720]/best'
                else:
                    ydl_opts['format'] = (
                        f'best[height>=1080][ext={video_format}]/'
                        f'best[height>=720][ext={video_format}]/'
                        f'best[height>=1080][ext=mp4]/'
                        f'best[height>=720][ext=mp4]/'
                        f'best[ext={video_format}]/best[ext=mp4]/best'
                    )
        if enable_time_crop:
            external_downloader_args = []
            if start_time is not None:
                external_downloader_args.extend(['-ss', str(start_time)])
            if duration is not None:
                external_downloader_args.extend(['-t', str(duration)])
            elif end_time is not None and start_time is not None:
                external_downloader_args.extend(['-t', str(end_time - start_time)])
            if external_downloader_args:
                ydl_opts['external_downloader_args'] = {
                    'ffmpeg': external_downloader_args
                }
                ydl_opts['external_downloader'] = 'ffmpeg'
                print(f"✂️ Time cropping configured: {' '.join(external_downloader_args)}")
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors
        
        print(f"🎯 Selected format string: {ydl_opts.get('format', 'best')}")
        if not use_cookies:
            print("⚠️ WARNING: No cookies enabled - YouTube may limit quality to 720p or lower")
            print("💡 TIP: Enable cookies (firefox recommended) for access to 1080p+ formats")
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d or 'total_bytes_estimate' in d:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        speed = d.get('speed', 0)
                        speed_str = f"{speed/1024/1024:.1f}MB/s" if speed else "Unknown"
                        filename = d.get('filename', 'Unknown')
                        basename = os.path.basename(filename) if filename else 'Unknown'
                        base_step = (link_idx * 3) + 1
                        detailed_progress = base_step + (percent / 100.0)
                        update_progress(int(detailed_progress), total_steps, f"Downloading {basename[:30]} - {percent:.1f}% ({speed_str})")
                        bar_length = 40
                        filled_length = int(bar_length * percent / 100)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        print(f"\r⬇️ [{bar}] {percent:5.1f}% | {speed_str} | {basename[:30]}", end='', flush=True)
            elif d['status'] == 'finished':
                filename = d.get('filename', 'Unknown')
                basename = os.path.basename(filename) if filename else 'Unknown'
                print(f"\n✅ Download completed: {basename}")
                update_progress((link_idx * 3) + 2, total_steps, f"Download completed: {basename}")
            elif d['status'] == 'processing':
                filename = d.get('filename', 'Unknown')
                basename = os.path.basename(filename) if filename else 'Unknown'
                print(f"\r⚙️ Processing: {basename[:40]}", end='', flush=True)
                update_progress((link_idx * 3) + 2, total_steps, f"Processing: {basename}")
            elif d['status'] == 'error':
                filename = d.get('filename', 'Unknown')
                basename = os.path.basename(filename) if filename else 'Unknown'
                print(f"\n❌ Download error: {basename}")
                update_progress((link_idx * 3) + 2, total_steps, f"Error downloading: {basename}")
        total_links = len(links)
        total_attempted = 0
        total_successful = 0
        total_failed = 0
        for link_idx, link in enumerate(links):
            if check_interrupted():
                print("\n🛑 Download cancelled by user")
                break
            current_step = link_idx * 3
            update_progress(current_step, total_steps, f"Extracting info for link {link_idx + 1}/{total_links}")
            print(f"\n{'='*60}")
            print(f"🔗 Processing link {link_idx + 1}/{total_links}")
            print(f"🌐 URL: {link}")
            print(f"{'='*60}")
            try:
                with yt_dlp.YoutubeDL({'quiet': True, **{k: v for k, v in ydl_opts.items() if k not in ['progress_hooks']}}) as info_ydl:
                    info = self.safe_extract_info(info_ydl, link, download=False)
                if not info:
                    print(f"❌ Could not extract information for {link}")
                    download_info.append({
                        'url': link,
                        'error': 'Failed to extract video information',
                        'status': 'failed'
                    })
                    total_failed += 1
                    continue
                if 'entries' in info:
                    entries = []
                    unavailable_count = 0
                    original_entries = list(info['entries']) if info['entries'] else []
                    for i, entry in enumerate(original_entries):
                        if entry is None:
                            print(f"⚠️ Skipping unavailable video #{i+1} in playlist")
                            unavailable_count += 1
                            continue
                        if entry and 'url' in entry:
                            try:
                                with yt_dlp.YoutubeDL({'quiet': True}) as entry_ydl:
                                    detailed_entry = entry_ydl.extract_info(entry['url'], download=False)
                                    if detailed_entry:
                                        entries.append(detailed_entry)
                                    else:
                                        print(f"⚠️ Could not get detailed info for video #{i+1}: {entry.get('title', 'Unknown')}")
                                        unavailable_count += 1
                            except Exception as e:
                                print(f"⚠️ Video #{i+1} unavailable: {entry.get('title', 'Unknown')} - {str(e)}")
                                unavailable_count += 1
                        else:
                            entries.append(entry)
                    total_videos = len(entries)
                    original_count = len(original_entries)
                    if download_playlist:
                        print(f"📋 Found playlist with {original_count} videos ({total_videos} available)")
                        if unavailable_count > 0:
                            print(f"⚠️ {unavailable_count} videos are unavailable and will be skipped")
                    else:
                        print(f"📋 Found playlist with {original_count} videos (downloading only first available)")
                        entries = entries[:1] if entries else []
                        total_videos = len(entries)
                else:
                    entries = [info]
                    total_videos = 1
                    print("🎵 Single video detected")
                if not entries:
                    print("❌ No available videos to download")
                    download_info.append({
                        'url': link,
                        'error': 'No available videos found',
                        'status': 'failed'
                    })
                    total_failed += 1
                    continue
                print(f"\n🚀 Starting download of {total_videos} available video(s)...")
                current_step = link_idx * 3 + 1
                update_progress(current_step, total_steps, f"Downloading from link {link_idx + 1}/{total_links}")
                with yt_dlp.YoutubeDL(ydl_opts) as download_ydl:
                    for video_idx, entry in enumerate(entries):
                        if entry is None:
                            continue
                        total_attempted += 1
                        video_title = entry.get('title', 'Unknown')
                        video_url = entry.get('webpage_url', entry.get('url', 'Unknown'))
                        try:
                            if total_videos > 1:
                                print(f"\n🎹 Video {video_idx + 1}/{total_videos}: {video_title}")
                            if enable_time_crop:
                                video_duration = entry.get('duration', 0)
                                if video_duration and end_time and end_time > video_duration:
                                    print(f"⚠️ End time ({end_time}s) is longer than video duration ({video_duration}s)")
                                    print(f"   Adjusting end time to video duration")
                            success = self.safe_download_single_video(download_ydl, entry, progress_hook, max_retries=3)
                            if success:
                                current_step = link_idx * 3 + 2
                                update_progress(current_step, total_steps, f"Processing downloaded file from link {link_idx + 1}/{total_links}")
                                expected_filename = download_ydl.prepare_filename(entry)
                                if enable_time_crop or (audio_only and audio_format != 'm4a'):
                                    base_name = os.path.splitext(expected_filename)[0]
                                    if audio_only:
                                        expected_filename = f"{base_name}.{audio_format}"
                                    else:
                                        expected_filename = f"{base_name}.{video_format}"
                                actual_file = None
                                if os.path.exists(expected_filename):
                                    actual_file = expected_filename
                                else:
                                    import glob
                                    base_pattern = os.path.splitext(expected_filename)[0]
                                    if audio_only:
                                        possible_extensions = [f'.{audio_format}', '.mp3', '.m4a', '.wav', '.flac', '.ogg']
                                    else:
                                        possible_extensions = [f'.{video_format}', '.mp4', '.webm', '.mkv']
                                    for ext in possible_extensions:
                                        pattern = f"{base_pattern}*{ext}"
                                        matches = glob.glob(pattern)
                                        if matches:
                                            actual_file = matches[0]
                                            break
                                    if not actual_file:
                                        potential_files = []
                                        for file in os.listdir(abs_output_folder):
                                            file_path = os.path.join(abs_output_folder, file)
                                            if os.path.isfile(file_path):
                                                extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.mkv', '.webm']
                                                if any(ext in file.lower() for ext in extensions):
                                                    potential_files.append(file_path)
                                        if potential_files:
                                            actual_file = max(potential_files, key=os.path.getmtime)
                                if actual_file and os.path.exists(actual_file):
                                    downloaded_files.append(actual_file)
                                    file_info = {
                                        'url': video_url,
                                        'title': video_title,
                                        'duration': entry.get('duration', 0),
                                        'file_path': actual_file,
                                        'file_size': os.path.getsize(actual_file),
                                        'playlist_index': video_idx + 1 if total_videos > 1 else None,
                                        'status': 'success'
                                    }
                                    if enable_time_crop:
                                        file_info.update({
                                            'cropped': True,
                                            'crop_start': start_time,
                                            'crop_end': end_time,
                                            'crop_duration': duration
                                        })
                                    download_info.append(file_info)
                                    print(f"💾 Saved: {os.path.basename(actual_file)}")
                                    total_successful += 1
                                else:
                                    print(f"⚠️ Downloaded file not found for: {video_title}")
                                    download_info.append({
                                        'url': video_url,
                                        'title': video_title,
                                        'error': 'Downloaded file not found',
                                        'playlist_index': video_idx + 1 if total_videos > 1 else None,
                                        'status': 'failed'
                                    })
                                    total_failed += 1
                            else:
                                download_info.append({
                                    'url': video_url,
                                    'title': video_title,
                                    'error': 'Download failed',
                                    'playlist_index': video_idx + 1 if total_videos > 1 else None,
                                    'status': 'failed'
                                })
                                total_failed += 1
                                if not continue_on_error:
                                    print("🛑 Stopping due to error (continue_on_error is disabled)")
                                    break
                        except Exception as video_error:
                            error_msg = f"Error downloading video: {str(video_error)}"
                            print(f"\n❌ {error_msg}")
                            download_info.append({
                                'url': video_url,
                                'title': video_title,
                                'error': error_msg,
                                'playlist_index': video_idx + 1 if total_videos > 1 else None,
                                'status': 'failed'
                            })
                            total_failed += 1
                            if not continue_on_error:
                                print("🛑 Stopping due to error (continue_on_error is disabled)")
                                break
                        if video_idx < total_videos - 1:
                            import time
                            time.sleep(1)
            except Exception as link_error:
                error_msg = f"Error processing {link}: {str(link_error)}"
                print(f"\n❌ {error_msg}")
                download_info.append({
                    'url': link,
                    'error': error_msg,
                    'status': 'failed'
                })
                total_failed += 1
                if not continue_on_error:
                    print("🛑 Stopping due to error (continue_on_error is disabled)")
                    break
        print(f"\n{'='*60}")
        print(f"🎉 DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Total videos attempted: {total_attempted}")
        print(f"✅ Successfully downloaded: {total_successful}")
        print(f"❌ Failed downloads: {total_failed}")
        print(f"📁 Files saved to: {abs_output_folder}")
        if total_successful > 0:
            print(f"🎵 {total_successful} files are ready for use!")
        if enable_time_crop and total_successful > 0:
            print(f"✂️ Time cropping applied to {total_successful} files")
        if total_failed > 0:
            print(f"⚠️ {total_failed} downloads failed (see details above)")
        print(f"{'='*60}")
        update_progress(total_steps, total_steps, f"Completed! Downloaded {total_successful}/{total_attempted} files")
        files_output = '\n'.join(downloaded_files) if downloaded_files else ""
        summary = {
            'summary': {
                'total_attempted': total_attempted,
                'successful': total_successful,
                'failed': total_failed,
                'success_rate': round((total_successful / total_attempted * 100) if total_attempted > 0 else 0, 1),
                'time_cropping_enabled': enable_time_crop,
                'media_type': media_type,
                'format': audio_format if audio_only else video_format
            },
            'downloads': download_info
        }
        info_output = json.dumps(summary, indent=2)
        return (files_output, info_output)
class YTDLPreviewAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "downloaded_files": ("STRING",),
                "file_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "display": "number"
                }),
            }
        }
    RETURN_TYPES = ("AUDIO", "STRING", "STRING", "INT")
    RETURN_NAMES = ("audio_file", "current_file_path", "file_info_json", "total_files_count")
    FUNCTION = "prepare_audio_preview"
    CATEGORY = "audio/ytdl"
    OUTPUT_NODE = True
    def prepare_audio_preview(self, downloaded_files: str, file_index: int = 0):
        import json
        if not downloaded_files or downloaded_files.strip() == "":
            print("⚠️ No downloaded files available")
            empty_info = {"error": "No files available", "total_files": 0}
            return (None, "", json.dumps(empty_info), 0)
        file_paths = [path.strip() for path in downloaded_files.split('\n') if path.strip()]
        if not file_paths:
            print("⚠️ No valid file paths found")
            empty_info = {"error": "No valid file paths", "total_files": 0}
            return (None, "", json.dumps(empty_info), 0)
        if file_index >= len(file_paths):
            file_index = 0
        current_file = file_paths[file_index]
        if not os.path.exists(current_file):
            error_info = {"error": f"File not found: {current_file}", "total_files": len(file_paths)}
            print(f"❌ File not found: {current_file}")
            return (None, "", json.dumps(error_info), len(file_paths))
        try:
            import torch
            import torchaudio
            waveform, sample_rate = torchaudio.load(current_file)
            audio_data = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
        except Exception as e:
            print(f"❌ Could not load audio file: {e}")
            try:
                import tempfile
                temp_wav = tempfile.mktemp(suffix='.wav')
                subprocess.run([
                    'ffmpeg', '-i', current_file, '-ar', '44100', '-ac', '2',
                    '-y', temp_wav
                ], capture_output=True, check=True)
                waveform, sample_rate = torchaudio.load(temp_wav)
                audio_data = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
                os.unlink(temp_wav)
                print("✅ Audio converted successfully with ffmpeg")
            except Exception as e2:
                print(f"❌ Audio conversion also failed: {e2}")
                error_info = {"error": f"Could not load audio: {str(e)}", "total_files": len(file_paths)}
                return (None, "", json.dumps(error_info), len(file_paths))
        file_size = os.path.getsize(current_file)
        file_name = os.path.basename(current_file)
        try:
            duration = float(waveform.shape[-1]) / sample_rate
        except:
            duration = 0
        file_info = {
            "name": file_name,
            "path": current_file,
            "size_mb": round(file_size / (1024*1024), 2),
            "duration_seconds": round(duration, 2),
            "sample_rate": sample_rate,
            "channels": waveform.shape[0],
            "current_index": file_index,
            "total_files": len(file_paths),
            "all_files": [os.path.basename(f) for f in file_paths]
        }
        self.create_audio_player_display(current_file, file_info)
        return (audio_data, current_file, json.dumps(file_info, indent=2), len(file_paths))
    def create_audio_player_display(self, current_file: str, file_info: dict):
        print("=" * 60)
        print(f"🎵 YTDL AUDIO PLAYER")
        print("=" * 60)
        print(f"📁 File: {file_info['name']}")
        print(f"📊 Size: {file_info['size_mb']} MB")
        print(f"⏱️ Duration: {file_info['duration_seconds']} seconds")
        print(f"📋 Index: {file_info['current_index'] + 1}/{file_info['total_files']}")
        print(f"🎯 Path: {current_file}")
        print(f"🎼 Sample Rate: {file_info.get('sample_rate', 'Unknown')} Hz")
        print(f"🔢 Channels: {file_info.get('channels', 'Unknown')}")
        print("-" * 60)
        print("🎮 CONTROLS:")
        print("   • Change 'file_index' to switch tracks (0-based)")
        print("   • File will be available for other audio nodes")
        print("-" * 60)
        if len(file_info['all_files']) > 1:
            print("📂 ALL FILES:")
            for i, fname in enumerate(file_info['all_files']):
                marker = "🎵" if i == file_info['current_index'] else "⏸️"
                print(f"   [{i}] {marker} {fname}")
            print("-" * 60)
        print(f"✅ Ready to play: {file_info['name']}")
        print("=" * 60)
class YTDLPreview:
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "downloaded_files": ("STRING",),
                "file_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "display": "number"
                }),
            },
            "optional": {}
        }
    RETURN_TYPES = ("AUDIO", "STRING", "STRING", "INT")
    RETURN_NAMES = ("audio", "current_file_path", "media_info_json", "total_files_count")
    FUNCTION = "preview_media"
    CATEGORY = "audio/ytdl"
    OUTPUT_NODE = True
    def detect_media_type(self, file_path):
        
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('audio/'):
                    return 'audio'
                elif mime_type.startswith('video/'):
                    return 'video'
            ext = os.path.splitext(file_path)[1].lower()
            audio_exts = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma']
            video_exts = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.flv']
            if ext in audio_exts:
                return 'audio'
            elif ext in video_exts:
                return 'video'
            return 'unknown'
        except:
            return 'unknown'
    def load_audio_data(self, file_path):
        
        try:
            import torch
            import torchaudio
            waveform, sample_rate = torchaudio.load(file_path)
            return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
        except Exception as e:
            print(f"⚠️ Direct audio load failed: {e}")
            try:
                import tempfile
                temp_wav = tempfile.mktemp(suffix='.wav')
                subprocess.run([
                    'ffmpeg', '-i', file_path, '-ar', '44100', '-ac', '2',
                    '-y', temp_wav
                ], capture_output=True, check=True)
                waveform, sample_rate = torchaudio.load(temp_wav)
                os.unlink(temp_wav)
                print("✅ Audio converted successfully with ffmpeg")
                return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
            except Exception as e2:
                print(f"❌ Audio fallback also failed: {e2}")
                return None
    def load_video_data(self, file_path):
        
        print(f"🎬 Loading video data from: {os.path.basename(file_path)}")
        try:
            import cv2
            import numpy as np
            import torch
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                print("⚠️ Could not open video file with OpenCV")
                return None
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"📊 Video properties: {width}x{height}, {fps} FPS, {frame_count} frames")
            frames = []
            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = frame.astype(np.float32) / 255.0
                frames.append(frame)
            cap.release()
            if frames:
                frames_tensor = torch.from_numpy(np.stack(frames))
                video_tensor = frames_tensor.unsqueeze(0)
                print(f"✅ Video loaded successfully: {video_tensor.shape}")
                return video_tensor
            else:
                print("⚠️ No frames could be read from video")
                return None
        except ImportError:
            print("⚠️ OpenCV not available for video loading")
            return None
        except Exception as e:
            print(f"⚠️ Video loading failed: {e}")
            return None
    def create_media_player_html(self, file_path, media_type, auto_play=False, volume=0.5, speed=1.0):
        
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        autoplay_attr = "autoplay" if auto_play else ""
        if media_type == 'video':
            player_html = f"""
            <div style="width: 100%; max-width: 640px; margin: 10px auto; background: #2a2a2a; border-radius: 12px; padding: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                <div style="text-align: center; color: #fff; margin-bottom: 10px; font-family: Arial, sans-serif;">
                    <h3 style="margin: 0; font-size: 14px; font-weight: 500;">🎬 {os.path.basename(file_path)}</h3>
                </div>
                <video controls {autoplay_attr} preload="metadata"
                       style="width: 100%; height: auto; border-radius: 8px; background: #000;"
                       onloadstart="this.volume={volume};">
                    <source src="{file_url}" type="video/mp4">
                    <source src="{file_url}" type="video/webm">
                    <source src="{file_url}" type="video/x-matroska">
                    <p style="color: #fff; text-align: center; padding: 20px;">
                        Your browser does not support HTML5 video.<br>
                        <a href="{file_url}" style="color: #4CAF50;">Download video file</a>
                    </p>
                </video>
                <div style="margin-top: 10px; text-align: center; font-size: 12px; color: #aaa;">
                    Volume: {int(volume * 100)}% | Speed: {speed}x | Auto-play: {'On' if auto_play else 'Off'}
                </div>
            </div>
            
            <div style="width: 100%; max-width: 500px; margin: 10px auto; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                <div style="text-align: center; color: white; margin-bottom: 15px; font-family: Arial, sans-serif;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 500;">🎵 {os.path.basename(file_path)}</h3>
                </div>
                <audio controls {autoplay_attr} preload="metadata" style="width: 100%; height: 40px;" onloadstart="this.volume={volume};">
                    <source src="{file_url}" type="audio/mpeg">
                    <source src="{file_url}" type="audio/wav">
                    <source src="{file_url}" type="audio/ogg">
                    <source src="{file_url}" type="audio/m4a">
                    <source src="{file_url}" type="audio/flac">
                    <p style="color: #fff; text-align: center; padding: 10px;">
                        Your browser does not support HTML5 audio.<br>
                        <a href="{file_url}" style="color: #fff; text-decoration: underline;">Download audio file</a>
                    </p>
                </audio>
                <div style="margin-top: 15px; text-align: center; font-size: 12px; color: rgba(255,255,255,0.8);">
                    Volume: {int(volume * 100)}% | Speed: {speed}x | Auto-play: {'On' if auto_play else 'Off'}
                </div>
            </div>
            """
        return player_html
    def preview_media(self, downloaded_files: str, file_index: int = 0):
        import json
        import torch
        if not downloaded_files or downloaded_files.strip() == "":
            print("⚠️ No downloaded files available")
            empty_info = {"error": "No files available", "total_files": 0}
            empty_audio = {"waveform": torch.zeros((1, 2, 1024)), "sample_rate": 44100}
            return (empty_audio, [], "", json.dumps(empty_info), 0)
        file_paths = [path.strip() for path in downloaded_files.split('\n') if path.strip()]
        if not file_paths:
            print("⚠️ No valid file paths found")
            empty_info = {"error": "No valid file paths", "total_files": 0}
            empty_audio = {"waveform": torch.zeros((1, 2, 1024)), "sample_rate": 44100}
            return (empty_audio, [], "", json.dumps(empty_info), 0)
        if file_index >= len(file_paths):
            file_index = 0
        elif file_index < 0:
            file_index = len(file_paths) - 1
        current_file = file_paths[file_index]
        if not os.path.exists(current_file):
            error_info = {"error": f"File not found: {current_file}", "total_files": len(file_paths)}
            print(f"❌ File not found: {current_file}")
            empty_audio = {"waveform": torch.zeros((1, 2, 1024)), "sample_rate": 44100}
            return (empty_audio, [], "", json.dumps(error_info), len(file_paths))
        media_type = self.detect_media_type(current_file)
        audio_data = None
        video_data = None
        if media_type in ['audio', 'video']:
            audio_data = self.load_audio_data(current_file)
        if media_type == 'video':
            print(f"✅ Video file available: {os.path.basename(current_file)}")
        else:
            print("⚠️ Not a video file")
        file_size = os.path.getsize(current_file)
        file_name = os.path.basename(current_file)
        duration = 0
        try:
            if audio_data and "waveform" in audio_data:
                duration = float(audio_data["waveform"].shape[-1]) / audio_data["sample_rate"]
        except:
            pass
        media_info = {
            "name": file_name,
            "path": current_file,
            "type": media_type,
            "size_mb": round(file_size / (1024*1024), 2),
            "duration_seconds": round(duration, 2),
            "current_index": file_index,
            "total_files": len(file_paths),
            "all_files": [{"index": i, "name": os.path.basename(f), "path": f} for i, f in enumerate(file_paths)],
            "controls": {}
        }
        if audio_data:
            media_info.update({
                "sample_rate": audio_data.get("sample_rate", 0),
                "channels": audio_data["waveform"].shape[1] if "waveform" in audio_data else 0
            })
        if media_type == 'video':
            try:
                import cv2
                cap = cv2.VideoCapture(current_file)
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    cap.release()
                    media_info.update({
                        "video_height": height,
                        "video_width": width,
                        "video_frames": frame_count,
                        "video_fps": fps,
                        "has_video": True
                    })
            except:
                pass
        self.create_enhanced_player_display(current_file, media_info)
        if audio_data is None:
            audio_data = {"waveform": torch.zeros((1, 2, 1024)), "sample_rate": 44100}
        return (audio_data, current_file, json.dumps(media_info, indent=2), len(file_paths))
    def create_enhanced_player_display(self, current_file: str, media_info: dict):
        
        media_type = media_info.get('type', 'unknown')
        print("=" * 70)
        print(f"🎬 YTDL MEDIA PREVIEW - {media_type.upper()}")
        print("=" * 70)
        print(f"📁 File: {media_info['name']}")
        print(f"📊 Size: {media_info['size_mb']} MB")
        print(f"⏱️ Duration: {media_info['duration_seconds']} seconds")
        print(f"📋 Index: {media_info['current_index'] + 1}/{media_info['total_files']}")
        print(f"🎯 Path: {current_file}")
        if media_type == 'audio':
            print(f"🎼 Sample Rate: {media_info.get('sample_rate', 'Unknown')} Hz")
            print(f"🔢 Channels: {media_info.get('channels', 'Unknown')}")
            print("🎵 Type: Audio File")
        elif media_type == 'video':
            print(f"📺 Resolution: {media_info.get('video_width', '?')}x{media_info.get('video_height', '?')}")
            print(f"🎼 Sample Rate: {media_info.get('sample_rate', 'Unknown')} Hz")
            print(f"🔢 Audio Channels: {media_info.get('channels', 'Unknown')}")
            print("🎬 Type: Video File (with audio)")
        print("-" * 70)
        print("🎮 CONTROLS:")
        print("   • Change 'file_index' to switch between files")
        print("   • Adjust 'volume' and 'playback_speed' for playback preferences")
        print("   • 'auto_play' to set playback behavior")
        print("   • Video frame available as IMAGE output for other nodes")
        print("   • Audio data available as AUDIO output for other nodes")
        print("-" * 70)
        if len(media_info['all_files']) > 1:
            print("📂 MEDIA LIBRARY:")
            for file_info in media_info['all_files']:
                i = file_info['index']
                fname = file_info['name']
                marker = "▶️" if i == media_info['current_index'] else "⏸️"
                ftype = "🎬" if self.detect_media_type(file_info['path']) == 'video' else "🎵"
                print(f"   [{i}] {marker} {ftype} {fname}")
            print("-" * 70)
        print(f"✅ Ready to preview: {media_info['name']}")
        print(f"🔊 Audio Data: Available as AUDIO output for playback nodes")
        print(f"📁 File Path: Available as STRING output for other nodes")
        print("=" * 70)
NODE_CLASS_MAPPINGS = {
    "YTDLLinksInput": YTDLLinksInput,
    "YTDLDownloader": YTDLDownloader,
    "YTDLPreviewAudio": YTDLPreviewAudio,
    "YTDLPreview": YTDLPreview,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "YTDLLinksInput": "YTDL Links Input",
    "YTDLDownloader": "YTDL Downloader",
    "YTDLPreviewAudio": "YTDL Preview Audio (Legacy)",
    "YTDLPreview": "YTDL Preview",
}
