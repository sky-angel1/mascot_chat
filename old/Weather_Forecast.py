import json
import requests
import os


def load_city_codes():
    """都市コードを外部ファイルから読み込む。ファイルが存在しない場合は新規作成。"""
    file_path = "city_codes.json"
    if not os.path.exists(file_path):
        update_city_codes()  # ファイルがなければ最新情報を取得
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def update_city_codes():
    """最新の都市コードを気象庁のデータから取得し、JSONファイルを更新する"""
    url = "https://www.jma.go.jp/bosai/common/const/area.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        latest_city_codes = {}
        count = 0

        # 解析対象のキーリスト
        target_keys = ["class10s", "class15s", "class20s"]
        for key in target_keys:
            entries = data.get(key, {})
            for code, info in entries.items():
                if isinstance(info, dict) and "name" in info:
                    # 例: {"２３区西部": "130012", ...}
                    latest_city_codes[info["name"]] = code
                    count += 1

        print(f"抽出した自治体数: {count}")
        with open("city_codes.json", "w", encoding="utf-8") as file:
            json.dump(latest_city_codes, file, ensure_ascii=False, indent=4)
        print("都市コードが正常に更新されました。")
    except requests.exceptions.RequestException as e:
        print(f"都市コードの更新に失敗しました: {e}")
    except json.JSONDecodeError as e:
        print(f"JSONの解析に失敗しました: {e}")
    except Exception as e:
        print(f"不明なエラーが発生しました: {e}")


def get_weather_forecast(city_code):
    """気象庁の防災JSONから天気予報を取得"""
    base_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/"
    url = f"{base_url}{city_code}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        areas = data[0]["timeSeries"][0]["areas"]
        forecasts = []
        for area in areas:
            area_name = area["area"]["name"]
            weather = area["weathers"][:3]  # 3日分取得
            forecasts.append(
                f"📍 {area_name} の天気予報\n"
                f"📅 今日: {weather[0]}\n"
                f"📅 明日: {weather[1]}\n"
                f"📅 明後日: {weather[2]}"
            )
        return "\n\n".join(forecasts)
    except requests.exceptions.RequestException as e:
        return f"天気情報の取得に失敗しました: {e}"


def get_city_code(city, city_codes):
    """渡された自治体名から気象庁のコードを取得"""
    return city_codes.get(city)


def handle_weather_request(message, city_codes):
    """メッセージから天気情報リクエストを処理"""
    if message.startswith("天気予報"):
        city = message.replace("天気予報", "").strip()
        if not city:
            city = "東京"  # デフォルトは東京
        city_code = get_city_code(city, city_codes)
        if city_code:
            return get_weather_forecast(city_code)
        else:
            return "指定された都市の天気情報を取得できません。"
    return None


def register_plugin():
    """プラグイン登録用関数（最新の都市コードを利用）"""
    update_city_codes()  # 起動時に都市コードを更新
    city_codes = load_city_codes()
    return {
        "name": "Weather Forecast Plugin",
        "on_message": lambda msg: handle_weather_request(msg, city_codes),
    }


if __name__ == "__main__":
    # 動作確認用
    register_plugin()
