import requests
from bs4 import BeautifulSoup
import json


def load_mapping(mapping_file="prefecture_city_mapping.json"):
    """
    JSONマッピングファイルを読み込み、都道府県→地域コード→都市名と都市コードの辞書を返す
    """
    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        return mapping
    except Exception as e:
        print("マッピングファイルの読み込みエラー:", e)
        return {}


def find_region_and_city_code(city_name, mapping):
    """
    マッピングデータ内から、指定された都市名に一致する地域コード・都市コード、
    さらに該当する県名も返す。複数ある場合は最初の一致を採用。
    """
    for prefecture, regions in mapping.items():
        for region_code, cities in regions.items():
            for name, city_code in cities.items():
                if name == city_name:
                    return prefecture, region_code, city_code
    return None, None, None


def get_weather_forecast(region_code, city_code):
    """
    指定された region_code と city_code を用いて、Yahoo天気予報サイトから
    今日と明日の天気および気温を抽出し、辞書型で返す。

    Yahoo側のHTML構造は以下のようになっています:
      ・<div class="forecastCity"> 内の<table>の各<td>に、日付や天気情報が含まれる
      ・各<td>内に<p class="date">, <p class="pict">, <ul class="temp">が存在する
    """
    base_url = "https://weather.yahoo.co.jp/weather"
    url = f"{base_url}/{region_code}/{city_code}.html"
    print(f"天気情報取得URL: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print("URL取得エラー:", e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    forecast_section = soup.find("div", class_="forecastCity")
    if not forecast_section:
        print("forecastCityセクションが見つかりません")
        return None

    # <td>要素の中から、<p class="date">が存在するセルだけを対象とする
    all_cells = forecast_section.find_all("td")
    forecast_cells = [cell for cell in all_cells if cell.find("p", class_="date")]

    if len(forecast_cells) < 2:
        print("今日・明日の予報情報が不足しています")
        return None

    forecast_data = {}
    day_labels = ["今日", "明日"]

    for cell, label in zip(forecast_cells[:2], day_labels):
        # 日付情報（例：<p class="date">内のテキスト）
        date_tag = cell.find("p", class_="date")
        date_text = date_tag.get_text(strip=True) if date_tag else ""

        # 天気情報（例：<p class="pict">内の画像alt属性またはテキスト）
        pict_tag = cell.find("p", class_="pict")
        if pict_tag:
            img_tag = pict_tag.find("img")
            weather_desc = (
                img_tag.get("alt", "").strip()
                if img_tag
                else pict_tag.get_text(strip=True)
            )
        else:
            weather_desc = ""

        # 気温情報（例：<ul class="temp">内の<li>要素から最高・最低温度を取得）
        temp_tag = cell.find("ul", class_="temp")
        if temp_tag:
            high_li = temp_tag.find("li", class_="high")
            low_li = temp_tag.find("li", class_="low")
            high_temp = (
                high_li.find("em").get_text(strip=True)
                if high_li and high_li.find("em")
                else ""
            )
            low_temp = (
                low_li.find("em").get_text(strip=True)
                if low_li and low_li.find("em")
                else ""
            )
            temp_text = f"最高: {high_temp}℃, 最低: {low_temp}℃"
        else:
            temp_text = ""

        forecast_data[label] = {
            "date": date_text,
            "weather": weather_desc,
            "temperature": temp_text,
        }
    return forecast_data


def get_weather_by_city(city_name):
    """
    main.pyから送られてくる都市名を元に、JSONマッピングから該当する
    地域コード・都市コード・県名を取得し、天気予報情報を抽出、結果を辞書で返す
    """
    mapping = load_mapping()
    prefecture, region_code, city_code = find_region_and_city_code(city_name, mapping)
    if not all([prefecture, region_code, city_code]):
        print(f"マッピング内に都市名 '{city_name}' の情報が見つかりません。")
        return None

    forecast = get_weather_forecast(region_code, city_code)
    if not forecast:
        print("天気予報情報が取得できませんでした。")
        return None

    result = {
        "prefecture": prefecture,
        "city_name": city_name,
        "region_code": region_code,
        "city_code": city_code,
        "forecast": forecast,
    }
    return result


def handle_message(message):
    """メッセージを解析して時刻情報を提供"""
    if message.startswith("天気予報 "):
        city_name = message.replace("天気予報 ", "").strip()
        return get_weather_by_city(city_name)
    return None


def register_plugin():
    """プラグイン登録"""
    return {"name": "Weather Forecast Info", "on_message": handle_message}
