import os
import sqlite3
import sys
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

app = Flask(__name__)
app.json.ensure_ascii = False
DB = "mia_memory.db"

PERSONA = """
你叫 Mia，是用户的长期 AI 朋友。
你的性格：自然、聪明、温柔但不讨好，偶尔吐槽，有自己的观点。
你喜欢摄影、电影、旅行、音乐，以及一些有趣但不一定有用的话题。
聊天时不要像客服，不要每句话都总结或列清单。
用户只是想聊天时，优先陪伴和交流，不要动不动就给解决方案。
用户认真提问时，认真思考并给出清晰答案。
可以不同意用户，但要尊重对方。
不要假装拥有现实世界经历；不要编造不存在的记忆。
如果记忆与当前对话冲突，以用户当前明确说法为准。
"""

def get_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn

def get_memories():
    conn = get_db()
    rows = conn.execute("SELECT text FROM memories ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()
    return [str(r[0]) for r in rows]

def save_memory(text):
    conn = get_db()
    conn.execute("INSERT INTO memories(text) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def get_client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("服务器还没有设置 OPENAI_API_KEY。请在 Render 的 Environment 中添加它。")
    return OpenAI(api_key=key)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    memories = get_memories()
    memory_text = "\n".join(f"- {m}" for m in memories) or "暂无长期记忆"
    instructions = f"""{PERSONA}

你目前知道的长期记忆：
{memory_text}

不要主动告诉用户你看到了“数据库”或“记忆系统”，除非用户问起。
"""

    input_items = []
    for item in history[-12:]:
        role = item.get("role")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            input_items.append({"role": role, "content": str(content)})
    input_items.append({"role": "user", "content": message})

    try:
        response = get_client().responses.create(
            model=os.getenv("MIA_MODEL", "gpt-5.6-luna"),
            instructions=instructions,
            input=input_items,
        )
        reply = (response.output_text or "").strip() or "我刚才好像走神了，再说一次？"
    except Exception as e:
        print(f"Mia API error: {type(e).__name__}: {e}", file=sys.stderr)
        return jsonify({
            "error": f"AI 请求失败：{type(e).__name__}。请稍后重试；如果持续出现，请查看 Render Logs。"
        }), 500

    if any(t in message for t in ("记住", "以后", "我喜欢", "我不喜欢", "我的计划", "我正在")):
        save_memory(message)

    return jsonify({"reply": reply, "memories": get_memories()})

if __name__ == "__main__":
    get_db().close()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
