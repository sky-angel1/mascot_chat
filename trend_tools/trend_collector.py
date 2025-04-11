import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import logging
from deep_translator import GoogleTranslator

logging.basicConfig(level=logging.INFO)


class TrendCollector:
    def __init__(self):
        self.trend_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "trending_words": [],
            "topics": {},
        }
        self.spotify_api_key = os.getenv("SPOTIFY_API_KEY")  # Spotify APIキー
        self.tmdb_api_key = os.getenv("TMDB_API_KEY")  # TMDb APIキー

    def fetch_music_trends(self):
        logging.info("Fetching music trends...")
        url = "https://www.udiscovermusic.jp/music/news"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = []
            for article in soup.select(".mvp-blog-story-text h2"):
                title = article.text.strip()
                try:
                    translated_title = GoogleTranslator(
                        source="ja", target="en"
                    ).translate(title)
                except Exception as e:
                    logging.error(f"Translation error for title '{title}': {e}")
                    translated_title = title
                trends.append(translated_title)
            self.trend_data["topics"]["音楽"] = trends
            self.trend_data["trending_words"].extend(trends)
            logging.info(f"Music trends: {trends}")
        logging.info("Music trends fetched successfully.")

    def fetch_movie_trends(self):
        logging.info("Fetching movie trends...")
        url = "https://uscinemas.jp/now-showing/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = []
            for movie_box in soup.select(".now-showing-box"):
                title = (
                    movie_box.select_one("h3").text.strip()
                    if movie_box.select_one("h3")
                    else ""
                )
                try:
                    translated_title = GoogleTranslator(
                        source="ja", target="en"
                    ).translate(title)
                except Exception as e:
                    logging.error(f"Translation error for title '{title}': {e}")
                    translated_title = title
                trends.append(translated_title)

            self.trend_data["topics"]["映画"] = trends
            self.trend_data["trending_words"].extend(trends)
            logging.info(f"Movie trends: {trends}")

        logging.info("Movie trends fetched successfully.")

    def fetch_wikipedia_trends(self):
        logging.info("Fetching Wikipedia trends...")
        url = "https://ja.wikipedia.org/wiki/Portal:今日の出来事"
        try:
            response = requests.get(url)
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logging.error(f"Wikipedia page not found: {url}")
                return
            else:
                logging.error(f"Error fetching data from {url}: {e}")
                return
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = [item.text.strip() for item in soup.select(".mw-headline")]
            self.trend_data["topics"]["Wikipedia"] = trends
            self.trend_data["trending_words"].extend(trends)
        logging.info("Wikipedia trends fetched successfully.")

    def fetch_trend_words(self):
        logging.info("Fetching trend words from Yahoo Chiebukuro...")
        url = "https://chiebukuro.yahoo.co.jp/?tab=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = []
            for question in soup.select(
                ".ClapLv2TopListItem_Chie-ListItem__Question__11BeL h2"
            ):
                title = question.text.strip()
                try:
                    translated_title = GoogleTranslator(
                        source="ja", target="en"
                    ).translate(title)
                except Exception as e:
                    logging.error(f"Translation error for title '{title}': {e}")
                    translated_title = title
                trends.append(translated_title)
            self.trend_data["topics"]["Yahoo知恵袋"] = trends
            self.trend_data["trending_words"].extend(trends)
            logging.info(f"Trend words: {trends}")

    def fetch_nhk_news_trends(self):
        logging.info("Fetching NHK news trends...")
        url = "https://www3.nhk.or.jp/news/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.encoding = (
                response.apparent_encoding
            )  # エンコーディングを明示的に設定
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = []
            for article in soup.select(".content--list li dl dd a"):
                title = (
                    article.select_one("em.title").text.strip()
                    if article.select_one("em.title")
                    else ""
                )

                # タイトルを英語に翻訳
                try:
                    translated_title = GoogleTranslator(
                        source="ja", target="en"
                    ).translate(title)
                except Exception as e:
                    logging.error(f"Translation error for title '{title}': {e}")
                    translated_title = title  # 翻訳に失敗した場合は元のタイトルを使用

                trends.append(translated_title)

            self.trend_data["topics"]["NHKニュース"] = trends
            self.trend_data["trending_words"].extend(trends)
            logging.info(f"NHK news trends: {trends}")

        logging.info("NHK news trends fetched successfully.")

    def fetch_toyokeizai_trends(self):
        logging.info("Fetching Toyo Keizai trends...")
        url = "https://toyokeizai.net/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # HTTPエラーを発生させる
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            trends = []
            for item in soup.select(".ranking-list.hourly.clearfix ul li"):
                title_tag = item.select_one(".ttl a span.title")
                title = title_tag.text.strip() if title_tag else ""

                # タイトルを英語に翻訳
                try:
                    translated_title = GoogleTranslator(
                        source="ja", target="en"
                    ).translate(title)
                except Exception as e:
                    logging.error(f"Translation error for title '{title}': {e}")
                    translated_title = title  # 翻訳に失敗した場合は元のタイトルを使用

                trends.append(translated_title)

            self.trend_data["topics"]["東洋経済"] = trends
            self.trend_data["trending_words"].extend(trends)
            logging.info(f"Toyo Keizai trends: {trends}")

        logging.info("Toyo Keizai trends fetched successfully.")

    def save_trends(self, file_path):
        logging.info(f"Saving trends to {file_path}...")
        # 出力先フォルダが存在しない場合は作成
        output_dir = os.path.dirname(file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        logging.info(f"Output directory ensured: {output_dir}")

        # 翻訳を収集時に行うため、保存時にはそのまま保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.trend_data, f, ensure_ascii=False, indent=2)
        logging.info("Trends saved successfully.")


def translate_to_english(data):
    try:
        return [
            GoogleTranslator(source="ja", target="en").translate(item) for item in data
        ]
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return data


if __name__ == "__main__":
    collector = TrendCollector()
    collector.fetch_music_trends()
    collector.fetch_movie_trends()
    collector.fetch_wikipedia_trends()
    collector.fetch_trend_words()
    collector.fetch_nhk_news_trends()
    collector.fetch_toyokeizai_trends()
    collector.save_trends("../chat_data/trend_data.json")
