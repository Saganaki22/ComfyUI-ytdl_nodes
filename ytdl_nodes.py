import os
import json
import subprocess
import sys
from typing import List, Tuple, Optional


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
            print("📦 Installing ffmpeg-python (one-time setup)...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ffmpeg-python", "--quiet"])
            print("✅ ffmpeg-python installed!")
            return True
        except Exception as e:
            print(f"⚠️ Could not install ffmpeg-python: {e}")
            return False

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
                "audio_only": ("BOOLEAN", {"default": True}),
                "audio_format": (["mp3", "wav", "m4a", "flac", "ogg"], {"default": "mp3"}),
                "quality": (["best", "worst", "320", "256", "192", "128"], {"default": "best"}),
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
    
    def download_media(self, links: List[str], output_folder: str, audio_only: bool, 
                      audio_format: str, quality: str, use_cookies: bool, browser_for_cookies: str,
                      download_playlist: bool, continue_on_error: bool, 
                      custom_filename: str = "%(title)s.%(ext)s", cookie_file: str = ""):
        
        yt_dlp = ensure_yt_dlp()
        
        ffmpeg_available = check_ffmpeg()
        if audio_only and audio_format != 'm4a':
            if not ffmpeg_available:
                print("=" * 60)
                print("⚠️ FFMPEG NOT FOUND!")
                print("For audio conversion, please install ffmpeg:")
                print("  Windows: winget install ffmpeg")
                print("  Mac:     brew install ffmpeg")
                print("  Linux:   sudo apt install ffmpeg")
                print("  Or download from: https://ffmpeg.org/download.html")
                print("=" * 60)
            else:
                install_ffmpeg_python()  
        
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
        
        if download_playlist:
            print("📋 Playlist mode: ENABLED - Will download available videos from playlists")
        else:
            print("📋 Playlist mode: DISABLED - Will download only single videos from playlist URLs")
        
        if continue_on_error:
            print("🛡️ Error handling: CONTINUE - Will skip unavailable videos and continue")
        else:
            print("🛡️ Error handling: STOP - Will stop on first error")
        
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
            else:
                ydl_opts['format'] = (
                    f'bestaudio[abr<={quality}][ext=m4a]/bestaudio[abr<={quality}][ext=mp3]/'
                    f'bestaudio[abr<={quality}]/bestaudio[ext=m4a]/bestaudio[ext=mp3]/'
                    f'bestaudio/best[height<=720]/best'
                )
            
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': quality if quality.isdigit() else None,
            }]
        else:
            if quality == "best":
                ydl_opts['format'] = 'best[ext=mp4]/best[ext=webm]/best'
            elif quality == "worst":
                ydl_opts['format'] = 'worst[ext=mp4]/worst[ext=webm]/worst'
            else:
                ydl_opts['format'] = (
                    f'best[height<={quality}][ext=mp4]/best[height<={quality}][ext=webm]/'
                    f'best[height<={quality}]/best[ext=mp4]/best[ext=webm]/best'
                )
        
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
                        
                        bar_length = 40
                        filled_length = int(bar_length * percent / 100)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        
                        print(f"\r⬇️ [{bar}] {percent:5.1f}% | {speed_str} | {basename[:30]}", end='', flush=True)
            elif d['status'] == 'finished':
                print(f"\n✅ Download completed: {os.path.basename(d.get('filename', 'Unknown'))}")
            elif d['status'] == 'error':
                print(f"\n❌ Download error: {d.get('filename', 'Unknown')}")
        
        total_links = len(links)
        total_attempted = 0
        total_successful = 0
        total_failed = 0
        
        for link_idx, link in enumerate(links):
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
                            
                            success = self.safe_download_single_video(download_ydl, entry, progress_hook, max_retries=3)
                            
                            if success:
                                expected_filename = download_ydl.prepare_filename(entry)
                                if audio_only:
                                    base_name = os.path.splitext(expected_filename)[0]
                                    expected_filename = f"{base_name}.{audio_format}"
                                
                                actual_file = None
                                if os.path.exists(expected_filename):
                                    actual_file = expected_filename
                                else:
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
                                    download_info.append({
                                        'url': video_url,
                                        'title': video_title,
                                        'duration': entry.get('duration', 0),
                                        'file_path': actual_file,
                                        'file_size': os.path.getsize(actual_file),
                                        'playlist_index': video_idx + 1 if total_videos > 1 else None,
                                        'status': 'success'
                                    })
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
        
        if total_failed > 0:
            print(f"⚠️ {total_failed} downloads failed (see details above)")
        
        print(f"{'='*60}")
        
        files_output = '\n'.join(downloaded_files) if downloaded_files else ""
        
        summary = {
            'summary': {
                'total_attempted': total_attempted,
                'successful': total_successful,
                'failed': total_failed,
                'success_rate': round((total_successful / total_attempted * 100) if total_attempted > 0 else 0, 1)
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


NODE_CLASS_MAPPINGS = {
    "YTDLLinksInput": YTDLLinksInput,
    "YTDLDownloader": YTDLDownloader,
    "YTDLPreviewAudio": YTDLPreviewAudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YTDLLinksInput": "YTDL Links Input",
    "YTDLDownloader": "YTDL Downloader", 
    "YTDLPreviewAudio": "YTDL Preview Audio",
}
