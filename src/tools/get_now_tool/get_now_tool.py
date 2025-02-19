from typing import Optional
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from datetime import datetime


class GetNowTool(BaseTool):
    name: str = "get_now_tool"
    description: str = """获取当前时间的工具，以年-月-日 时:分:秒的格式返回"""

    def _run(self,
             run_manager: Optional[CallbackManagerForToolRun] = None,
             ) -> str:

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')