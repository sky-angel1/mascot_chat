import json
from bs4 import BeautifulSoup

# 県対応テーブル（URL の最初の部分から県名を決定）
prefecture_mapping = {
    "1a": "北海道",
    "1b": "北海道",
    "1c": "北海道",
    "1d": "北海道",
    "2": "青森",
    "5": "秋田",
    "3": "岩手",
    "6": "山形",
    "4": "宮城",
    "7": "福島",
    "8": "茨城",
    "9": "栃木",
    "10": "群馬",
    "13": "東京都",
    "12": "千葉",
    "11": "埼玉",
    "19": "山梨",
    "15": "新潟",
    "20": "長野",
    "22": "静岡",
    "16": "富山",
    "17": "石川",
    "21": "岐阜",
    "23": "愛知",
    "18": "福井",
    "25": "滋賀",
    "24": "三重",
    "26": "京都",
    "27": "大阪",
    "28": "兵庫",
    "30": "和歌山",
    "31": "鳥取",
    "33": "岡山",
    "36": "徳島",
    "32": "島根",
    "37": "香川",
    "34": "広島",
    "39": "高知",
    "38": "愛媛",
    "35": "山口",
    "44": "大分",
    "40": "福岡",
    "43": "熊本",
    "45": "宮崎",
    "41": "佐賀",
    "42": "長崎",
    "46": "鹿児島",
    "47": "沖縄",
}
# 修正後の HTML 断片
html_fragment = """
<div>
    <a href="https://weather.yahoo.co.jp/weather/jp/1a/1100.html"><dt class="name">稚内</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1a/1200.html"><dt class="name">旭川</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1a/1300.html"><dt class="name">留萌</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/1710.html"><dt class="name">網走</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/1720.html"><dt class="name">北見</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/1730.html"><dt class="name">紋別</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/1800.html"><dt class="name">根室</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/1900.html"><dt class="name">釧路</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1c/2000.html"><dt class="name">帯広</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1b/1400.html"><dt class="name">札幌</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1b/1500.html"><dt class="name">岩見沢</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1b/1600.html"><dt class="name">倶知安</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1d/2100.html"><dt class="name">室蘭</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1d/2200.html"><dt class="name">浦河</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1d/2300.html"><dt class="name">函館</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/1d/2400.html"><dt class="name">江差</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/2/3110.html"><dt class="name">青森</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/2/3120.html"><dt class="name">むつ</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/2/3130.html"><dt class="name">八戸</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/5/3210.html"><dt class="name">秋田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/5/3220.html"><dt class="name">横手</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/3/3310.html"><dt class="name">盛岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/3/3320.html"><dt class="name">宮古</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/3/3330.html"><dt class="name">大船渡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/6/3510.html"><dt class="name">山形</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/6/3520.html"><dt class="name">米沢</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/6/3530.html"><dt class="name">酒田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/6/3540.html"><dt class="name">新庄</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/4/3410.html"><dt class="name">仙台</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/4/3420.html"><dt class="name">白石</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/7/3610.html"><dt class="name">福島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/7/3620.html"><dt class="name">小名浜</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/7/3630.html"><dt class="name">若松</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/8/4010.html"><dt class="name">水戸</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/8/4020.html"><dt class="name">土浦</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/9/4110.html"><dt class="name">宇都宮</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/9/4120.html"><dt class="name">大田原</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/13/4410.html"><dt class="name">東京</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/13/4420.html"><dt class="name">大島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/13/4430.html"><dt class="name">八丈島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/13/4440.html"><dt class="name">父島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/12/4510.html"><dt class="name">千葉</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/12/4520.html"><dt class="name">銚子</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/12/4530.html"><dt class="name">館山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/11/4310.html"><dt class="name">さいたま</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/11/4320.html"><dt class="name">熊谷</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/11/4330.html"><dt class="name">秩父</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/10/4210.html"><dt class="name">前橋</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/10/4220.html"><dt class="name">みなかみ</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/19/4910.html"><dt class="name">甲府</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/19/4920.html"><dt class="name">河口湖</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/20/4810.html"><dt class="name">長野</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/20/4820.html"><dt class="name">松本</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/20/4830.html"><dt class="name">飯田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/15/5410.html"><dt class="name">新潟</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/15/5420.html"><dt class="name">長岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/15/5430.html"><dt class="name">高田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/15/5440.html"><dt class="name">相川</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/22/5010.html"><dt class="name">静岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/22/5020.html"><dt class="name">網代</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/22/5030.html"><dt class="name">三島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/22/5040.html"><dt class="name">浜松</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/16/5510.html"><dt class="name">富山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/16/5520.html"><dt class="name">伏木</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/17/5610.html"><dt class="name">金沢</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/17/5620.html"><dt class="name">輪島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/21/5210.html"><dt class="name">岐阜</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/21/5220.html"><dt class="name">高山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/23/5110.html"><dt class="name">名古屋</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/23/5120.html"><dt class="name">豊橋</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/18/5710.html"><dt class="name">福井</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/18/5720.html"><dt class="name">敦賀</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/25/6010.html"><dt class="name">大津</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/25/6020.html"><dt class="name">彦根</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/24/5310.html"><dt class="name">津</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/24/5320.html"><dt class="name">尾鷲</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/26/6110.html"><dt class="name">京都</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/26/6120.html"><dt class="name">舞鶴</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/27/6200.html"><dt class="name">大阪</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/28/6310.html"><dt class="name">神戸</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/28/6320.html"><dt class="name">豊岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/30/6510.html"><dt class="name">和歌山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/30/6520.html"><dt class="name">潮岬</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/31/6910.html"><dt class="name">鳥取</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/31/6920.html"><dt class="name">米子</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/33/6610.html"><dt class="name">岡山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/33/6620.html"><dt class="name">津山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/36/7110.html"><dt class="name">徳島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/36/7120.html"><dt class="name">日和佐</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/32/6810.html"><dt class="name">松江</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/32/6820.html"><dt class="name">浜田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/32/6830.html"><dt class="name">西郷</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/37/7200.html"><dt class="name">高松</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/34/6710.html"><dt class="name">広島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/34/6720.html"><dt class="name">庄原</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/39/7410.html"><dt class="name">高知</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/39/7420.html"><dt class="name">室戸岬</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/39/7430.html"><dt class="name">清水</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/38/7310.html"><dt class="name">松山</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/38/7320.html"><dt class="name">新居浜</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/38/7330.html"><dt class="name">宇和島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/35/8110.html"><dt class="name">下関</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/35/8120.html"><dt class="name">山口</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/35/8130.html"><dt class="name">柳井</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/35/8140.html"><dt class="name">萩</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/44/8310.html"><dt class="name">大分</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/44/8320.html"><dt class="name">中津</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/44/8330.html"><dt class="name">日田</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/44/8340.html"><dt class="name">佐伯</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/40/8210.html"><dt class="name">福岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/40/8220.html"><dt class="name">八幡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/40/8230.html"><dt class="name">飯塚</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/40/8240.html"><dt class="name">久留米</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/43/8610.html"><dt class="name">熊本</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/43/8620.html"><dt class="name">阿蘇乙姫</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/43/8630.html"><dt class="name">牛深</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/43/8640.html"><dt class="name">人吉</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/45/8710.html"><dt class="name">宮崎</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/45/8720.html"><dt class="name">延岡</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/45/8730.html"><dt class="name">都城</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/45/8740.html"><dt class="name">高千穂</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/41/8510.html"><dt class="name">佐賀</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/41/8520.html"><dt class="name">伊万里</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/42/8410.html"><dt class="name">長崎</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/42/8420.html"><dt class="name">佐世保</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/42/8430.html"><dt class="name">厳原</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/42/8440.html"><dt class="name">福江</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/46/1000.html"><dt class="name">名瀬</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/46/8810.html"><dt class="name">鹿児島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/46/8820.html"><dt class="name">鹿屋</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/46/8830.html"><dt class="name">種子島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9110.html"><dt class="name">那覇</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9120.html"><dt class="name">名護</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9130.html"><dt class="name">久米島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9200.html"><dt class="name">南大東</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9300.html"><dt class="name">宮古島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9410.html"><dt class="name">石垣島</dt></a>
    <a href="https://weather.yahoo.co.jp/weather/jp/47/9420.html"><dt class="name">与那国島</dt></a>
</div>
"""

# BeautifulSoup で解析
soup = BeautifulSoup(html_fragment, "html.parser")

# データ格納用
weather_data = {}

# <a> タグを走査
for a_tag in soup.find_all("a", href=True):
    href = a_tag["href"]
    dt_tag = a_tag.find("dt", class_="name")

    if dt_tag and href:
        # URL から地域コードと市町村コードを抽出
        parts = href.split("/")
        if len(parts) >= 6:
            region_code = parts[-2]  # 例: "1a"
            city_code = parts[-1].replace(".html", "")  # 例: "1100"
            city_name = dt_tag.text.strip()  # 市町村名

            # 県名を取得
            prefecture = prefecture_mapping.get(region_code, "不明")

            # JSON データ構造の作成
            if prefecture not in weather_data:
                weather_data[prefecture] = {}
            if region_code not in weather_data[prefecture]:
                weather_data[prefecture][region_code] = {}

            # 市町村データを格納
            weather_data[prefecture][region_code][city_name] = city_code

# JSON 出力
json_output = json.dumps(weather_data, ensure_ascii=False, indent=4)
print(json_output)

# JSON をファイルに保存
with open("prefecture_city_mapping.json", "w", encoding="utf-8") as f:
    f.write(json_output)
