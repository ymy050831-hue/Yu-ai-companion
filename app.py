import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

app = Flask(__name__)
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

def db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def get_memories():
    conn = db()
    rows = conn.execute(
        "SELECT text FROM memories ORDER BY id DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_memory(text):
    conn = db()
    conn.execute("INSERT INTO memories(text) VALUES (?)", (text,))
    conn.commit()
    conn.close()

def client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("没有找到 OPENAI_API_KEY。请先设置 API Key。")
    return OpenAI(api_key=key)

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    memories = get_memories()
    memory_text = "\n".join(f"- {m}" for m in memories) or "暂无长期记忆"

    instructions = f"""{PERSONA}

你目前知道的长期记忆：
{memory_text}

重要：不要主动告诉用户你看到了“数据库”或“记忆系统”，除非用户问起。
"""

    input_items = []
    for item in history[-12:]:
        role = item.get("role")
        content = item.get("content", "")
        if role in ("user", "assistant") and content:
            input_items.append({"role": role, "content": content})
    input_items.append({"role": "user", "content": message})

    try:
        response = client().responses.create(
            model=os.getenv("MIA_MODEL", "gpt-5.6-luna"),
            instructions=instructions,
            input=input_items,
        )
        reply = response.output_text.strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 非强制的简单记忆：用户明确说“记住/以后/我喜欢”等时保存。
    triggers = ("记住", "以后", "我喜欢", "我不喜欢", "我的计划", "我正在")
    if any(t in message for t in triggers):
        save_memory(message)

    return jsonify({"reply": reply, "memories": get_memories()})

if __name__ == "__main__":
    db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
