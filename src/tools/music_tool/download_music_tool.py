from typing import Type, Optional
import yt_dlp

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class DownloadMusicInputArgs(BaseModel):
    url: str = Field(..., description="需要下载音乐的URL")


class DownloadMusicTool(BaseTool):
    name: str = "download_music_tool"
    description: str = "通过 analysis_music_url_tool 获取URL后，使用此工具进行实际下载"
    args_schema: Type[DownloadMusicInputArgs] = DownloadMusicInputArgs

    def _run(
            self,
            url: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:

        if not url:
            raise ValueError("url必须为非空字符串")

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }],
            'outtmpl': '%(title)s.%(ext)s',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info['duration'] <= 600:
                    if 'requested_downloads' in info:
                        filepath = info['requested_downloads'][0]['filepath']
                    else:
                        filepath = ydl.prepare_filename(info)
                else:
                    return f"下载失败:视频时长为{info['duration_string']},时长过长"
        except Exception as e:
            return f"下载失败:{str(e)}"

        return "所有音乐下载成功。" + "音乐文件保存本地路径:" + filepath
