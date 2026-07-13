import os
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


@app.route("/data", methods=["POST"])
def translate_and_send():
    pg_data = request.get_json(silent=True) or {}
    
    # Check if the packet contains account data
    if "account" in pg_data:
        # Check standard container slots or look for loose keys in the JSON dump
        pokemon_list = pg_data.get("pokemon", []) or pg_data.get("items", [])
        
        # If the structure is loose, check if the payload itself acts as a direct list wrapper
        if not pokemon_list and isinstance(pg_data, list):
            pokemon_list = pg_data

        special_pokemon = []

        # Scan the 6,000 lines for the keys found in your snippet!
        for mon in pokemon_list:
            if not isinstance(mon, dict):
                continue
                
            display = mon.get("pokemonDisplay", {})
            
            # Extract data using the exact keys from your VS Code snippet
            is_shiny = display.get("shiny") == True
            location_card = display.get("locationCard")
            has_bg = location_card is not None and location_card != 0 and location_card != "null"
            
            if is_shiny or has_bg:
                mon_id = mon.get("pokemonId", "Unknown")
                form_name = display.get("formName", "")
                cp = mon.get("cp", 0)
                
                # Format visual descriptions
                traits = []
                if is_shiny:
                    traits.append("✨ Shiny")
                if has_bg:
                    traits.append(f"🖼️ BG ({location_card})")
                    
                traits_text = " + ".join(traits)
                special_pokemon.append(f"• **ID {mon_id}** ({form_name}) - CP {cp} [{traits_text}]")

        # Package the collection overview text block
        if special_pokemon:
            report_text = "\n".join(special_pokemon[:30]) # Show top 30 to stay within Discord size rules
            if len(special_pokemon) > 30:
                report_text += f"\n*...and {len(special_pokemon) - 30} more special targets found!*"
        else:
            report_text = "No custom Shiny or Location Card profiles detected inside this snapshot loop."

        discord_payload = {
            "embeds": [
                {
                    "title": "🏆 Collector Vault Synced Successfully",
                    "color": 16753920, # Warm Gold
                    "description": report_text,
                    "footer": {"text": "24/7 PGSharp Inventory Sync Enabled"}
                }
            ]
        }

        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
