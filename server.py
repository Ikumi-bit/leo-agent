"""
LINE Webhook受信サーバー
ユーザーからの返信を受け取りレオが応答する
"""

import os
import logging
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from line_bot import get_webhook_handler
from main import handle_user_reply

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
handler = get_webhook_handler()


@app.route("/webhook", methods=["POST"])
def webhook():
    """LINE Webhookエンドポイント"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("無効な署名のリクエストを受信")
        abort(400)

    return "OK"


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック用エンドポイント（Railway用）"""
    return {"status": "ok", "agent": "Leo"}, 200
    
@app.route("/test-morning", methods=["GET"])
def test_morning():
    """動作テスト用：朝のルーティンを手動実行"""
    from main import run_morning_routine
    run_morning_routine()
    return {"status": "ok", "message": "朝のルーティンを実行しました"}, 200


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    """テキストメッセージを受信したときの処理"""
    user_id = event.source.user_id
    user_message = event.message.text

    logger.info(f"メッセージ受信 from {user_id}: {user_message[:50]}")

    from knowledge import find_matching_knowledge
    knowledge = find_matching_knowledge(user_message)

    if knowledge and knowledge.get("content") == "__WEEKDAY_TRIGGER__":
        # 平日モードを手動起動
        from main import _handle_weekday
        _handle_weekday(user_id)
    elif knowledge and knowledge.get("content") == "__HOLIDAY_TRIGGER__":
        # 休日モードを手動起動
        from main import _handle_holiday
        _handle_holiday(user_id)
    else:
        handle_user_reply(user_message, user_id)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
