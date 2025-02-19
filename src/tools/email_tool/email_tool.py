import os
import smtplib

from typing import Type, Optional
from apscheduler.triggers.date import DateTrigger
from pydantic import BaseModel, Field
from email.mime.text import MIMEText
from email.utils import formataddr
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from datetime import datetime
from tools.email_tool.scheduler import Scheduler

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': os.getenv('SMTP_PORT'),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),
    'sender_name': os.getenv('SENDER_NAME'),
}

scheduler = Scheduler()
scheduler.start()


def send_email(subject, content):
    """发送邮件函数"""
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = formataddr((EMAIL_CONFIG['sender_name'], EMAIL_CONFIG['sender_email']))
    msg['To'] = EMAIL_CONFIG['receiver_email']
    msg['Subject'] = subject

    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], int(EMAIL_CONFIG['smtp_port'])) as server:
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.sendmail(EMAIL_CONFIG['sender_email'],
                            [EMAIL_CONFIG['receiver_email']],
                            msg.as_string())
            print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")


class EmailInputArgs(BaseModel):
    receiver_email: str = Field(..., description="需要发送邮件的目标邮箱URL", example="abcd1234@gmail.com")
    subject: str = Field(..., description="需要发送邮件的标题", example="你好，这是一个标题")
    content: str = Field(..., description="需要发送邮件的正文", example="这是一个正文内容")
    year: Optional[int] = Field(default=None, description="年", example=2020)
    month: Optional[int] = Field(default=None, description="月", example=11)
    day: Optional[int] = Field(default=None, description="日", example=14)
    hour: Optional[int] = Field(default=None, description="时", example=3)
    minute: Optional[int] = Field(default=None, description="分", example=54)
    second: Optional[int] = Field(default=None, description="秒", example=30)


class EmailTool(BaseTool):
    name: str = "email_tool"
    description: str = """邮件发送工具需求说明
                        一、核心功能：
                        通过调用专用工具实现两种邮件发送模式：
                        立即发送模式 - 实时投递邮件
                        定时发送模式 - 按指定时间调度发送
                        发送邮件不需要二次确认
                        二、必填参数（所有模式必须包含）：
                        目标邮箱URL（如果没有必须先询问获取）
                        邮件标题（字符串类型）
                        邮件正文（字符串类型）
                        三、模式选择与参数规范：
                        [模式选择]
                        当选择定时发送模式时：
                        必须首先使用专用时间获取工具get_now_tool取得时间参数，然后填入年月日时分秒参数
                        例如：{'year': 2020, 'month': 1, 'day': 19, 'hour': 15, 'minute': 47, 'month': 2,
                          'second': 0}
                        [模式切换]
                        当不提供时间参数时：
                        系统自动识别为立即发送模式，即立即发送邮件
                        四、时间参数获取规范：
                        禁止手动输入时间数值
                        必须使用get_now_tool工具首先获取
                        五、优先级逻辑：
                        定时参数存在时自动覆盖立即发送模式，执行定时调度流程"""
    args_schema: Type[BaseModel] = EmailInputArgs

    def _run(self,
             receiver_email: str,
             subject: str,
             content: str,
             year: Optional[int] = None,
             month: Optional[int] = None,
             day: Optional[int] = None,
             hour: Optional[int] = None,
             minute: Optional[int] = None,
             second: Optional[int] = None,
             run_manager: Optional[CallbackManagerForToolRun] = None,
             ) -> str:

        if not receiver_email:
            return "请填写需要发送的目标邮箱URL"

        variables = [year, month, day, hour, minute, second]

        if all(v is not None for v in variables):
            try:
                EMAIL_CONFIG['receiver_email'] = receiver_email
                target_time = datetime(year, month, day, hour, minute, second)
                scheduler.add_job(
                    send_email,
                    trigger=DateTrigger(run_date=target_time),
                    args=[subject, content]
                )
                return f"任务已经提交, 邮件发送时间为: {target_time.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception as e:
                return f"定时任务创建失败: {str(e)}"
        elif all(v is None for v in variables):
            EMAIL_CONFIG['receiver_email'] = receiver_email
            send_email(subject, content)
            return f"邮件发送成功, 发送时间为: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            return "年月日时分秒参数有误，请重新确认并填写"
