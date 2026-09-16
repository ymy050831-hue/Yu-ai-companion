Mia V1 新手指南
================

这是一个最小可用的 AI 聊天伙伴原型。
它包含：
- Mia 固定人格
- 网页聊天
- 简单长期记忆
- 最近对话上下文

一、准备
--------
需要一个可以运行 Python 的环境，以及 OpenAI API Key。

二、安装
--------
在项目目录打开终端：

1. 创建虚拟环境（可选但推荐）
   python -m venv .venv

2. 激活环境
   Windows:
   .venv\Scripts\activate
   macOS/Linux:
   source .venv/bin/activate

3. 安装依赖
   pip install -r requirements.txt

三、设置 API Key
----------------
不要把 API Key 写进网页代码，也不要发给别人。

Windows PowerShell:
   $env:OPENAI_API_KEY="你的API_KEY"

macOS/Linux:
   export OPENAI_API_KEY="你的API_KEY"

也可以使用 .env，但需要自行加入 python-dotenv。
为了让第一版尽量简单，本项目默认读取系统环境变量。

四、启动
--------
python app.py

然后浏览器打开：
http://127.0.0.1:5000

五、重要
--------
API Key 具有账户使用权限，务必保密。
不要把 .env、API Key 或 mia_memory.db 上传到公开 GitHub。

六、下一版
----------
V2：更聪明的长期记忆
V3：语音输入/输出
V4：图片理解
V5：主动聊天
