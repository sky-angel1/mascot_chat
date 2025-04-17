import sys
import json
import random
import threading
import importlib.util
from pathlib import Path
from datetime import datetime
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from deep_translator import GoogleTranslator
import logging
import random
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QTextEdit,
    QVBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSlider,
    QSizeGrip,
)
from PyQt6.QtGui import QPixmap, QFont, QKeyEvent, QTextCursor
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QThread

import threading
from trend_tools.trend_collector import TrendCollector
import torch

# 設定定数
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
CONVERSATION_HISTORY_FILE = BASE_DIR / "conversation_history.json"
IMAGE_DIR = BASE_DIR / "assets"
MAX_HISTORY_ENTRIES = 100
EXIT_KEYWORDS = ["exit", "bye", "quit", "ばいばい", "さようなら", "またあとで"]

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class SignalEmitter(QObject):
    update_requested = pyqtSignal(str, str)  # (message_type, content)


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}


config = load_config()


class HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []  # 入力履歴リスト
        self.history_index = -1  # 現在の履歴インデックス（-1は未選択）

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            if self.history:
                if self.history_index == -1:
                    self.history_index = len(self.history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1
                self.setText(self.history[self.history_index])
                return
        elif event.key() == Qt.Key.Key_Down:
            if self.history and self.history_index != -1:
                if self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    self.setText(self.history[self.history_index])
                else:
                    self.history_index = -1
                    self.clear()
                return
        super().keyPressEvent(event)

    def add_to_history(self, text):
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
            if len(self.history) > 10:
                self.history.pop(0)
        self.history_index = -1


class Mascot(QWidget):
    def __init__(self):
        super().__init__()
        self.emitter = SignalEmitter()
        self.initUI()
        self._setup_timers()
        self._current_expression = "normal"
        self.show_mascot = True  # マスコットの表示状態を管理

        # バックグラウンドでトレンド情報を収集
        self._collect_trend_data()

    def _collect_trend_data(self):
        def collect_data():
            logging.info("Collecting trend data...")
            collector = TrendCollector()
            collector.fetch_nhk_news_trends()
            collector.fetch_toyokeizai_trends()
            collector.fetch_music_trends()
            collector.fetch_movie_trends()
            collector.fetch_trend_words()
            collector.save_trends("../chat_data/trend_data.json")
            logging.info("Trend data collection completed.")

        trend_thread = threading.Thread(target=collect_data, daemon=True)
        trend_thread.start()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFont(QFont("メイリオ", 12))
        self.expressions = {
            "normal": QPixmap(str(IMAGE_DIR / "mascot.png")),
            "happy": QPixmap(str(IMAGE_DIR / "mascot_happy.png")),
            "angry": QPixmap(str(IMAGE_DIR / "mascot_angry.png")),
            "blink": QPixmap(str(IMAGE_DIR / "mascot_blink.png")),
        }
        self.label = QLabel(self)
        self.label.setPixmap(self.expressions["normal"])
        self.resize(self.expressions["normal"].size())

    def _setup_timers(self):
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._random_move)
        self.move_timer.start(30000)
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._trigger_blink)
        self.blink_timer.start(15000)

    def _random_move(self):
        screen = QApplication.primaryScreen().availableGeometry()
        new_x = random.randint(0, screen.width() - self.width())
        new_y = random.randint(0, screen.height() - self.height())
        self.move(new_x, new_y)

    def _trigger_blink(self):
        if self._current_expression == "normal":
            self._change_expression("blink", 800)

    def _change_expression(self, expression, duration):
        self._current_expression = expression
        self.label.setPixmap(self.expressions[expression])
        QTimer.singleShot(duration, self._reset_expression)

    def _reset_expression(self):
        self._current_expression = "normal"
        self.label.setPixmap(self.expressions["normal"])

    def handle_expression(self, user_input):
        normalized = self._normalize_input(user_input)
        if "怒" in normalized:
            self._change_expression("angry", 1500)
        elif any(kw in normalized for kw in ["笑", "楽"]):
            self._change_expression("happy", 1500)
        elif "驚" in normalized or "びっくり" in normalized:
            self._change_expression("blink", 800)

    def _normalize_input(self, text):
        return text.translate(
            str.maketrans(
                "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ",
                "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
            )
        ).strip()


class ResponseGeneratorThread(QThread):
    response_generated = pyqtSignal(str, str)  # (user_input, response)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_input, tokenizer, model, model_lock):
        super().__init__()
        self.user_input = user_input
        self.tokenizer = tokenizer
        self.model = model
        self.model_lock = model_lock

    def run(self):
        try:
            logging.info(f"User input: {self.user_input}")
            logging.info(f"Input to translation: {self.user_input}")
            try:
                translated = GoogleTranslator(source="ja", target="en").translate(
                    self.user_input
                )
                logging.info(f"Translated input: {translated}")
            except Exception as e:
                logging.error(f"Error during translation (JA to EN): {e}")
                self.error_occurred.emit(
                    "翻訳エラー: 日本語から英語への翻訳に失敗しました。"
                )
                return

            try:
                # inputs = self.tokenizer(translated, return_tensors="pt")
                inputs = self.tokenizer(
                    translated, return_tensors="pt", truncation=True, max_length=128
                )

                with self.model_lock:
                    response_ids = self.model.generate(
                        **inputs,
                        max_length=100,
                        temperature=0.9,
                        top_k=50,
                        top_p=0.95,
                        do_sample=True,
                    )
                response_en = self.tokenizer.decode(
                    response_ids[0], skip_special_tokens=True
                )
                logging.info(f"Generated response (EN): {response_en}")
            except Exception as e:
                logging.error(f"Error during model response generation: {e}")
                self.error_occurred.emit(
                    "モデル応答生成エラー: 応答生成に失敗しました。"
                )
                return

            try:
                response = GoogleTranslator(source="en", target="ja").translate(
                    response_en
                )
                logging.info(f"Translated response (JA): {response}")
                self.response_generated.emit(self.user_input, response)
            except Exception as e:
                logging.error(f"Error during translation (EN to JA): {e}")
                self.error_occurred.emit(
                    "翻訳エラー: 英語から日本語への翻訳に失敗しました。"
                )
        except Exception as e:
            logging.error(f"Error during response generation: {e}")
            self.error_occurred.emit(str(e))


class ChatInterface(QWidget):
    def __init__(self, mascot):
        super().__init__()
        self.mascot = mascot
        self.emitter = mascot.emitter
        self.config = load_config()
        self.initUI()
        self._load_history()
        self._setup_connections()
        self.plugins = self.load_plugins()
        self.tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-3B")
        self.model = BlenderbotForConditionalGeneration.from_pretrained(
            "facebook/blenderbot-3B"
        )
        self.model_lock = threading.Lock()
        self.is_minimized = False  # 最小化状態を管理

    def load_plugins(self):
        plugins = []
        plugin_folder = Path(__file__).parent / "plugins"
        for file in plugin_folder.glob("*.py"):
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register_plugin"):
                plugin = module.register_plugin()
                plugins.append(plugin)
                print(f"プラグイン {plugin['name']} を登録しました。")
        return plugins

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(500, 650)
        layout = QVBoxLayout()

        self.title_bar = QLabel(" Virtual Mascot Chat ")
        self.title_bar.setStyleSheet("background: rgba(100,100,100,0.5); color: white;")
        self.title_bar.mousePressEvent = self._start_move
        self.title_bar.mouseMoveEvent = self._move_window
        layout.addWidget(self.title_bar)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(75)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        layout.addWidget(self.opacity_slider)

        self.legend_toggle_btn = QPushButton("凡例表示")
        self.legend_toggle_btn.clicked.connect(self.toggle_legend)
        layout.addWidget(self.legend_toggle_btn)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background: rgba(255,255,255,0.9);")
        self.chat_display.setFont(QFont("メイリオ", 12))

        self.input_field = HistoryLineEdit()
        self.input_field.setPlaceholderText("メッセージを入力...")
        self.input_field.returnPressed.connect(self._process_input)
        self.input_field.setFont(QFont("メイリオ", 12))

        self.splitter.addWidget(self.chat_display)
        self.splitter.addWidget(self.input_field)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter)

        self.legend_panel = QTextEdit()
        self.legend_panel.setReadOnly(True)
        self.legend_panel.setStyleSheet("background: rgba(255,255,255,0.9);")
        self.legend_panel.setText(
            "―――――――――――――――――――――――\n"
            "【プラグイン操作凡例】\n\n"
            "■ アマゾン音楽操作\n"
            "　・検索：音楽検索+半角SP+検索名\n"
            "　・再生/一時停止：音楽操作\n"
            "　・次曲送り：次の曲\n"
            "　・前曲戻り：前の曲\n\n"
            "■ その他の操作\n"
            "　・検索：検索+半角SP+検索内容\n"
            "　・世界時刻：時刻+半角SP+都市名(外国主要都市)\n"
            "　・天気予報：天気予報+半角SP+都市名(県庁所在地他)\n"
            "―――――――――――――――――――――――"
        )
        self.legend_panel.setVisible(False)
        layout.addWidget(self.legend_panel)

        # 最小化/復元ボタン
        self.minimize_button = QPushButton("最小化")
        self.minimize_button.clicked.connect(self.toggle_minimize)
        layout.addWidget(self.minimize_button)

        self.restore_button = QPushButton("復元")
        self.restore_button.clicked.connect(self.toggle_minimize)
        self.restore_button.setVisible(False)  # 初期状態では非表示
        layout.addWidget(self.restore_button)

        # サイズグリップを追加
        self.size_grip = QSizeGrip(self)
        layout.addWidget(
            self.size_grip,
            0,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
        )

        self.setLayout(layout)
        self.update_opacity(self.opacity_slider.value())

    def resizeEvent(self, event):
        # サイズグリップの位置を更新
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height(),
        )

    def toggle_minimize(self):
        if not self.is_minimized:
            self.original_geometry = self.geometry()  # 元のウィンドウサイズを保存
            self.setMinimumSize(0, 0)  # 最小サイズを無効化
            self.setGeometry(0, 0, 50, 100)  # 最小化したサイズ
            self.chat_display.setVisible(False)
            self.input_field.setVisible(False)
            self.legend_panel.setVisible(False)
            self.minimize_button.setVisible(False)
            self.restore_button.setVisible(True)
            self.is_minimized = True
            self.mascot.show_mascot = False  # マスコットを非表示
            self.mascot.hide()
        else:
            self.setGeometry(self.original_geometry)  # 元のサイズに復元
            self.setMinimumSize(500, 650)  # 最小サイズを復元
            self.chat_display.setVisible(True)
            self.input_field.setVisible(True)
            self.minimize_button.setVisible(True)
            self.restore_button.setVisible(False)
            self.is_minimized = False
            self.mascot.show_mascot = True  # マスコットを表示
            self.mascot.show()

    def update_opacity(self, value):
        alpha = value / 100.0
        chat_bg = f"background-color: rgba(255,255,255,{alpha});"
        input_bg = f"background-color: rgba(255,255,255,{alpha});"
        legend_bg = f"background-color: rgba(240,240,240,{alpha});"
        self.chat_display.setStyleSheet(chat_bg)
        self.input_field.setStyleSheet(input_bg)
        self.legend_panel.setStyleSheet(legend_bg)
        self.setStyleSheet(f"background-color: rgba(255,255,255,{alpha});")

    def toggle_legend(self):
        if self.legend_panel.isVisible():
            self.legend_panel.setVisible(False)
            self.legend_toggle_btn.setText("凡例表示")
        else:
            self.legend_panel.setVisible(True)
            self.legend_toggle_btn.setText("凡例非表示")

    def _setup_connections(self):
        self.emitter.update_requested.connect(self._handle_updates)

    def _handle_updates(self, msg_type, content):
        if msg_type == "new_message":
            self._append_message(content)
        elif msg_type == "error":
            QMessageBox.critical(self, "エラー", content)

    def _start_move(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.pos()

    def _move_window(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def _process_input(self):
        user_input = self.input_field.text().strip()
        if not user_input:
            return

        self.input_field.add_to_history(user_input)

        if any(kw in user_input for kw in EXIT_KEYWORDS):
            QApplication.quit()

        self.input_field.clear()
        self.mascot.handle_expression(user_input)

        plugin_response = None
        for plugin in self.plugins:
            if "on_message" in plugin:
                response = plugin["on_message"](user_input)
                if response:
                    plugin_response = response
                    break

        if plugin_response:
            self.emitter.update_requested.emit(
                "new_message",
                f"[{datetime.now().strftime('%H:%M')}] mascot(プラグイン): {plugin_response}\n",
            )
        else:
            self._start_response_thread(user_input)

    def _load_trend_data(self):
        try:
            with open("../chat_data/trend_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"トレンドデータの読み込みエラー: {e}")
            return {
                "topics": {
                    "NHKニュース": [],
                    "東洋経済": [],
                    "音楽": [],
                    "映画": [],
                    "Yahoo知恵袋": [],
                }
            }

    def _generate_dialog_prompt(self, translated_user_input, trend_data):
        import random

        def sample_trends(category, max_items=2):
            items = [x for x in trend_data["topics"].get(category, []) if x.strip()]
            return random.sample(items, min(len(items), max_items))

        all_categories = {
            "NHKニュース": "NHK",
            "東洋経済": "Toyo Keizai",
            "音楽": "Music",
            "映画": "Movies",
            "Yahoo知恵袋": "Yahoo Answers",
            "スポーツ": "Sports",
            "IT・テクノロジー": "Technology",
            "海外ニュース": "World News",
            "ゲーム": "Games"
        }

        selected_cats = random.sample(list(all_categories.items()), k=3)

        trend_lines = []
        for jp_cat, en_cat in selected_cats:
            trends = sample_trends(jp_cat)
            if trends:
                trend_lines.append(f"- {en_cat}: " + "; ".join(trends))

        # 🌟 Few-shot 会話例（改善効果大）
        example = [
            "Example:",
            "User: What's popular today?",
            "Assistant: According to recent trends, Lady Gaga's Coachella performance is the talk of the town!",
            "",
        ]

        prompt_lines = [
            "You are a friendly assistant having a conversation with a user.",
            "",
            "Here are some current trending topics (use them if relevant):",
            *trend_lines,
            "",
            *example,
            f"User: {translated_user_input}",
            "Assistant (please reply naturally, using trends only if helpful):"
        ]

        prompt = "\n".join(prompt_lines)
        return prompt[:700]  # 約150トークン程度に制限（モデルが反応しやすい）



    def _start_response_thread(self, user_input):
        self.original_user_input = user_input

        # ① ユーザー入力を翻訳（日本語→英語）
        try:
            translated_input = GoogleTranslator(source="ja", target="en").translate(
                user_input
            )
            logging.info(f"Translated user input: {translated_input}")
        except Exception as e:
            logging.error(f"Error translating user input: {e}")
            self._handle_response_error("ユーザー入力の翻訳に失敗しました。")
            return

        # ② トレンドデータを読み込み
        trend_data = self._load_trend_data()

        # ③ プロンプトを生成（翻訳済ユーザー入力 + トレンド）
        final_prompt = self._generate_dialog_prompt(translated_input, trend_data)
        logging.info(f"Final prompt input to model:\n{final_prompt}")

        # ④ 応答生成スレッドを起動
        self.response_thread = ResponseGeneratorThread(
            final_prompt, self.tokenizer, self.model, self.model_lock
        )
        self.response_thread.response_generated.connect(self._handle_generated_response)
        self.response_thread.error_occurred.connect(self._handle_response_error)
        self.response_thread.start()

    def _is_english(self, text):
        # 簡易的に英語かどうかを判定
        return all(ord(char) < 128 for char in text)

    def _handle_generated_response(self, user_input, response):
        # 日本語のユーザー入力と応答を表示
        self.emitter.update_requested.emit(
            "new_message",
            f"[{datetime.now().strftime('%H:%M')}] あなた\n👹:{self.original_user_input}\n"
            f"[{datetime.now().strftime('%H:%M')}] mascot\n🐰:{response}\n",
        )
        self._save_conversation(self.original_user_input, response)

    def _get_original_user_input(self, user_input):
        # ユーザー入力を元の日本語に戻す（翻訳前のデータを保持する仕組みを仮定）
        return getattr(self, "original_user_input", user_input)

    def _handle_response_error(self, error_message):
        self.emitter.update_requested.emit("error", error_message)

    def _append_message(self, message):
        self.chat_display.append(message)
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)

    def _load_history(self):
        try:
            if CONVERSATION_HISTORY_FILE.exists():
                with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for entry in history:
                        self.chat_display.append(
                            f"[{entry['time']}] あなた\n👹: {entry['input']}\n[{entry['time']}] mascot\n🐰: {entry['response']}"
                        )
        except Exception as e:
            print(f"履歴読み込みエラー: {e}")

    def _save_conversation(self, user_input, response):
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "input": user_input,
            "response": response,
        }
        try:
            history = []
            if CONVERSATION_HISTORY_FILE.exists():
                with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.append(entry)
            if len(history) > MAX_HISTORY_ENTRIES:
                history = history[-MAX_HISTORY_ENTRIES:]
            with open(CONVERSATION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"履歴保存エラー: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mascot = Mascot()
    mascot.show()
    chat_ui = ChatInterface(mascot)
    chat_ui.show()
    sys.exit(app.exec())
