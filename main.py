import os
from flask import Flask, request
import requests

app = Flask(__name__)

# This securely grabs your hidden Discord URL from Render's settings
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    pg_data = request.json
    print("Incoming data:", pg_data)

    message_content = f"📍 **Spawn Detected!**\nData: {pg_data}"
    discord_payload = {"content": message_content}

    # Only send if the environment variable was configured properly
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    else:
        print("Error: DISCORD_URL environment variable is missing!")

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
