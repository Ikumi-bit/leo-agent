"""
定時実行スケジューラー
毎朝7時（JST）に朝のルーティンを実行する
"""

import logging
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_morning_routine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

JST = pytz.timezone("Asia/Tokyo")

scheduler = BlockingScheduler(timezone=JST)

# 毎朝7:00 JSTに実行（MORNING_HOUR環境変数で変更可能）
import os
morning_hour = int(os.getenv("MORNING_HOUR", "7"))
morning_minute = int(os.getenv("MORNING_MINUTE", "0"))

@scheduler.scheduled_job("cron", hour=morning_hour, minute=morning_minute)
def morning_job():
    logger.info(f"定時実行: 朝のルーティン開始")
    run_morning_routine()


if __name__ == "__main__":
    logger.info(f"レオ スケジューラー起動（毎朝 {morning_hour:02d}:{morning_minute:02d} JST）")
    scheduler.start()
