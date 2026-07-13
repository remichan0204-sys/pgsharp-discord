import os
import io
import json
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    raw_bytes = request.data
    data_length = len(raw_bytes) if raw_bytes else 0

    # 1. Handle Empty Test Connection Ping
    if data_length == 0:
        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json={
                "embeds": [{
                    "title": "✅ PGSharp Test Connection Successful!",
                    "description": "Cloud server is live. Now log out and log back in to dump your profile!",
                    "color": 65280
                }]
            })
        return "OK", 200

    # 2. Handle Massive Profile Dumps (3.7MB+)
    # We turn the raw payload directly into a file stream to bypass Discord limits
    file_stream = io.BytesIO(raw_bytes)
    file_stream.seek(0)

    if DISCORD_WEBHOOK_URL:
        # Create a text prompt for Discord
        payload_data = {
            "content": f"📦 **Massive Profile Data Dump Received!**\n• **Packet Size:** `{data_length:,}` bytes (~{round(data_length/1024/1024, 2)} MB)\n• *Your full inventory is attached below as a readable text file!*"
        }
        
        # Send it to Discord as a file attachment named 'profile_dump.json'
        requests.post(
            DISCORD_WEBHOOK_URL,
            data=payload_data,
            files={"file": ("profile_dump.json", file_stream, "application/json")}
        )

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
