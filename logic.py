import discord
import asyncio
import json
import os
import datetime
import requests
import random
import time
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts")
SKINS_PATH = "assets/skins"

def load_skin_config(skin_name="default"):
    try:
        path = os.path.join(SKINS_PATH, skin_name, "config.json")
        with open(path, "r") as f:
            return json.load(f)
    except:
        # fallback a default si algo falla
        path = os.path.join(SKINS_PATH, "default", "config.json")
        with open(path, "r") as f:
            return json.load(f)

# 🔹 archivos
USERS_FILE = "usuarios.json"
SESSIONS_FILE = "sesiones.json"

file_lock = asyncio.Lock()

DATA_CACHE = {
    "users": {},
    "sessions": {},
    "queue": [],
    "matches": {},
    "prelocke": {},
    "lobby": {},
    "search_interactions": {},
    "tienda": {}
}

SPRITE_CACHE = {}

import random
 
SHINY_CHANCE = 0.05  

TIENDA_FILE = "tienda.json"
TIENDA_ELITE_FILE = "tienda_elite.json"

STARTERS = {
    "aron": "steel",
    "squirtle": "water",
    "weedle": "bug",
    "dratini": "dragon",
    "mareep": "electric",
    "gastly": "ghost",
    "charmander": "fire",
    "cleffa": "fairy",
    "frigibax": "ice",
    "torchic": "fighting",
    "starly": "normal",
    "bulbasaur": "grass",
    "ralts": "psychic",
    "larvitar": "rock",
    "froakie": "dark",
    "gible": "ground",
    "bellsprout": "poison",
    "pidgey": "flying"
}

TYPE_TO_SKIN = {
    "steel": "steel",
    "water": "water",
    "bug": "bug",
    "dragon": "dragon",
    "electric": "electric",
    "ghost": "ghost",
    "fire": "fire",
    "fairy": "fairy",
    "ice": "ice",
    "fighting": "fighting",
    "normal": "normal",
    "grass": "grass",
    "psychic": "psychic",
    "rock": "rock",
    "dark": "dark",
    "ground": "ground",
    "poison": "poison",
    "flying": "flying"
}

SKIN_DISPLAY_NAMES = {
    "default": "Default",

    "fire": "Fuego",
    "water": "Agua",
    "grass": "Planta",
    "electric": "Eléctrico",
    "ice": "Hielo",
    "fighting": "Lucha",
    "poison": "Veneno",
    "ground": "Tierra",
    "rock": "Roca",
    "bug": "Bicho",
    "ghost": "Fantasma",
    "dragon": "Dragón",
    "dark": "Siniestro",
    "steel": "Acero",
    "fairy": "Hada",
    "normal": "Normal",
    "psychic": "Psíquico",
    "flying": "Volador",
    "rocket": "Team Rocket"
}

EVOLUTIONS_BY_LEVEL = {
    "aron": ["lairon", "aggron", "aggron-mega"],
    "squirtle": ["wartortle", "blastoise", "blastoise-mega"],
    "weedle": ["kakuna", "beedrill", "beedrill-mega"],
    "dratini": ["dragonair", "dragonite", "dragonite-mega"],
    "mareep": ["flaaffy", "ampharos", "ampharos-mega"],
    "gastly": ["haunter", "gengar", "gengar-mega"],
    "charmander": ["charmeleon", "charizard", "charizard-mega-x"],
    "cleffa": ["clefairy", "clefable", "clefable-mega"],
    "frigibax": ["arctibax", "baxcalibur", "baxcalibur-mega"],
    "torchic": ["combusken", "blaziken", "blaziken-mega"],
    "starly": ["staravia", "staraptor", "staraptor-mega"],
    "bulbasaur": ["ivysaur", "venusaur", "venusaur-mega"],
    "ralts": ["kirlia", "gardevoir", "gardevoir-mega"],
    "larvitar": ["pupitar", "tyranitar", "tyranitar-mega"],
    "froakie": ["frogadier", "greninja", "greninja-mega"],
    "gible": ["gabite", "garchomp", "garchomp-mega"],
    "bellsprout": ["weepinbell", "victreebel", "victreebel-mega"],
    "pidgey": ["pidgeotto", "pidgeot", "pidgeot-mega"]
}

LEVEL_EVOLUTIONS = {
    "aron": ["aron", "lairon", "aggron", "aggron-mega"],
    "squirtle": ["squirtle", "wartortle", "blastoise", "blastoise-mega"],
    "weedle": ["weedle", "kakuna", "beedrill", "beedrill-mega"],
    "dratini": ["dratini", "dragonair", "dragonite", "dragonite-mega"],
    "mareep": ["mareep", "flaaffy", "ampharos", "ampharos-mega"],
    "gastly": ["gastly", "haunter", "gengar", "gengar-mega"],
    "charmander": ["charmander", "charmeleon", "charizard", "charizard-mega-x"],
    "cleffa": ["cleffa", "clefairy", "clefable", "clefable-mega"],
    "frigibax": ["frigibax", "arctibax", "baxcalibur", "baxcalibur-mega"],
    "torchic": ["torchic", "combusken", "blaziken", "blaziken-mega"],
    "starly": ["starly", "staravia", "staraptor", "staraptor-mega"],
    "bulbasaur": ["bulbasaur", "ivysaur", "venusaur", "venusaur-mega"],
    "ralts": ["ralts", "kirlia", "gardevoir", "gardevoir-mega"],
    "larvitar": ["larvitar", "pupitar", "tyranitar", "tyranitar-mega"],
    "froakie": ["froakie", "frogadier", "greninja", "greninja-mega"],
    "gible": ["gible", "gabite", "garchomp", "garchomp-mega"],
    "bellsprout": ["bellsprout", "weepinbell", "victreebel", "victreebel-mega"],
    "pidgey": ["pidgey", "pidgeotto", "pidgeot", "pidgeot-mega"],
    "phantump": ["phantump", "trevenant"],
}

POKEMON_FORM_MAP = {

    # Formas obligatorias / problemáticas
    "aegislash": "aegislash-shield",
    "basculin": "basculin-red-striped",
    "basculegion": "basculegion-male",
    "darmanitan": "darmanitan-standard",
    "deoxys": "deoxys-normal",
    "giratina": "giratina-altered",
    "keldeo": "keldeo-ordinary",
    "landorus": "landorus-incarnate",
    "meloetta": "meloetta-aria",
    "meowstic": "meowstic-male",
    "oinkologne": "oinkologne-male",
    "oricorio": "oricorio-baile",
    "pumpkaboo": "pumpkaboo-average",
    "gourgeist": "gourgeist-average",
    "shaymin": "shaymin-land",
    "tornadus": "tornadus-incarnate",
    "thundurus": "thundurus-incarnate",
    "toxtricity": "toxtricity-amped",
    "urshifu": "urshifu-single-strike",
    "wishiwashi": "wishiwashi-solo",
    "zacian": "zacian-hero",
    "zamazenta": "zamazenta-hero",
    "zygarde": "zygarde-50",
    "lycanroc": "lycanroc-midday",
    "minior": "minior-red-meteor",
    "mimikyu": "mimikyu-disguised",
    "palafin": "palafin-zero",
    "tatsugiri": "tatsugiri-curly",
    "squawkabilly": "squawkabilly-green-plumage",
    "maushold": "maushold-family-of-four",

    # Formas con variantes pero donde conviene fijar una
    "indeedee": "indeedee-male",
    "basculegion": "basculegion-male",
    "enamorus": "enamorus-incarnate",

    # tamaños múltiples
    "pumpkaboo": "pumpkaboo-average",
    "gourgeist": "gourgeist-average",

    # battle forms que rompen sprites si no se fija base
    "eiscue": "eiscue-ice",
    "morpeko": "morpeko-full-belly",

    # paradox / especiales
    "tatsugiri": "tatsugiri-curly",

    # legendarios con múltiples formas
    "hoopa": "hoopa-confined",
    "necrozma": "necrozma",
    "calyrex": "calyrex",

    # tauros paldea
    "tauros": "tauros-paldea-combat",

    # rotom (base ya funciona pero lo dejamos explícito)
    "rotom": "rotom",
    "pyroar": "pyroar-male"
}

BADGES = {
    "jovenM": { "icon": "jovenM.png", "name": "Rango Joven" },
    "entrenadorM": { "icon": "entrenadorM.png", "name": "Rango Entrenador" },
    "cazabichosM": { "icon": "cazabichosM.png", "name": "Rango Cazabichos" },
    "montaneroM": { "icon": "montaneroM.png", "name": "Rango Montañero" },
    "especialistaM": { "icon": "especialistaM.png", "name": "Rango Especialista" },
    "veteranoM": { "icon": "veteranoM.png", "name": "Rango Veterano" },
    "liderM": { "icon": "liderM.png", "name": "Rango Líder de Gimnasio" },
    "altoMandoM": { "icon": "altoMandoM.png", "name": "Rango Alto Mando" },
    "campeonM": { "icon": "campeonM.png", "name": "Rango Campeón" },
    "maestroM": { "icon": "maestroM.png", "name": "Rango Maestro Pokémon" },
    "primera_gen":  { "icon": "primera_gen.png",  "name": "Victoria en Kanto" },
    "segunda_gen":  { "icon": "segunda_gen.png",  "name": "Victoria en Jotho" },
    "tercera_gen":  { "icon": "tercera_gen.png",  "name": "Victoria en Hoenn" },
    "cuarta_gen":   { "icon": "cuarta_gen.png",   "name": "Victoria en Sinnoh" },
    "quinta_gen":   { "icon": "quinta_gen.png",   "name": "Victoria en Teselia" },
    "sexta_gen":    { "icon": "sexta_gen.png",    "name": "Victoria en Kalos" },
    "septima_gen":  { "icon": "septima_gen.png",  "name": "Victoria en Alola" },
    "octava_gen":   { "icon": "octava_gen.png",   "name": "Victoria en Galar" },
    "shiny": { "icon": "shiny.png", "name": "Insignia Shiny" },
    "inrocket": { "icon": "inrocket.png", "name": "Insignia Rocket" }
}

def is_elite(member):
    for role in member.roles:
        if role.name == "Élite":
            return True
    return False

def load_tienda():
    if not os.path.exists(TIENDA_FILE):
        return {"pokemon_machine": [], "avatar_machine": []}

    with open(TIENDA_FILE, "r") as f:
        return json.load(f)

def load_tienda_elite():

    if not os.path.exists(TIENDA_ELITE_FILE):
        return {"items": []}

    with open(TIENDA_ELITE_FILE, "r") as f:
        return json.load(f)

async def give_badge(member, user, badge_id):
    ensure_inventory(user)

    print("DEBUG give_badge llamado:", badge_id)
    print("DEBUG badges actuales:", user.get("inventory", {}).get("badges"))
    if badge_id not in BADGES:
        return False

    badges = user["inventory"].setdefault("badges", [])

    if badge_id in badges:
        return False

    badges.append(badge_id)

    # 🔔 DM
    try:
        badge_name = BADGES[badge_id]["name"]
        await member.send(
            f"🏅 Has conseguido la insignia **{badge_name}**."
        )
    except:
        pass

    return True

def get_display_pokemon_name(pokemon_name: str, nivel: int) -> str:

    shiny = False

    if pokemon_name.endswith("_shiny"):
        shiny = True
        pokemon_name = pokemon_name.replace("_shiny", "")

    # calcular stage como ya haces
    stage = 0
    if nivel >= 45:
        stage = 3
    elif nivel >= 30:
        stage = 2
    elif nivel >= 15:
        stage = 1

    for base, chain in LEVEL_EVOLUTIONS.items():
        if pokemon_name in chain:

            if stage >= len(chain):
                final = chain[-1]
            else:
                final = chain[stage]

            if shiny:
                return f"{final}_shiny"
            return final

    # si no está en sistema cerrado
    return f"{pokemon_name}_shiny" if shiny else pokemon_name

def get_stage_index(level):
    if level >= 45:
        return 3
    elif level >= 30:
        return 2
    elif level >= 15:
        return 1
    return 0

def get_evolution_for_level(starter_name, level):
    chain = EVOLUTIONS_BY_LEVEL.get(starter_name)
    if not chain:
        return starter_name

    if level >= 45:
        return chain[2]
    elif level >= 30:
        return chain[1]
    elif level >= 15:
        return chain[0]
    else:
        return starter_name

async def check_level_evolution(user):
    starter = user.get("starter")
    if not starter:
        return False

    nivel = user.get("nivel", 0)

    new_form = get_evolution_for_level(starter, nivel)
    current = user.get("pokemon")

    if new_form == current:
        return False  # no hay cambio

    user["pokemon"] = new_form

    # 🔹 actualizar equipado
    # solo actualizar pokemon base si no tiene equipado
    if not user.get("equipped", {}).get("pokemon"):
        user["pokemon"] = new_form
        if "equipped" in user:
            user["equipped"]["pokemon"] = new_form

    # 🔹 inventario
    ensure_inventory(user)
    if new_form not in user["inventory"]["pokemons"]:
        user["inventory"]["pokemons"].append(new_form)

    return True

async def sync_all_user_evolutions():
    changed_any = False

    for user in DATA_CACHE["users"].values():
        changed = await check_level_evolution(user)
        if changed:
            changed_any = True

    if changed_any:
        await save_cache()

def sync_user_pokemon_with_level(user):

    ensure_inventory(user)

    level = user.get("nivel", 0)
    stage = get_stage_index(level)

    # 🔹 actualizar pokemon activo
    starter = user.get("starter")

    if starter in LEVEL_EVOLUTIONS:
        evolved_form = LEVEL_EVOLUTIONS[starter][stage]

        # solo si no tiene pokemon activo
        if not user.get("pokemon"):
            user["pokemon"] = evolved_form

    # 👉 solo actualizar equipado si no tiene o si la forma actual no existe en inventario
    equipped = user.get("equipped", {}).get("pokemon")

    if equipped:
        user["pokemon"] = equipped
    else:
        user["equipped"]["pokemon"] = evolved_form
        user["pokemon"] = evolved_form

    # 🔹 actualizar inventario
    inv = user.get("inventory", {}).get("pokemons", [])

    nuevos = []
    for p in inv:

        shiny = p.endswith("_shiny")
        clean = p.replace("_shiny", "")

        base = None

        for s, chain in LEVEL_EVOLUTIONS.items():
            if clean in chain:
                base = s
                break

        if base:
            chain = LEVEL_EVOLUTIONS[base]

            if stage >= len(chain):
                nuevos.append(chain[-1])
            else:
                evo = chain[min(stage, len(chain)-1)]

                if shiny:
                    evo = f"{evo}_shiny"

                nuevos.append(evo)
        else:
            nuevos.append(p)

    user["inventory"]["pokemons"] = list(dict.fromkeys(nuevos))

RANK_LEVELS = {
    0: "Joven",
    5: "Entrenador",
    10: "Cazabichos",
    15: "Montañero",
    20: "Especialista",
    25: "Veterano",
    30: "Líder de Gimnasio",
    35: "Alto Mando",
    40: "Campeón",
    50: "Maestro Pokémon"
}

RANK_BADGES = {
    "Joven": "jovenM",                
    "Entrenador": "entrenadorM",      
    "Cazabichos": "cazabichosM",      
    "Montañero": "montañeroM",        
    "Especialista": "especialistaM",  
    "Veterano": "veteranoM",          
    "Líder de Gimnasio": "liderM",    
    "Alto Mando": "altoMandoM",      
    "Campeón": "campeonM",           
    "Maestro Pokémon": "maestroM"     
}

# ---------------- RANKING ----------------

def get_league_name(rank_name):
    if not rank_name:
        return "Liga Desconocida"
    return f"Liga {rank_name}"

def get_sorted_ranking(guild):
    ranking = []

    for uid, user in DATA_CACHE["users"].items():
        member = guild.get_member(int(uid))
        if not member:
            continue

        rank_name = get_user_rank(member)

        if rank_name == "—":
            continue

        ranking.append({
            "member": member,
            "nivel": user.get("nivel", 0),
            "exp": user.get("exp", 0),
            "rank": rank_name
        })

    ranking.sort(key=lambda x: (x["nivel"], x["exp"]), reverse=True)
    return ranking

def get_user_position(ranking, user_id):
    for i, entry in enumerate(ranking):
        if entry["member"].id == user_id:
            return i
    return None

def get_ranking_by_league(ranking, league_name):
    return [r for r in ranking if r["rank"] == league_name]

def get_all_leagues_desc():
    # ordenadas de mayor a menor nivel
    return [v for k, v in sorted(RANK_LEVELS.items(), reverse=True)]

def find_user_by_name(guild, query):
    query = query.lower()

    for uid, user in DATA_CACHE["users"].items():
        member = guild.get_member(int(uid))
        if not member:
            continue

        discord_name = member.display_name.lower()
        trainer_name = user.get("trainer_name", "").lower()

        if query in discord_name or query in trainer_name:
            return member, user

    return None, None

async def apply_level_change(member, user, new_level):

    ensure_inventory(user)

    old_level = user.get("nivel", 0)

    print("DEBUG apply_level_change llamado")
    print("member:", member)
    print("nivel anterior:", old_level)
    print("nivel nuevo:", new_level)

    # guardar nivel
    user["nivel"] = new_level

    # actualizar rango
    old_rank, new_rank = await update_rank(member, new_level)

    print("DEBUG rank change:", old_rank, "→", new_rank)

    # dar insignia del rango nuevo
    if new_rank in RANK_BADGES:

        badge_id = RANK_BADGES[new_rank]

        await give_badge(member, user, badge_id)

    # evento especial primer rango
    if new_rank == "Joven" and new_level == 0:
        await on_rank_up(member, "Joven", 0)

    # recompensa subida de rango
    if old_rank != new_rank and old_rank != "—":

        ensure_monedas(user)

        user["monedas_dual"] += 2

        try:
            await member.send(
                "🎖️ Has subido de rango y recibido **2 Monedas Dual** 🪙"
            )
        except:
            pass

    # sincronizar evolución
    sync_user_pokemon_with_level(user)

    # actualizar posiciones
    update_league_positions(member.guild)

    await save_cache()

# ---------------- JSON ----------------

def load_data():
    users = {}
    sessions = {}

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)

    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            sessions = json.load(f)

    return {"users": users, "sessions": sessions}

def get_data():
    return DATA_CACHE

def save_data(data):
    # 🛡️ evitar sobrescribir con vacío
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            existing = json.load(f)
        if existing and not data.get("users"):
            print("⚠️ SAVE CANCELADO: cache vacío")
            return

    temp_users = USERS_FILE + ".tmp"
    temp_sessions = SESSIONS_FILE + ".tmp"

    with open(temp_users, "w") as f:
        json.dump(data.get("users", {}), f, indent=4)
    os.replace(temp_users, USERS_FILE)

    with open(temp_sessions, "w") as f:
        json.dump(data.get("sessions", {}), f, indent=4)
    os.replace(temp_sessions, SESSIONS_FILE)

async def save_cache():
    async with file_lock:
        save_data(DATA_CACHE)

def get_match(user_id):
    return DATA_CACHE["matches"].get(user_id)
# ---------------- UTILS ----------------

def hearts(current, MAX_LIVES):
    return "❤️" * current + "🤍" * (MAX_LIVES - current)

def score_icons(wins):
    return "🟩" * wins if wins > 0 else "—"

def log_event(s, texto):
    timestamp = datetime.datetime.utcnow().strftime("%d/%m %H:%M")
    s["log"].append(f"[{timestamp}] {texto}")

def normalize_category(cat: str):
    cat = cat.lower()

    mapping = {
        "avatar": "avatars",
        "avatars": "avatars",
        "pokemon": "pokemons",
        "pokemons": "pokemons",
        "ui": "ui_skins",
        "skin": "ui_skins",
        "ui_skins": "ui_skins",
        "badge": "badges",
        "badges": "badges"
    }

    return mapping.get(cat)

def migrate_add_available_field():
    data = DATA_CACHE
    users = data.get("users", {})

    changed = False

    for uid, user in users.items():
        if "available" not in user:
            user["available"] = False
            changed = True

    return changed, len(users)

# ---------------- INVENTARIO ----------------

def ensure_inventory(user):
    starter = user.get("pokemon")
    avatar_default = "Rojo" if user.get("gender") == "Masculino" else "Verde"

    if "inventory" not in user:
        user["inventory"] = {
            "avatars": ["Rojo", "Verde"],
            "pokemons": [starter] if starter else [],
            "ui_skins": ["default"],
            "badges": []
        }

    inv = user["inventory"]

    inv.setdefault("avatars", ["Rojo", "Verde"])
    inv.setdefault("pokemons", [])
    inv.setdefault("ui_skins", ["default"])
    inv.setdefault("badges", [])

    if "equipped" not in user:
        user["equipped"] = {
            "avatar": avatar_default,
            "pokemon": user.get("pokemon") or (inv["pokemons"][0] if inv["pokemons"] else None),
            "ui_skin_card": inv["ui_skins"][0] if inv["ui_skins"] else "default",
            "ui_skin_team": inv["ui_skins"][0] if inv["ui_skins"] else "default"
        }

    user["equipped"].setdefault("ui_skin_card", "default")
    user["equipped"].setdefault("ui_skin_team", "default")
    user["equipped"].setdefault("badges", [])
    user.setdefault("league_position", None)
    ensure_monedas(user)
    user.setdefault("search_cooldown", 0)

def ensure_monedas(user):
    user.setdefault("monedas_dual", 0)
    user.setdefault("monedas_elite", 0)

async def inv_add(uid, category, value):
    data = DATA_CACHE
    user = data["users"].get(uid)

    if not user:
        return False

    ensure_inventory(user)

    category = normalize_category(category)
    if not category:
        return False

    if value not in user["inventory"][category]:
        user["inventory"][category].append(value)

    await save_cache()
    return True

async def inv_remove(uid, category, value):

    data = DATA_CACHE
    user = data["users"].get(uid)

    if not user:
        return False

    ensure_inventory(user)

    category = normalize_category(category)
    if not category:
        return False

    inv_list = user["inventory"][category]

    for item in inv_list:
        if item.lower() == value.lower():
            inv_list.remove(item)
            await save_cache()
            return True

    return False

async def equip_badge(user, badge_id):

    ensure_inventory(user)

    if badge_id not in user["inventory"]["badges"]:
        return False  # no la posee

    equipped = user["equipped"].setdefault("badges", [])

    if badge_id in equipped:
        return False  # ya equipada

    if len(equipped) >= 12:
        return False  # límite lleno

    equipped.append(badge_id)
    await save_cache()
    return True

async def unequip_badge(user, badge_id):

    ensure_inventory(user)

    equipped = user["equipped"].setdefault("badges", [])

    if badge_id not in equipped:
        return False

    equipped.remove(badge_id)
    await save_cache()
    return True

# ---------------- SPRITES ----------------

def normalize_pokemon_name(name: str):

    name = name.lower().strip()

    shiny = False

    if name.endswith("_shiny"):
        shiny = True
        name = name.replace("_shiny", "")

    if name in POKEMON_FORM_MAP:
        name = POKEMON_FORM_MAP[name]

    if shiny:
        name = f"{name}_shiny"

    return name

def get_pokemon_sprite(name):
    try:
        if name in SPRITE_CACHE:
            return SPRITE_CACHE[name]

        shiny = False

        if name.endswith("_shiny"):
            shiny = True
            base_name = name.replace("_shiny", "")
        else:
            base_name = name

        if base_name == "aegislash":
            base_name = "aegislash-shield"

        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{base_name}", timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()

        sprite = data["sprites"]["front_shiny"] if shiny else data["sprites"]["front_default"]

        if not sprite:
            sprite = data["sprites"]["other"]["official-artwork"]["front_default"]

        if not sprite:
            sprite = data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_default"]

        SPRITE_CACHE[name] = sprite
        return sprite

    except Exception as e:
        print("SPRITE ERROR:", e)
        return None

def get_trainer_avatar(avatar):

    avatars = {
        "Rojo": "https://play.pokemonshowdown.com/sprites/trainers/red.png",
        "Verde": "https://play.pokemonshowdown.com/sprites/trainers/green.png",
        "Giovanni": "https://play.pokemonshowdown.com/sprites/trainers/giovanni.png",

        # Johto
        "Ethan": "https://play.pokemonshowdown.com/sprites/trainers/ethan.png",
        "Lyra": "https://play.pokemonshowdown.com/sprites/trainers/lyra.png",

        # Hoenn
        "Brendan": "https://play.pokemonshowdown.com/sprites/trainers/brendan.png",
        "May": "https://play.pokemonshowdown.com/sprites/trainers/may.png",

        # Sinnoh
        "Lucas": "https://play.pokemonshowdown.com/sprites/trainers/lucas.png",
        "Dawn": "https://play.pokemonshowdown.com/sprites/trainers/dawn.png",
    }

    try:
        url = avatars.get(avatar)

        # fallback
        if not url:
            url = avatars["Rojo"]

        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            return r.content

        return None

    except Exception as e:
        print("Error trainer avatar:", e)
        return None
    
def generar_tarjeta_entrenador(
    nombre,
    genero,
    rango,
    puntos,
    nivel,
    exp,
    avatar_pokemon_bytes=None,
    discord_avatar_bytes=None,
    pokemon_sprite_bytes=None,
    pokemon_name=None,
    skin="default",
    badges=None,
    badge_equipped=None,
    es_elite=False
):
    
    badges = badges or []
    badge_equipped = badge_equipped or []

    cfg = load_skin_config(skin)

    bg_top = tuple(cfg.get("bg_top", (34, 40, 49)))
    bg_bottom = tuple(cfg.get("bg_bottom", (24, 30, 38)))

    panel_color = tuple(cfg.get("panel_color", (240, 242, 245)))
    panel_border = tuple(cfg.get("outline_color", (60, 80, 110)))
    inner_border = tuple(cfg.get("inner_outline_color", (170, 185, 210)))

    accent_color = tuple(cfg.get("accent_color", (90, 120, 150)))

    title_color = tuple(cfg.get("title_color", (50, 70, 100)))
    text_color = tuple(cfg.get("text_color", (30, 30, 30)))

    separator_color = tuple(cfg.get("separator_color", (210, 210, 210)))
    decor_line_color = tuple(cfg.get("decor_line_color", separator_color))

    badge_color = tuple(cfg.get("badge_panel_color", accent_color))

    exp_bar_fill = tuple(cfg.get("exp_bar_fill", (90, 140, 220)))
    exp_bar_bg = tuple(cfg.get("exp_bar_bg", (210, 210, 210)))

    width, height = 920, 520

    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(bg_top[0]*(1-ratio) + bg_bottom[0]*ratio)
        g = int(bg_top[1]*(1-ratio) + bg_bottom[1]*ratio)
        b = int(bg_top[2]*(1-ratio) + bg_bottom[2]*ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    bar_color = accent_color
    draw.rectangle((0, 0, width, 5), fill=bar_color)
    draw.rectangle((0, height-5, width, height), fill=bar_color)

    panel_margin = 35
    draw.rounded_rectangle(
        (panel_margin, panel_margin, width-panel_margin, height-panel_margin),
        radius=35,
        fill=panel_color,
        outline=panel_border,
        width=4
    )

    draw.rounded_rectangle(
        (panel_margin+6, panel_margin+6, width-panel_margin-6, height-panel_margin-6),
        radius=30,
        outline=inner_border,
        width=2
    )

    print("----- DEBUG FUENTES -----")
    print("BASE_DIR:", BASE_DIR)
    print("FONT_PATH:", FONT_PATH)

    try:
        print("Archivos en carpeta fonts:", os.listdir(FONT_PATH))
    except Exception as e:
        print("Error listando fonts:", e)

    try:
        title_font = ImageFont.truetype(os.path.join(FONT_PATH,"Roboto-Bold.ttf"), 42)
        label_font = ImageFont.truetype(os.path.join(FONT_PATH,"Roboto-Bold.ttf"), 28)
        text_font = ImageFont.truetype(os.path.join(FONT_PATH,"Roboto-Regular.ttf"), 26)
        badge_font = ImageFont.truetype(os.path.join(FONT_PATH,"seguiemj.ttf"), 40)
    except:
        title_font = label_font = text_font = badge_font = ImageFont.load_default()

    title = "TARJETA DE ENTRENADOR"
    tw = draw.textlength(title, font=title_font)
    draw.text(((width - tw) / 2 + 2, 52), title, fill=(0,0,0,80), font=title_font)
    draw.text(((width - tw) / 2, 50), title, fill=title_color, font=title_font)

    draw.line(
        ((width - tw) / 2, 95, (width + tw) / 2, 95),
        fill=decor_line_color,
        width=2
    )

    separator_x = 450
    separator_top = 120
    separator_bottom = height - 120

    draw.line(
        (separator_x, separator_top, separator_x, separator_bottom),
        fill=separator_color,
        width=2
    )

    x_text = 80
    y_text = 140

    draw.text((x_text, y_text), "Nombre:", fill=text_color, font=label_font)

    nombre_x = x_text + 110
    nombre_y = y_text - 2  # pequeño ajuste para mantener alineación al aumentar tamaño

    # fuente bold un poco más grande
    try:
        name_font = ImageFont.truetype(os.path.join(FONT_PATH,"Roboto-Bold.ttf"), 34)
    except:
        name_font = text_font

    nombre_color = (255, 146, 0) if es_elite else text_color

    # sombra suave
    if es_elite:
        draw.text(
            (nombre_x+1, nombre_y+1),
            nombre,
            fill=(0,0,0),
            font=name_font
        )

    # texto principal
    draw.text(
        (nombre_x, nombre_y),
        nombre,
        fill=nombre_color,
        font=name_font
    )

    draw.text((x_text, y_text+40), "Rango:", fill=text_color, font=label_font)
    draw.text((x_text+100, y_text+40), rango, fill=text_color, font=text_font)

    posicion_texto = f"Top {puntos}" if puntos is not None else "—"

    draw.text((x_text, y_text+80), "Posición de liga:", fill=text_color, font=label_font)
    draw.text((x_text+210, y_text+80), posicion_texto, fill=text_color, font=text_font)

    # ===== PANEL INSIGNIAS =====
    badge_left = x_text - 10
    badge_right = 440 - 20
    badge_top = y_text + 125
    badge_bottom = height - 70

    draw.rounded_rectangle(
        (badge_left, badge_top, badge_right, badge_bottom),
        radius=30,
        fill=badge_color
    )

    # 🔹 DIBUJAR SOLO LA INSIGNIA EQUIPADA
    # ================= GRID 3x4 =================

    COLUMNS = 4
    ROWS = 3
    MAX_BADGES = 12
    BADGE_SIZE = 76
    INNER_PADDING = 15

    panel_width = badge_right - badge_left
    panel_height = badge_bottom - badge_top

    usable_width = panel_width - (INNER_PADDING * 2)
    usable_height = panel_height - (INNER_PADDING * 2)

    H_SPACING = usable_width // COLUMNS
    V_SPACING = usable_height // ROWS

    start_x = badge_left + INNER_PADDING
    start_y = badge_top + INNER_PADDING

    badges_to_draw = badge_equipped[:MAX_BADGES]

    for i, badge_id in enumerate(badges_to_draw):

        badge = BADGES.get(badge_id)
        if not badge:
            continue

        icon_file = badge.get("icon")
        if not icon_file:
            continue

        try:
            path = os.path.join("assets", "badges", icon_file)
            icon = Image.open(path).convert("RGBA")
            icon = icon.resize((BADGE_SIZE, BADGE_SIZE), Image.NEAREST)

            col = i % COLUMNS
            row = i // COLUMNS

            x = start_x + col * H_SPACING
            y = start_y + row * V_SPACING

            img.paste(icon, (x, y), icon)

        except Exception as e:
            print("BADGE ERROR:", e)
    
    
    trainer_x = width - 420
    trainer_y = 135

    # ===============================
    # 🚀 DECORACIÓN TEAM ROCKET
    # ===============================

    if skin == "rocket":
        try:
            r_logo = Image.open("assets/skins/rocket/r.png").convert("RGBA")
            r_logo = r_logo.resize((260, 260), Image.NEAREST)

            # bajar opacidad
            alpha = r_logo.split()[3].point(lambda p: p * 0.25)
            r_logo.putalpha(alpha)

            # centrar entre entrenador y pokemon
            r_x = trainer_x + 37
            r_y = trainer_y - 30   # subir un poco

            img.paste(r_logo, (r_x, r_y), r_logo)

        except Exception as e:
            print("Rocket logo error:", e)

    if avatar_pokemon_bytes:
        trainer = Image.open(BytesIO(avatar_pokemon_bytes)).convert("RGBA")
        trainer = trainer.resize((160, 160), Image.NEAREST)

        shadow = Image.new("RGBA", trainer.size, (0, 0, 0, 0))
        shadow_pixels = shadow.load()

        for y in range(trainer.height):
            for x in range(trainer.width):
                if trainer.getpixel((x, y))[3] > 0:
                    shadow_pixels[x, y] = (0, 0, 0, 45)

        img.paste(shadow, (trainer_x + 3, trainer_y + 4), shadow)
        img.paste(trainer, (trainer_x, trainer_y), trainer)

    if pokemon_sprite_bytes:
        sprite = Image.open(BytesIO(pokemon_sprite_bytes)).convert("RGBA")
        # 🔎 detectar tamaño real original
        original_width, original_height = sprite.size

        base_size = 170

        # 🔹 escalar dinámicamente según tamaño original
        if original_height < 80:
            scale_size = 190
        elif original_height < 110:
            scale_size = 180
        else:
            scale_size = 170

        sprite = sprite.resize((scale_size, scale_size), Image.NEAREST)

        # 🔹 Detectar el píxel visible más bajo
        lowest_pixel = 0
        for y in range(sprite.height - 1, -1, -1):
            for x in range(sprite.width):
                if sprite.getpixel((x, y))[3] > 0:
                    lowest_pixel = y
                    break
            if lowest_pixel:
                break
        
        # 🔹 detectar píxel visible más a la izquierda
        leftmost = sprite.width
        for x in range(sprite.width):
            for y in range(sprite.height):
                if sprite.getpixel((x, y))[3] > 0:
                    leftmost = x
                    break
            if leftmost != sprite.width:
                break

        # 🔹 línea base del entrenador
        trainer_height = 160
        trainer_bottom = trainer_y + trainer_height

        # 🔹 calcular offset real
        visible_height = lowest_pixel
        pokemon_y = trainer_bottom - visible_height - 1
        # 🔹 ancho del área reservada para el Pokémon
        BASE_OFFSET = 150  # punto base respecto al entrenador

        # compensar espacio transparente izquierdo
        pokemon_x = trainer_x + BASE_OFFSET - leftmost

        # sombra
        shadow = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
        shadow_pixels = shadow.load()

        for y in range(sprite.height):
            for x in range(sprite.width):
                if sprite.getpixel((x, y))[3] > 0:
                    shadow_pixels[x, y] = (0, 0, 0, 45)

        img.paste(shadow, (pokemon_x + 4, pokemon_y + 6), shadow)
        img.paste(sprite, (pokemon_x, pokemon_y), sprite)

    bloque_center_x = trainer_x + 140
    exp_y = 355

    if nivel >= 50:
        texto_exp = f"Nivel {nivel}   •   EXP MAX"
    else:
        needed = exp_needed(nivel)
        texto_exp = f"Nivel {nivel}   •   EXP {exp}/{needed}"

    tw = draw.textlength(texto_exp, font=label_font)
    draw.text((bloque_center_x - tw/2, exp_y), texto_exp, fill=text_color, font=label_font)

    bar_width = 320
    bar_height = 16
    bar_x = bloque_center_x - bar_width // 2
    bar_y = exp_y + 50

    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
        radius=8,
        fill=exp_bar_bg
    )

    try:
        nivel_num = int(nivel)
        exp_num = int(exp)
    except:
        nivel_num = 0
        exp_num = 0

    if nivel_num >= 50:
        exp_ratio = 1
    else:
        needed = exp_needed(nivel_num)
        exp_ratio = min(exp_num / needed, 1)

    progress = int(bar_width * exp_ratio)

    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + progress, bar_y + bar_height),
        radius=8,
        fill=exp_bar_fill
    )

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def generar_preview_desde_equipped(member, user, equipped):
    
    nombre = user.get("trainer_name", member.display_name)
    nivel = user.get("nivel", 0)
    exp = user.get("exp", 0)

    genero = equipped.get("avatar", user.get("gender"))
    pokemon = equipped.get("pokemon", user.get("pokemon"))

    trainer_avatar = get_trainer_avatar(genero)

    pokemon_sprite = None
    if pokemon:
        url = get_pokemon_sprite(pokemon)
        if url:
            pokemon_sprite = requests.get(url).content

    rango = get_user_rank(member)

    ranking = get_sorted_ranking(member.guild)

    posicion = None
    for entry in ranking:
        if entry["member"].id == member.id:
            # calcular posición dentro de su liga
            liga = [r for r in ranking if r["rank"] == entry["rank"]]
            for i, r in enumerate(liga, start=1):
                if r["member"].id == member.id:
                    posicion = i
                    break
            break

    liga = [r for r in ranking if r["rank"] == rango]


    posicion = None
    for i, r in enumerate(liga, start=1):
        if int(r["member"].id) == int(member.id):
            posicion = i
            break

    if posicion is None:
        posicion = 1

    badges = user.get("inventory", {}).get("badges", [])
    badge_equipped = equipped.get("badges", [])

    return generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=posicion,
        nivel=nivel,
        exp=exp,
        avatar_pokemon_bytes=trainer_avatar,
        pokemon_sprite_bytes=pokemon_sprite,
        pokemon_name=pokemon,
        skin=equipped.get("ui_skin_card", "default"),
        badges=badges,
        badge_equipped=badge_equipped,
        es_elite=is_elite(member)
    )

def get_user_rank(member: discord.Member):
    if not member.roles:
        return "—"

    rank_roles = set(RANK_LEVELS.values())

    # filtrar solo roles de progresión
    roles = [r for r in member.roles if r.name in rank_roles]

    if not roles:
        return "—"

    # devolver el de mayor nivel según RANK_LEVELS
    roles_sorted = sorted(
        roles,
        key=lambda r: list(RANK_LEVELS.values()).index(r.name)
    )

    return roles_sorted[-1].name

def exp_needed(level):

    if level < 10:
        return 600

    elif level < 20:
        return 900

    elif level < 30:
        return 1200

    elif level < 40:
        return 1500

    else:
        return 1800

def get_pokemon_id(name):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
        if r.status_code != 200:
            return None
        return r.json()["id"]
    except:
        return None

async def generar_log_canal(channel):
    mensajes = []

    async for msg in channel.history(limit=None, oldest_first=True):
        timestamp = msg.created_at.strftime("%d/%m %H:%M")
        autor = msg.author.display_name
        contenido = msg.content if msg.content else ""

        # adjuntos
        if msg.attachments:
            contenido += " " + " ".join(a.url for a in msg.attachments)

        linea = f"[{timestamp}] {autor}: {contenido}"
        mensajes.append(linea)

    return "\n".join(mensajes)

MAX_LIVES = 20

def get_starter_sprite(name):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}", timeout=10)
        if r.status_code != 200:
            return None

        url = r.json()["sprites"]["other"]["official-artwork"]["front_default"]
        if not url:
            return None

        img = requests.get(url).content
        return img

    except:
        return None

def render_team_inline(team):
    if not team:
        return "—"

    sprites = []
    for p in team:
        sprite = get_pokemon_sprite(p)
        if sprite:
            sprites.append(sprite)

    return " ".join(sprites) if sprites else "—"

def get_pokemon_pixel_sprite(name):
    try:
        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}", timeout=10)
        if r.status_code != 200:
            return None

        url = r.json()["sprites"]["front_default"]
        if not url:
            return None

        return requests.get(url).content
    except:
        return None

session_locks = {}

def get_session_lock(session_id):
    if session_id not in session_locks:
        session_locks[session_id] = asyncio.Lock()
    return session_locks[session_id]

async def refrescar_sesion_embed(session_id, guild):
    data = get_data()

    s = data["sessions"].get(str(session_id))
    if not s:
        return

    channel = guild.get_channel(s["s_channel"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(s["s_message"])
    except:
        return

    uid1 = str(s["player1"])
    uid2 = str(s["player2"])

    p1 = guild.get_member(int(uid1))
    p2 = guild.get_member(int(uid2))

    vidas1 = s["lives"][uid1]
    vidas2 = s["lives"][uid2]
    max_vidas = s["max_lives"]

    embed = discord.Embed(
        title=f"{p1.display_name}  🆚  {p2.display_name}",
        description=(
            f"**{s['game']} {s['type'].capitalize()}**\n\n"
            f"{'🟢 ACTIVA' if s['status'] == 'active' else '🔴 INACTIVA'}\n"
        ),
        color=discord.Color.green() if s["status"] == "active" else discord.Color.red()
    )

    embed.add_field(
        name=f"👤 {p1.display_name}",
        value=f"❤️ {hearts(vidas1, max_vidas)} ({vidas1}/{max_vidas})\n⚔️ Victorias: {score_icons(s['score'][uid1])}",
        inline=False
    )

    embed.add_field(
        name=" ",
        value="----------------------------------------------",
        inline=False
    )

    embed.add_field(
        name=f"👤 {p2.display_name}",
        value=f"❤️ {hearts(vidas2, max_vidas)} ({vidas2}/{max_vidas})\n⚔️ Victorias: {score_icons(s['score'][uid2])}",
        inline=False
    )

    if s.get("status") == "finished" and s.get("winner") is not None:
        winner_member = guild.get_member(int(s["winner"]))
        if winner_member:
            embed.add_field(
                name="🏆 Ganador",
                value=f"**{winner_member.display_name}**",
                inline=False
            )

    await msg.edit(embed=embed)

def puede_evolucionar(pokemon):
    try:
        base = pokemon.replace("_shiny", "")

        r = requests.get(
            f"https://pokeapi.co/api/v2/pokemon-species/{base}",
            timeout=8
        )

        if r.status_code != 200:
            return False

        evo_chain_url = r.json()["evolution_chain"]["url"]
        evo_data = requests.get(evo_chain_url, timeout=8).json()

        def buscar(chain, name):
            if chain["species"]["name"] == name:
                return bool(chain["evolves_to"])

            for evo in chain["evolves_to"]:
                res = buscar(evo, name)
                if res is not None:
                    return res
            return None

        return buscar(evo_data["chain"], base)

    except Exception as e:
        print("CHECK EVO ERROR:", e)
        return False

def generar_collage(team, player_name=None, skin="default"):

    cfg = load_skin_config(skin)

    bg_top = tuple(cfg.get("bg_top", (34, 40, 49)))
    bg_bottom = tuple(cfg.get("bg_bottom", (24, 30, 38)))
    accent_color = tuple(cfg.get("accent_color", (90, 120, 150)))
    text_color = tuple(cfg.get("text_color", (200, 220, 240)))

    spacing = 36
    padding = 80
    canvas_height = 250

    # ===============================
    # 🎨 FONDO BASE
    # ===============================
    def crear_canvas(width):
        top_color = bg_top
        bottom_color = bg_bottom

        canvas = Image.new("RGBA", (width, canvas_height))

        for y in range(canvas_height):
            ratio = y / canvas_height
            r = int(top_color[0]*(1-ratio) + bottom_color[0]*ratio)
            g = int(top_color[1]*(1-ratio) + bottom_color[1]*ratio)
            b = int(top_color[2]*(1-ratio) + bottom_color[2]*ratio)

            for x in range(width):
                canvas.putpixel((x, y), (r, g, b, 255))

        bar_color = accent_color
        for x in range(width):
            for y in range(4):
                canvas.putpixel((x, y), (*bar_color, 255))
                canvas.putpixel((x, canvas_height-1-y), (*bar_color, 255))

        return canvas

    # ===============================
    # 🪶 EQUIPO VACÍO
    # ===============================

    if not team:
        canvas_width = 920
        canvas = crear_canvas(canvas_width)

        draw = ImageDraw.Draw(canvas)
        text = f"TEAM  {player_name.upper() if player_name else 'PLAYER'}"  # 👈 doble espacio

        # 🅰️ intentar fuente estilo cómic
        try:
            font = ImageFont.truetype("comic.ttf", 56)
        except:
            try:
                font = ImageFont.truetype("ComicSansMS.ttf", 56)
            except:
                font = ImageFont.load_default()

        # 📏 tamaño
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x = (canvas_width - tw) // 2
        y = (canvas_height - th) // 2 - 18   # 👈 subir un poco

        # 🌫️ sombra suave
        draw.text((x+4, y+4), text, fill=(0, 0, 0, 110), font=font)

        # 🪶 inclinación simulada
        for i, char in enumerate(text):
            offset_x = x + draw.textlength(text[:i], font=font)
            offset_y = y - int(i * 0.15)
            draw.text((offset_x, offset_y), char, fill=text_color, font=font)

        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    
    # ===============================
    # 🧩 GENERAR SPRITES
    # ===============================
    sprites = []

    for name in team:
        url = get_pokemon_sprite(name)
        if not url:
            continue

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue

            pokemon = Image.open(BytesIO(r.content)).convert("RGBA")

            scale = 1.6
            pokemon = pokemon.resize(
                (int(pokemon.width * scale), int(pokemon.height * scale)),
                Image.NEAREST
            )

            shadow = Image.new("RGBA", pokemon.size, (0, 0, 0, 0))
            shadow_pixels = shadow.load()

            for y in range(pokemon.height):
                for x in range(pokemon.width):
                    if pokemon.getpixel((x, y))[3] > 0:
                        shadow_pixels[x, y] = (0, 0, 0, 70)

            sprites.append((shadow, pokemon))

        except Exception as e:
            print("COLLAGE ERROR:", e)

    if not sprites:
        return None

    # 🔥 ancho real dinámico
    total_width = sum(img.width for _, img in sprites) + spacing * (len(sprites) - 1)
    canvas_width = max(920, total_width + padding)

    canvas = crear_canvas(canvas_width)

    x = (canvas_width - total_width) // 2

    for shadow, img in sprites:
        y = (canvas_height - img.height) // 2
        canvas.paste(shadow, (x+6, y+8), shadow)
        canvas.paste(img, (x, y), img)
        x += img.width + spacing

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

async def refrescar_collages(s, guild, session_id):
    channel = guild.get_channel(s["s_channel"])
    if not channel:
        print("Canal no encontrado")
        return

    uid1 = str(s["player1"])
    uid2 = str(s["player2"])

    p1 = guild.get_member(int(uid1))
    p2 = guild.get_member(int(uid2))

    team1 = s["teams"].get(uid1, [])
    team2 = s["teams"].get(uid2, [])

    user1 = DATA_CACHE["users"].get(uid1, {})
    user2 = DATA_CACHE["users"].get(uid2, {})

    skin1 = user1.get("equipped", {}).get("ui_skin_team", "default")
    skin2 = user2.get("equipped", {}).get("ui_skin_team", "default")

    # 🔹 generar collages
    file1 = generar_collage(team1, p1.display_name, skin=skin1)
    file2 = generar_collage(team2, p2.display_name, skin=skin2)

    discord_file1 = discord.File(file1, filename="team.png") if file1 else None
    discord_file2 = discord.File(file2, filename="team.png") if file2 else None

    # ================= PLAYER 1 =================
    msg1 = None
    if s.get("s_team_msg_1"):
        try:
            msg1 = await channel.fetch_message(s["s_team_msg_1"])
        except:
            msg1 = None

    if msg1:
        if discord_file1:
            await msg1.edit(
                content=f"🖥️ Equipo de **{p1.display_name}**",
                attachments=[discord_file1]
            )
        else:
            await msg1.edit(
                content=f"🖥️ Equipo de **{p1.display_name}**\n*(sin Pokémon todavía)*",
                attachments=[]
            )
    else:
        if discord_file1:
            new_msg = await channel.send(
                content=f"🖥️ Equipo de **{p1.display_name}**",
                file=discord_file1
            )
        else:
            new_msg = await channel.send(
                content=f"🖥️ Equipo de **{p1.display_name}**\n*(sin Pokémon todavía)*"
            )

        s["s_team_msg_1"] = new_msg.id

    # ================= PLAYER 2 =================
    msg2 = None
    if s.get("s_team_msg_2"):
        try:
            msg2 = await channel.fetch_message(s["s_team_msg_2"])
        except:
            msg2 = None

    if msg2:
        if discord_file2:
            await msg2.edit(
                content=f"🖥️ Equipo de **{p2.display_name}**",
                attachments=[discord_file2]
            )
        else:
            await msg2.edit(
                content=f"🖥️ Equipo de **{p2.display_name}**\n*(sin Pokémon todavía)*",
                attachments=[]
            )
    else:
        if discord_file2:
            new_msg = await channel.send(
                content=f"🖥️ Equipo de **{p2.display_name}**",
                file=discord_file2
            )
        else:
            new_msg = await channel.send(
                content=f"🖥️ Equipo de **{p2.display_name}**\n*(sin Pokémon todavía)*"
            )

        s["s_team_msg_2"] = new_msg.id

    # 🔹 guardar cambios
    DATA_CACHE["sessions"][str(session_id)] = s
    await save_cache()

def obtener_sesion_por_canal(channel_id):
    data = get_data()
    for sid, s in data["sessions"].items():
        if s.get("s_channel") == channel_id and s.get("status") == "active":
            return sid, s
    return None, None

def is_user_in_active_session(user_id: str):
    sessions = DATA_CACHE.get("sessions", {})

    for s in sessions.values():
        if s.get("status") == "active":
            if user_id in (s.get("player1"), s.get("player2")):
                return True

    return False

async def quitar_vida_logic(user_id, channel_id, display_name):
    data = DATA_CACHE
    sessions = data["sessions"]

    sid = None
    s = None

    for k, v in sessions.items():
        if v.get("s_channel") == channel_id and v.get("status") == "active":
            sid = k
            s = v
            break

    if not s:
        return {"ok": False, "error": "no_session"}

    uid = str(user_id)

    if uid not in (s["player1"], s["player2"]):
        return {"ok": False, "error": "not_player"}

    lock = get_session_lock(sid)

    async with lock:
        s = DATA_CACHE["sessions"][sid]
        lives = s["lives"]

        if lives[uid] <= 0:
            return {"ok": False, "error": "no_lives"}

        lives[uid] -= 1
        log_event(s, f"{display_name} pierde una vida ({lives[uid]} restantes)")
        await save_cache()

        vidas_restantes = lives[uid]

    return {
        "ok": True,
        "sid": sid,
        "vidas": vidas_restantes,
        "session": s
    }

async def sumar_punto_logic(user_id, channel_id, display_name):
    sid, s = obtener_sesion_por_canal(channel_id)
    if not s:
        return {"ok": False, "error": "no_session"}

    lock = get_session_lock(sid)

    async with lock:
        s = DATA_CACHE["sessions"][sid]
        uid = str(user_id)

        if uid not in (s["player1"], s["player2"]):
            return {"ok": False, "error": "not_player"}

        s["score"][uid] += 1
        log_event(s, f"{display_name} gana un punto (total {s['score'][uid]})")

        await save_cache()

        puntos = s["score"][uid]

    return {
        "ok": True,
        "sid": sid,
        "puntos": puntos,
        "session": s
    }

def set_user_available(user_id: str, value: bool):
    data = DATA_CACHE
    users = data["users"]

    if user_id not in users:
        return False, "no_user"

    if value:  # quiere ponerse disponible
        if is_user_in_active_session(user_id):
            return False, "in_session"

    users[user_id]["available"] = value
    return True, None

def is_user_searching(user_id: str):
    return user_id in DATA_CACHE.get("queue", [])

def add_to_queue(user_id: str):

    users = DATA_CACHE["users"]
    user = users.get(user_id)

    if not user:
        return False, "no_user"

    now = time.time()

    cooldown = user.get("search_cooldown", 0)

    if cooldown > now:
        return False, int(cooldown - now)

    if user_id not in DATA_CACHE["queue"]:
        DATA_CACHE["queue"].append(user_id)

    # 🔹 activar cooldown 60s
    user["search_cooldown"] = now + 60

    return True, None

def remove_from_queue(user_id: str):
    if user_id in DATA_CACHE["queue"]:
        DATA_CACHE["queue"].remove(user_id)

def is_on_cooldown(p1, p2):
    users = DATA_CACHE["users"]

    return (
        p2 in users.get(p1, {}).get("recent_matches", []) or
        p1 in users.get(p2, {}).get("recent_matches", [])
    )

def register_recent_match(p1, p2, max_history=2):
    users = DATA_CACHE["users"]

    users.setdefault(p1, {}).setdefault("recent_matches", [])
    users.setdefault(p2, {}).setdefault("recent_matches", [])

    users[p1]["recent_matches"].insert(0, p2)
    users[p2]["recent_matches"].insert(0, p1)

    users[p1]["recent_matches"] = users[p1]["recent_matches"][:max_history]
    users[p2]["recent_matches"] = users[p2]["recent_matches"][:max_history]

def try_matchmaking(guild):

    queue = DATA_CACHE.get("queue", [])

    # 🔹 limpiar usuarios que ya no existen
    queue[:] = [
        uid for uid in queue
        if guild.get_member(int(uid)) and uid in DATA_CACHE["users"]
    ]

    print("🧪 QUEUE:", queue)
    if len(queue) < 2:
        return None

    # 🔹 agrupar por rango
    rank_groups = {}

    for uid in queue:
        member = guild.get_member(int(uid))
        if not member:
            continue

        rank = get_user_rank(member)
        print("🧪 rank", uid, rank)
        rank_groups.setdefault(rank, []).append(uid)

    # 🔹 revisar cada rango
    import random

    for rank, players in rank_groups.items():

        if len(players) < 2:
            continue

        posibles = []

        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                p1 = players[i]
                p2 = players[j]

                if not is_on_cooldown(p1, p2):
                    posibles.append((p1, p2))
                else:
                    print("⛔ cooldown bloqueando", p1, p2)

        if not posibles:
            continue  # nadie compatible aún

        p1, p2 = random.choice(posibles)

        queue.remove(p1)
        queue.remove(p2)

        return p1, p2

    return None

def get_rank(member):
    roles = [r for r in member.roles if r.name != "@everyone"]

    if not roles:
        return None

    top_role = max(roles, key=lambda r: r.position)
    return top_role.name

async def create_prelocke_channel(guild, p1, p2):

    member1 = guild.get_member(int(p1))
    member2 = guild.get_member(int(p2))

    name = f"pre-{member1.display_name}-{member2.display_name}"
    name = name.lower().replace(" ", "-")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        member2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    channel = await guild.create_text_channel(name=name, overwrites=overwrites)
    

    DATA_CACHE["lobby"][str(channel.id)] = {
        "players": [p1, p2],
        "form": None,
        "status": "filling"
    }

    return channel

def init_prelocke(match_id, p1, p2, data):
    DATA_CACHE["prelocke"][match_id] = {
    "players": [p1, p2],
    "data": data,
    "confirmed": [],
    "status": "active"
}

def confirm_prelocke(match_id, user_id):
    pl = DATA_CACHE["prelocke"].get(match_id)
    if not pl:
        return False, False

    if user_id not in pl["confirmed"]:
        pl["confirmed"].append(user_id)

    done = len(pl["confirmed"]) == 2
    return True, done

def get_prelocke(match_id):
    return DATA_CACHE["prelocke"].get(match_id)

def clear_prelocke(match_id):
    pl = DATA_CACHE["prelocke"].get(match_id)
    if pl:
        pl["status"] = "waiting_session"

def is_user_in_prelocke(user_id):
    for pl in DATA_CACHE.get("prelocke", {}).values():

        # 👇 solo bloquea si el prelocke sigue en fase activa
        if pl.get("status", "active") == "active":
            if user_id in pl.get("players", []):
                return True

    return False

def get_user_match(uid):
    for mid, pl in DATA_CACHE.get("prelocke", {}).items():
        if uid in pl.get("players", []):
            return pl
    return None

async def update_rank(member, new_level):

    guild = member.guild

    # 🔹 1. rango anterior
    old_rank = get_user_rank(member)

    # 🔹 2. detectar rango correcto según nivel
    target_rank = None

    for lvl, role_name in sorted(RANK_LEVELS.items(), reverse=True):
        if new_level >= lvl:
            target_rank = role_name
            break

    if not target_rank:
        return old_rank, old_rank

    new_role = discord.utils.get(guild.roles, name=target_rank)

    if not new_role:
        return old_rank, old_rank

    # 🔹 si ya tiene el rango correcto
    if new_role in member.roles:
        return old_rank, old_rank

    # 🔹 quitar rangos antiguos
    roles_to_remove = [r for r in member.roles if r.name in RANK_LEVELS.values()]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

    # 🔹 añadir nuevo rango
    await member.add_roles(new_role)

    update_league_positions(member.guild)

    await save_cache()

    # 🔹 aviso público
    await on_rank_up(member, target_rank, new_level)

    return old_rank, target_rank

async def on_rank_up(member, rank_name, level):

    guild = member.guild
    canal = discord.utils.get(guild.text_channels, name="【🗞️】noticias")

    if not canal:
        return

    # 🌱 MENSAJE DE BIENVENIDA
    if rank_name == "Joven" and level == 0:
        await canal.send(
            f"🌱 {member.mention} se ha unido a la aventura.\n¡Buena suerte en su viaje Pokémon!",
            reference=None
        )
        return

    mensajes = {
        "Entrenador": "🎒 ¡Comienza su aventura como Entrenador!",
        "Cazabichos": "🐛 Se abre paso en el mundo Pokémon.",
        "Montañero": "🏔️ Supera nuevos desafíos.",
        "Especialista": "🧠 Empieza a destacar entre los entrenadores.",
        "Veterano": "🏅 Su experiencia ya es notable.",
        "Líder de Gimnasio": "🏟️ Se convierte en un referente.",
        "Alto Mando": "🔥 Está entre la élite.",
        "Campeón": "🏆 Ha alcanzado la gloria.",
        "Maestro Pokémon": "👑 Ha alcanzado el nivel máximo."
    }

    texto = mensajes.get(rank_name, "Ha subido de rango.")

    await canal.send(
        f"🌟 {member.mention} ha ascendido a **{rank_name}**!\n{texto}",
        reference=None
    )

def generar_template_tarjeta(ui_skin="default"):

    width, height = 920, 520

    # ================= CARGAR CONFIG =================
    config = {}

    if ui_skin != "default":
        try:
            with open(f"assets/ui_skins/{ui_skin}/config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            config = {}

    # ================= CREAR BASE =================
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    # ================= FONDO =================
    if config.get("background"):

        try:
            bg = Image.open(f"assets/ui_skins/{ui_skin}/{config['background']}").convert("RGBA")
            bg = bg.resize((width, height))
            img.paste(bg, (0, 0))
        except:
            pass

    else:
        # fondo default
        top_color = (34, 40, 49)
        bottom_color = (24, 30, 38)

        for y in range(height):
            ratio = y / height
            r = int(top_color[0]*(1-ratio) + bottom_color[0]*ratio)
            g = int(top_color[1]*(1-ratio) + bottom_color[1]*ratio)
            b = int(top_color[2]*(1-ratio) + bottom_color[2]*ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ================= COLORES =================
    accent = tuple(config.get("accent_color", [90,120,150]))

    draw.rectangle((0, 0, width, 5), fill=accent)
    draw.rectangle((0, height-5, width, height), fill=accent)

    panel_margin = 35

    draw.rounded_rectangle(
        (panel_margin, panel_margin, width-panel_margin, height-panel_margin),
        radius=35,
        fill=(240, 242, 245),
        outline=(60, 80, 110),
        width=4
    )

    # ================= TEXTO =================
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 40)
        label_font = ImageFont.truetype("arialbd.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = label_font = text_font = ImageFont.load_default()

    title = "TARJETA DE ENTRENADOR"
    tw = draw.textlength(title, font=title_font)

    draw.text(((width - tw) / 2, 50), title, fill=(50,70,100), font=title_font)

    # ================= OUTPUT =================
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def update_league_positions(guild):

    ranking = get_sorted_ranking(guild)

    # agrupar por liga
    leagues = {}

    for entry in ranking:
        league = entry["rank"]
        leagues.setdefault(league, []).append(entry)

    # asignar posiciones
    for league, players in leagues.items():
        for i, entry in enumerate(players, start=1):
            uid = str(entry["member"].id)

            if uid in DATA_CACHE["users"]:
                DATA_CACHE["users"][uid]["league_position"] = i

async def add_exp(member, amount):
    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        return

    users[uid]["exp"] += amount

    old_level = users[uid]["nivel"]

    # 🔼 subir niveles en silencio
    while users[uid]["nivel"] < 50 and users[uid]["exp"] >= exp_needed(users[uid]["nivel"]):
        users[uid]["exp"] -= exp_needed(users[uid]["nivel"])
        users[uid]["nivel"] += 1

    if users[uid]["nivel"] >= 50:
        users[uid]["nivel"] = 50
        users[uid]["exp"] = 0

    new_level = users[uid]["nivel"]
    sync_user_pokemon_with_level(users[uid])

    # 🟢 SOLO si ha subido nivel mostramos mensaje
    if new_level > old_level:
        try:
            await member.send(
                f"📈 Has subido al **Nivel {new_level}**."
            )
        except:
            pass

        await apply_level_change(member, users[uid], new_level)

        # ✨ EVOLUCIÓN AUTOMÁTICA
        changed = await check_level_evolution(users[uid])
        if changed:
            try:
                await member.send(
                    f"✨ Tu Pokémon ha evolucionado a **{users[uid]['pokemon'].capitalize()}**."
                )
            except:
                pass

    await save_cache()

async def tirar_maquina(member, machine_type):
    """
    machine_type: 'pokemon_machine' o 'avatar_machine'
    """

    user = DATA_CACHE["users"].get(str(member.id))
    if not user:
        return False, "no_user"

    ensure_inventory(user)
    ensure_monedas(user)

    if user["monedas_dual"] <= 0:
        return False, "no_coins"

    tienda = DATA_CACHE.get("tienda", {})
    pool = tienda.get(machine_type, [])

    if not pool:
        return False, "empty_machine"

    # 🔹 detectar categoría inventario correspondiente
    if machine_type == "pokemon_machine":
        category = "pokemons"
    elif machine_type == "avatar_machine":
        category = "avatars"
    else:
        return False, "invalid_machine"

    owned = set(user["inventory"].get(category, []))
    disponibles = []

    for entry in pool:

        if machine_type == "pokemon_machine":

            base_name = entry["name"]

            # buscar si el usuario ya tiene alguna forma de esta línea evolutiva
            linea_completa = LEVEL_EVOLUTIONS.get(base_name, [base_name])

            tiene_linea = any(p.replace("_shiny", "") in linea_completa for p in owned)

            if not tiene_linea:
                disponibles.append(entry)

        else:
            if entry["name"] not in owned:
                disponibles.append(entry)

    if not disponibles:
        return False, "no_more_items"

    entry = random.choice(disponibles)
    
    premio_base = entry["name"]
    premio_base = apply_shiny_if_lucky(premio_base, member)
    tipo_declared = entry.get("type")

    user["monedas_dual"] -= 1

    if machine_type == "pokemon_machine":

        nivel = user.get("nivel", 0)

        forma_final = get_display_pokemon_name(premio_base, nivel)

        if forma_final not in user["inventory"]["pokemons"]:
            user["inventory"]["pokemons"].append(forma_final)
        
        # ✨ INSIGNIA SHINY
        if "_shiny" in forma_final:
            await give_badge(member, user, "shiny")
        
        try:
            nombre = premio_base.capitalize()
            if "_shiny" in forma_final:
                nombre += " ✨"

            await member.send(
                f"🐾 Has conseguido un nuevo Pokémon: **{nombre}**."
            )
        except:
            pass

        # 🎨 desbloquear skin por tipo declarado
        if tipo_declared:
            skin = TYPE_TO_SKIN.get(tipo_declared)

            if skin and skin not in user["inventory"]["ui_skins"]:
                user["inventory"]["ui_skins"].append(skin)

                try:
                    skin_name = SKIN_DISPLAY_NAMES.get(skin, skin)
                    await member.send(
                        f"🎨 Has desbloqueado una nueva **tarjeta {skin_name}**."
                    )
                except:
                    pass

        await save_cache()

        # 🔹 devolvemos SIEMPRE la base para mostrar en mensaje
        return True, premio_base

    elif machine_type == "avatar_machine":

        user["inventory"]["avatars"].append(premio_base)

        try:
            await member.send(
                f"👤 Has desbloqueado un nuevo avatar: **{premio_base}**."
            )
        except:
            pass

        await save_cache()
        return True, premio_base

def apply_shiny_if_lucky(pokemon_name: str, member=None) -> str:

    chance = SHINY_CHANCE

    if member and is_elite(member):
        chance = SHINY_CHANCE * 1.5   # 50% más probabilidad

    if random.random() < chance:
        return f"{pokemon_name}_shiny"

    return pokemon_name

def ranking_name(member):

    name = member.display_name

    if is_elite(member):
        name = f"{name} 💎"

    return name