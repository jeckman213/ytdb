from pytube import YouTube
import yt_dlp as youtube_dl
import os
import asyncio

async def download(url: str) -> str:
    youtube_dl.utils.bug_reports_message = lambda: ''
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }
    ffmpeg_options = {
        'options': '-vn',
    }
    ytdl = youtube_dl.YoutubeDL(ydl_opts)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
    if 'entries' in data:
        # take first item from a playlist
        data = data['entries'][0]

    filename = ytdl.prepare_filename(data)
    return filename

if __name__ == "__main__":
    url = str(input("Enter the URL of the video: \n>>"))
    dest = str(input("Enter the destination (leave blank for current directory) \n>>")) or "."
    asyncio.run(download(url, dest))