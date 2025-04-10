import sys
import json
import random
import threading
import importlib.util
from pathlib import Path
from datetime import datetime
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from deep_translator import GoogleTranslator

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
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal, QSize

# 設定定数
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
CONVERSATION_HISTORY_FILE = BASE_DIR / "conversation_history.json"
IMAGE_DIR = BASE_DIR / "assets"
MAX_HISTORY_ENTRIES = 100
EXIT_KEYWORDS = ["exit", "bye", "quit", "ばいばい", "さようなら", "またあとで"]


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
            threading.Thread(target=self._generate_response, args=(user_input,)).start()

    def _generate_response(self, user_input):
        try:
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
                f"[{datetime.now().strftime('%H:%M')}] mascot\n🐰: {response}\n"
                f"(最新の3Bパワーでお届けします！)",
            )
            self._save_conversation(user_input, response)

        except Exception as e:
            self.emitter.update_requested.emit("error", str(e))

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
