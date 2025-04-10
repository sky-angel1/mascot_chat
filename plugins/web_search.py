import re
import requests
import urllib.parse

# Wikipedia REST API のエンドポイント（日本語版）
WIKIPEDIA_API_URL = "https://ja.wikipedia.org/api/rest_v1/page/summary/{}"


def search_wikipedia(query):
    """
    Wikipedia API を呼び出して、指定したキーワードの概要情報を取得する関数。
    検索不能の場合は Google/Yahoo 検索のURLを返す。
    """
    encoded_query = urllib.parse.quote(query)
    url = WIKIPEDIA_API_URL.format(encoded_query)

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data and data["extract"]:
                return data["extract"]
    except Exception:
        pass

    # Wikipedia で見つからない場合、Google/Yahoo 検索のURLを返す
    google_search_url = f"https://www.google.com/search?q={encoded_query}"
    yahoo_search_url = f"https://search.yahoo.co.jp/search?p={encoded_query}"
    return (
        f"「{query}」に関する情報は見つかりませんでした。\n"
        f"Google検索: {google_search_url}\n"
        f"Yahoo検索: {yahoo_search_url}"
    )


def on_message_received(message):
    """
    ユーザーからのメッセージを処理し、
    「検索 ○○」の形式なら Wikipedia検索を実行。
    他のプラグインが作動しないように strict match を使用。
    """
    match = re.fullmatch(r"検索\s+(.+)", message.strip())
    if match:
        query = match.group(1).strip()
        return search_wikipedia(query)
    return None  # 他のプラグインに影響を与えないよう None を返す


def register_plugin():
    """
    プラグインをシステムに登録する。
    """
    return {"name": "Wikipedia検索プラグイン", "on_message": on_message_received}
