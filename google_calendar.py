"""
Googleカレンダー連携モジュール
当日の予定を取得する
"""

import os
import json
import logging
from datetime import datetime, date, timezone, timedelta
import pytz

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_service():
    """Google Calendar APIのサービスオブジェクトを取得"""
    # 環境変数からサービスアカウントのJSONを取得
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not credentials_json:
        raise ValueError(
            "環境変数 GOOGLE_CREDENTIALS_JSON が設定されていません。"
            "Google Cloud のサービスアカウントキーをJSON文字列として設定してください。"
        )

    credentials_info = json.loads(credentials_json)
    credentials = Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )

    service = build("calendar", "v3", credentials=credentials)
    return service


def get_today_events() -> list:
    """
    今日の予定を取得してリストで返す。

    Returns:
        list of dict: [{"title": str, "time": str, "is_all_day": bool}, ...]
        予定がない場合は空リスト
    """
    service = _get_service()
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    # 今日の0:00〜23:59:59 (JST) をUTCに変換
    today_jst = datetime.now(JST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    tomorrow_jst = today_jst + timedelta(days=1)

    time_min = today_jst.astimezone(timezone.utc).isoformat()
    time_max = tomorrow_jst.astimezone(timezone.utc).isoformat()

    logger.info(f"カレンダー取得範囲: {time_min} 〜 {time_max}")

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    raw_events = events_result.get("items", [])
    logger.info(f"取得した予定数: {len(raw_events)}")

    processed_events = []
    for event in raw_events:
        processed = _parse_event(event)
        if processed:
            processed_events.append(processed)

    return processed_events


def _parse_event(event: dict) -> dict | None:
    """
    Google Calendarのイベントオブジェクトをレオのフォーマットに変換する
    """
    title = event.get("summary", "（タイトルなし）")
    start = event.get("start", {})

    # 終日予定の場合
    if "date" in start:
        return {
            "title": title,
            "time": "終日",
            "is_all_day": True,
            "description": event.get("description", ""),
        }

    # 時刻付き予定の場合
    if "dateTime" in start:
        dt = datetime.fromisoformat(start["dateTime"])
        dt_jst = dt.astimezone(JST)
        time_str = dt_jst.strftime("%H:%M")
        return {
            "title": title,
            "time": time_str,
            "is_all_day": False,
            "description": event.get("description", ""),
        }

    return None
