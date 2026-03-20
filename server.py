import os
import logging
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from line_bot import get_webhook_handler, send_line_message
from main import handle_user_reply, _handle_weekday, _handle_holiday, run_morning_routine
from knowledge import find_matching_knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
handler = get_webhook_handler()

# ユーザーの会話状態を管理（休日の会話中かどうか）
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "agent": "Leo"}, 200

@app.route("/test-morning", methods=["GET"])
def test_morning():
    run_morning_routine()
    return {"status": "ok", "message": "朝のルーティンを実行しました"}, 200

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    user_message = event.message.text
    logger.info(f"メッセージ受信 from {user_id}: {user_message[:50]}")

    knowledge = find_matching_knowledge(user_message)

    # 平日トリガー
    if knowledge and knowledge.get("content") == "__WEEKDAY_TRIGGER__":
        user_state[user_id] = "weekday"
        _handle_weekday(user_id)
        return

    # 休日トリガー
    if knowledge and knowledge.get("content") == "__HOLIDAY_TRIGGER__":
        user_state[user_id] = "holiday_waiting"
        _handle_holiday(user_id)
        return

    # 休日の問いかけへの返答待ち状態
    if user_state.get(user_id) == "holiday_waiting":
        user_state[user_id] = "holiday_chatting"
        _send_mood_question(user_id, user_message)
        return

    # 通常の返信処理
    handle_user_reply(user_message, user_id)

def _send_mood_question(user_id: str, user_message: str):
    """気分を聞いてから提案する"""
    from ai_response import generate_rest_suggestion
    from knowledge import find_matching_knowledge

    knowledge = find_matching_knowledge(user_message)
    if knowledge and knowledge.get("content") not in ["__WEEKDAY_TRIGGER__", "__HOLIDAY_TRIGGER__"]:
        from main import _format_knowledge_reply
        reply = _format_knowledge_reply(knowledge)
    else:
        reply = generate_rest_suggestion(user_message)

    send_line_message(user_id, reply)
