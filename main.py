"""
AIエージェント「レオ」- メインファイル
毎朝Googleカレンダーを確認し、LINEで通知する執事型AIエージェント
"""

import os
import json
import logging
from datetime import datetime, date
import pytz

from google_calendar import get_today_events
from line_bot import send_line_message, get_user_id
from ai_response import generate_task_summary, generate_rest_suggestion
from knowledge import find_matching_knowledge

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")


def is_holiday() -> bool:
    """
    今日が休日かどうかを判定する。
    Google カレンダーに「休日」または終日予定（終日フラグ）がある場合、または土日を休日とみなす。
    環境変数 HOLIDAY_MODE=true でも強制休日モードになる。
    """
    if os.getenv("HOLIDAY_MODE", "false").lower() == "true":
        return True

    today = datetime.now(JST).weekday()  # 0=月曜 ... 6=日曜
    if today >= 5:  # 土・日
        return True

    return False


def run_morning_routine():
    """毎朝実行されるメインルーティン"""
    logger.info("=== レオ 朝のルーティン開始 ===")
    user_id = get_user_id()

    try:
        if is_holiday():
            _handle_holiday(user_id)
        else:
            _handle_weekday(user_id)

    except Exception as e:
        _handle_error(user_id, "朝のルーティン全体", str(e))

    logger.info("=== レオ 朝のルーティン終了 ===")


def _handle_weekday(user_id: str):
    """平日の処理"""
    logger.info("平日モードで処理開始")

    try:
        events = get_today_events()
    except Exception as e:
        _handle_error(user_id, "Googleカレンダー取得処理", str(e))
        return

    if not events:
        message = (
            "おはようございます。\n\n"
            "本日は特段ご予定がないようでございます。\n"
            "ゆったりとお仕事にお取り組みいただけますよう、\n"
            "穏やかな一日をお過ごしくださいませ。"
        )
        send_line_message(user_id, message)
        logger.info("予定なし通知を送信しました")
        return

    try:
        summary = generate_task_summary(events)
    except Exception as e:
        # AI生成に失敗した場合はシンプルなフォーマットで送信
        logger.warning(f"AI要約生成失敗、フォールバック使用: {e}")
        summary = _simple_event_summary(events)

    send_line_message(user_id, summary)
    logger.info(f"タスク要約を送信しました（予定数: {len(events)}）")


def _handle_holiday(user_id: str):
    """休日の処理"""
    logger.info("休日モードで処理開始")
    message = (
        "おはようございます。\n\n"
        "本日はお休みでございますね。\n"
        "今日の休み方はいかがなさいますか？\n\n"
        "（例：のんびりしたい、外に出たい、何か学びたい、など\n"
        "　お気軽にお伝えくださいませ）"
    )
    send_line_message(user_id, message)
    logger.info("休日問いかけメッセージを送信しました")


def handle_user_reply(user_message: str, user_id: str):
    """
    ユーザーからのLINE返信を受け取り、応答を生成して返す。
    LINE Webhookから呼ばれる。
    """
    logger.info(f"ユーザー返信受信: {user_message[:50]}...")

    try:
        # まずナレッジを検索
        knowledge_response = find_matching_knowledge(user_message)

        if knowledge_response:
            logger.info("ナレッジから返答を生成")
            reply = _format_knowledge_reply(knowledge_response)
        else:
            logger.info("ナレッジ該当なし、AI生成を使用")
            reply = generate_rest_suggestion(user_message)

        send_line_message(user_id, reply)

    except Exception as e:
        _handle_error(user_id, "返信生成処理", str(e))


def _simple_event_summary(events: list) -> str:
    """AI生成失敗時のシンプルな予定フォーマット"""
    lines = ["おはようございます。\n\n本日は以下のご予定がございます。\n"]
    for event in events:
        time_str = event.get("time", "終日")
        title = event.get("title", "（タイトルなし）")
        lines.append(f"・{time_str}　{title}")
    lines.append("\n本日も穏やかな一日となりますように。")
    return "\n".join(lines)


def _format_knowledge_reply(knowledge: dict) -> str:
    """ナレッジデータを会話文に整形"""
    category = knowledge.get("category", "")
    content = knowledge.get("content", "")
    scene = knowledge.get("scene", "")

    reply = f"かしこまりました。\n\n"
    if category:
        reply += f"【{category}】\n"
    reply += f"{content}\n"
    if scene:
        reply += f"\n（{scene}）\n"
    reply += "\nご自身のペースで、どうぞゆっくりお過ごしくださいませ。"
    return reply


def _handle_error(user_id: str, process_name: str, error_detail: str):
    """エラー発生時にLINEへ通知"""
    logger.error(f"エラー発生 - {process_name}: {error_detail}")

    message = (
        "申し訳ございません。\n"
        "本日の処理中に問題が発生いたしました。\n\n"
        f"【エラー箇所】\n{process_name}\n\n"
        f"【エラー内容】\n{error_detail[:200]}"
    )

    try:
        send_line_message(user_id, message)
    except Exception as e:
        logger.critical(f"エラー通知の送信にも失敗しました: {e}")


if __name__ == "__main__":
    run_morning_routine()
