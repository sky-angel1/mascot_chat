from deep_translator import GoogleTranslator

try:
    translated = GoogleTranslator(source="ja", target="en").translate("こんにちは")
    print(f"Translated text: {translated}")
except Exception as e:
    print(f"Translation error: {e}")
