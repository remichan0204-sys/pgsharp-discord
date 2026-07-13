import os
import json
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_URL")

# Pokemon name lookup (common ones + legendaries)
POKEMON_NAMES = {
    1:"Bulbasaur",4:"Charmander",7:"Squirtle",25:"Pikachu",
    133:"Eevee",143:"Snorlax",144:"Articuno",145:"Zapdos",146:"Moltres",
    149:"Dragonite",150:"Mewtwo",151:"Mew",152:"Chikorita",155:"Cyndaquil",
    158:"Totodile",175:"Togepi",196:"Espeon",197:"Umbreon",
    202:"Wobbuffet",212:"Scizor",214:"Heracross",216:"Teddiursa",
    228:"Houndour",234:"Stantler",238:"Smoochum",239:"Elekid",240:"Magby",
    241:"Miltank",242:"Blissey",243:"Raikou",244:"Entei",245:"Suicune",
    246:"Larvitar",249:"Lugia",250:"Ho-Oh",251:"Celebi",
    252:"Treecko",255:"Torchic",258:"Mudkip",
    351:"Castform",359:"Absol",371:"Bagon",374:"Beldum",
    380:"Latias",381:"Latios",382:"Kyogre",383:"Groudon",384:"Rayquaza",
    385:"Jirachi",386:"Deoxys",
    387:"Turtwig",390:"Chimchar",393:"Piplup",
    425:"Drifloon",427:"Buneary",431:"Glameow",
    438:"Bonsly",439:"Mime Jr",440:"Happiny",
    446:"Munchlax",447:"Riolu",448:"Lucario",
    479:"Rotom",480:"Uxie",481:"Mesprit",482:"Azelf",
    483:"Dialga",484:"Palkia",485:"Heatran",486:"Regigigas",
    487:"Giratina",488:"Cresselia",491:"Darkrai",492:"Shaymin",
    493:"Arceus",
    495:"Snivy",498:"Tepig",501:"Oshawott",
    570:"Zorua",571:"Zoroark",
    607:"Litwick",610:"Axew",
    638:"Cobalion",639:"Terrakion",640:"Virizion",
    641:"Tornadus",642:"Thundurus",643:"Reshiram",644:"Zekrom",
    645:"Landorus",646:"Kyurem",647:"Keldeo",648:"Meloetta",649:"Genesect",
    650:"Chespin",653:"Fennekin",656:"Froakie",
    669:"Flabébé",700:"Sylveon",
    716:"Xerneas",717:"Yveltal",718:"Zygarde",719:"Diancie",
    720:"Hoopa",721:"Volcanion",
    722:"Rowlet",725:"Litten",728:"Popplio",
    742:"Cutiefly",746:"Wishiwashi",
    772:"Type: Null",773:"Silvally",
    785:"Tapu Koko",786:"Tapu Lele",787:"Tapu Bulu",788:"Tapu Fini",
    789:"Cosmog",790:"Cosmoem",791:"Solgaleo",792:"Lunala",
    793:"Nihilego",800:"Necrozma",
    802:"Marshadow",807:"Zeraora",808:"Meltan",809:"Melmetal",
    810:"Grookey",813:"Scorbunny",816:"Sobble",
    888:"Zacian",889:"Zamazenta",890:"Eternatus",
    891:"Kubfu",892:"Urshifu",893:"Zarude",
    894:"Regieleki",895:"Regidrago",896:"Glastrier",897:"Spectrier",
    898:"Calyrex",
    906:"Sprigatito",909:"Fuecoco",912:"Quaxly",
    997:"Koraidon",998:"Miraidon",
    211:"Qwilfish",
}

def get_pokemon_name(pid):
    return POKEMON_NAMES.get(pid, f"#{pid}")

def iv_percent(atk, dfs, sta):
    return round((atk + dfs + sta) / 45 * 100)

def iv_grade(pct):
    if pct == 100: return "💎 Perfect"
    if pct >= 93:  return "⭐ Excellent"
    if pct >= 82:  return "✅ Good"
    if pct >= 66:  return "🆗 Fair"
    return "❌ Poor"

def format_timestamp(ms):
    if not ms or ms == 0:
        return "Unknown"
    try:
        return datetime.utcfromtimestamp(ms/1000).strftime("%Y-%m-%d %H:%M UTC")
    except:
        return "Unknown"


@app.route("/data", methods=["POST"])
def receive_pgsharp_data():
    raw_bytes = request.data
    data_length = len(raw_bytes) if raw_bytes else 0

    # ── Empty ping = test connection ──────────────────────────────
    if data_length == 0:
        send_embed({
            "title": "✅ PGSharp Hook Online",
            "description": "Connection test successful! You'll receive a full report on next login.",
            "color": 0x00FF00,
            "footer": {"text": "Smart PGSharp Bot • Test Ping"}
        })
        return "OK", 200

    # ── Parse JSON ────────────────────────────────────────────────
    try:
        pg_data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        print(f"JSON parse error: {e}")
        return "Parse Error", 400

    account = pg_data.get("account", {})
    if not account:
        return "No account data", 200

    # ── Extract account info ──────────────────────────────────────
    trainer    = account.get("name", "Unknown")
    team_id    = account.get("team", 0)
    team_name  = ["None", "Mystic 🔵", "Valor 🔴", "Instinct 🟡"][team_id] if team_id < 4 else "Unknown"
    max_poke   = account.get("maxPokemonStorage", 300)
    max_items  = account.get("maxItemStorage", 350)
    created_ms = account.get("creationTimeMs", 0)
    acc_created = format_timestamp(created_ms)

    stardust = 0
    coins    = 0
    for c in account.get("currencyBalance", []):
        if c.get("currencyType") == "STARDUST":  stardust = c.get("quantity", 0)
        if c.get("currencyType") == "POKECOIN":   coins    = c.get("quantity", 0)

    # ── PvP stats ─────────────────────────────────────────────────
    combat     = account.get("combatLog", {})
    season     = combat.get("currentSeasonResults", {})
    pvp_rank   = season.get("rank", 1)
    pvp_wins   = season.get("totalWins", 0)
    pvp_total  = season.get("totalBattles", 0)
    pvp_sd     = season.get("stardustEarned", 0)

    # ── Player stats ──────────────────────────────────────────────
    player   = pg_data.get("player", {})
    xp       = player.get("experience", 0)
    km       = player.get("kmWalked", 0)
    stops    = player.get("pokeStopVisits", 0)
    caught   = player.get("pokemonsCaptured", 0)
    evolved  = player.get("pokemonsEvolved", 0)
    hatched  = player.get("eggsHatched", 0)
    raids    = player.get("raidBattlesWon", 0)
    friends  = player.get("numFriends", 0)
    pdex     = player.get("pokedexSizeActual", 0)
    pdex_seen= player.get("pokedexSizeSeen", 0)

    # ── Items ─────────────────────────────────────────────────────
    items    = pg_data.get("items", [])
    item_map = {i["itemName"]: i["count"] for i in items}

    balls      = item_map.get("PokeBall",0) + item_map.get("GreatBall",0) + item_map.get("UltraBall",0)
    revives    = item_map.get("Revive",0) + item_map.get("MaxRevive",0)
    rare_candy = item_map.get("RareCandy",0)
    lure       = item_map.get("TroyDisk",0)
    golden_rzz = item_map.get("GoldenRazzBerry",0)
    star_piece = item_map.get("StarPiece",0)
    lucky_egg  = item_map.get("LuckyEgg",0)
    incubators = item_map.get("IncubatorBasic",0) + item_map.get("IncubatorSpecial",0)
    fusion_bk  = item_map.get("FusionResourceBlackKyurem",0)
    fusion_wk  = item_map.get("FusionResourceWhiteKyurem",0)

    # ── Pokemon analysis ──────────────────────────────────────────
    pokemons = pg_data.get("pokemons", [])
    real_mons   = [p for p in pokemons if not p.get("isEgg")]
    eggs        = [p for p in pokemons if p.get("isEgg")]
    shiny_mons  = [p for p in real_mons if p.get("pokemonDisplay",{}).get("shiny")]
    lucky_mons  = [p for p in real_mons if p.get("isLucky")]
    fav_mons    = [p for p in real_mons if p.get("favorite")]

    # Top CP
    sorted_cp  = sorted(real_mons, key=lambda x: x.get("cp",0), reverse=True)
    top5       = sorted_cp[:5]

    # IV stats
    perfect_iv = [p for p in real_mons
                  if p.get("individualAttack")==15
                  and p.get("individualDefense")==15
                  and p.get("individualStamina")==15]
    near_perf  = [p for p in real_mons
                  if iv_percent(p.get("individualAttack",0),
                                p.get("individualDefense",0),
                                p.get("individualStamina",0)) >= 93]

    # Egg distances
    egg_km = {}
    for e in eggs:
        dist = e.get("eggKmWalkedTarget", 0)
        egg_km[dist] = egg_km.get(dist, 0) + 1

    egg_str = "  ".join([f"{int(k)}km×{v}" for k,v in sorted(egg_km.items())]) or "None"

    # ── Build shiny detail list ───────────────────────────────────
    shiny_lines = []
    for p in shiny_mons:
        pid  = p.get("pokemonId", 0)
        name = get_pokemon_name(pid)
        cp   = p.get("cp", 0)
        atk  = p.get("individualAttack", 0)
        dfs  = p.get("individualDefense", 0)
        sta  = p.get("individualStamina", 0)
        pct  = iv_percent(atk, dfs, sta)
        nick = p.get("nickname", "")
        nick_str = f' "{nick}"' if nick else ""
        shiny_lines.append(f"✨ **{name}**{nick_str} — CP {cp} | IV {atk}/{dfs}/{sta} ({pct}%) {iv_grade(pct)}")

    shiny_block = "\n".join(shiny_lines) if shiny_lines else "*No shinies found*"

    # ── Build top CP list ─────────────────────────────────────────
    top_lines = []
    for i, p in enumerate(top5, 1):
        pid  = p.get("pokemonId", 0)
        name = get_pokemon_name(pid)
        cp   = p.get("cp", 0)
        atk  = p.get("individualAttack", 0)
        dfs  = p.get("individualDefense", 0)
        sta  = p.get("individualStamina", 0)
        pct  = iv_percent(atk, dfs, sta)
        medals = "✨" if p.get("pokemonDisplay",{}).get("shiny") else ""
        medals += "🍀" if p.get("isLucky") else ""
        top_lines.append(f"`{i}.` **{name}** {medals} — CP **{cp}** | {atk}/{dfs}/{sta} ({pct}%)")

    top_block = "\n".join(top_lines) if top_lines else "*No Pokémon found*"

    # ── Build fusion block ────────────────────────────────────────
    fusion_block = ""
    if fusion_bk or fusion_wk:
        fusion_block = f"⚫ Black Kyurem DNA: **{fusion_bk}**\n⚪ White Kyurem DNA: **{fusion_wk}**"

    # ── Compose Discord embeds ────────────────────────────────────
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    embeds = [
        # Embed 1 — Account summary
        {
            "title": f"🎮 {trainer} — Login Report",
            "color": 0xF5A623,
            "fields": [
                {"name": "👤 Trainer",   "value": f"**{trainer}** ({team_name})", "inline": True},
                {"name": "📅 Account Created", "value": acc_created, "inline": True},
                {"name": "⭐ Total XP",  "value": f"`{xp:,}`",      "inline": True},
                {"name": "✨ Stardust",  "value": f"`{stardust:,}`", "inline": True},
                {"name": "💰 PokéCoins", "value": f"`{coins:,}`",    "inline": True},
                {"name": "🚶 Km Walked", "value": f"`{km:.1f} km`",  "inline": True},
                {"name": "🏪 PokéStops", "value": f"`{stops:,}`",    "inline": True},
                {"name": "📖 Pokédex",   "value": f"`{pdex} caught / {pdex_seen} seen`", "inline": True},
                {"name": "🥚 Eggs",      "value": f"`{egg_str}`",    "inline": False},
            ],
            "footer": {"text": f"Synced at {now_str} • {data_length:,} bytes"}
        },

        # Embed 2 — Pokemon vault
        {
            "title": "🗃️ Pokémon Vault",
            "color": 0x4FC3F7,
            "fields": [
                {"name": "📦 Storage",    "value": f"`{len(real_mons)} / {max_poke}`", "inline": True},
                {"name": "✨ Shinies",    "value": f"**{len(shiny_mons)}**",           "inline": True},
                {"name": "🍀 Lucky",      "value": f"**{len(lucky_mons)}**",           "inline": True},
                {"name": "❤️ Favorited",  "value": f"**{len(fav_mons)}**",            "inline": True},
                {"name": "💎 Perfect IV", "value": f"**{len(perfect_iv)}**",           "inline": True},
                {"name": "⭐ Near-Perfect (≥93%)", "value": f"**{len(near_perf)}**",  "inline": True},
                {"name": "🏆 Top 5 by CP", "value": top_block,   "inline": False},
                {"name": "✨ Shiny List",  "value": shiny_block,  "inline": False},
            ]
        },

        # Embed 3 — Items & PvP
        {
            "title": "🎒 Items & Battle Stats",
            "color": 0x81C784,
            "fields": [
                {"name": "🎒 Bag",         "value": f"`{sum(i['count'] for i in items)} / {max_items}`", "inline": True},
                {"name": "⚾ Balls",        "value": f"`{balls}`",      "inline": True},
                {"name": "💊 Revives",      "value": f"`{revives}`",    "inline": True},
                {"name": "🍬 Rare Candy",   "value": f"`{rare_candy}`", "inline": True},
                {"name": "🍓 Golden Razz",  "value": f"`{golden_rzz}`", "inline": True},
                {"name": "🥚 Incubators",   "value": f"`{incubators}`", "inline": True},
                {"name": "⭐ Star Piece",   "value": f"`{star_piece}`", "inline": True},
                {"name": "🥚 Lucky Egg",    "value": f"`{lucky_egg}`",  "inline": True},
                {"name": "🌀 Lure Modules", "value": f"`{lure}`",       "inline": True},
                {"name": "⚔️ PvP This Season", "value": f"Rank **{pvp_rank}** | {pvp_wins}W / {pvp_total} battles | {pvp_sd:,} SD earned", "inline": False},
                {"name": "👥 Friends",       "value": f"**{friends}**", "inline": True},
                {"name": "🏟️ Raids Won",    "value": f"**{raids}**",   "inline": True},
                {"name": "🐣 Eggs Hatched", "value": f"**{hatched}**", "inline": True},
            ]
        }
    ]

    # Fusion embed (only if relevant)
    if fusion_block:
        embeds.append({
            "title": "🧬 Fusion Resources",
            "color": 0x9C27B0,
            "description": fusion_block,
            "footer": {"text": "Fuse Kyurem with Reshiram/Zekrom at the fusion station"}
        })

    send_embeds(embeds)
    return "OK", 200


def send_embed(embed):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})

def send_embeds(embeds):
    if not DISCORD_WEBHOOK_URL:
        return
    # Discord allows max 10 embeds per message
    for i in range(0, len(embeds), 10):
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds[i:i+10]})


@app.route("/", methods=["GET"])
def health():
    return "✅ PGSharp Discord Bot is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
