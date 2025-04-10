import pytz
from datetime import datetime


def get_world_time(city):
    """指定した都市の現在時刻を取得する"""
    city_timezones = {
        # アジア・オセアニア
        "東京": "Asia/Tokyo",
        "北京": "Asia/Shanghai",
        "香港": "Asia/Hong_Kong",
        "ソウル": "Asia/Seoul",
        "シンガポール": "Asia/Singapore",
        "ムンバイ": "Asia/Kolkata",
        "ドバイ": "Asia/Dubai",
        "シドニー": "Australia/Sydney",
        # アメリカ
        "ニューヨーク": "America/New_York",
        "ワシントンD.C.": "America/New_York",
        "ボストン": "America/New_York",
        "マイアミ": "America/New_York",
        "シカゴ": "America/Chicago",
        "ダラス": "America/Chicago",
        "デンバー": "America/Denver",
        "フェニックス": "America/Phoenix",
        "ロサンゼルス": "America/Los_Angeles",
        "サンフランシスコ": "America/Los_Angeles",
        "シアトル": "America/Los_Angeles",
        # ヨーロッパ
        "ロンドン": "Europe/London",
        "パリ": "Europe/Paris",
        "ベルリン": "Europe/Berlin",
        "マドリード": "Europe/Madrid",
        "ローマ": "Europe/Rome",
        "アムステルダム": "Europe/Amsterdam",
        "ブリュッセル": "Europe/Brussels",
        "ストックホルム": "Europe/Stockholm",
        "ウィーン": "Europe/Vienna",
        "ジュネーブ": "Europe/Zurich",
        "チューリッヒ": "Europe/Zurich",
        "オスロ": "Europe/Oslo",
        "ヘルシンキ": "Europe/Helsinki",
        "モスクワ": "Europe/Moscow",
        # 南米・アフリカ
        "リオデジャネイロ": "America/Sao_Paulo",
        "ブエノスアイレス": "America/Argentina/Buenos_Aires",
        "ヨハネスブルグ": "Africa/Johannesburg",
    }

    if city not in city_timezones:
        return f"⚠️ '{city}' の時刻情報は取得できません。"

    tz = pytz.timezone(city_timezones[city])
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return f"🕒 {city}の現在時刻: {now}"


def handle_message(message):
    """メッセージを解析して時刻情報を提供"""
    if message.startswith("時刻 "):
        city = message.replace("時刻 ", "").strip()
        return get_world_time(city)
    return None


def register_plugin():
    """プラグイン登録"""
    return {"name": "World Time Info", "on_message": handle_message}
