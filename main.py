import os
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    pg_data = request.get_json(silent=True) or {}

    # Base payload for Discord
    discord_payload = {}

    # Check if this is a real Pokémon spawn by looking for latitude
    if "latitude" in pg_data and pg_data["latitude"] is not None:
        # Handle Real Pokemon Data Feed
        pokemon_id = pg_data.get("pokemon_id", "Unknown Pokemon")
        lat = pg_data["latitude"]
        lng = pg_data["longitude"]
        
        # Calculate IV Percentage safely
        atk = pg_data.get("individual_attack", 0)
        dfn = pg_data.get("individual_defense", 0)
        sta = pg_data.get("individual_stamina", 0)
        iv_total = atk + dfn + sta
        iv_percent = round((iv_total / 45) * 100) if iv_total <= 45 else iv_total
        
        level = pg_data.get("pokemon_level", "??")
        maps_link = f"https://google.com{lat},{lng}"
        
        discord_payload = {
            "embeds": [
                {
                    "title": f"⭐ Spawn Detected: ID {pokemon_id}",
                    "color": 16711680,  # Red
                    "fields": [
                        {"name": "📊 IV Percentage", "value": f"**{iv_percent}%**", "inline": True},
                        {"name": "⚔️ Level", "value": f"Lvl {level}", "inline": True},
                        {"name": "📍 Coordinates (Tap to Copy)", "value": f"`{lat}, {lng}`", "inline": False},
                    ],
                    "description": f"🔗 [Open in Google Maps]({maps_link})"
                }
            ]
        }
    else:
        # Handle Test Connection Pings (empty payload or missing coords)
        discord_payload = {
            "embeds": [
                {
                    "title": "✅ PGSharp Connection Successful!",
                    "description": "Your cloud server is live and listening for spawns.",
                    "color": 65280,  # Green
                }
            ]
        }

    # Send formatted embed to Discord
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
