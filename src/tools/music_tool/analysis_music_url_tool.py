import os
from typing import Type, Optional

import numpy as np
import requests
from bs4 import BeautifulSoup
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_ollama import OllamaEmbeddings
from pydantic import BaseModel, Field


class AnalysisMusicUrlInputArgs(BaseModel):
    song_name: str = Field(description="歌曲名称", examples=["绿光"])
    artist: Optional[str] = Field(
        default=None,
        description="歌手名称(可选)",
        examples=["孙燕姿"]
    )


def find_video_card_by_url(headers, search_url):
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 找到所有表示视频卡片的容器
    video_cards = soup.find_all("div", class_="bili-video-card__info--right")
    return video_cards


class AnalysisMusicUrlTool(BaseTool):
    name: str = "analysis_music_url_tool"
    description: str = """爬取网站获取歌曲备选URL列表。传入音乐名称和歌手名称(可选)
                    返回结果后选择其中最相关的一个视频标题, 使用它的url必须调用 download_music_tool 进行下载"""
    args_schema: Type[BaseModel] = AnalysisMusicUrlInputArgs

    def _run(
            self,
            song_name: str,
            artist: Optional[str] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:

        if not song_name:
            raise ValueError("song_name为必填字段")

        headers = {
            "Cookie": os.getenv("COOKIE"),
            "User-Agent": os.getenv("USER_AGENT")
        }

        def cosine_similarity(vec1, vec2):
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            return dot_product / (norm1 * norm2)

        embeddings = OllamaEmbeddings(model="all-minilm:l6-v2")
        if artist:
            click_search_url = f"https://search.bilibili.com/all?keyword={artist} {song_name}&order=click"
            vector1 = embeddings.embed_documents([f"{song_name}{artist}官方Hi-ResMV"])[0]
        else:
            click_search_url = f"https://search.bilibili.com/all?keyword={song_name}&order=click"
            vector1 = embeddings.embed_documents([f"{song_name}官方Hi-ResMV"])[0]
        click_video_cards = find_video_card_by_url(headers, click_search_url)

        search_url = click_search_url.split('&order=click')[0]
        video_cards = find_video_card_by_url(headers, search_url)

        sum_video_cards = list(click_video_cards) + list(video_cards)
        results_dict = dict()
        # 遍历每一个卡片，提取视频链接和标题
        for card in sum_video_cards:
            # 查找 a 标签，确保它包含 href 属性
            a_tag = card.find("a", href=True)
            if not a_tag:
                continue  # 若没有找到 a 标签则跳过当前块

            # 提取视频链接
            video_url = a_tag['href']

            # 在 a 标签内查找 h3 标签，并获取其文本
            title_tag = a_tag.find("h3", class_="bili-video-card__info--tit")
            if title_tag:
                title = title_tag.get_text(strip=False)
            else:
                title = "标题未找到"

            vector2 = embeddings.embed_documents([title])[0]

            similarity = cosine_similarity(vector1, vector2)

            results_dict[video_url] = {
                "title": title,
                "url": f"https:{video_url}",
                "similarity": float(similarity)
            }

        result_list = list(results_dict.values())
        if result_list:
            # 按相似度降序排序
            sorted_results = sorted(result_list, key=lambda x: x["similarity"], reverse=True)

            sorted_results = sorted_results[:15]

            # 格式化成字符串
            formatted_results = [
                f"标题: {item['title']} | URL: {item['url']} | 相似度得分: {item['similarity']:.4f}"
                for item in sorted_results
            ]

            return (
                    "找到以下备选下载链接: \n" + '\n'.join(formatted_results) +
                    "\n必须且只能从以上选择里选择一个你认为最有可能是匹配歌曲文件的选项, 只返回对应的URL"
            )
        else:
            return "没有找到任何链接"
