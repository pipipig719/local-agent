import logging
from dotenv import load_dotenv
from app import launch_demo

# 加载配置文件
load_dotenv('config.env')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    logging.info("启动应用程序……")
    launch_demo()


if __name__ == '__main__':
    main()
