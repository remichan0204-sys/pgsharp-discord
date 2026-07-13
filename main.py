import os
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    # 1. Grab the completely raw, untouched data bytes from your phone
    raw_bytes = request.data
    data_length = len(raw_bytes) if raw_bytes else 0

    # 2. Try to pull out any readable words/text hidden inside the raw packet
    extracted_text = ""
    if data_length > 0:
        # Extract letters, numbers, and symbols from the binary data
        readable_chars = [chr(b) for b in raw_bytes if 32 <= b <= 126]
        extracted_text = "".join(readable_chars)[:300]  # Grab the first 300 characters

    # 3. Create a raw debugger alert for Discord
    debug_message = (
        "🛰️ **Raw Stream Packet Caught!**\n"
        f"• **Total Packet Size:** `{data_length}` bytes\n"
        f"• **First 300 Text Snippets:** `{extracted_text}`"
    )

    discord_payload = {"content": debug_message}

    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
