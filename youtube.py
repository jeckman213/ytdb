import asyncio
import json
import yt_dlp as youtube_dl
import os


async def download(url: str) -> str:
    """Download from url or search string????
    
    Arguments:
        url (str): The url of the youtube video or search???
    """
    youtube_dl.utils.bug_reports_message = lambda: ""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }
    ytdl = youtube_dl.YoutubeDL(ydl_opts)

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(url, download=True)
    )

    if "entries" in data:
        # take first item from a playlist
        data = data["entries"][0]

    # f = open("log.json", "a")
    # f.write(json.dumps(data, indent=4))
    # f.close()

    filename = ytdl.prepare_filename(data)
    return {"id": data["id"], "file": filename, "title": data["title"], "url": data["webpage_url"]}


if __name__ == "__main__":
    URL = str(input("Enter the URL of the video: \n>>"))
    # DEST = (
    #     str(input("Enter the destination (leave blank for current directory) \n>>"))
    #     or "."
    # )
    asyncio.run(download(URL))
