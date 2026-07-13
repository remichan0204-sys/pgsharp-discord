import os
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    pg_data = request.get_json(silent=True) or {}

    # Gather the primary top-level layout blocks
    main_keys = list(pg_data.keys())

    # Look one step deeper into the "account" block if it exists
    account_keys = []
    if "account" in pg_data and isinstance(pg_data["account"], dict):
        account_keys = list(pg_data["account"].keys())

    # Build a simple text summary of your file's layout
    debug_message = (
        "🔬 **Diagnostic Reset Triggered**\n\n"
        f"**Top-Level Keys found:** `{main_keys}`\n\n"
        f"**Keys inside 'account' block:** `{account_keys[:15]}`..."
    )

    discord_payload = {"content": debug_message}

    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
