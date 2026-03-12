import discord
from discord.ext import commands
import requests
import json
import os
import secretos 
import asyncio
import datetime
from logic import *
from ui import *
from discord import app_commands

GUILD_ID = 1468388666899566605

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

#Prefijo del bot
bot = commands.Bot(command_prefix='!', intents=intents)

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

async def autosave_task():
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            await save_cache()
        except Exception as e:
            print("AUTOSAVE ERROR:", e)

        await asyncio.sleep(30)

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

async def get_discord_avatar(user):
    asset = user.display_avatar.replace(size=256)
    return await asset.read()

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

    # 🧹 quitar todos los rangos de progresión
    roles_rango = [r for r in member.roles if r.name in RANK_LEVELS.values()]
    if roles_rango:
        await member.remove_roles(*roles_rango)

    # ➕ poner Joven
    rol_joven = discord.utils.get(ctx.guild.roles, name="Joven")
    if rol_joven:
        await member.add_roles(rol_joven)

    # 📢 mensaje de bienvenida opcional
    await on_rank_up(member, "Joven", 0)


    await save_cache()

    await ctx.send(f"🔄 {member.display_name} ha sido reseteado")

@bot.command()
@commands.has_permissions(administrator=True)
async def migrardisponibilidad(ctx):

    changed, total = migrate_add_available_field()

    if changed:
        await save_cache()
        await ctx.send(f"✅ Campo 'available' añadido a {total} usuarios.")
    else:
        await ctx.send("ℹ️ Todos los usuarios ya tenían el campo.")

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
    ranking = get_sorted_ranking(ctx.guild)
    print("MI RANGO:", rango)
    print("RANKS EN RANKING:", [r["rank"] for r in ranking])
    posicion = None
    liga = None

    for entry in ranking:
        if entry["member"].id == member.id:
            liga = entry["rank"]
            break

    if liga:
        misma_liga = [r for r in ranking if r["rank"] == liga]

        for i, r in enumerate(misma_liga, start=1):
            if r["member"].id == member.id:
                posicion = i
                break

    if posicion is None:
        posicion = 1
    # 🔹 generar tarjeta
    img = generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=posicion,
        nivel=nivel,
        exp=exp,
        avatar_pokemon_bytes=trainer_avatar,
        pokemon_sprite_bytes=pokemon_sprite,
        skin=ui_skin
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

@bot.command()
@commands.has_permissions(administrator=True)
async def giveskins(ctx):

    uid = str(ctx.author.id)
    data = DATA_CACHE
    users = data["users"]

    if uid not in users:
        await ctx.send("❌ No tienes perfil.")
        return

    user = users[uid]

    # asegurar inventario
    ensure_inventory(user)

    skins = [
        "fire","water","grass","electric","ice","fighting","poison","ground",
        "rock","bug","ghost","dragon","psychic","flying","steel","fairy",
        "normal","dark"
    ]

    añadidas = 0

    for skin in skins:
        if skin not in user["inventory"]["ui_skins"]:
            user["inventory"]["ui_skins"].append(skin)
            añadidas += 1

    await save_cache()

    await ctx.send(f"🎨 {añadidas} skins añadidas a tu inventario.")

import json, os

@bot.command()
@commands.has_permissions(administrator=True)
async def cambiarskin(ctx):

    skins_path = "skins"

    if not os.path.exists(skins_path):
        await ctx.send("❌ No existe la carpeta skins.")
        return

    # 🎨 PALETA BASE
    base_config = {
        "trainer_card": {
            "bg_top": [198, 185, 140],       # caqui claro
            "bg_bottom": [178, 165, 120],    # caqui oscuro
            "panel": [235, 232, 220],        # panel interior
            "panel_border": [70, 95, 140],   # azul oscuro
            "accent": [210, 90, 70],         # rojo sutil
            "text": [35, 35, 35],
            "title": [60, 90, 140]
        },
        "team_card": {
            "bg_top": [198, 185, 140],
            "bg_bottom": [178, 165, 120],
            "accent": [210, 90, 70],
            "bar": [60, 90, 140]
        }
    }

    count = 0

    for skin_name in os.listdir(skins_path):

        skin_folder = os.path.join(skins_path, skin_name)
        if not os.path.isdir(skin_folder):
            continue

        config_path = os.path.join(skin_folder, "config.json")

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(base_config, f, indent=4)

        count += 1

    await ctx.send(f"🎨 {count} skins actualizadas con el nuevo estilo.")

@bot.command()
async def plantilla_skin(ctx):

    img = lg.generar_template_tarjeta()
    file = discord.File(img, filename="plantilla_tarjeta.png")

    await ctx.send(
        "🎨 Plantilla base para crear skins",
        file=file
    )


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
    privada=False
):
    data = DATA_CACHE
    sessions = data["sessions"]

    session_id = str(max([int(x) for x in sessions.keys()], default=0) + 1)

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),

        player1: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            read_message_history=True
        ),

        player2: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=False,
            read_message_history=True
        ),

        ctx.guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True
        )
    }

    if privada:
        channel_name = f"privado-{player1.display_name}-vs-{player2.display_name}".lower().replace(" ", "-")
    else:
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
        "privada": privada,
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
    # 🔒 PRIVADA → mensaje de confirmación (al final)
    if privada:

        await channel.send(
            f"🎮 **Sesión privada**\n\n"
            f"{player2.mention}, ¿aceptas la sesión contra **{player1.display_name}**?",
            view=AceptarSesionPrivadaView(player2.id, session_id)
        )

    sessions[session_id]["control_panel"] = panel_msg.id
    await save_cache()

    # Confirmación al admin
    if not channel_name.startswith("privado-"):

        await ctx.send(
            f"✅ **Sesión {session_id} creada**\n"
            f"{player1.display_name} vs {player2.display_name}\n"
            f"Canal: {channel.mention}"
        )
    # 🔒 PRIVADA → no anunciar
    if not channel_name.startswith("privado-"):

        noticias = discord.utils.get(ctx.guild.text_channels, name="【🗞️】noticias")

        if noticias:
            await noticias.send(
                f"**Nuevo Dualocke iniciad0**\n"
                f"{player1.display_name} 🆚 {player2.display_name}\n"
                f"{game.replace('_', ' ')} {locke_type.capitalize()}"
            )

@bot.command()
@commands.has_permissions(administrator=True)
async def quitavida(ctx):

    res = await quitar_vida_logic(
        ctx.author.id,
        ctx.channel.id,
        ctx.author.display_name
    )

    if not res["ok"]:
        if res["error"] == "no_session":
            await enviar_y_borrar(ctx, "❌ No hay sesión activa.")
        elif res["error"] == "not_player":
            await enviar_y_borrar(ctx, "❌ No formas parte de esta sesión.")
        elif res["error"] == "no_lives":
            await enviar_y_borrar(ctx, "❌ Ya no tienes vidas.")
        return

    await refrescar_sesion_embed(res["sid"], ctx.guild)

    await enviar_y_borrar(
        ctx,
        f"💀 {ctx.author.display_name} pierde una vida.\n❤️ Vidas restantes: **{res['vidas']}**"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def sumapunto(ctx):

    res = await sumar_punto_logic(
        ctx.author.id,
        ctx.channel.id,
        ctx.author.display_name
    )

    if not res["ok"]:
        if res["error"] == "no_session":
            await enviar_y_borrar(ctx, "❌ No hay sesión activa.")
        elif res["error"] == "not_player":
            await enviar_y_borrar(ctx, "❌ No formas parte de esta sesión.")
        return

    await refrescar_sesion_embed(res["sid"], ctx.guild)
    await enviar_y_borrar(
        ctx,
        f"⚔️ Punto para {ctx.author.display_name}. Total: **{res['puntos']}**"
    )

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

        p1: discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True
        ),

        p2: discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True
        ),

        ctx.guild.me: discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True
        )
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

    # ❌ sin ganador, sin anuncios
    await finalizar_sesion(ctx, sid, None, mostrar_mensaje=False)

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
async def cerrarregistro(ctx, *, ganador_nombre: str):

    ganador = None

    for member in ctx.guild.members:
        if (
            ganador_nombre.lower() == member.display_name.lower()
            or ganador_nombre.lower() == member.name.lower()
        ):
            ganador = member
            break

    if not ganador:
        await ctx.send("❌ No se encontró ese usuario.")
        return

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
    
    # 🔁 Reactivar matchmaking para los jugadores
    p1_id = sesion["player1"]
    p2_id = sesion["player2"]

    users = DATA_CACHE["users"]

    if p1_id in users and p2_id in users:

        users[p1_id]["available"] = True
        users[p2_id]["available"] = True

        users[p1_id].setdefault("recent_matches", [])
        users[p2_id].setdefault("recent_matches", [])

        users[p1_id]["recent_matches"].append(p2_id)
        users[p2_id]["recent_matches"].append(p1_id)

        users[p1_id]["recent_matches"] = users[p1_id]["recent_matches"][-2:]
        users[p2_id]["recent_matches"] = users[p2_id]["recent_matches"][-2:]

        # =========================
        # 🧹 LIMPIAR MATCHMAKING
        # =========================

        remove_from_queue(p1_id)
        remove_from_queue(p2_id)

        # limpiar prelocke
        for mid, pl in list(DATA_CACHE["prelocke"].items()):
            if p1_id in pl["players"] or p2_id in pl["players"]:
                del DATA_CACHE["prelocke"][mid]

        # limpiar lobby
        for cid, lobby in list(DATA_CACHE["lobby"].items()):
            if p1_id in lobby["players"] or p2_id in lobby["players"]:
                del DATA_CACHE["lobby"][cid]

        await save_cache()

    await ctx.send("🧾 Revisión finalizada. Cerrando registro en 5 segundos...")
    noticias = discord.utils.get(ctx.guild.text_channels, name="【🗞️】noticias")

    if noticias:
        await noticias.send(
            f"🏁 **Dualocke finalizado**\n"
            f"🏆 Ganador: **{ganador.display_name}**"
        )
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

    
    # 📜 Registro admin

    s["finished_at"] = str(datetime.datetime.utcnow())

    # 🔒 Si es sesión privada, no hacer sistema de revisión
    # 🔒 sesión privada → cerrar directamente
    if s.get("privada"):

        channel = ctx.guild.get_channel(s.get("s_channel"))

        if channel:
            await channel.send("🏁 **Sesión privada finalizada.**")
            await asyncio.sleep(5)
            await channel.delete(reason="Sesión privada finalizada")

        del DATA_CACHE["sessions"][sid]
        await save_cache()
        return

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

            nombre_canal = f"revision-dualocke-{sid}-{p1.display_name.lower()}-{p2.display_name.lower()}"
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

            # 📩 Aviso a administración
            staff_channel = discord.utils.get(ctx.guild.text_channels, name="tickets-admin")

            if staff_channel:

                p1 = ctx.guild.get_member(int(s["player1"]))
                p2 = ctx.guild.get_member(int(s["player2"]))

                await staff_channel.send(
                    "📨 **Sesión DualLocke finalizada para revisión**\n\n"
                    f"👥 {p1.display_name} vs {p2.display_name}\n"
                    f"🔹 Discord: {p1.name} vs {p2.name}\n"
                    f"🎮 Juego: {s['game']}\n"
                    f"⚙️ Modalidad: {s['type']}\n\n"
                    f"📂 Canal de revisión: {review_channel.mention}",
                    view=TicketAdminView()
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

@bot.command()
async def disponible(ctx, estado: str = None):

    uid = str(ctx.author.id)

    if estado is None:
        user = DATA_CACHE["users"].get(uid)
        if not user:
            await ctx.send("❌ No tienes perfil.")
            return

        estado_actual = "🟢 Disponible" if user.get("available") else "🔴 No disponible"
        await ctx.send(f"Tu estado: {estado_actual}")
        return

    valor = estado.lower() in ["si", "sí", "true", "on", "1"]

    ok, error = set_user_available(uid, valor)

    if not ok:
        if error == "in_session":
            await ctx.send("❌ Estás en una sesión activa.")
        else:
            await ctx.send("❌ Error.")
        return

    await save_cache()

    if valor:
        await ctx.send("🟢 Ahora estás disponible para matchmaking.")
    else:
        await ctx.send("🔴 Ya no estás disponible.")

@bot.command()
@commands.has_permissions(administrator=True)
async def pepino(ctx):

    uid = str(ctx.author.id)
    users = DATA_CACHE["users"]

    if uid not in users:
        await ctx.send("❌ No tienes perfil.")
        return

    actual = users[uid].get("test_mode", False)
    nuevo = not actual

    users[uid]["test_mode"] = nuevo
    await save_cache()

    txt = "🧪 TEST MODE ACTIVADO" if nuevo else "🧪 TEST MODE DESACTIVADO"
    await ctx.send(txt)

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

    # 🔹 calcular ranking real
    ranking = get_sorted_ranking(member.guild)

    liga = [r for r in ranking if r["rank"] == rango]

    posicion = None
    for i, r in enumerate(liga, start=1):
        if int(r["member"].id) == int(member.id):
            posicion = i
            break

    if posicion is None:
        posicion = 1

    img = generar_tarjeta_entrenador(
        nombre=nombre,
        genero=genero,
        rango=rango,
        puntos=posicion,
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

@bot.command()
@commands.has_permissions(administrator=True)
async def juju(ctx):

    data = DATA_CACHE
    uid = str(ctx.author.id)

    if uid not in data["users"]:
        await ctx.send("❌ No tienes perfil creado.")
        return

    user = data["users"][uid]

    # asegurar estructura
    ensure_inventory(user)

    inv = user["inventory"]

    # 🎒 AVATARES
    inv["avatars"] = ["Rojo", "Verde"]

    # 🐾 TODOS LOS POKEMON (los iniciales definidos)
    inv["pokemons"] = list(STARTERS.keys())

    # 🎨 UI skins
    inv["ui_skins"] = ["default"]

    # 🏅 insignias (vacío o puedes meter test)
    inv["badges"] = []

    # ⚙️ equipado por defecto si no existe
    user.setdefault("equipped", {
        "avatar": "Rojo",
        "pokemon": inv["pokemons"][0],
        "ui_skin": "default"
    })

    await save_cache()

    await ctx.send("🧃 Inventario completo desbloqueado. Modo admin ON 😎")

@bot.command()
@commands.has_permissions(administrator=True)
async def resetmatch(ctx, user1_id: str = None, user2_id: str = None):
    """
    Limpia completamente el estado de matchmaking.
    Si pasas IDs → solo limpia esos usuarios
    Si no pasas nada → limpia TODO
    """

    data = lg.DATA_CACHE

    # 🔹 función para limpiar usuario
    def limpiar_usuario(uid):
        if uid in data["users"]:
            data["users"][uid]["available"] = False
            data["users"][uid]["recent_matches"] = []

        lg.remove_from_queue(uid)

    # =========================
    # 🧹 LIMPIEZA GLOBAL
    # =========================
    if not user1_id and not user2_id:

        # limpiar cola
        data["queue"] = []

        # limpiar disponibilidad y cooldown
        for uid in data["users"]:
            data["users"][uid]["available"] = False
            data["users"][uid]["recent_matches"] = []

        # limpiar prelocke y lobby
        data["prelocke"].clear()
        data["lobby"].clear()

        await lg.save_cache()

        await ctx.send("🧹 Matchmaking global reseteado.")
        return

    # =========================
    # 🧹 LIMPIEZA POR USUARIOS
    # =========================
    limpiar_usuario(user1_id)

    if user2_id:
        limpiar_usuario(user2_id)

    # borrar prelockes donde estén
    to_delete = []
    for mid, pl in data["prelocke"].items():
        if user1_id in pl["players"] or (user2_id and user2_id in pl["players"]):
            to_delete.append(mid)

    for mid in to_delete:
        del data["prelocke"][mid]

    # borrar lobby
    to_delete = []
    for cid, lobby in data["lobby"].items():
        if user1_id in lobby["players"] or (user2_id and user2_id in lobby["players"]):
            to_delete.append(cid)

    for cid in to_delete:
        del data["lobby"][cid]

    await lg.save_cache()

    await ctx.send("🧹 Matchmaking reseteado para los usuarios.")

@bot.command()
@commands.has_permissions(administrator=True)
async def puntuacion(ctx):

    texto = (
        "📊 **Chuleta de puntuación DualLocke**\n\n"

        "🏆 Resultado del locke\n"
        "• Ganador → 3 pts\n"
        "• Perdedor → 1 pt\n\n"

        "⚔️ Combates totales\n"
        "• Gana más combates → 2 pts\n"
        "• Pierde → 1 pt\n\n"

        "❤️ Vidas sobrantes\n"
        "• Cada 5 vidas → +1 pt\n\n"

        "━━━━━━━━━━━━━━\n"
        "⭐ Máximo aprox: 8 pts\n\n"

        "📈 Conversión EXP\n"
        "👉 1 punto = 650 EXP\n\n"

        "🧮 Ejemplos\n"
        "• 8 pts → 5200 EXP\n"
        "• 6 pts → 3900 EXP\n"
        "• 3 pts → 1950 EXP\n\n"
    )

    await ctx.send(texto)

@bot.command()
@commands.has_permissions(administrator=True)
async def vampiro(ctx):

    guild = ctx.guild

    permisos_base = discord.Permissions(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        connect=True,
        speak=True,
        use_voice_activation=True,
        add_reactions=True,
        attach_files=True,
        embed_links=True
    )

    ignorar = ["@everyone", "🆕 Sin registrar"]

    cambiados = 0

    for role in guild.roles:
        if role.name in ignorar:
            continue

        try:
            await role.edit(permissions=permisos_base)
            cambiados += 1
        except Exception as e:
            print("Error vampiro:", role.name, e)

    await ctx.send(f"🧛 Permisos normalizados en {cambiados} roles.", delete_after=5)

@bot.command()
async def ruleta(ctx):
    if not lg.is_elite(ctx.author):
        await ctx.send(
            "💎 La ruleta personalizada es exclusiva para usuarios **Élite**. Más información en el canal【📋】información"
        )
        return

    modal = RuletaModal(ctx.author.id)

    # necesitamos interaction para abrir modal, así que enviamos botón
    view = RuletaStartView(ctx.author.id)

    await ctx.send(
        "🎡 **Crear ruleta**",
        view=view
    )


@bot.command()
async def statspokemon(ctx):
    if not lg.is_elite(ctx.author):
        await ctx.send(
            "💎 Esta función es exclusiva para usuarios **Élite**. Más información en el canal【📋】información"
        )
        return

    view = StatsPokemonStartView(ctx.author.id)

    await ctx.send(
        "📊 **Consultar estadísticas de Pokémon**",
        view=view
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def rls(ctx):

    guild = ctx.guild
    lineas = []

    lineas.append(f"=== DIAGNÓSTICO DE PERMISOS: {guild.name} ===\n")

    for channel in guild.channels:

        lineas.append(f"\n--- CANAL: #{channel.name} ({type(channel).__name__}) ---")

        overwrites = channel.overwrites

        for target, perms in overwrites.items():

            if isinstance(target, discord.Role):
                nombre = f"ROL: {target.name}"
            else:
                nombre = f"USER: {target.name}"

            p = perms

            resumen = (
                f"ver:{p.view_channel} | "
                f"enviar:{p.send_messages if hasattr(p,'send_messages') else '-'} | "
                f"hablar:{p.connect if hasattr(p,'connect') else '-'} | "
                f"admin:{p.administrator}"
            )

            lineas.append(f"{nombre} → {resumen}")

    texto = "\n".join(lineas)

    # ⚠️ Discord límite 2000 chars → dividir
    chunks = [texto[i:i+1900] for i in range(0, len(texto), 1900)]

    for chunk in chunks:
        await ctx.send(f"```{chunk}```")

@bot.command(name="diag_usuario_full")
@commands.has_permissions(administrator=True)
async def diag_usuario_full(ctx, member: discord.Member):

    guild = ctx.guild
    lineas = []

    lineas.append(f"=== DIAGNÓSTICO DE VISIBILIDAD PARA: {member.display_name} ===\n")

    for channel in guild.channels:

        perms = channel.permissions_for(member)
        visible = perms.view_channel

        estado = "✅ VE" if visible else "❌ NO VE"

        lineas.append(f"\n--- {channel.name} ({type(channel).__name__}) → {estado}")

        # 🔎 analizar overwrites
        overwrites = channel.overwrites

        for target, overwrite in overwrites.items():

            if isinstance(target, discord.Role) and target in member.roles:

                if overwrite.view_channel is False:
                    lineas.append(f"   🚫 DENY por rol: {target.name}")

                elif overwrite.view_channel is True:
                    lineas.append(f"   ✔️ ALLOW por rol: {target.name}")

        # 📂 revisar categoría
        if channel.category:
            cat_overwrites = channel.category.overwrites

            for target, overwrite in cat_overwrites.items():

                if isinstance(target, discord.Role) and target in member.roles:

                    if overwrite.view_channel is False:
                        lineas.append(f"   🚫 DENY en CATEGORÍA por rol: {target.name}")

                    elif overwrite.view_channel is True:
                        lineas.append(f"   ✔️ ALLOW en CATEGORÍA por rol: {target.name}")

    texto = "\n".join(lineas)

    chunks = [texto[i:i+1900] for i in range(0, len(texto), 1900)]

    for chunk in chunks:
        await ctx.send(f"```{chunk}```")

@bot.command(name="badge_test")
@commands.has_permissions(administrator=True)
async def badge_test(ctx, member: discord.Member, badge_id: str):

    user = lg.DATA_CACHE["users"].get(str(member.id))

    if not user:
        await ctx.send("❌ Ese usuario no tiene perfil")
        return

    added = await lg.give_badge(user, badge_id)

    if added:
        await lg.save_cache()
        await ctx.send(f"🏅 Insignia `{badge_id}` añadida a {member.display_name}")
    else:
        await ctx.send("⚠️ No se añadió (no existe o ya la tenía)")

@bot.command()
@commands.has_permissions(administrator=True)
async def cerbero(ctx, nombre_insignia: str):

    uid = str(ctx.author.id)
    data = DATA_CACHE

    if uid not in data["users"]:
        await ctx.send("❌ No tienes perfil.")
        return

    user = data["users"][uid]
    lg.ensure_inventory(user)

    eliminado = False

    # 🔥 quitar del inventario
    if nombre_insignia in user["inventory"]["badges"]:
        user["inventory"]["badges"].remove(nombre_insignia)
        eliminado = True

    # 🔥 quitar de equipadas
    equipped = user["equipped"].get("badges", [])
    if nombre_insignia in equipped:
        equipped.remove(nombre_insignia)
        eliminado = True

    await lg.save_cache()

    if eliminado:
        await ctx.send(f"🔥 {nombre_insignia} destruida por Cerbero.")
    else:
        await ctx.send("⚠️ No estaba en tu inventario ni equipada.")

@bot.command()
@commands.has_permissions(administrator=True)
async def borrar_usuario(ctx, member: discord.Member):

    uid = str(member.id)

    if uid not in DATA_CACHE["users"]:
        await ctx.send("❌ Ese usuario no tiene perfil.")
        return

    del DATA_CACHE["users"][uid]

    await save_cache()

    await ctx.send(f"🗑️ Perfil de **{member.display_name}** eliminado.")

@bot.tree.command(
    name="panel",
    description="Panel admin",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def panel_slash(interaction: discord.Interaction):

    await interaction.response.send_message(
        "## 🛠️ Panel de administración",
        view=AdminPanelView(),
        ephemeral=True
    )
#----------------------EVENTOS-----------------------------------
@bot.event
async def on_ready():
    data_loaded = load_data()

    DATA_CACHE.clear()
    DATA_CACHE.update(data_loaded)

    # 🔹 estructuras volátiles
    DATA_CACHE.setdefault("search_interactions", {})
    DATA_CACHE.setdefault("queue", [])
    DATA_CACHE.setdefault("matches", {})
    DATA_CACHE.setdefault("prelocke", {})
    DATA_CACHE.setdefault("lobby", {})

    panel_id = DATA_CACHE.get("panel_inicio_msg")

    if panel_id:
        bot.add_view(PanelInicioView(), message_id=panel_id)
    else:
        bot.add_view(PanelInicioView())

    

    # 🔹 asegurar queue
    if "queue" not in DATA_CACHE:
        DATA_CACHE["queue"] = []

    data = DATA_CACHE
    changed = False

    if "matches" not in DATA_CACHE:
        DATA_CACHE["matches"] = {}

    for s in data.get("sessions", {}).values():
        if "status" not in s:
            s["status"] = "active"
            changed = True

    # 🔹 asegurar historial de matchmaking en usuarios
    for uid, user in DATA_CACHE["users"].items():
        if "recent_matches" not in user:
            user["recent_matches"] = []
            changed = True

    DATA_CACHE["tienda"] = load_tienda()

    if changed:
        await save_cache()

    for user in DATA_CACHE["users"].values():
        sync_user_pokemon_with_level(user)

    for guild in bot.guilds:

        elite_role = discord.utils.get(guild.roles, name="Élite")

        for member in guild.members:

            if any(r.name.startswith("Twitch Subscriber") for r in member.roles):

                if elite_role not in member.roles:

                    await member.add_roles(elite_role)

                    user = DATA_CACHE["users"].get(str(member.id))

                    if user:
                        try:
                            await member.send(
                                "💎 **Mensaje de Moncho**\n\n"
                                "Gracias por apoyar el servidor.\n\n"
                                "Has recibido tu **Pack Élite**:\n"
                                "🪙 +2 Monedas Dual\n"
                                "💎 +2 Monedas Élite"
                            )
                        except:
                            pass



    bot.loop.create_task(voice_watcher())
    bot.loop.create_task(enviar_panel_bienvenida(bot))
    bot.loop.create_task(autosave_task())
    bot.loop.create_task(enviar_panel_inicio(bot))
    bot.loop.create_task(elite_rewards_task())
    bot.loop.create_task(enviar_panel_roms(bot))


    # 🔹 views persistentes
    bot.add_view(PanelRegistro())
    bot.add_view(BotonCrearPerfil())
    bot.add_view(PerfilView())
    bot.add_view(VerPerfilView())
    bot.add_view(PanelInicioView())
    bot.add_view(PanelSesionView())
    bot.add_view(TicketAdminView())
    bot.add_view(PanelRomsView())

    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)

    print("📦 Datos cargados en cache")
    await lg.sync_all_user_evolutions()
    print("🔄 Evoluciones sincronizadas")
    print("Slash commands sincronizados (guild)")
    print(f"Estamos dentro {bot.user}")

async def elite_rewards_task():
    await bot.wait_until_ready()

    while not bot.is_closed():

        data = DATA_CACHE
        users = data["users"]

        now = datetime.datetime.utcnow()

        for guild in bot.guilds:

            for member in guild.members:

                if not lg.is_elite(member):
                    continue

                uid = str(member.id)

                if uid not in users:
                    continue

                user = users[uid]

                # 🔧 asegurar campos
                user.setdefault("monedas_dual", 0)
                user.setdefault("monedas_elite", 0)
                user.setdefault("elite_last_reward", None)

                last = user["elite_last_reward"]

                # 👑 primera vez que recibe Élite
                if last is None:

                    ensure_monedas(user)
                    user.setdefault("monedas_dual", 0)
                    user.setdefault("monedas_elite", 0)
                    user["monedas_dual"] += 2
                    user["monedas_elite"] += 2
                    user["elite_last_reward"] = now.isoformat()

                    try:
                        await member.send(
                            "💎 **Mensaje de Moncho**\n\n"
                            "Has recibido tus monedas del **Pack Élite**:\n"
                            "🪙 +2 Monedas Dual\n"
                            "💎 +2 Monedas Élite"
                        )
                    except:
                        pass

                    print(f"[ELITE] Recompensa inicial para {member.display_name}")
                    continue

                last = datetime.datetime.fromisoformat(last)

                # ⏳ esperar 30 días
                if (now - last).days < 30:
                    continue

                # 💎 recompensa mensual
                user["monedas_dual"] += 2
                user["monedas_elite"] += 2
                user["elite_last_reward"] = now.isoformat()

                print(f"[ELITE] Recompensa mensual para {member.display_name}")

        await save_cache()

        await asyncio.sleep(86400)  # revisar cada día

@bot.event
async def on_member_update(before, after):
    data = DATA_CACHE
    users = data["users"]
    uid = str(after.id)

    before_roles = {role.name.lower() for role in before.roles}
    after_roles = {role.name.lower() for role in after.roles}

    new_roles = after_roles - before_roles

    # =========================
    # 💎 DETECTAR ROL ÉLITE
    # =========================

    elite_role = discord.utils.get(after.guild.roles, name="Élite")

    if elite_role:

        before_elite = elite_role in before.roles
        after_elite = elite_role in after.roles

        # 👑 ACABA DE RECIBIR EL ROL
        if not before_elite and after_elite:

            if uid in users:

                user = users[uid]

                user.setdefault("monedas_dual", 0)
                user.setdefault("monedas_elite", 0)
                user.setdefault("elite_last_reward", None)

                # 💎 recompensa inicial
                user["monedas_dual"] += 2
                user["monedas_elite"] += 2
                user["elite_last_reward"] = datetime.datetime.utcnow().isoformat()

                await save_cache()

                print(f"[ELITE] Recompensa inicial para {after.display_name}")

    # =========================
    # TWITCH → ROL ÉLITE
    # =========================

    elite_role = discord.utils.get(after.guild.roles, name="Élite")

    before_twitch = any(r.name.startswith("Twitch Subscriber") for r in before.roles)
    after_twitch = any(r.name.startswith("Twitch Subscriber") for r in after.roles)

    # Recibe sub
    if not before_twitch and after_twitch:
        if elite_role and elite_role not in after.roles:
            await after.add_roles(elite_role)
            print(f"[TWITCH] {after.display_name} recibió Élite")

    # Pierde sub
    if before_twitch and not after_twitch:
        if elite_role and elite_role in after.roles:
            await after.remove_roles(elite_role)
            print(f"[TWITCH] {after.display_name} perdió Élite")


    # =========================
    # ⭐ ELECCIÓN DE STARTER
    # =========================

    for role in new_roles:
        if role in STARTERS:

            if uid in users:
                return

            tipo = STARTERS[role]
            skin_tipo = TYPE_TO_SKIN.get(tipo, "default")

            users[uid] = {
                "pokemon": role,
                "starter": role,
                "nivel": 0,
                "exp": 0
            }

            ensure_inventory(users[uid])

            inv = users[uid]["inventory"]

            if "default" not in inv["ui_skins"]:
                inv["ui_skins"].append("default")

            if skin_tipo not in inv["ui_skins"]:
                inv["ui_skins"].append(skin_tipo)

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

async def sync_roles_with_profiles():
    await bot.wait_until_ready()

    for guild in bot.guilds:

        rol_joven = discord.utils.get(guild.roles, name="Joven")
        if not rol_joven:
            continue

        for member in guild.members:
            uid = str(member.id)

            tiene_perfil = uid in DATA_CACHE["users"]
            tiene_rol = rol_joven in member.roles

            # ❌ Tiene rol pero no perfil → quitar
            if tiene_rol and not tiene_perfil:
                try:
                    await member.remove_roles(rol_joven)
                    print(f"[SYNC] Quitado Joven a {member.display_name}")
                except:
                    pass

            # ⚠️ Tiene perfil pero no rol → añadir (por si acaso)
            if tiene_perfil and not tiene_rol:
                try:
                    await member.add_roles(rol_joven)
                    print(f"[SYNC] Añadido Joven a {member.display_name}")
                except:
                    pass

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
#----------------------ARRANQUE-----------------------------------
bot.run(secretos.TOKEN)