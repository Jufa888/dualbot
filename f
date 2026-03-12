import discord
from discord.ext import commands
import requests
import json
import os
import secretos 
import asyncio
import datetime
from PIL import Image
from io import BytesIO
from PIL import ImageFont, ImageDraw, ImageFilter
from discord import app_commands

file_lock = asyncio.Lock()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

#Prefijo del bot
bot = commands.Bot(command_prefix='!', intents=intents)

#Archivos donde se guardan los datos
USERS_FILE = "usuarios.json"
SESSIONS_FILE = "sesiones.json"
DATA_CACHE = {
    "users": {},
    "sessions": {}
}
SPRITE_CACHE = {}

#Starters
STARTERS = {
    "aron": "acero",
    "squirtle": "agua",
    "caterpie": "bicho",
    "dratini": "dragón",
    "mareep": "electrico",
    "gastly": "fantasma",
    "charmander": "fuego",
    "cleffa": "hada",
    "frigibax": "hielo",
    "torchic": "lucha",
    "starly": "normal",
    "bulbasaur": "planta",
    "ralts": "psiquico",
    "larvitar": "roca",
    "froakie": "siniestro",
    "gible": "tierra",
    "bellsprout": "veneno",
    "pidgey": "volador"
}

#Definición de a que nivel se evoluciona (cambio de rol)
EVOLUTIONS = {
    "charmander": [
        (10, "charmeleon"),
        (20, "charizard")
    ],
    "squirtle": [
        (10, "wartortle"),
        (20, "blastoise")
    ],
    "bulbasaur": [
        (10, "ivysaur"),
        (20, "venusaur")
    ]
}

#Color de cada tipo
TYPE_COLORS = {
    "grass": discord.Color.green(),
    "fire": discord.Color.red(),
    "water": discord.Color.blue(),
    "electric": discord.Color.yellow(),
    "psychic": discord.Color.purple(),
    "ice": discord.Color.from_rgb(150, 220, 255),
    "dragon": discord.Color.dark_purple(),
    "dark": discord.Color.dark_gray(),
    "fairy": discord.Color.magenta(),
    "normal": discord.Color.light_grey(),
    "fighting": discord.Color.orange(),
    "flying": discord.Color.teal(),
    "poison": discord.Color.from_rgb(160, 64, 160),
    "ground": discord.Color.from_rgb(200, 180, 120),
    "rock": discord.Color.from_rgb(180, 160, 120),
    "bug": discord.Color.from_rgb(120, 200, 80),
    "ghost": discord.Color.from_rgb(100, 80, 160),
    "steel": discord.Color.from_rgb(180, 180, 200)
}

session_locks = {}

def get_session_lock(session_id):
    if session_id not in session_locks:
        session_locks[session_id] = asyncio.Lock()
    return session_locks[session_id]

#----------------------FUNCIONES JSON-----------------------------------

#Carga los datos (json) del usuario
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

async def save_cache():
    async with file_lock:
        save_data(DATA_CACHE)
#Guarda los datos (json) del usuario
def save_data(data):
    temp_users = USERS_FILE + ".tmp"
    temp_sessions = SESSIONS_FILE + ".tmp"

    with open(temp_users, "w") as f:
        json.dump(data.get("users", {}), f, indent=4)
    os.replace(temp_users, USERS_FILE)

    with open(temp_sessions, "w") as f:
        json.dump(data.get("sessions", {}), f, indent=4)
    os.replace(temp_sessions, SESSIONS_FILE)

async def autosave_task():
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            await save_cache()
        except Exception as e:
            print("AUTOSAVE ERROR:", e)

        await asyncio.sleep(30)

#Añade la experiencia al usuario (uso de admin)
async def add_exp(member, amount):
    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        return

    users[uid]["exp"] += amount

    while users[uid]["exp"] >= exp_needed(users[uid]["nivel"]):
        users[uid]["exp"] -= exp_needed(users[uid]["nivel"])
        users[uid]["nivel"] += 1

    channel = discord.utils.get(member.guild.text_channels, name="【🗞️】noticias")
    if channel:
        await channel.send(
            f"📈 {member.mention} ha subido al **Nivel {users[uid]['nivel']}**!"
        )

    await check_evolution(member, users[uid])


    await save_cache()

#Experiencia necesaria para subir de nivel
def exp_needed(level):
    return 1000

#Función que controla si un usuario llega a un nivel en el cual tiene que evolucionar
async def check_evolution(member, user_data):
    pokemon = user_data["pokemon"]
    nivel = user_data["nivel"]

    if pokemon not in EVOLUTIONS:
        return

    new_pokemon = None  

    for evo_level, evo_name in EVOLUTIONS[pokemon]:
        if nivel >= evo_level:
            new_pokemon = evo_name
        else:
            break  

    if new_pokemon is None or new_pokemon == pokemon:
        return

    guild = member.guild

    old_role = discord.utils.get(guild.roles, name=pokemon.capitalize())
    new_role = discord.utils.get(guild.roles, name=new_pokemon.capitalize())

    if new_role is None:
        return

    if old_role:
        await member.remove_roles(old_role)

    await member.add_roles(new_role)

    user_data["pokemon"] = new_pokemon

    result = requests.get(f"https://pokeapi.co/api/v2/pokemon/{new_pokemon}")
    sprites = result.json()["sprites"]
    gif_url = sprites["versions"]["generation-v"]["black-white"]["animated"]["front_default"]
    if gif_url is None:
        gif_url = sprites["front_default"]

    embed = discord.Embed(
        title="✨ ¡ESTÁ EVOLUCIONANDO!",
        description=f"{member.mention} ha evolucionado a **{new_pokemon.capitalize()}**",
        color=discord.Color.green()
    )
    embed.set_image(url=gif_url)

    channel = discord.utils.get(guild.text_channels, name="【🗞️】noticias")
    if channel:
        await channel.send(embed=embed)


# Función para obtener el ID de un Pokémon (para sprite estático)
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

#Función corazones
MAX_LIVES = 20

async def get_discord_avatar(user):
    asset = user.display_avatar.replace(size=256)
    return await asset.read()

def get_trainer_avatar(avatar):
    try:
        if avatar in ("Masculino", "Rojo"):
            url = "https://play.pokemonshowdown.com/sprites/trainers/red.png"
        else:
            url = "https://play.pokemonshowdown.com/sprites/trainers/green.png"

        r = requests.get(url, timeout=10)
        return r.content if r.status_code == 200 else None

    except Exception as e:
        print("Error trainer avatar:", e)
        return None

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

    return generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=0,
        nivel=nivel,
        exp=exp,
        avatar_pokemon_bytes=trainer_avatar,
        pokemon_sprite_bytes=pokemon_sprite
    )

def generar_tarjeta_entrenador(
    nombre,
    genero,
    rango,
    puntos,
    nivel,
    exp,
    avatar_pokemon_bytes=None,
    discord_avatar_bytes=None,
    pokemon_sprite_bytes=None
):
    width, height = 920, 520

    # 🎨 FONDO degradado oscuro
    top_color = (34, 40, 49)
    bottom_color = (24, 30, 38)

    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(top_color[0]*(1-ratio) + bottom_color[0]*ratio)
        g = int(top_color[1]*(1-ratio) + bottom_color[1]*ratio)
        b = int(top_color[2]*(1-ratio) + bottom_color[2]*ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 🔹 BARRAS estilo UI
    bar_color = (90, 120, 150)
    draw.rectangle((0, 0, width, 5), fill=bar_color)
    draw.rectangle((0, height-5, width, height), fill=bar_color)

    # 🪟 PANEL PRINCIPAL
    panel_margin = 35
    draw.rounded_rectangle(
        (panel_margin, panel_margin, width-panel_margin, height-panel_margin),
        radius=35,
        fill=(240, 242, 245),
        outline=(60, 80, 110),
        width=4
    )

    # borde interior
    draw.rounded_rectangle(
        (panel_margin+6, panel_margin+6, width-panel_margin-6, height-panel_margin-6),
        radius=30,
        outline=(170, 185, 210),
        width=2
    )

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 40)
        label_font = ImageFont.truetype("arialbd.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = label_font = text_font = ImageFont.load_default()

    # 🏷️ TITULO
    title = "TARJETA DE ENTRENADOR"
    tw = draw.textlength(title, font=title_font)
    draw.text(((width - tw) / 2 + 2, 52), title, fill=(0,0,0,80), font=title_font)
    draw.text(((width - tw) / 2, 50), title, fill=(50, 70, 100), font=title_font)

    # línea decorativa
    draw.line(((width - tw) / 2, 95, (width + tw) / 2, 95), fill=(180,190,210), width=2)

    # 🔹 SEPARADOR vertical
    draw.line((440, 120, 440, 400), fill=(210,210,210), width=2)

    # ================= INFO IZQUIERDA =================
    x_text = 80
    y_text = 140

    draw.text((x_text, y_text), "Nombre:", fill=(30,30,30), font=label_font)
    draw.text((x_text+110, y_text), nombre, fill=(30,30,30), font=text_font)

    draw.text((x_text, y_text+40), "Rango:", fill=(30,30,30), font=label_font)
    draw.text((x_text+100, y_text+40), rango, fill=(30,30,30), font=text_font)

    draw.text((x_text, y_text+80), "Puntos de liga:", fill=(30,30,30), font=label_font)
    draw.text((x_text+210, y_text+80), str(puntos), fill=(30,30,30), font=text_font)

    # ================= INSIGNIAS =================
    ins_y = y_text + 140
    draw.text((x_text, ins_y), "INSIGNIAS", fill=(40,40,40), font=label_font)

    circle_y = ins_y + 45
    radius = 18
    spacing = 50

    for i in range(6):
        cx = x_text + i * spacing
        draw.ellipse(
            (cx, circle_y, cx + radius*2, circle_y + radius*2),
            outline=(120,120,120),
            width=3,
            fill=(220,225,235)
        )

    # ================= ENTRENADOR DERECHA =================
    trainer_x = width - 420
    trainer_y = 135

    if avatar_pokemon_bytes:
        trainer = Image.open(BytesIO(avatar_pokemon_bytes)).convert("RGBA")
        trainer = trainer.resize((160, 160), Image.NEAREST)

        # 🕶️ crear sombra
        shadow = Image.new("RGBA", trainer.size, (0, 0, 0, 0))
        shadow_pixels = shadow.load()

        for y in range(trainer.height):
            for x in range(trainer.width):
                if trainer.getpixel((x, y))[3] > 0:
                    shadow_pixels[x, y] = (0, 0, 0, 45)  # 👈 antes 90

        img.paste(shadow, (trainer_x + 3, trainer_y + 4), shadow)  # 👈 antes 6,8
        img.paste(trainer, (trainer_x, trainer_y), trainer)

    # ================= POKÉMON =================
    if pokemon_sprite_bytes:
        sprite = Image.open(BytesIO(pokemon_sprite_bytes)).convert("RGBA")
        sprite = sprite.resize((140, 140), Image.NEAREST)

        # 🕶️ sombra
        shadow = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
        shadow_pixels = shadow.load()

        for y in range(sprite.height):
            for x in range(sprite.width):
                if sprite.getpixel((x, y))[3] > 0:
                    shadow_pixels[x, y] = (0, 0, 0, 45)

        img.paste(shadow, (trainer_x + 153, trainer_y + 44), shadow)
        img.paste(sprite, (trainer_x + 150, trainer_y + 40), sprite)

    # ================= NIVEL / EXP =================
    bloque_center_x = trainer_x + 140
    exp_y = 355

    texto_exp = f"Nivel {nivel}   •   EXP {exp}"
    tw = draw.textlength(texto_exp, font=label_font)
    draw.text((bloque_center_x - tw/2, exp_y), texto_exp, fill=(40,40,40), font=label_font)

    # ===== BARRA EXP =====
    bar_width = 320
    bar_height = 16
    bar_x = bloque_center_x - bar_width // 2
    bar_y = exp_y + 30

    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
        radius=8,
        fill=(210,210,210)
    )

    # 🛡️ convertir a número si es posible
    try:
        nivel_num = int(nivel)
        exp_num = int(exp)
    except:
        nivel_num = 0
        exp_num = 0

    exp_ratio = 0 if nivel_num == 0 else min(exp_num / 1000, 1)
    progress = int(bar_width * exp_ratio)

    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + progress, bar_y + bar_height),
        radius=8,
        fill=(90, 140, 220)
    )

    # brillo superior
    if progress > 4:
        draw.rectangle(
            (bar_x+2, bar_y+2, bar_x+progress-2, bar_y+5),
            fill=(255,255,255,90)
        )

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

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

def hearts(current, MAX_LIVES):
    return "❤️" * current + "🤍" * (MAX_LIVES - current)

async def refrescar_sesion(guild, session_id):
    data = DATA_CACHE
    s = data["sessions"].get(str(session_id))

    if not s:
        return

    channel = guild.get_channel(s.get("channel_id"))
    if not channel:
        return

    try:
        msg = await channel.fetch_message(s.get("s_message"))
    except:
        return

    p1 = guild.get_member(int(s["player1"]))
    p2 = guild.get_member(int(s["player2"]))

    embed = discord.Embed(
        title=f"🎮 Sesión {session_id}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👥 Jugadores",
        value=f"{p1.display_name} vs {p2.display_name}",
        inline=False
    )

    embed.add_field(
        name="❤️ Vidas",
        value=(
            f"{p1.display_name}: **{s['lives'][str(p1.id)]}**\n"
            f"{p2.display_name}: **{s['lives'][str(p2.id)]}**"
        ),
        inline=False
    )

    embed.add_field(
        name="📌 Estado",
        value="🟢 Activa" if s["status"] == "active" else "🔴 Finalizada",
        inline=False
    )

    await msg.edit(embed=embed)

def render_team_inline(team):
    if not team:
        return "—"

    sprites = []
    for p in team:
        sprite = get_pokemon_sprite(p)
        if sprite:
            sprites.append(sprite)

    return " ".join(sprites) if sprites else "—"

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

    # 🔹 generar collages
    file1 = generar_collage(team1, p1.display_name)
    file2 = generar_collage(team2, p2.display_name)

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
                content=f"🧩 Equipo de **{p2.display_name}**",
                attachments=[discord_file2]
            )
        else:
            await msg2.edit(
                content=f"🧩 Equipo de **{p2.display_name}**\n*(sin Pokémon todavía)*",
                attachments=[]
            )
    else:
        if discord_file2:
            new_msg = await channel.send(
                content=f"🧩 Equipo de **{p2.display_name}**",
                file=discord_file2
            )
        else:
            new_msg = await channel.send(
                content=f"🧩 Equipo de **{p2.display_name}**\n*(sin Pokémon todavía)*"
            )

        s["s_team_msg_2"] = new_msg.id

    # 🔹 guardar cambios
    DATA_CACHE["sessions"][str(session_id)] = s
    await save_cache()

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

def obtener_sesion_por_canal(channel_id):
    data = get_data()
    for sid, s in data["sessions"].items():
        if s.get("s_channel") == channel_id and s.get("status") == "active":
            return sid, s
    return None, None

async def enviar_y_borrar(ctx, texto, segundos=7):
    msg = await ctx.send(texto)
    await asyncio.sleep(segundos)

    try:
        await msg.delete()

        # 👇 solo borrar si es un comando escrito
        if hasattr(ctx, "message") and ctx.message and ctx.message.author != bot.user:
            await ctx.message.delete()

    except:
        pass

async def borrar_suave(msg, delay=5):
    try:
        await asyncio.sleep(delay)

        # 👻 Paso 1: vaciar contenido (efecto fade fake)
        await msg.edit(content=" ", embed=None, attachments=[])

        # pequeño tiempo para que el ojo lo perciba
        await asyncio.sleep(0.5)

        await msg.delete()
    except:
        pass
#Función victoria
def score_icons(wins):
    return "🟩" * wins if wins > 0 else "—"

def log_event(s, texto):
    timestamp = datetime.datetime.utcnow().strftime("%d/%m %H:%M")
    s["log"].append(f"[{timestamp}] {texto}")

async def enviar_panel_inicio():
    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🔰】inicio")

    if not canal:
        print("Canal inicio no encontrado")
        return

    texto = (
        "## 🎮 Panel principal\n\n"
        "Usa los botones para navegar por el sistema."
    )

    # evitar duplicados
    async for msg in canal.history(limit=10):
        if msg.author == bot.user and msg.components:
            return

    await canal.purge(limit=5)

    mensaje = await canal.send(
        texto,
        view=PanelInicioView()
    )

    await mensaje.pin()

    # 🧹 borrar mensaje de sistema "ha fijado un mensaje"
    async for msg in canal.history(limit=5):
        if msg.type == discord.MessageType.pins_add:
            try:
                await msg.delete()
            except:
                pass

    print("Panel inicio enviado")

def ensure_inventory(user):
    if "inventory" not in user:
        starter = user.get("pokemon")
        genero = user.get("gender", "Masculino")
        avatar = "Rojo" if user.get("gender") == "Masculino" else "Verde"

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

    # equipado
    if "equipped" not in user:
        user["equipped"] = {
            "avatar": avatar,
            "pokemon": inv["pokemons"][0] if inv["pokemons"] else None,
            "ui_skin": inv["ui_skins"][0] if inv["ui_skins"] else None
        }

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

    if value in user["inventory"][category]:
        user["inventory"][category].remove(value)
        await save_cache()
        return True

    return False

#Funcion pillar sprite 
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

        # 🔥 FIX FORMAS PROBLEMÁTICAS
        if base_name == "aegislash":
            base_name = "aegislash-shield"  # forma estable con sprite

        r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{base_name}", timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()

        sprite = data["sprites"]["front_shiny"] if shiny else data["sprites"]["front_default"]

        # fallback artwork
        if not sprite:
            sprite = data["sprites"]["other"]["official-artwork"]["front_default"]

        # fallback animado
        if not sprite:
            sprite = data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_default"]

        SPRITE_CACHE[name] = sprite
        return sprite

    except Exception as e:
        print("SPRITE ERROR:", e)
        return None

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

def generar_collage(team, player_name=None):
    spacing = 36
    padding = 80
    canvas_height = 250

    # ===============================
    # 🎨 FONDO BASE
    # ===============================
    def crear_canvas(width):
        top_color = (34, 40, 49)
        bottom_color = (24, 30, 38)

        canvas = Image.new("RGBA", (width, canvas_height))

        for y in range(canvas_height):
            ratio = y / canvas_height
            r = int(top_color[0]*(1-ratio) + bottom_color[0]*ratio)
            g = int(top_color[1]*(1-ratio) + bottom_color[1]*ratio)
            b = int(top_color[2]*(1-ratio) + bottom_color[2]*ratio)

            for x in range(width):
                canvas.putpixel((x, y), (r, g, b, 255))

        bar_color = (90, 120, 150)
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
            draw.text((offset_x, offset_y), char, fill=(200, 220, 240), font=font)

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
#----------------------COMANDOS-----------------------------------

@bot.command()
async def r(ctx, *args):
    respuesta = ""
    await ctx.send(respuesta)
#ComandosPR
@bot.command()
async def comandos(ctx):
    await ctx.send("**!addexp <usuario> <cantidad>"+'\n'
                   "!restexp <usuario> <cantidad>"+'\n'
                   "!resetusu <usuario>"+'\n'
                   "!perfil"+'\n'
                   "!clasificacion"+'\n'
                   "!crearsesion <jugador1> <jugador2> <juego> <tipodelocke> <numvidas>"+'\n'
                   "!sesion <id>"+'\n'
                   "!resetsesion <id>"+'\n'
                   "!terminarsesion <id> <ganador>"+'\n'
                   "!borrarsesion <id>"+'\n'
                   "!quitavida <id_sesion> <jugador>"+'\n'
                   "!sumapunto <id_sesion> <jugador>**" 
                   )
#InfoPuntos
@bot.command()
async def infoPuntos(ctx):
    await ctx.send("**GANADOR DEL LOCKE ----> 2 PUNTOS"+'\n'
                   "PERDEDOR DEL LOCKE ----> 1 PUNTO"+'\n'
                   "---------------------------------"+'\n'
                   "GANADOR DE COMBATES ----> 2 PUNTOS"+'\n'
                   "PERDEDOR DE COMBATES ----> 1 PUNTO"+'\n'
                   "---------------------------------"+'\n'
                   "CADA 5 VIDAS QUE SOBREN ----> 1 PUNTO **" 
                   )

#Comando limpiar
@bot.command()
@commands.has_permissions(manage_messages=True)
async def l(ctx, cantidad: int):
    if cantidad <= 0:
        await ctx.send("❌ La cantidad debe ser mayor que 0.")
        return

    if cantidad > 100:
        await ctx.send("❌ No puedes borrar más de 100 mensajes a la vez.")
        return

    await ctx.channel.purge(limit=cantidad + 1)

#Comando de admin para añadir exp
@bot.command()
@commands.has_permissions(administrator=True)
async def addexp(ctx, member: discord.Member, amount: int):
    await add_exp(member, amount)
    await ctx.send(f"➕ {amount} EXP añadida a {member.display_name}")

#Comando de admin para quitar exp
@bot.command()
@commands.has_permissions(administrator=True)
async def restexp(ctx, member: discord.Member, amount: int):
    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        await ctx.send("❌ Ese usuario no tiene datos.")
        return

    users[uid]["exp"] -= amount

    if users[uid]["exp"] < 0:
        users[uid]["exp"] = 0

    await save_cache()
    await ctx.send(f"➖ {amount} EXP retirada a {member.display_name}")

#Comando de admin para resetear usuario
@bot.command()
@commands.has_permissions(administrator=True)
async def resetusu(ctx, member: discord.Member):
    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        await ctx.send("❌ Ese usuario no tiene datos.")
        return

    old_pokemon = users[uid]["pokemon"]
    starter = users[uid]["starter"]

    guild = ctx.guild

    old_role = discord.utils.get(guild.roles, name=old_pokemon.capitalize())
    starter_role = discord.utils.get(guild.roles, name=starter.capitalize())

    if old_role:
        await member.remove_roles(old_role)
    if starter_role:
        await member.add_roles(starter_role)

    users[uid]["pokemon"] = starter
    users[uid]["nivel"] = 0
    users[uid]["exp"] = 0

    await save_cache()

    await ctx.send(f"🔄 {member.display_name} ha sido reseteado")

#Comando para mostrar tarjeta de entrenador
@bot.command()
async def perfil(ctx, member: discord.Member = None):
    # 🔹 borrar el comando inmediatamente
    try:
        await ctx.message.delete()
    except:
        pass

    if member is None:
        member = ctx.author

    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        msg = await ctx.send("❌ Este usuario no tiene datos.")
        await asyncio.sleep(5)
        await msg.delete()
        return

    user = users[uid]

    equipped = user.get("equipped", {})
    pokemon = equipped.get("pokemon") or user.get("pokemon")

    nivel = user.get("nivel", 0)
    exp = user.get("exp", 0)
    nombre = user.get("trainer_name", member.display_name)
    equipped = user.get("equipped", {})
    genero = equipped.get("avatar") or user.get("gender", "—")
    pokemon = equipped.get("pokemon") or user.get("pokemon")
    ui_skin = equipped.get("ui_skin", "default")

    # 🔹 sprite entrenador
    trainer_avatar = get_trainer_avatar(genero)

    # 🔹 sprite Pokémon
    pokemon_sprite = None
    if pokemon:
        url = get_pokemon_sprite(pokemon)
        if url:
            pokemon_sprite = requests.get(url).content

    # 🔹 rango por rol
    rango = get_user_rank(member)

    # 🔹 generar tarjeta
    img = generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=0,
        nivel=nivel,
        exp=exp,
        avatar_pokemon_bytes=trainer_avatar,
        pokemon_sprite_bytes=pokemon_sprite
    )

    file = discord.File(img, filename="perfil.png")

    await ctx.send(
        file=file,
        view=PerfilView()
    )

#Comando para clasificacion
@bot.command()
async def clasificacion(ctx):
    data = DATA_CACHE
    users = data["users"]

    ranking = []

    for uid, user in users.items():
        if not isinstance(user, dict):
            continue
        if "nivel" not in user:
            continue

        ranking.append((
            int(user.get("nivel", 0)),
            int(user.get("exp", 0)),
            uid
        ))

    if not ranking:
        await ctx.send("❌ No hay datos para la clasificación.")
        return

    ranking.sort(reverse=True)

    embed = discord.Embed(
        title="🏆 Clasificación",
        color=discord.Color.gold()
    )

    for i, (nivel, exp, uid) in enumerate(ranking[:10], start=1):
        member = ctx.guild.get_member(int(uid))
        nombre = member.display_name if member else "Usuario desconocido"

        embed.add_field(
            name=f"{i}. {nombre}",
            value=f"Nivel {nivel} · EXP {exp}",
            inline=False
        )

    await ctx.send(embed=embed)

#Comando para crear sesión del dualocke
@bot.command()
@commands.has_permissions(administrator=True)
async def crearsesion(
    ctx,
    player1: discord.Member,
    player2: discord.Member,
    game: str,
    locke_type: str,
    lives: int,
):
    data = DATA_CACHE
    sessions = data["sessions"]

    session_id = str(max([int(x) for x in sessions.keys()], default=0) + 1)

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        player1: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        player2: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    # 📛 Nombre del canal
    channel_name = f"{player1.display_name} vs {player2.display_name}"
    channel = await ctx.guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites
    )

    # 📦 Guardar sesión
    sessions[session_id] = {
        "player1": str(player1.id),
        "player2": str(player2.id),
        "game": game.replace("_", " "),
        "type": locke_type.lower(),
        "status": "active",
        "s_channel": channel.id,
        "s_team_msg_1": None,
        "s_team_msg_2": None,
        "s_message": None,
        "max_lives": lives,
        "log": [],
        "lives": {
            str(player1.id): lives,
            str(player2.id): lives
        },
        "score": {
            str(player1.id): 0,
            str(player2.id): 0
        },
        "winner": None,
        "teams": {
        str(player1.id): [],
        str(player2.id): []
        },
        "created_at": str(datetime.datetime.utcnow()),
        "finished_at": None,
        "voice_channel": None,
        "voice_last_active": None
    }

    # Crear embed igual que antes
    embed = discord.Embed(
    title=f"{player1.display_name}  🆚  {player2.display_name}",
    description=(
    f"**{game.replace('_', ' ')} {locke_type.capitalize()}**\n\n"
    "🟢 ACTIVA\n"),
    color=discord.Color.green()
    )


    # Jugadores y vidas
    max_vidas = lives
    p1_vidas = sessions[session_id]["lives"][str(player1.id)]
    p2_vidas = sessions[session_id]["lives"][str(player2.id)]

    embed.add_field(
        name=f"👤 {player1.display_name}",
        value=f"❤️ {hearts(p1_vidas, max_vidas)} ({p1_vidas}/{max_vidas})\n⚔️ Victorias: {score_icons(sessions[session_id]['score'][str(player1.id)])}",
        inline=False
    )
    embed.add_field(
    name=" ",
    value="----------------------------------------------",
    inline=False
)

    embed.add_field(
        name=f"👤 {player2.display_name}",
        value=f"❤️ {hearts(p2_vidas, max_vidas)} ({p2_vidas}/{max_vidas})\n⚔️ Victorias: {score_icons(sessions[session_id]['score'][str(player2.id)])}",
        inline=False
    )

    # Enviar embed al canal de la sesión
    msg = await channel.send(embed=embed)
    sessions[session_id]["s_message"] = msg.id
    await save_cache()

    # 👇 primero equipos
    await refrescar_collages(sessions[session_id], ctx.guild, session_id)

    # 👇 luego panel
    panel_msg = await channel.send(view=PanelSesionView())

    sessions[session_id]["control_panel"] = panel_msg.id
    await save_cache()

    # Confirmación al admin
    await ctx.send(
        f"✅ **Sesión {session_id} creada**\n"
        f"{player1.display_name} vs {player2.display_name}\n"
        f"Canal: {channel.mention}"
    )
    noticias = discord.utils.get(ctx.guild.text_channels, name="【🗞️】noticias")
    if noticias:
        await noticias.send(
            f"🎮 **Nueva DualLocke iniciada**\n"
            f"{player1.display_name} 🆚 {player2.display_name}\n"
            f"🎯 {game.replace('_', ' ')} {locke_type.capitalize()}"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def quitavida(ctx):
    data = DATA_CACHE
    sessions = data["sessions"]

    sid = None
    s = None

    for k, v in sessions.items():
        if v.get("s_channel") == ctx.channel.id and v.get("status") == "active":
            sid = k
            s = v
            break

    if not s:
        msg = await ctx.send("❌ Este comando solo puede usarse en el canal de una sesión activa.")
        await asyncio.sleep(10)
        await msg.delete()
        await ctx.message.delete()
        return

    uid = str(ctx.author.id)

    if uid not in (s["player1"], s["player2"]):
        msg = await ctx.send("❌ No formas parte de esta sesión.")
        await asyncio.sleep(10)
        await msg.delete()
        await ctx.message.delete()
        return

    # 🔒 LOCK DE SESIÓN
    lock = get_session_lock(sid)

    async with lock:
        data = DATA_CACHE
        s = data["sessions"][sid]

        lives = s["lives"]

        if lives[uid] <= 0:
            msg = await ctx.send("❌ Ya no tienes vidas.")
            await asyncio.sleep(10)
            await msg.delete()
            await ctx.message.delete()
            return

        # 💀 quitar vida
        lives[uid] -= 1
        log_event(s, f"{ctx.author.display_name} pierde una vida ({lives[uid]} restantes)")
        await save_cache()

        vidas_restantes = lives[uid]  # 👈 guardamos para usar fuera del lock

    # 🔓 FUERA DEL LOCK (todo lo pesado)
    if vidas_restantes == 0:
        ganador_id = (
            s["player1"] if uid == s["player2"]
            else s["player2"]
        )

        await enviar_y_borrar(
            ctx,
            f"💀 {ctx.author.display_name} pierde una vida.\n❤️ Vidas restantes: **0**",
            10
        )

        await refrescar_sesion_embed(sid, ctx.guild)

        await finalizar_sesion(
            ctx,
            sid,
            ganador_id,
            mostrar_mensaje=False,
            member=ctx.author
        )

        await asyncio.sleep(10)
        await msg.delete()
        await ctx.message.delete()
        return

    await refrescar_sesion_embed(sid, ctx.guild)
    await enviar_y_borrar(ctx, f"💀 {ctx.author.display_name} pierde una vida.\n❤️ Vidas restantes: **{vidas_restantes}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def sumapunto(ctx):

    sid, s = obtener_sesion_por_canal(ctx.channel.id)
    if not s:
        msg = await ctx.send("❌ Este comando solo puede usarse en el canal de una sesión activa.")
        await asyncio.sleep(10)
        await msg.delete()
        await ctx.message.delete()
        return

    lock = get_session_lock(sid)

    async with lock:
        data = DATA_CACHE
        s = data["sessions"][sid]

        uid = str(ctx.author.id)

        if uid not in (s["player1"], s["player2"]):
            await enviar_y_borrar(ctx, "❌ No formas parte de esta sesión.")
            return

        s["score"][uid] += 1
        log_event(s, f"{ctx.author.display_name} gana un punto (total {s['score'][uid]})")

        await save_cache()

    await refrescar_sesion_embed(sid, ctx.guild)
    await enviar_y_borrar(ctx, f"⚔️ Punto para {ctx.author.display_name}. Total: **{s['score'][uid]}**")

# Comando para añadir Pokémon al equipo
@bot.command()
async def añadepoke(ctx, pokemon: str):

    sid, s = obtener_sesion_por_canal(ctx.channel.id)
    if not s:
        await enviar_y_borrar(ctx, "❌ Este comando solo funciona dentro del canal de la sesión.")
        return

    lock = get_session_lock(sid)

    async with lock:
        data = DATA_CACHE
        s = data["sessions"][sid]

        uid = str(ctx.author.id)

        if uid not in s["teams"]:
            await enviar_y_borrar(ctx, "❌ No formas parte de esta sesión.")
            return

        if not get_pokemon_id(pokemon):
            await enviar_y_borrar(ctx, "❌ Pokémon no válido.")
            return

        team = s["teams"][uid]

        if len(team) >= 6:
            await enviar_y_borrar(ctx, "❌ Tu equipo ya tiene 6 Pokémon.")
            return

        if pokemon.lower() in team:
            await enviar_y_borrar(ctx, "❌ Ese Pokémon ya está en tu equipo.")
            return

        team.append(pokemon.lower())
        log_event(s, f"{ctx.author.display_name} añade {pokemon.capitalize()}")

        await save_cache()

    await refrescar_collages(s, ctx.guild, sid)
    await enviar_y_borrar(ctx, f"✅ {pokemon.capitalize()} añadido a tu equipo.")
    
# Comando para quitar Pokémon del equipo
@bot.command()
async def quitapoke(ctx, pokemon: str):

    sid, s = obtener_sesion_por_canal(ctx.channel.id)
    if not s:
        await enviar_y_borrar(ctx, "❌ Este comando solo funciona dentro del canal de la sesión.")
        return

    lock = get_session_lock(sid)

    async with lock:
        data = DATA_CACHE
        s = data["sessions"][sid]

        uid = str(ctx.author.id)
        team = s["teams"].get(uid, [])

        if pokemon.lower() not in team:
            await enviar_y_borrar(ctx, "❌ Ese Pokémon no está en tu equipo.")
            return

        team.remove(pokemon.lower())
        log_event(s, f"{ctx.author.display_name} quita {pokemon.capitalize()}")

        await save_cache()

    await refrescar_collages(s, ctx.guild, sid)
    await enviar_y_borrar(ctx, f"➖ {pokemon.capitalize()} eliminado del equipo.")

#Comando para ver sesión
@bot.command()
@commands.has_permissions(administrator=True)
async def sesion(ctx):
    data = DATA_CACHE
    sessions = data["sessions"]

    sid = None
    s = None

    # 🔍 Buscar la sesión donde esté el autor
    for session_id, session in sessions.items():
        if ctx.author.id in (int(session["player1"]), int(session["player2"])):
            sid = session_id
            s = session
            break

    if not s:
        await ctx.send("❌ No perteneces a ninguna sesión activa.")
        return

    guild = ctx.guild
    p1 = guild.get_member(int(s["player1"]))
    p2 = guild.get_member(int(s["player2"]))

    if not p1 or not p2:
        await ctx.send("❌ Error al obtener los jugadores.")
        return

    lives = s["lives"]

    # 🧱 EMBED DE LA SESIÓN
    embed = discord.Embed(
        title=f"🎮 Sesión {sid}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👥 Jugadores",
        value=f"{p1.display_name} vs {p2.display_name}",
        inline=False
    )

    embed.add_field(
        name="❤️ Vidas",
        value=(
            f"{p1.display_name}: **{lives[str(p1.id)]}**\n"
            f"{p2.display_name}: **{lives[str(p2.id)]}**"
        ),
        inline=False
    )

    embed.add_field(
        name="📌 Estado",
        value="🟢 Activa" if s["status"] == "active" else "🔴 Finalizada",
        inline=False
    )

    # 🔁 EDITAR o CREAR mensaje
    if s.get("s_message"):
        try:
            msg = await ctx.channel.fetch_message(s["s_message"])
            await msg.edit(embed=embed)
        except:
            msg = await ctx.send(embed=embed)
            s["s_message"] = msg.id
            await save_cache()
    else:
        msg = await ctx.send(embed=embed)
        s["s_message"] = msg.id
        await save_cache()

@bot.command()
async def voz(ctx):
    data = DATA_CACHE
    sessions = data["sessions"]

    sid, s = obtener_sesion_por_canal(ctx.channel.id)
    if not s:
        await ctx.send("❌ Este comando solo funciona dentro de un canal de sesión.")
        return

    # Si ya existe
    if s.get("voice_channel"):
        vc = ctx.guild.get_channel(s["voice_channel"])
        if vc:
            await ctx.send(f"🎤 El canal ya existe ---> {vc.mention}")
            return

    p1 = ctx.guild.get_member(int(s["player1"]))
    p2 = ctx.guild.get_member(int(s["player2"]))

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        p1: discord.PermissionOverwrite(view_channel=True, connect=True),
        p2: discord.PermissionOverwrite(view_channel=True, connect=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    vc = await ctx.guild.create_voice_channel(
        name=f"🔊 {p1.display_name} vs {p2.display_name}",
        overwrites=overwrites,
        reason="Canal de voz DualLocke"
    )

    s["voice_channel"] = vc.id
    s["voice_last_active"] = datetime.datetime.utcnow().isoformat()
    s["voice_warn_3"] = False
    s["voice_warn_2"] = False
    s["voice_warn_1"] = False

    data["sessions"][sid] = s   # 🔥 CLAVE

    await save_cache()

    print(f"[DEBUG] voice_channel guardado para sesión {sid}: {vc.id}")

    await enviar_y_borrar(ctx, f"🎤 Canal de voz creado ---> {vc.mention}", 10)
#Comando para resetear sesión
@bot.command()
async def resetsesion(ctx, session_id: int):
    data = DATA_CACHE
    sid = str(session_id)

    if sid not in data["sessions"]:
        await ctx.send("❌ Sesión no encontrada.")
        return

    s = data["sessions"][sid]

    for pid in s["lives"]:
        s["lives"][pid] = s["max_lives"]
        s["score"][pid] = 0

    s["status"] = "active"

    await save_cache()
    await ctx.send(f"🔄 Sesión {sid} reiniciada.")

@bot.command()
@commands.has_permissions(administrator=True)
async def jeje(ctx):

    guild = ctx.guild

    # =========================
    # 🔹 Crear roles
    # =========================
    sin_registrar = discord.utils.get(guild.roles, name="🆕 Sin registrar")
    if not sin_registrar:
        sin_registrar = await guild.create_role(name="🆕 Sin registrar")
    
    joven = discord.utils.get(guild.roles, name="Joven")
    if not joven:
        joven = await guild.create_role(name="Joven")

    await ctx.send("✅ Roles creados o verificados")

    # =========================
    # 🔹 Buscar canal bienvenido
    # =========================
    canal_bienvenida = discord.utils.get(guild.text_channels, name="【🙋‍♂️】bienvenido")

    if not canal_bienvenida:
        await ctx.send("❌ No encuentro el canal 【🙋‍♂️】bienvenido")
        return

    # =========================
    # 🔹 Ajustar permisos canal bienvenido
    # =========================
    await canal_bienvenida.set_permissions(guild.default_role, view_channel=False)
    await canal_bienvenida.set_permissions(sin_registrar, view_channel=True, send_messages=True)
    await canal_bienvenida.set_permissions(joven, view_channel=True)

    # =========================
    # 🔹 Ajustar resto de canales
    # =========================
    for channel in guild.text_channels:
        if channel == canal_bienvenida:
            continue

        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(sin_registrar, view_channel=False)
        await channel.set_permissions(joven, view_channel=True, send_messages=True)

    await ctx.send("🚀 Sistema de acceso configurado. Puedes borrar este comando si quieres.")

#Comando para terminar sesión
@bot.command()
@commands.has_permissions(administrator=True)
async def terminarsesion(ctx):
    data = DATA_CACHE
    sessions = data["sessions"]

    sid = None
    s = None

    for k, v in sessions.items():
        if v.get("s_channel") == ctx.channel.id and v.get("status") == "active":
            sid = k
            s = v
            break

    if not s:
        await enviar_y_borrar(ctx, "❌ Este comando solo puede usarse dentro de una sesión activa.")
        return

    uid1 = s["player1"]
    uid2 = s["player2"]

    vidas1 = s["lives"][uid1]
    vidas2 = s["lives"][uid2]

    score1 = s["score"][uid1]
    score2 = s["score"][uid2]

    ganador_id = None
    empate = False

    if vidas1 == 0 and vidas2 == 0:
        empate = True
    elif vidas1 > 0 and vidas2 == 0:
        ganador_id = uid1
    elif vidas2 > 0 and vidas1 == 0:
        ganador_id = uid2
    else:
        if score1 == score2:
            empate = True
        else:
            ganador_id = uid1 if score1 > score2 else uid2

    if empate:
        await enviar_y_borrar(ctx, "🤝 **La sesión ha terminado en EMPATE.**", 10)
        await finalizar_sesion(ctx, sid, None, mostrar_mensaje=False)
    else:
        ganador = ctx.guild.get_member(int(ganador_id))
        await enviar_y_borrar(ctx, f"🏆 **Ganador:** {ganador.display_name}", 10)
        await finalizar_sesion(ctx, sid, ganador_id, mostrar_mensaje=False)

#Comando para borrar sesión
@bot.command()
async def borrarsesion(ctx, session_id: int):
    data = DATA_CACHE
    sid = str(session_id)

    if sid not in data["sessions"]:
        await ctx.send("❌ Sesión no encontrada.")
        return

    del data["sessions"][sid]
    await save_cache()

    await ctx.send(f"🗑️ Sesión {sid} eliminada por completo.")

@bot.command()
@commands.has_permissions(administrator=True)
async def cerrarregistro(ctx):

    hist_file = "sesiones_terminadas.json"

    if not os.path.exists(hist_file):
        await ctx.send("❌ No hay sesiones en histórico.")
        return

    with open(hist_file, "r") as f:
        hist = json.load(f)

    sid_encontrado = None
    sesion = None

    for sid, s in hist.items():
        if s.get("review_channel") == ctx.channel.id:
            sid_encontrado = sid
            sesion = s
            break

    if not sesion:
        await ctx.send("❌ Este canal no es un registro activo de sesión.")
        return

    await ctx.send("🧾 Revisión finalizada. Cerrando registro en 5 segundos...")
    await asyncio.sleep(5)

    try:
        await ctx.channel.delete(reason="Registro DualLocke cerrado por admin")
    except:
        pass

    # 🔥 eliminar del histórico si quieres
    del hist[sid_encontrado]

    with open(hist_file + ".tmp", "w") as f:
        json.dump(hist, f, indent=4)

    os.replace(hist_file + ".tmp", hist_file)

async def finalizar_sesion(ctx, sid, ganador_id, mostrar_mensaje, member: discord.Member = None):
    data = DATA_CACHE
    s = data["sessions"][sid]

    # 🔊 eliminar canal de voz si existe
    vc_id = s.get("voice_channel")
    if vc_id:
        vc = ctx.guild.get_channel(vc_id)
        if vc:
            try:
                await vc.delete(reason="Sesión finalizada")
                print(f"[{sid}] 🔇 Canal de voz eliminado al finalizar sesión")
            except Exception as e:
                print("ERROR eliminando VC:", e)

        s["voice_channel"] = None
        s["voice_last_active"] = None
        s["voice_warn_3"] = False
        s["voice_warn_2"] = False
        s["voice_warn_1"] = False

    # 🔒 Blindaje
    if s.get("status") == "finished":
        return

    # 💀 Mensaje de pérdida de vida si aplica
    if mostrar_mensaje and member:
        lives = s["lives"]
        uid = str(member.id)

        await ctx.send(
            f"💀 {member.display_name} pierde una vida.\n"
            f"❤️ Vidas restantes: **{lives[uid]}**"
        )

    # 🏁 Finalizar sesión
    s["status"] = "finished"

    if ganador_id is None:
        s["winner"] = None
    else:
        s["winner"] = str(ganador_id)

    await save_cache()
    await refrescar_sesion_embed(sid, ctx.guild)


    ganador = None
    if ganador_id is not None:
        ganador = ctx.guild.get_member(int(ganador_id))


    noticias = discord.utils.get(ctx.guild.text_channels, name="【🗞️】noticias")
    if noticias:
        if ganador:
            await noticias.send(
                f"🏁 **DualLocke finalizado**\n"
                f"🏆 Ganador: **{ganador.display_name}**"
            )
        else:
            await noticias.send("🏁 **DualLocke finalizado en empate**")
    
    # 📜 Registro admin

    s["finished_at"] = str(datetime.datetime.utcnow())

    registro = discord.utils.get(ctx.guild.text_channels, name="registro-dualocke")

    if registro:
        p1 = ctx.guild.get_member(int(s["player1"]))
        p2 = ctx.guild.get_member(int(s["player2"]))

        await registro.send(
            f"📜 **Registro Sesión {sid}**\n"
            f"{p1.display_name} vs {p2.display_name}\n"
            f"🎮 {s['game']} {s['type']}\n"
            f"🏆 Ganador: {ganador.display_name if ganador else 'Empate'}\n"
            f"📅 Inicio: {s['created_at']}\n"
            f"📅 Fin: {s['finished_at']}\n"
        )

    # 🧨 Canal juego → snapshot + review + borrar canal juego
    channel_id = s.get("s_channel")
    if channel_id:
        channel = ctx.guild.get_channel(channel_id)

        if channel:
            # 📜 historial completo
            log_texto = "\n".join(s.get("log", []))

            # 👤 nombres jugadores
            p1 = ctx.guild.get_member(int(s["player1"]))
            p2 = ctx.guild.get_member(int(s["player2"]))

            nombre_canal = f"revision-dualocke-{p1.display_name.lower()}-{p2.display_name.lower()}"
            nombre_canal = nombre_canal.replace(" ", "-")

            # 🔐 permisos solo admin
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                ctx.guild.me: discord.PermissionOverwrite(view_channel=True),
            }

            for role in ctx.guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True)

            review_channel = await ctx.guild.create_text_channel(
                name=nombre_canal,
                overwrites=overwrites,
                reason="Revisión sesión DualLocke"
            )

            # 🧠 guardar estado
            s["review_channel"] = review_channel.id
            s["status"] = "pending_review"
            await save_cache()

            # =========================
            # 🧩 REENVIAR EMBED FINAL
            # =========================
            try:
                msg_sesion = await channel.fetch_message(s["s_message"])
                await review_channel.send(embed=msg_sesion.embeds[0])
            except:
                pass

           # =========================
           # 🧩 REENVIAR EQUIPOS
           # =========================
            for key in ("s_team_msg_1", "s_team_msg_2"):
                msg_id = s.get(key)

                if not msg_id:
                    continue

                try:
                    msg_equipo = await channel.fetch_message(msg_id)
                except discord.NotFound:
                    continue  # 👈 mensaje ya no existe, normal
                except Exception as e:
                    print("ERROR inesperado equipo:", e)
                    continue

                files = [await a.to_file() for a in msg_equipo.attachments]

                await review_channel.send(
                    content=msg_equipo.content,
                    files=files
                )

            # =========================
            # 📜 HISTORIAL COMPLETO
            # =========================
            partes = [log_texto[i:i+1900] for i in range(0, len(log_texto), 1900)]

            await review_channel.send("🧾 HISTORIAL DEL CANAL")

            for parte in partes:
                await review_channel.send(f"```{parte}```")

            # 📢 aviso final
            await channel.send(
                "🏁 **Sesión finalizada**\n"
                "🔒 El canal se cerrará y pasará a revisión."
            )

            await asyncio.sleep(5)

            await channel.delete(reason="DualLocke finalizado → en revisión")
    # mover a histórico
    hist_file = "sesiones_terminadas.json"

    hist = {}
    if os.path.exists(hist_file):
        with open(hist_file, "r") as f:
            hist = json.load(f)

    hist[sid] = s

    with open(hist_file + ".tmp", "w") as f:
        json.dump(hist, f, indent=4)

    os.replace(hist_file + ".tmp", hist_file)

    del data["sessions"][sid]

# Comando para añadir Pokémon a otro jugador
@bot.command()
@commands.has_permissions(administrator=True)
async def añadepokea(ctx, member: discord.Member, pokemon: str):
    data = DATA_CACHE

    sid, s = obtener_sesion_por_canal(ctx.channel.id)
    if not s:
        await enviar_y_borrar(ctx, "❌ Solo puedes usar este comando en una sesión activa.")
        return

    uid = str(member.id)

    if uid not in (s["player1"], s["player2"]):
        await enviar_y_borrar(ctx, "❌ Este usuario no forma parte de la sesión.")
        return

    if not get_pokemon_id(pokemon):
        await enviar_y_borrar(ctx, "❌ Pokémon no válido.")
        return

    team = s["teams"].setdefault(uid, [])

    if len(team) >= 6:
        await enviar_y_borrar(ctx, "❌ El equipo ya tiene 6 Pokémon.")
        return

    if pokemon.lower() in team:
        await enviar_y_borrar(ctx, "❌ Ese Pokémon ya está en el equipo.")
        return

    team.append(pokemon.lower())
    await save_cache()

    await refrescar_collages(s, ctx.guild, sid)
    await enviar_y_borrar(ctx, f"➕ **{pokemon.capitalize()}** añadido al equipo de {member.display_name}.")

@bot.tree.command(name="perfil", description="Ver tu perfil de entrenador")
async def perfil_slash(interaction: discord.Interaction, usuario: discord.Member = None):

    member = usuario or interaction.user

    data = DATA_CACHE
    users = data["users"]
    uid = str(member.id)

    if uid not in users:
        await interaction.response.send_message(
            "❌ Este usuario no tiene perfil.",
            ephemeral=True
        )
        return

    user = users[uid]

    equipped = user.get("equipped", {})
    pokemon = equipped.get("pokemon") or user.get("pokemon")
    nivel = user.get("nivel", 0)
    exp = user.get("exp", 0)
    nombre = user.get("trainer_name", member.display_name)
    equipped = user.get("equipped", {})

    genero = equipped.get("avatar") or user.get("gender", "—")
    pokemon = equipped.get("pokemon") or user.get("pokemon")
    ui_skin = equipped.get("ui_skin", "default")

    trainer_avatar = get_trainer_avatar(genero)

    pokemon_sprite = None
    if pokemon:
        url = get_pokemon_sprite(pokemon)
        if url:
            pokemon_sprite = requests.get(url).content

    rango = get_user_rank(member)

    img = generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=0,
        nivel=nivel,
        exp=exp,
        avatar_pokemon_bytes=trainer_avatar,
        pokemon_sprite_bytes=pokemon_sprite
    )

    file = discord.File(img, filename="perfil.png")

    await interaction.response.send_message(
        file=file,
        view=PerfilView(),
        ephemeral=True
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def copiarpermisosinicio(ctx):
    guild = ctx.guild

    canal_noticias = discord.utils.get(guild.text_channels, name="【🗞️】noticias")
    canal_inicio = discord.utils.get(guild.text_channels, name="【🔰】inicio")

    if not canal_noticias or not canal_inicio:
        await ctx.send("❌ No encuentro los canales noticias o inicio.")
        return

    # 🔄 copiar overwrites completos
    await canal_inicio.edit(overwrites=canal_noticias.overwrites)

    # 🛠️ asegurar permisos de Joven
    rol_joven = discord.utils.get(guild.roles, name="Joven")
    if rol_joven:
        await canal_inicio.set_permissions(
            rol_joven,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    await ctx.send("✅ Permisos de 【🔰】inicio sincronizados con noticias.")

@bot.command()
@commands.has_permissions(administrator=True)
async def invadd(ctx, member: discord.Member, categoria: str, valor: str):
    if await  inv_add(str(member.id), categoria, valor):
        await ctx.send(f"➕ {valor} añadido a {categoria} de {member.display_name}")
    else:
        await ctx.send("❌ Error")

@bot.command()
@commands.has_permissions(administrator=True)
async def invremove(ctx, member: discord.Member, categoria: str, valor: str):
    if await  inv_remove(str(member.id), categoria, valor):
        await ctx.send(f"➖ {valor} eliminado")
    else:
        await ctx.send("❌ No estaba")

@bot.command()
async def inv(ctx, member: discord.Member = None):
    member = member or ctx.author

    data = DATA_CACHE
    user = data["users"].get(str(member.id))

    if not user:
        await ctx.send("❌ Sin datos")
        return

    ensure_inventory(user)
    inv = user["inventory"]

    texto = (
        f"🎒 Inventario de {member.display_name}\n\n"
        f"🧑 Avatares: {', '.join(inv['avatars']) or '—'}\n"
        f"🐾 Pokémon: {', '.join(inv['pokemons']) or '—'}\n"
        f"🎨 UI: {', '.join(inv['ui_skins']) or '—'}\n"
        f"🏅 Insignias: {', '.join(inv['badges']) or '—'}"
    )

    await ctx.send(texto)

#----------------------EVENTOS-----------------------------------
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

@bot.event
async def on_ready():
    global DATA_CACHE

    DATA_CACHE = load_data() 

    data = DATA_CACHE
    changed = False

    for s in data.get("sessions", {}).values():
        if "status" not in s:
            s["status"] = "active"
            changed = True

    if changed:
        await save_cache()

    bot.loop.create_task(voice_watcher())
    bot.loop.create_task(enviar_panel_bienvenida())
    bot.loop.create_task(enviar_panel_inicio())
    bot.loop.create_task(autosave_task())

    bot.add_view(PanelRegistro())
    bot.add_view(BotonCrearPerfil())
    bot.add_view(PerfilView())
    bot.add_view(VerPerfilView())
    bot.add_view(PanelInicioView())
    bot.add_view(PanelSesionView())

    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)

    print("Slash commands sincronizados (guild)")

    print(f"Estamos dentro {bot.user}")

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="🆕 Sin registrar")
    if role:
        await member.add_roles(role)

    canal = discord.utils.get(member.guild.text_channels, name="【🙋‍♂️】bienvenido")
    if canal:
        await canal.send(
            f"👋 Bienvenido {member.mention}!\n"
            "Para empezar tu aventura escribe **!start**"
        )

#Evento de elección de starter en inicio
@bot.event
async def on_member_update(before, after):
    data = DATA_CACHE
    users = data["users"]
    uid = str(after.id)

    before_roles = {role.name.lower() for role in before.roles}
    after_roles = {role.name.lower() for role in after.roles}

    new_roles = after_roles - before_roles

    for role in new_roles:
        if role in STARTERS:
            if uid in users:
                return  

            users[uid] = {
                "pokemon": role,
                "starter": role,
                "nivel": 0,
                "exp": 0
            }


            await save_cache()

            channel = discord.utils.get(after.guild.text_channels, name="【🗞️】noticias")
            if channel:
                await channel.send(
                    f"🎉 {after.mention} ha elegido a **{role.capitalize()}** como su Pokémon inicial!"
                )

@bot.event
async def on_voice_state_update(member, before, after):
    if not after.channel and not before.channel:
        return

    data = DATA_CACHE
    sessions = data["sessions"]
    changed = False

    for sid, s in sessions.items():
        vc_id = s.get("voice_channel")
        if not vc_id:
            continue

        if (after.channel and after.channel.id == vc_id) or (
            before.channel and before.channel.id == vc_id
        ):
            s["voice_last_active"] = datetime.datetime.utcnow().isoformat()
            changed = True

    if changed:
        await save_cache()

async def voice_watcher():
    await bot.wait_until_ready()
    print("🟢 Voice watcher iniciado")

    while not bot.is_closed():
        data = DATA_CACHE
        sessions = data["sessions"]
        changed = False

        for sid, s in sessions.items():
            vc_id = s.get("voice_channel")
            if not vc_id:
                continue

            vc = bot.get_channel(vc_id)
            if not vc:
                s["voice_channel"] = None
                s["voice_last_active"] = None
                s["voice_warn_3"] = False
                s["voice_warn_2"] = False
                s["voice_warn_1"] = False
                changed = True
                continue

            players = {int(s["player1"]), int(s["player2"])}
            members_in_vc = [m for m in vc.members if m.id in players]

            now = datetime.datetime.utcnow()

            # 🟢 alguien dentro → reset contador
            if members_in_vc:
                s["voice_last_active"] = now.isoformat()
                s["voice_warn_3"] = False
                s["voice_warn_2"] = False
                s["voice_warn_1"] = False
                changed = True
                continue

            if not s.get("voice_last_active"):
                continue

            last = datetime.datetime.fromisoformat(s["voice_last_active"])
            elapsed = (now - last).total_seconds()

            text_channel = bot.get_channel(s["s_channel"])

            print(f"[{sid}] ⏱️ {int(elapsed)}s sin actividad")

            # 🔔 aviso 3 min
            if 0 <= elapsed < 60 and not s.get("voice_warn_3"):
                if text_channel:
                    aviso = await text_channel.send("⏳ La sala de voz se cerrará en **3 minutos** si no se utiliza.")
                    await asyncio.sleep(5)
                    await aviso.delete()
                s["voice_warn_3"] = True
                changed = True

            # 🔔 aviso 2 min
            if 60 <= elapsed < 120 and not s.get("voice_warn_2"):
                if text_channel:
                    aviso = await text_channel.send("⏳ La sala de voz se cerrará en **2 minutos** si no se utiliza.")
                    await asyncio.sleep(5)
                    await aviso.delete()
                s["voice_warn_2"] = True
                changed = True

            # 🔔 aviso 1 min
            if 120 <= elapsed < 180 and not s.get("voice_warn_1"):
                if text_channel:
                    aviso = await text_channel.send("⏳ La sala de voz se cerrará en **1 minuto**. si no se utiliza")
                    await asyncio.sleep(5)
                    await aviso.delete()
                s["voice_warn_1"] = True
                changed = True

            # 🔇 cierre
            if elapsed >= 180:
                print(f"[{sid}] 🔇 Cerrando canal")

                if text_channel:
                    aviso = await text_channel.send("🔇 Sala de voz cerrada por inactividad.")
                    await asyncio.sleep(5)
                    await aviso.delete()

                try:
                    await vc.delete(reason="Canal de voz inactivo")
                except Exception as e:
                    print("ERROR borrando VC:", e)

                s["voice_channel"] = None
                s["voice_last_active"] = None
                s["voice_warn_3"] = False
                s["voice_warn_2"] = False
                s["voice_warn_1"] = False
                changed = True

        if changed:
            await save_cache()

        await asyncio.sleep(20)

#----------------------CLASES-----------------------------------

class SeleccionarItemView(discord.ui.View):
    def __init__(self, parent_view, category):
        super().__init__(timeout=120)
        self.parent_view = parent_view
        self.category = category

        data = DATA_CACHE
        user = data["users"][str(parent_view.user_id)]
        ensure_inventory(user)

        opciones = [
            discord.SelectOption(label=str(item).capitalize(), value=str(item))
            for item in user["inventory"][category]
        ]

        self.add_item(SeleccionarItemSelect(opciones, parent_view, category))

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.parent_view)

class SeleccionarItemSelect(discord.ui.Select):
    def __init__(self, options, editor_view, category):
        super().__init__(placeholder="Selecciona", options=options)
        self.editor_view = editor_view   # 👈 nombre nuevo
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        valor = self.values[0]

        if self.category == "avatars":
            self.editor_view.temp_equipped["avatar"] = valor
        elif self.category == "pokemons":
            self.editor_view.temp_equipped["pokemon"] = valor
        elif self.category == "ui_skins":
            self.editor_view.temp_equipped["ui_skin"] = valor

        # 👇 no manda mensaje
        await interaction.response.defer()

        # 🔄 refresca la tarjeta existente
        await self.editor_view.refrescar_preview(interaction)

class EditarPerfilView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

        data = DATA_CACHE
        user = data["users"][str(user_id)]
        ensure_inventory(user)

        self.temp_equipped = user["equipped"].copy()

    async def refrescar_preview(self, interaction: discord.Interaction):
        data = DATA_CACHE
        user = data["users"][str(self.user_id)]

        preview = generar_preview_desde_equipped(
            interaction.user,
            user,
            self.temp_equipped
        )

        file = discord.File(preview, filename="perfil.png")

        # 👇 actualiza el mismo mensaje efímero
        await interaction.edit_original_response(
            attachments=[file],
            view=self
        )

    # 🧑 AVATAR
    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.secondary, emoji="🧑")
    async def avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
        view=SeleccionarItemView(self, "avatars")
    )

    # 🐾 POKEMON
    @discord.ui.button(label="Pokémon", style=discord.ButtonStyle.secondary, emoji="🐾")
    async def pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):
       await interaction.response.edit_message(
        view=SeleccionarItemView(self, "pokemons")
    )

    # 🎨 UI
    @discord.ui.button(label="UI", style=discord.ButtonStyle.secondary, emoji="🎨")
    async def ui(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
        view=SeleccionarItemView(self, "ui_skins")
    )

    # 💾 GUARDAR
    @discord.ui.button(label="Guardar", style=discord.ButtonStyle.success, emoji="💾")
    async def guardar(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = DATA_CACHE
        user = data["users"][str(self.user_id)]

        user["equipped"] = self.temp_equipped
        await save_cache()

        preview = generar_preview_desde_equipped(
            interaction.user,
            user,
            user["equipped"]
        )

        file = discord.File(preview, filename="perfil.png")

        await interaction.response.edit_message(
            attachments=[file],
            view=PerfilView()
        )
    
    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
        emoji="↩️",
        row=1
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = DATA_CACHE
        user = data["users"][str(self.user_id)]

        # 👈 restaurar equipado original
        preview = generar_preview_desde_equipped(
            interaction.user,
            user,
            user["equipped"]
        )

        file = discord.File(preview, filename="perfil.png")

        await interaction.response.edit_message(
            attachments=[file],
            view=PerfilView()
        )

class PanelInicioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Perfil", style=discord.ButtonStyle.primary, emoji="👤", custom_id="inicio_perfil")
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        data = DATA_CACHE
        users = data["users"]
        uid = str(member.id)

        if uid not in users:
            await interaction.response.send_message("❌ No tienes perfil creado.", ephemeral=True)
            return

        user = users[uid]

        equipped = user.get("equipped", {})
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        nivel = user.get("nivel", 0)
        exp = user.get("exp", 0)
        nombre = user.get("trainer_name", member.display_name)
        equipped = user.get("equipped", {})

        genero = equipped.get("avatar") or user.get("gender", "—")
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        ui_skin = equipped.get("ui_skin", "default")

        trainer_avatar = get_trainer_avatar(genero)

        pokemon_sprite = None
        if pokemon:
            url = get_pokemon_sprite(pokemon)
            if url:
                pokemon_sprite = requests.get(url).content

        rango = get_user_rank(member)

        img = generar_tarjeta_entrenador(
            nombre=nombre,
            genero=genero,
            rango=rango,
            puntos=0,
            nivel=nivel,
            exp=exp,
            avatar_pokemon_bytes=trainer_avatar,
            pokemon_sprite_bytes=pokemon_sprite
        )

        file = discord.File(img, filename="perfil.png")

        await interaction.response.send_message(
            file=file,
            view=PerfilView(),
            ephemeral=True
        )

    @discord.ui.button(label="Mi clasificación", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="inicio_miclasif")
    async def miclasif(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ Próximamente…", ephemeral=True)

    @discord.ui.button(label="Top clasificación", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="inicio_top")
    async def top(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ Próximamente…", ephemeral=True)

    @discord.ui.button(label="Buscar rival", style=discord.ButtonStyle.success, emoji="🔎", custom_id="inicio_buscar")
    async def buscar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ Próximamente…", ephemeral=True)

    @discord.ui.button(label="Botón sesión", style=discord.ButtonStyle.secondary, emoji="🎮", custom_id="inicio_sesion")
    async def sesion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠️ Próximamente…", ephemeral=True)

class VerPerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="👤 Ver mi perfil",
        style=discord.ButtonStyle.primary,
        custom_id="ver_perfil_btn"
    )
    async def ver_perfil(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        data = DATA_CACHE
        users = data["users"]
        uid = str(member.id)

        if uid not in users:
            await interaction.response.send_message(
                "❌ Aún no tienes perfil creado.",
                ephemeral=True
            )
            return

        user = users[uid]

        equipped = user.get("equipped", {})
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        nivel = user.get("nivel", 0)
        exp = user.get("exp", 0)
        nombre = user.get("trainer_name", member.display_name)
        equipped = user.get("equipped", {})

        genero = equipped.get("avatar") or user.get("gender", "—")
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        ui_skin = equipped.get("ui_skin", "default")

        trainer_avatar = get_trainer_avatar(genero)

        pokemon_sprite = None
        if pokemon:
            url = get_pokemon_sprite(pokemon)
            if url:
                pokemon_sprite = requests.get(url).content

        rango = get_user_rank(member)

        img = generar_tarjeta_entrenador(
            nombre=nombre,
            genero=genero,
            rango=rango,
            puntos=0,
            nivel=nivel,
            exp=exp,
            avatar_pokemon_bytes=trainer_avatar,
            pokemon_sprite_bytes=pokemon_sprite
        )

        file = discord.File(img, filename="perfil.png")

        await interaction.response.send_message(
            file=file,
            view=PerfilView(),
            ephemeral=True
        )

class PerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✏️ Editar perfil",
        style=discord.ButtonStyle.secondary,
        custom_id="perfil_editar",
        row=0
    )
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = DATA_CACHE
        user = data["users"][str(interaction.user.id)]
        ensure_inventory(user)

        view = EditarPerfilView(interaction.user.id)

        preview = generar_preview_desde_equipped(
            interaction.user,
            user,
            user["equipped"]
        )

        file = discord.File(preview, filename="perfil.png")

        await interaction.response.edit_message(
            attachments=[file],
            view=view
        )

    # 👇 BOTÓN CERRAR (a la derecha)
    @discord.ui.button(
        label="Cerrar",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="perfil_cerrar"
    )
    async def cerrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

class BotonCrearPerfil(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Crear perfil",
        style=discord.ButtonStyle.success,
        custom_id="boton_crear_perfil"
    )
    async def crear(self, interaction: discord.Interaction, button: discord.ui.Button):
        # abrir panel individual
        img = generar_tarjeta_entrenador(
            nombre="—",
            genero="—",
            rango="—",
            puntos="—",
            nivel=0,
            exp=0
        )

        file = discord.File(img, "tarjeta.png")

        await interaction.response.send_message(
            file=file,
            view=PanelRegistro(),
            ephemeral=True  # 👈 SOLO PARA ESTE USUARIO
        )

class NombreModal(discord.ui.Modal, title="Nombre de entrenador"):

    nombre = discord.ui.TextInput(
        label="Tu nombre",
        placeholder="Ej: Rojo"
    )

    def __init__(self, panel, user_id):
        super().__init__()
        self.panel = panel
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        user = self.panel.get_user(self.user_id)
        user["nombre"] = self.nombre.value

        await interaction.response.defer()
        await self.panel.actualizar_pantalla(interaction)

class PanelRegistro(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.user_data = {}

        # 🔒 botón crear empieza desactivado
        self.finalizar_btn.disabled = True

    def get_user(self, uid):
        if uid not in self.user_data:
            self.user_data[uid] = {"genero": None, "nombre": None, "starter": None}
        return self.user_data[uid]

    # 🔎 comprobar si todo está completo
    def check_completo(self, user):
        return all(user.values())

    async def actualizar_pantalla(self, interaction: discord.Interaction):
        user = self.get_user(interaction.user.id)

        # 👉 activar botón si todo listo
        self.finalizar_btn.disabled = not self.check_completo(user)

        pokemon_sprite = None
        if user["starter"]:
            sprite_url = get_pokemon_sprite(user["starter"])
            if sprite_url:
                pokemon_sprite = requests.get(sprite_url).content

        trainer_avatar = None
        if user["genero"]:
            trainer_avatar = get_trainer_avatar(user["genero"])

        img = generar_tarjeta_entrenador(
            nombre=user["nombre"] or "—",
            genero=user["genero"] or "—",
            rango="—",
            puntos=0,
            nivel=0,
            exp=0,
            avatar_pokemon_bytes=trainer_avatar,
            pokemon_sprite_bytes=pokemon_sprite
        )

        file = discord.File(img, filename="tarjeta.png")

        try:
            await interaction.response.edit_message(
                attachments=[file],
                view=self
            )
        except:
            await interaction.edit_original_response(
                attachments=[file],
                view=self
            )

    # ================= ORDEN UI =================

    # 1️⃣ NOMBRE
    @discord.ui.button(
        label="✏️ Nombre",
        style=discord.ButtonStyle.secondary,
        custom_id="registro_nombre"
    )
    async def nombre_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NombreModal(self, interaction.user.id))

    # 2️⃣ AVATAR
    @discord.ui.select(
        placeholder="Elige tu avatar",
        custom_id="registro_avatar",
        options=[
            discord.SelectOption(label="Rojo", value="Masculino"),
            discord.SelectOption(label="Verde", value="Femenino")
        ]
    )
    async def avatar_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        user = self.get_user(interaction.user.id)
        user["genero"] = select.values[0]

        await interaction.response.defer()
        await self.actualizar_pantalla(interaction)

    # 3️⃣ STARTER
    @discord.ui.select(
        placeholder="Elige tu inicial",
        custom_id="registro_starter",
        options=[discord.SelectOption(label=name.capitalize(), value=name) for name in STARTERS.keys()]
    )
    async def starter_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        user = self.get_user(interaction.user.id)
        user["starter"] = select.values[0]

        await interaction.response.defer()
        await self.actualizar_pantalla(interaction)

    # 4️⃣ CREAR PERFIL
    @discord.ui.button(
        label="Crear",
        style=discord.ButtonStyle.success,
        custom_id="registro_finalizar"
    )
    async def finalizar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = self.get_user(interaction.user.id)

        if not self.check_completo(user):
            await interaction.response.send_message(
                "❌ Completa todos los pasos primero.",
                ephemeral=True
            )
            return

        member = interaction.user
        data = DATA_CACHE
        users = data["users"]
        uid = str(member.id)

        avatar_map = {
            "Masculino": "Rojo",
            "Femenino": "Verde"
        }

        avatar_equipped = avatar_map.get(user["genero"], "Rojo")

        users[uid] = {
            "pokemon": user["starter"].lower(),
            "starter": user["starter"].lower(),
            "nivel": users.get(uid, {}).get("nivel", 0),
            "exp": users.get(uid, {}).get("exp", 0),
            "trainer_name": user["nombre"],
            "gender": user["genero"],
            "equipped": {
                "avatar": avatar_equipped,
                "pokemon": user["starter"].lower(),
                "ui_skin": "default"
            },
            "updated_at": str(datetime.datetime.utcnow())
        }

        ensure_inventory(users[uid])

        await save_cache()

        guild = interaction.guild
        sin_registro = discord.utils.get(guild.roles, name="🆕 Sin registrar")
        joven = discord.utils.get(guild.roles, name="Joven")
        canal_bienvenida = discord.utils.get(guild.text_channels, name="【🙋‍♂️】bienvenido")

        if sin_registro:
            await member.remove_roles(sin_registro)

        if joven and joven not in member.roles:
            await member.add_roles(joven)

        if canal_bienvenida:
            await canal_bienvenida.set_permissions(member, view_channel=False)

        await interaction.response.defer()
        await interaction.delete_original_response()

class PanelSesionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # 💀 PERDER VIDA
    @discord.ui.button(
        label="Perder vida",
        style=discord.ButtonStyle.danger,
        emoji="💀",
        custom_id="panel_perder_vida"
    )
    async def perder_vida(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()  # 👈 PRIMERO RESPONDER

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        await quitavida(ctx)

    # ⚔️ SUMAR VICTORIA
    @discord.ui.button(
        label="Sumar victoria",
        style=discord.ButtonStyle.success,
        emoji="⚔️",
        custom_id="panel_sumar_punto"
    )
    async def sumar_punto(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        await sumapunto(ctx)

    # ➕ AÑADIR POKEMON
    @discord.ui.button(
        label="Añadir Pokémon",
        style=discord.ButtonStyle.primary,
        emoji="➕",
        custom_id="panel_add_poke"
    )
    async def add_poke(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddPokemonModal())

    # ➖ QUITAR POKEMON
    @discord.ui.button(
        label="Quitar Pokémon",
        style=discord.ButtonStyle.secondary,
        emoji="➖",
        custom_id="panel_remove_poke"
    )
    async def remove_poke(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemovePokemonModal())

    @discord.ui.button(
    label="Evolucionar",
    style=discord.ButtonStyle.secondary,  # luego explico color
    emoji="✨",
    custom_id="panel_evolucionar"
    )
    async def evolucionar(self, interaction: discord.Interaction, button: discord.ui.Button):

        sid, s = obtener_sesion_por_canal(interaction.channel.id)
        if not s:
            return

        team = s["teams"].get(str(interaction.user.id), [])

        # 🔎 filtrar los que pueden evolucionar
        evolucionables = [p for p in team if puede_evolucionar(p)]

        if not evolucionables:
            await interaction.response.send_message(
                "❌ Ningún Pokémon de tu equipo puede evolucionar.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Selecciona el Pokémon a evolucionar:",
            view=EvolucionarView(evolucionables, sid),
            ephemeral=True
        )

class EvolucionarSelect(discord.ui.Select):
    def __init__(self, team, sid):
        options = [
            discord.SelectOption(label=p.capitalize(), value=p)
            for p in team
        ]

        super().__init__(
            placeholder="Selecciona el Pokémon a evolucionar",
            options=options
        )

        self.sid = sid

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer()

        # 🧹 borrar el mensaje del dropdown inmediatamente
        try:
            await interaction.delete_original_response()
        except:
            pass

        pokemon_original = self.values[0]

        # 🔍 detectar shiny
        if pokemon_original.endswith("_shiny"):
            pokemon = pokemon_original.replace("_shiny", "")
            shiny = True
        else:
            pokemon = pokemon_original
            shiny = False

        try:
            r = requests.get(
                f"https://pokeapi.co/api/v2/pokemon-species/{pokemon}",
                timeout=10
            )

            if r.status_code != 200:
                await interaction.response.send_message(
                    "❌ No se pudo consultar la evolución (API).",
                    ephemeral=True
                )
                return

            data = r.json()
            evo_chain_url = data["evolution_chain"]["url"]

            evo_data_req = requests.get(evo_chain_url, timeout=10)

            if evo_data_req.status_code != 200:
                await interaction.response.send_message(
                    "❌ Error obteniendo cadena evolutiva.",
                    ephemeral=True
                )
                return

            evo_data = evo_data_req.json()

        except Exception as e:
            print("EVO API ERROR:", e)
            await interaction.response.send_message(
                "❌ Error conectando con PokéAPI.",
                ephemeral=True
            )
            return

        def buscar_evo(chain, name):
            if chain["species"]["name"] == name:
                if chain["evolves_to"]:
                    return chain["evolves_to"][0]["species"]["name"]

            for evo in chain["evolves_to"]:
                res = buscar_evo(evo, name)
                if res:
                    return res
            return None

        evolucion = buscar_evo(evo_data["chain"], pokemon)

        if not evolucion:
            await interaction.response.send_message(
                "❌ Este Pokémon no puede evolucionar.",
                ephemeral=True
            )
            return

        sid = self.sid
        lock = get_session_lock(sid)

        async with lock:
            data = DATA_CACHE
            s = data["sessions"][sid]

            uid = str(interaction.user.id)
            team = s["teams"][uid]

            # 👇 IMPORTANTE usar original
            idx = team.index(pokemon_original)

            nuevo_nombre = f"{evolucion}_shiny" if shiny else evolucion
            team[idx] = nuevo_nombre

            nombre_final = evolucion.capitalize() + (" ✨" if shiny else "")

            log_event(
                s,
                f"{interaction.user.display_name} evoluciona {pokemon_original} → {nuevo_nombre}"
            )

            await save_cache()

        await refrescar_collages(s, interaction.guild, sid)

        msg = await interaction.channel.send(
            f"✨ **{pokemon.capitalize()} evolucionó a {nombre_final}!**"
        )

        await asyncio.sleep(10)

        try:
            await msg.delete()
        except:
            pass

        # 👇 borrar dropdown si sigue existiendo
        try:
            await interaction.delete_original_response()
        except:
            pass

class EvolucionarView(discord.ui.View):
    def __init__(self, team, sid):
        super().__init__(timeout=60)
        self.add_item(EvolucionarSelect(team, sid))

class AddPokemonModal(discord.ui.Modal, title="Añadir Pokémon"):

    pokemon = discord.ui.TextInput(
        label="Nombre del Pokémon",
        placeholder="Ej: charmander  |  charmander_shiny"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        sid, s = obtener_sesion_por_canal(ctx.channel.id)
        if not s:
            return

        lock = get_session_lock(sid)

        async with lock:
            data = DATA_CACHE
            s = data["sessions"][sid]

            uid = str(ctx.author.id)
            team = s["teams"][uid]

            if len(team) >= 6:
                await ctx.send("❌ Tu equipo ya tiene 6 Pokémon.", delete_after=5)
                return

            nombre = self.pokemon.value.lower().strip()

            # 🔍 detectar shiny
            if nombre.endswith("_shiny"):
                base_name = nombre.replace("_shiny", "")
                shiny = True
            else:
                base_name = nombre
                shiny = False

            if not get_pokemon_id(base_name):
                await ctx.send("❌ Pokémon no válido.", delete_after=5)
                return

            if nombre in team:
                await ctx.send("❌ Ese Pokémon ya está en tu equipo.", delete_after=5)
                return

            team.append(nombre)

            log_event(s, f"{ctx.author.display_name} añade {nombre}")
            await save_cache()

        await refrescar_collages(s, ctx.guild, sid)

        await ctx.send(
            f"✅ {base_name.capitalize()}{' ✨' if shiny else ''} añadido al equipo.",
            delete_after=5
        )

class RemovePokemonModal(discord.ui.Modal, title="Quitar Pokémon"):
    pokemon = discord.ui.TextInput(
        label="Nombre del Pokémon",
        placeholder="Ej: pikachu  |  pikachu_shiny"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        await quitapoke(ctx, self.pokemon.value.lower())

class EvolucionarModal(discord.ui.Modal, title="Evolucionar Pokémon"):

    actual = discord.ui.TextInput(label="Pokémon actual")
    evolucion = discord.ui.TextInput(label="Evolución")

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer()

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        sid, s = obtener_sesion_por_canal(ctx.channel.id)
        if not s:
            return

        lock = get_session_lock(sid)

        async with lock:
            data = DATA_CACHE
            s = data["sessions"][sid]

            uid = str(ctx.author.id)
            team = s["teams"].get(uid, [])

            actual = self.actual.value.lower()
            evolucion = self.evolucion.value.lower()

            if actual not in team:
                await ctx.send("❌ Ese Pokémon no está en tu equipo.", delete_after=6)
                return

            if not get_pokemon_id(evolucion):
                await ctx.send("❌ Evolución no válida.", delete_after=6)
                return

            index = team.index(actual)
            team[index] = evolucion

            log_event(s, f"{ctx.author.display_name} evoluciona {actual} → {evolucion}")

            await save_cache()

        await refrescar_collages(s, ctx.guild, sid)

        await ctx.send(
            f"✨ **{actual.capitalize()} ha evolucionado a {evolucion.capitalize()}!**",
            delete_after=6
        )

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

async def enviar_panel_bienvenida():
    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🙋‍♂️】bienvenido")

    if not canal:
        print("Canal bienvenido no encontrado")
        return

    texto = (
        "## 👋 Bienvenido al servidor\n\n"
        "Pulsa el botón para crear tu perfil y comenzar tu aventura."
    )

    # 🔍 comprobar si ya existe panel
    async for msg in canal.history(limit=10):
        if msg.author == bot.user and msg.components:
            return  # 👈 ya existe, no enviar otro

    mensaje = await canal.send(
        texto,
        view=BotonCrearPerfil()
    )

    await mensaje.pin()

    print("Panel de bienvenida enviado")

async def enviar_panel_perfil():
    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🗞️】noticias")

    if not canal:
        print("Canal noticias no encontrado")
        return

    texto = (
        "## 👤 Panel de Perfil\n\n"
        "Pulsa el botón para ver tu tarjeta de entrenador."
    )

    # evita duplicados al reiniciar
    async for msg in canal.history(limit=10):
        if msg.author == bot.user and msg.components:
            return

    mensaje = await canal.send(
        texto,
        view=VerPerfilView()
    )

    await mensaje.pin()
    print("Panel de perfil enviado")

async def get_avatar_bytes(user):
    asset = user.display_avatar.replace(size=128)
    return await asset.read()

def get_user_rank(member: discord.Member):
    if not member.roles:
        return "—"

    # ignorar @everyone
    roles = [r for r in member.roles if r.name != "@everyone"]

    if not roles:
        return "—"

    return roles[-1].name
#----------------------ARRANQUE-----------------------------------
bot.run(secretos.TOKEN)