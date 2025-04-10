import pyautogui
import time
import pygetwindow as gw
import pyperclip  # クリップボード経由で入力するため

# 反応するトリガーワード（リスト化）
TRIGGER_WORDS = ["音楽操作", "次の曲", "前の曲", "音楽検索 "]


def activate_amazon_music():
    """Amazon Music のウィンドウをアクティブにする。ただし最小化されている場合のみ復元"""
    windows = gw.getWindowsWithTitle("Amazon Music")
    if windows:
        win = windows[0]
        if win.isMinimized:  # 最小化されている場合のみ復元
            win.restore()
        win.activate()
        time.sleep(1)  # ウィンドウが前面になるまで待機
        return True
    return False


def search_music(query):
    """Amazon Music アプリで楽曲を検索する"""
    if not activate_amazon_music():
        return "Amazon Music ウィンドウが見つかりません。手動でアプリを開いてください。"

    # 検索バーの位置をクリックしてアクティブにする
    time.sleep(1)
    pyautogui.click(1800, 50)  # 座標の調整が必要かも

    time.sleep(1)  # 少し待機
    pyautogui.hotkey("ctrl", "a")  # 既存の入力を全選択
    pyautogui.press("backspace")  # 削除

    # クリップボードを使用して入力
    pyperclip.copy(query)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)

    pyautogui.press("enter")  # 検索実行

    # 検索結果を待つ
    time.sleep(5)

    # 再生ボタンをクリック（座標を調整）
    pyautogui.click(1700, 400)
    time.sleep(0.5)
    return f"🔍 『{query}』 を検索、再生しました。"


def play_pause():
    """再生 / 一時停止"""
    pyautogui.press("space")
    return "🎵 音楽を再生 / 一時停止しました。"


def next_track():
    """次の曲へ"""
    pyautogui.hotkey("right")
    return "⏭️ 次の曲にスキップしました。"


def prev_track():
    """前の曲へ"""
    pyautogui.hotkey("left")
    return "⏮️ 前の曲に戻しました。"


def handle_message(message):
    """メッセージ処理"""

    # まず、トリガーワードが含まれているかチェック
    if not any(message.startswith(word) for word in TRIGGER_WORDS):
        return None  # 関係ないメッセージには反応しない

    if not activate_amazon_music():
        return "Amazon Music ウィンドウが見つかりません。手動でアプリを開いてください。"

    if message == "音楽操作":
        return play_pause()
    elif message == "次の曲":
        return next_track()
    elif message == "前の曲":
        return prev_track()
    elif message.startswith("音楽検索 "):
        song_name = message.replace("音楽検索 ", "").strip()
        return search_music(song_name)
    return None


def register_plugin():
    """プラグイン登録用関数"""
    return {"name": "Amazon Music Controller", "on_message": handle_message}
