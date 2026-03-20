"""
AI返答生成モジュール（OpenAI API使用）
タスク要約と休み方提案を生成する
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

LEO_SYSTEM_PROMPT = """
あなたはAIエージェント「レオ」です。ユーザーの日常を支援する執事型アシスタントです。

【口調と態度】
- 丁寧語・執事風の言い回しを使う
- 命令せず、選択を尊重した提案にとどめる
- 押し付けず、控えめに
- 「何もしない」も否定しない、余白を大切にする

【返答の長さ】
- 簡潔にまとめる（LINEで読みやすい長さ）
- 箇条書きより自然な文章を優先する
"""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "環境変数 OPENAI_API_KEY が設定されていません。"
        )
    return OpenAI(api_key=api_key, http_client=None)


def generate_task_summary(events: list) -> str:
    """
    今日の予定リストからLINE送信用のタスク要約を生成する

    Args:
        events: [{"title": str, "time": str, "is_all_day": bool}, ...]

    Returns:
        str: 執事風のタスク要約テキスト
    """
    client = _get_client()

    events_text = "\n".join(
        [f"- {e['time']}　{e['title']}" for e in events]
    )

    prompt = f"""
以下は今日の予定リストです。これをもとに、執事レオとして朝のLINEメッセージを作成してください。

予定:
{events_text}

【条件】
- 「おはようございます。」で始める
- 予定を時刻順に整理して伝える
- 最後に一言、穏やかな締めの言葉を添える
- LINEで読みやすいよう、150〜200文字程度にまとめる
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": LEO_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=400,
        temperature=0.7,
    )

    result = response.choices[0].message.content.strip()
    logger.info("タスク要約をAI生成しました")
    return result


def generate_rest_suggestion(user_message: str) -> str:
    """
    ユーザーの休み方に関するメッセージに対して、提案を生成する

    Args:
        user_message: ユーザーからの返信テキスト

    Returns:
        str: 執事風の休み方提案テキスト
    """
    client = _get_client()

    prompt = f"""
ユーザーから以下のメッセージが届きました。休日の過ごし方について、執事レオとして優しく提案してください。

ユーザーのメッセージ: 「{user_message}」

【提案のポイント】
- 無理をさせない
- 「何もしない」「ぼーっとする」も立派な休み方として肯定する
- 具体的な過ごし方を1〜2つ提案する（押し付けない）
- 温かく、余白を感じる文体にする
- LINEで読みやすい長さ（200文字程度）
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": LEO_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=500,
        temperature=0.8,
    )

    result = response.choices[0].message.content.strip()
    logger.info("休み方提案をAI生成しました")
    return result
