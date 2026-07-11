# files/youtube.py
import os
import yt_dlp
from files import config
import urllib.request
import urllib.parse
import json
import re

# مفتاح الـ API للبحث
YOUTUBE_API_KEY = "AIzaSyCMhGUJzN_AEfvKGU28z4VwvwX-i4U-nO4"

def get_youtube_info(query):
    """جلب معلومات الفيديو عبر API Key"""
    try:
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(query)}&type=video&key={YOUTUBE_API_KEY}&maxResults=1"
        req = urllib.request.Request(search_url)
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
            
        if search_data.get("items"):
            video_id = search_data["items"][0]["id"]["videoId"]
            title = search_data["items"][0]["snippet"]["title"]
            
            # جلب المدة
            video_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
            duration = 0
            try:
                v_req = urllib.request.Request(video_url)
                with urllib.request.urlopen(v_req) as v_response:
                    v_data = json.loads(v_response.read().decode())
                    if v_data.get("items"):
                        iso_duration = v_data["items"][0]["contentDetails"]["duration"]
                        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
                        if match:
                            h = int(match.group(1) or 0)
                            m = int(match.group(2) or 0)
                            s = int(match.group(3) or 0)
                            duration = h * 3600 + m * 60 + s
            except:
                pass
                
            return {
                "id": video_id,
                "title": title,
                "duration": duration,
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
    except Exception as e:
        print(f"API Search Error: {e}")
    
    return None

# ========================================================
# التحميل بدون كوكيز (أكثر استقراراً)
# ========================================================

def download_youtube_file(url, is_video=False):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    ydl_opts = {
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'ignoreerrors': True,
        'source_address': '0.0.0.0',
        
        # تم تعطيل الكوكيز لأنها تجبر المكتبة على استخدام الويب المحظور
        # 'cookiefile': 'cookies.txt',
        
        # الاعتماد الكامل على عملاء الهواتف لتخطي حظر يوتيوب
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
            }
        },
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com',
        },
        
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'retries': 20,
        'fragment_retries': 20,
        'ratelimit': None,
        'throttledratelimit': None,
        'extractor_retries': 10,
        'file_access_retries': 10,
    }
    
    if is_video:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        
    try:
        print(f"🔄 جاري التحميل: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                print("❌ لا توجد معلومات عن الفيديو")
                return None
            media_path = ydl.prepare_filename(info)
            if not is_video:
                if media_path.endswith('.m4a'):
                    media_path = media_path.replace('.m4a', '.mp3')
                elif not media_path.endswith('.mp3'):
                    media_path = os.path.splitext(media_path)[0] + '.mp3'
            print(f"✅ تم التحميل: {media_path}")
            return media_path
    except Exception as e:
        print(f"❌ خطأ في التحميل: {e}")
        return None

# ========================================================
# دوال التخزين
# ========================================================

async def get_cached_file_id(client, yt_id, is_video=False):
    if not config.STORAGE_CHANNEL_ID:
        return None
        
    cache_key = "video" if is_video else "audio"
    cache = config.bot_cache.get(cache_key, {})
    
    if yt_id in cache:
        try:
            msg = await client.get_messages(config.STORAGE_CHANNEL_ID, cache[yt_id])
            if is_video and msg and msg.video:
                return msg.video.file_id
            elif not is_video and msg:
                if msg.audio: return msg.audio.file_id
                if msg.document: return msg.document.file_id
        except: pass
            
    try:
        async for msg in client.search_messages(config.STORAGE_CHANNEL_ID, query=yt_id, limit=50):
            if is_video and msg.video:
                cache[yt_id] = msg.id
                config.save_cache()
                return msg.video.file_id
            elif not is_video and (msg.audio or msg.document):
                cache[yt_id] = msg.id
                config.save_cache()
                if msg.audio: return msg.audio.file_id
                return msg.document.file_id
    except: pass
    return None

async def background_upload_by_id(client, file_path, yt_id, title, is_video=False):
    if not config.STORAGE_CHANNEL_ID or not file_path or not os.path.exists(file_path):
        return
        
    cache_key = "video" if is_video else "audio"
    if yt_id in config.bot_cache.get(cache_key, {}):
        return
        
    try:
        if is_video:
            msg = await client.send_video(config.STORAGE_CHANNEL_ID, video=file_path, caption=yt_id)
        else:
            msg = await client.send_audio(config.STORAGE_CHANNEL_ID, audio=file_path, caption=yt_id, title=title, performer="YouTube")
            
        if msg:
            config.bot_cache.setdefault(cache_key, {})[yt_id] = msg.id
            config.save_cache()
    except: pass
