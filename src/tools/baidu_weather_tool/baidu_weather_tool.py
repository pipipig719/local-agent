import csv
import os
from typing import Type, Optional

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


def find_code(csv_file_path, district_name) -> str:
    district_map = {}

    with open(csv_file_path, mode='r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            district_code = row['district_geocode'].strip()
            district = row['district'].strip()
            if district not in district_map:
                district_map[district] = district_code

        return district_map.get(district_name)


def get_ak():
    ak = os.getenv('AK')
    return ak


class WeatherInputsArgs(BaseModel):
    location: str = Field(..., description="用于查询天气的位置信息")


class WeatherTool(BaseTool):
    """定义工具"""
    name: str = 'weather_tool'
    description: str = '可以查询任意位置的当前天气情况'
    args_schema: Type[WeatherInputsArgs] = WeatherInputsArgs

    def _run(
            self,
            location: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """调用工具自动执行的函数"""

        district_code = find_code(os.path.join(os.path.dirname(__file__),
                                               'weather_district_id.csv'),
                                  location)
        ak = get_ak()

        print(f'需要查询的{location}的地区编码是: {district_code}')
        url = "https://api.map.baidu.com/weather/v1/"

        params = {
            "district_id": district_code,
            "data_type": "all",
            "ak": ak,
        }

        weather_resp = requests.get(url, params)
        if weather_resp:
            data = weather_resp.json()

            code = data['status']
            if code == 0:
                text = data["result"]["now"]['text']
                temp = data["result"]["now"]['temp']
                feels_like = data["result"]["now"]['feels_like']
                rh = data["result"]["now"]['rh']
                wind_dir = data["result"]["now"]['wind_dir']
                wind_class = data["result"]["now"]['wind_class']
                return (f"{location}的当前天气:{text}, 温度:{temp}摄氏度, 体感温度:{feels_like}摄氏度, "
                        f"相对湿度:百分之{rh}, {wind_dir}:{wind_class}。")
            else:
                return "当前暂时无法获取天气"
