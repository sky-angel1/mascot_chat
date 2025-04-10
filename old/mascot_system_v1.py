import sys
import os
import time
import json
import requests
import random
import threading
import re
import importlib.util
from pathlib import Path
from datetime import datetime
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from deep_translator import GoogleTranslator

# プラグインが格納されるフォルダを指定
PLUGIN_FOLDER = Path(__file__).parent / "plugins"

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QLabel,
        QWidget,
        QTextEdit,
        QVBoxLayout,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSplitter,  # 追加
    )
    from PyQt6.QtGui import QPixmap, QFont
    from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# 設定定数
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
CONVERSATION_HISTORY_FILE = BASE_DIR / "conversation_history.json"
IMAGE_DIR = BASE_DIR / "assets"
MAX_HISTORY_ENTRIES = 100
EXIT_KEYWORDS = ["exit", "bye", "quit", "ばいばい", "さようなら", "またあとで"]
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_KEYWORDS = ["天気", "weather", "気温"]


class SignalEmitter(QObject):
    update_requested = pyqtSignal(str, str)  # (message_type, content)


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}


# アプリケーションの起動前に設定を読み込む例:
config = load_config()
weather_api_key = config.get("weather_api_key")
if weather_api_key:
    os.environ["WEATHER_API_KEY"] = weather_api_key


class Mascot(QWidget):
    def __init__(self):
        super().__init__()
        self.emitter = SignalEmitter()
        self.initUI()
        self._setup_timers()
        self._current_expression = "normal"

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFont(QFont("メイリオ", 10))

        # 画像リソースの読み込み
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
        # ランダム移動タイマー
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._random_move)
        self.move_timer.start(30000)

        # 瞬きタイマー
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


class ChatInterface(QWidget):
    def __init__(self, mascot):
        super().__init__()
        self.mascot = mascot
        self.emitter = mascot.emitter
        self.config = load_config()
        self.weather_interval = int(self.config.get("weather_interval", 600))
        self.default_location = self.config.get("default_location", "Tokyo")
        self.last_weather_update = {}
        self.cached_weather_info = {}

        # Blenderbot‑3B の初期化
        self.tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-3B")
        self.model = BlenderbotForConditionalGeneration.from_pretrained(
            "facebook/blenderbot-3B"
        )
        self.model_lock = threading.Lock()

        self.initUI()
        self._load_history()
        self._setup_connections()

        self.plugins = self.load_plugins()

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(500, 600)
        layout = QVBoxLayout()

        # タイトルバー
        self.title_bar = QLabel(" Virtual Mascot Chat ")
        self.title_bar.setStyleSheet("background: rgba(100,100,100,0.5); color: white;")
        self.title_bar.mousePressEvent = self._start_move
        self.title_bar.mouseMoveEvent = self._move_window
        layout.addWidget(self.title_bar)

        # 凡例トグルボタン
        self.legend_toggle_btn = QPushButton("凡例表示")
        self.legend_toggle_btn.clicked.connect(self.toggle_legend)
        layout.addWidget(self.legend_toggle_btn)

        # QSplitter を使ってチャット表示と入力欄を可変サイズにする
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background: rgba(255,255,255,0.9);")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("メッセージを入力...")
        self.input_field.returnPressed.connect(self._process_input)
        self.splitter.addWidget(self.chat_display)
        self.splitter.addWidget(self.input_field)
        # splitter の初期比率（任意調整可能）
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        layout.addWidget(self.splitter)

        # 凡例パネル（初期は非表示）
        self.legend_panel = QTextEdit()
        self.legend_panel.setReadOnly(True)
        self.legend_panel.setStyleSheet("background: rgba(240,240,240,0.9);")
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
            "　・日本天気予報：天気予報+半角SP+都市名\n"
            "　・現在の天気情報：都市名+の天気\n"
            "―――――――――――――――――――――――"
        )
        self.legend_panel.setVisible(False)  # 非表示に設定
        layout.addWidget(self.legend_panel)

        self.setLayout(layout)

    def toggle_legend(self):
        # 凡例パネルの表示／非表示を切り替え、ボタンラベルを更新
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

        if any(kw in user_input for kw in EXIT_KEYWORDS):
            QApplication.quit()

        self.input_field.clear()
        self.mascot.handle_expression(user_input)

        # プラグイン処理
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
                f"[{datetime.now().strftime('%H:%M')}] マスコット (プラグイン): {plugin_response}\n",
            )
        else:
            threading.Thread(target=self._generate_response, args=(user_input,)).start()

    def _extract_location(self, text):
        match = re.search(r"(.+?)の天気", text)
        if match:
            return match.group(1).strip()
        match_en = re.search(r"weather in ([A-Za-z ]+)", text)
        if match_en:
            return match_en.group(1).strip()
        return self.default_location

    def _get_weather(self, location):
        now = time.time()
        if location in self.last_weather_update:
            if now - self.last_weather_update[location] < self.weather_interval:
                return self.cached_weather_info[location]
        try:
            if re.search(r"[^\x00-\x7F]", location):
                location_query = GoogleTranslator(source="ja", target="en").translate(
                    location
                )
            else:
                location_query = location

            weather_api_key = self.config.get("weather_api_key")
            if not weather_api_key:
                raise ValueError("APIキーが設定されていません")

            params = {
                "q": location_query,
                "appid": weather_api_key,
                "units": "metric",
                "lang": "ja",
            }
            response = requests.get(WEATHER_API_URL, params=params)
            data = response.json()
            weather_info = (
                f"{data['name']}の天気: {data['weather'][0]['description']}\n"
                f"気温: {data['main']['temp']}℃ / 湿度: {data['main']['humidity']}%"
            )
            self.cached_weather_info[location] = weather_info
            self.last_weather_update[location] = now
            return weather_info

        except Exception as e:
            return f"天気情報の取得に失敗: {str(e)}"

    def _generate_response(self, user_input):
        try:
            if any(kw in user_input for kw in WEATHER_KEYWORDS):
                location = self._extract_location(user_input)
                weather_info = self._get_weather(location)
                self.emitter.update_requested.emit(
                    "new_message", f"[天気情報] {location}: {weather_info}"
                )
                return

            translated = GoogleTranslator(source="ja", target="en").translate(
                user_input
            )
            inputs = self.tokenizer(translated, return_tensors="pt")
            with self.model_lock:
                response_ids = self.model.generate(**inputs)
            response_en = self.tokenizer.decode(
                response_ids[0], skip_special_tokens=True
            )
            response = GoogleTranslator(source="en", target="ja").translate(response_en)

            self.emitter.update_requested.emit(
                "new_message",
                f"[{datetime.now().strftime('%H:%M')}] あなた\n👹: {user_input}\n"
                f"[{datetime.now().strftime('%H:%M')}] マスコット\n🐰: {response}\n"
                f"(最新の3Bパワーでお届けしています！)",
            )
            self._save_conversation(user_input, response)

        except Exception as e:
            self.emitter.update_requested.emit("error", str(e))

    def _append_message(self, message):
        current = self.chat_display.toPlainText().split("\n")
        if len(current) >= MAX_HISTORY_ENTRIES:
            current = current[-MAX_HISTORY_ENTRIES // 2 :]
        current.append(message)
        self.chat_display.setPlainText("\n".join(current))
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _load_history(self):
        try:
            if CONVERSATION_HISTORY_FILE.exists():
                with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    self.chat_display.setPlainText(
                        "\n".join(
                            [
                                f"[{entry['time']}] あなた: {entry['input']}\n[{entry['time']}] マスコット: {entry['response']}"
                                for entry in history
                            ]
                        )
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


def load_plugins():
    plugins = []
    for file in PLUGIN_FOLDER.glob("*.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "register_plugin"):
            plugin = module.register_plugin()
            plugins.append(plugin)
            print(f"プラグイン {plugin['name']} を登録しました。")
    return plugins


if __name__ == "__main__":
    if not PYQT_AVAILABLE:
        print("PyQt6がインストールされていません")
        sys.exit(1)

    app = QApplication(sys.argv)
    mascot = Mascot()
    mascot.show()
    chat_ui = ChatInterface(mascot)
    chat_ui.show()
    sys.exit(app.exec())
