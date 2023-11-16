"""Youtube Utils
    - Downloads youtube video by url or search???

"""
import asyncio
import yt_dlp as youtube_dl


async def download(url_or_string: str, tag: str = "unknown") -> str:
    """Download from url or search string????

    Arguments:
        url_or_string (str): The url of the youtube video or search???
    """

    # Setup options
    youtube_dl.utils.bug_reports_message = lambda: ""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "{tag}-%(extractor)s-%(id)s-%(title)s.%(ext)s".format(tag=tag),
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

    # Go and download based off of url_or_string in background
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(url_or_string, download=True)
    )

    if "entries" in data:
        # take first item from a playlist
        data = data["entries"][0]

    # Create file and return information
    filename = ytdl.prepare_filename(data)
    return {
        "id": data["id"],
        "file": filename,
        "title": data["title"],
        "url": data["webpage_url"],
    }


if __name__ == "__main__":
    URL = str(input("Enter the URL of the video: \n>>"))
    # DEST = (
    #     str(input("Enter the destination (leave blank for current directory) \n>>"))
    #     or "."
    # )
    asyncio.run(download(URL))
