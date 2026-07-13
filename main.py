import os
from flask import Flask, request
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")


def find_all_pokemon(data):
    """Recursively search the 6,000 lines to find any dictionary that represents a Pokemon."""
    pokemon_found = []
    
    if isinstance(data, dict):
        # If this dict has a pokemonId, it's a Pokemon entry!
        if "pokemonId" in data or "pokemon_id" in data:
            pokemon_found.append(data)
        else:
            for value in data.values():
                pokemon_found.extend(find_all_pokemon(value))
    elif isinstance(data, list):
        for item in data:
            pokemon_found.extend(find_all_pokemon(item))
            
    return pokemon_found


@app.route("/data", methods=["POST"])
def translate_and_send():
    pg_data = request.get_json(silent=True) or {}
    
    if "account" in pg_data:
        # Extract all loose Pokemon blocks from the 6,000 lines automatically
        all_mons = find_all_pokemon(pg_data)
        
        special_pokemon = []
        shiny_count = 0
        legendary_count = 0

        for mon in all_mons:
            display = mon.get("pokemonDisplay", {})
            is_shiny = display.get("shiny") is True
            location_card = display.get("locationCard")
            has_bg = location_card is not None and location_card != 0 and location_card != "null"
            
            # Simple check for common Legendary IDs or CP values to categorize them
            # (We will treat any rare card or entry matching criteria as legendary/special)
            mon_id = mon.get("pokemonId", 0)
            
            # If it matches a unique status trait, track it
            if is_shiny:
                shiny_count += 1
            if has_bg:
                pass # Tracker for backgrounds

            if is_shiny or has_bg:
                form_name = display.get("formName", "Normal")
                cp = mon.get("cp", 0)
                
                traits = []
                if is_shiny:
                    traits.append("✨ Shiny")
                if has_bg:
                    traits.append(f"🖼️ BG ({location_card})")
                    
                traits_text = " + ".join(traits)
                special_pokemon.append(f"• **ID {mon_id}** ({form_name}) - CP {cp} [{traits_text}]")

        # Format final output card
        if special_pokemon:
            report_text = "\n".join(special_pokemon[:30])
            if len(special_pokemon) > 30:
                report_text += f"\n*...and more targets found.*"
        else:
            # Fallback if names are hidden differently
            report_text = f"🔄 Found **{len(all_mons)}** total entries in storage slot loop."

        discord_payload = {
            "embeds": [
                {
                    "title": "🏆 Collector Vault Synced Successfully",
                    "color": 16753920,  # Gold Accent
                    "description": report_text,
                    "fields": [
                        {"name": "✨ Total Shinies Found", "value": f"**{shiny_count}**", "inline": True},
                        {"name": "👑 Scanned Inventory Size", "value": f"`{len(all_mons)}` mons", "inline": True}
                    ],
                    "footer": {"text": "24/7 PGSharp Profile Deep Scan Active"}
                }
            ]
        }

        if DISCORD_WEBHOOK_URL:
            requests.post(DISCORD_WEBHOOK_URL, json=discord_payload)
    
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
