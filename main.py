import os
from flask import Flask, request
import requests

app = Flask(__name__)

# Securely grabs your hidden Discord URL from Render's settings
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    # 1. Safely handle the data even if PGSharp sends it as plain text/test ping
    pg_data = request.get_json(silent=True)

    # 2. If it's a test connection ping, pg_data will be empty or text
    if not pg_data:
        # Get the raw text if it wasn't JSON
        raw_text = request.data.decode("utf-8") if request.data else "Test Ping"
        print(f"Received Test Connection: {raw_text}")
        message_content = "✅ **PGSharp Test Connection Successful!** Your server is online."
    else:
        # It's real Pokémon data!
        print(f"Received Data: {pg_data}")
        message_content = f"📍 **Spawn Detected!**\nData: {pg_data}"

    # 3. Forward the message to Discord
    if DISCORD_WEBHOOK_URL:
        discord_payload = {"content": message_content}
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    else:
        print("Error: DISCORD_URL environment variable is missing!")

    # Return a 200 OK so PGSharp knows it succeeded
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
