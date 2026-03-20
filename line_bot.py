"""
LINE Messaging API 連携モジュール
メッセージ送信とWebhook受信を担当する
"""

import os
import logging
import hashlib
import hmac
import base64

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

logger = logging.getLogger(__name__)


def get_user_id() -> str:
    """送信先のLINEユーザーIDを環境変数から取得"""
    user_id = os.getenv("LINE_USER_ID")
    if not user_id:
        raise ValueError(
            "環境変数 LINE_USER_ID が設定されていません。"
            "LINE DevelopersでユーザーIDを確認してください。"
        )
    return user_id


def _get_messaging_api() -> MessagingApi:
    """LINE Messaging APIクライアントを取得"""
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not channel_access_token:
        raise ValueError(
            "環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません。"
        )
    configuration = Configuration(access_token=channel_access_token)
    api_client = ApiClient(configuration)
    return MessagingApi(api_client)


def send_line_message(user_id: str, message: str) -> bool:
    """
    指定ユーザーにLINEメッセージをプッシュ送信する

    Args:
        user_id: LINEユーザーID
        message: 送信するテキスト

    Returns:
        bool: 成功かどうか
    """
    try:
        api = _get_messaging_api()
        api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(type="text", text=message)],
            )
        )
        logger.info(f"LINEメッセージ送信成功: {message[:30]}...")
        return True
    except Exception as e:
        logger.error(f"LINEメッセージ送信失敗: {e}")
        raise


def get_webhook_handler() -> WebhookHandler:
    """LINE Webhookハンドラーを取得"""
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    if not channel_secret:
        raise ValueError(
            "環境変数 LINE_CHANNEL_SECRET が設定されていません。"
        )
    return WebhookHandler(channel_secret)
