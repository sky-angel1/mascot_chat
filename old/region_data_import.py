import requests
from bs4 import BeautifulSoup
import json
import time

# Yahoo天気予報のURL構造
base_url = "https://weather.yahoo.co.jp/weather"
# 都道府県リスト（必要に応じて追加）
prefecture_codes = [
    ("茨城県", "8"),
    ("東京都", "13"),
    ("大阪府", "27"),
    ("北海道", "1"),  # 他の都道府県コードを追加
]

# 地方や市区町村のリスト（都道府県ごとに必要な地域コードを追加）
# 実際には地域コードを抽出する方法を実装する部分に応じて、他の地域データを使う
region_codes = {
    "茨城県": [("土浦地方", "4020"), ("つくば市", "8220")],
    "東京都": [("23区", "13000"), ("八王子市", "13120")],
    "大阪府": [("大阪市", "270000")],
}


# 地域データを抽出してJSONとして保存する
def extract_region_data(prefecture_codes, region_codes):
    all_regions = {}

    # 都道府県ごとに巡回してページ解析
    for prefecture, prefecture_code in prefecture_codes:
        region_data = {}
        for region_name, region_code in region_codes.get(prefecture, []):
            # 地域ページのURL構築
            url = f"{base_url}/{prefecture_code}/{region_code}.html"
            print(f"アクセス中: {url}")
            try:
                # ページを取得して解析
                response = requests.get(url)
                soup = BeautifulSoup(response.text, "html.parser")

                # 必要な地域情報を抽出（例えば、地域名や天気情報など）
                region_data[region_name] = region_code

                # 必要に応じて、天気予報のデータを抽出する処理を追加
                # 例: soup.find() などで天気情報を抽出

                # サーバーへの負荷を避けるために少し待機
                time.sleep(1)
            except Exception as e:
                print(f"エラー: {url} - {e}")

        # 取得した地域データを都道府県別に格納
        all_regions[prefecture] = region_data

    # JSONファイルとして保存
    with open("region_data.json", "w", encoding="utf-8") as json_file:
        json.dump(all_regions, json_file, ensure_ascii=False, indent=4)

    print("地域データをJSONファイルに保存しました。")


# 地域データを取得して保存
extract_region_data(prefecture_codes, region_codes)
