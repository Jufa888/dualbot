import discord
import asyncio
import requests
import datetime
import random
import logic as lg
import time
import io

TYPE_ES = {
    "normal": "Normal",
    "fire": "Fuego",
    "water": "Agua",
    "electric": "Eléctrico",
    "grass": "Planta",
    "ice": "Hielo",
    "fighting": "Lucha",
    "poison": "Veneno",
    "ground": "Tierra",
    "flying": "Volador",
    "psychic": "Psíquico",
    "bug": "Bicho",
    "rock": "Roca",
    "ghost": "Fantasma",
    "dragon": "Dragón",
    "dark": "Siniestro",
    "steel": "Acero",
    "fairy": "Hada"
}

ITEM_ES = {

"fire-stone": "Piedra Fuego",
"water-stone": "Piedra Agua",
"thunder-stone": "Piedra Trueno",
"leaf-stone": "Piedra Hoja",
"moon-stone": "Piedra Lunar",
"sun-stone": "Piedra Solar",
"shiny-stone": "Piedra Día",
"dusk-stone": "Piedra Noche",
"dawn-stone": "Piedra Alba",
"ice-stone": "Piedra Hielo",

"oval-stone": "Piedra Oval",
"kings-rock": "Roca del Rey",
"metal-coat": "Revestimiento Metálico",
"dragon-scale": "Escama Dragón",
"deep-sea-tooth": "Diente Marino",
"deep-sea-scale": "Escama Marina",
"protector": "Protector",
"electirizer": "Electrizador",
"magmarizer": "Magmatizador",
"dubious-disc": "Disco Extraño",
"reaper-cloth": "Tela Terrible",
"prism-scale": "Escama Bella",
"sachet": "Saquito Fragante",
"whipped-dream": "Dulce de Nata",
"cracked-pot": "Tetera Agrietada",
"chipped-pot": "Tetera Auténtica",

# Charcadet
"auspicious-armor": "Armadura Auspiciosa",
"malicious-armor": "Armadura Maliciosa",

# otros
"peat-block": "Bloque de Turba"
}

TRIGGER_ES = {
    "level-up": "Subiendo de nivel",
    "trade": "Intercambio",
    "use-item": "Usando objeto",
    "shed": "Cambio especial"
}

class SeleccionarItemView(discord.ui.View):
    def __init__(self, parent_view, category):
        super().__init__(timeout=120)
        self.parent_view = parent_view
        self.category = category

        data = lg.DATA_CACHE
        user = data["users"][str(parent_view.user_id)]
        lg.ensure_inventory(user)

        if category.startswith("ui_skins"):
            source = user["inventory"]["ui_skins"]
        else:
            source = user["inventory"][category]

        opciones = []

        for item in source:
            
            label = str(item)
            # 🐾 POKÉMON → mostrar forma evolucionada
            if category == "pokemons":
                level = user.get("nivel", 0)
                display_name = lg.get_display_pokemon_name(item, level)
                label = display_name.replace("-", " ").capitalize()

            # 🎨 SKINS → nombre traducido
            elif category.startswith("ui_skins"):
                label = lg.SKIN_DISPLAY_NAMES.get(item, item.capitalize())

            elif category == "badges":
                badge_data = lg.BADGES.get(item, {})
                label = badge_data.get("name", item)

            opciones.append(
                discord.SelectOption(
                    label=label,
                    value=str(item)  # ⚠️ IMPORTANTE mantener el original
                )
            )

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
        elif self.category == "ui_skins_card":
            self.editor_view.temp_equipped["ui_skin_card"] = valor

        elif self.category == "ui_skins_team":
            self.editor_view.temp_equipped["ui_skin_team"] = valor

        # 🔥 elimina el dropdown instantáneamente
        await interaction.response.edit_message(view=None)

        # 🔄 refresca preview
        await self.editor_view.refrescar_preview(interaction)

class EditarPerfilView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

        data = lg.DATA_CACHE
        user = data["users"][str(user_id)]
        lg.ensure_inventory(user)

        self.temp_equipped = user["equipped"].copy()
        self.temp_equipped.setdefault("badges", [])

    async def refrescar_preview(self, interaction: discord.Interaction):
        data = lg.DATA_CACHE
        user = data["users"][str(self.user_id)]

        preview = lg.generar_preview_desde_equipped(
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
    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.secondary, emoji="🟣")
    async def avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
        view=SeleccionarItemView(self, "avatars")
    )

    # 🐾 POKEMON
    @discord.ui.button(label="Pokémon", style=discord.ButtonStyle.secondary, emoji="🔴")
    async def pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):
       await interaction.response.edit_message(
        view=SeleccionarItemView(self, "pokemons")
    )

    # 🎨 UI
    @discord.ui.button(label="Tarjetas", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def ui(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
        view=SeleccionarUISlotView(self)
    )

    @discord.ui.button(label="Insignias", style=discord.ButtonStyle.secondary, emoji="🟡")
    async def insignias(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=MenuInsigniasView(self)
        )

    # 💾 GUARDAR
    @discord.ui.button(label="Guardar", style=discord.ButtonStyle.success)
    async def guardar(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = lg.DATA_CACHE
        user = data["users"][str(self.user_id)]

        user["equipped"] = self.temp_equipped
        await lg.save_cache()

        preview = lg.generar_preview_desde_equipped(
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
        style=discord.ButtonStyle.danger,
        row=1
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = lg.DATA_CACHE
        user = data["users"][str(self.user_id)]

        # 👈 restaurar equipado original
        preview = lg.generar_preview_desde_equipped(
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

    @discord.ui.button(label="Perfil", style=discord.ButtonStyle.primary, custom_id="inicio_perfil")
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.user
        data = lg.DATA_CACHE
        users = data["users"]
        uid = str(member.id)

        if uid not in users:
            await interaction.response.send_message("❌ No tienes perfil creado.", ephemeral=True)
            return

        user = users[uid]

        equipped = user.get("equipped", {})
        nivel = user.get("nivel", 0)
        exp = user.get("exp", 0)
        nombre = user.get("trainer_name", member.display_name)

        genero = equipped.get("avatar") or user.get("gender", "—")
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        ui_skin = equipped.get("ui_skin_card", "default")

        preview = lg.generar_preview_desde_equipped(
            member,
            user,
            equipped
        )
        
        file = discord.File(preview, filename="perfil.png")

        await interaction.response.send_message(
            file=file,
            view=PerfilView(),
            ephemeral=True
        )

    @discord.ui.button(label="Clasificación", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="inicio_clasif")
    async def clasificacion(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "## 📊 Clasificación",
            view=ClasificacionMainView(),
            ephemeral=True
        )

    @discord.ui.button(label="Buscar rival", style=discord.ButtonStyle.success, emoji="🔎", custom_id="inicio_buscar")
    async def buscar(self, interaction: discord.Interaction, button: discord.ui.Button):

        uid = str(interaction.user.id)

        # 🔎 comprobar si ya tiene prelocke
        pl = lg.get_user_match(uid)

        if pl:
            status = pl.get("status", "active")
            p1, p2 = pl["players"]

            rival_id = p2 if uid == p1 else p1
            rival = interaction.guild.get_member(int(rival_id))

            if status == "waiting_session":
                await interaction.response.send_message(
                    "⏳ Ya tienes un locke a punto de comenzar.",
                    ephemeral=True
                )
                return

            canal = None
            for cid, lobby in lg.DATA_CACHE["lobby"].items():
                if uid in lobby.get("players", []):
                    canal = interaction.guild.get_channel(int(cid))
                    break

            user_data = lg.DATA_CACHE["users"][str(rival.id)]
            preview = lg.generar_preview_desde_equipped(
                rival,
                user_data,
                user_data.get("equipped", {})
            )
            file = discord.File(preview, filename="perfil.png")

            await interaction.response.send_message(
                f"🎯 **Rival encontrado: {rival.display_name}**\n\n"
                f"Preparad el locke en {canal.mention if canal else 'el canal prelocke'}.",
                file=file,
                ephemeral=True
            )
            return

        if uid not in lg.DATA_CACHE["users"]:
            await interaction.response.send_message("❌ No tienes perfil.", ephemeral=True)
            return

        user = lg.DATA_CACHE["users"][uid]

        if lg.is_user_in_active_session(uid) and not user.get("test_mode"):
            await interaction.response.send_message(
                "❌ Estás en una sesión activa.",
                ephemeral=True
            )
            return

        if lg.is_user_searching(uid):
            await interaction.response.send_message(
                "🔎 Sigues buscando rival...",
                view=BuscandoRivalView(uid),
                ephemeral=True
            )
            return

        # 🧠 guardar interacción para push
        lg.DATA_CACHE["search_interactions"][uid] = interaction

        ok, tiempo = lg.add_to_queue(uid)

        if not ok:
            await interaction.response.send_message(
                f"⏳ Espera **{tiempo}s** antes de volver a buscar rival.",
                ephemeral=True
            )
            return

        lg.set_user_available(uid, True)

        match = lg.try_matchmaking(interaction.guild)
        await lg.save_cache()

        # 🎯 MATCH
        if match:
            await interaction.response.defer(ephemeral=True)

            p1, p2 = match

            match_id = f"{p1}_{p2}_{int(time.time())}"
            lg.init_prelocke(match_id, p1, p2, data=None)

            channel = await lg.create_prelocke_channel(interaction.guild, p1, p2)

            await channel.send(
                "## 🤝 Preparación del DualLocke\n\nRellenad el formulario y confirmad ambos.",
                view=PrelockeView(match_id)
            )

            lg.register_recent_match(p1, p2)
            await lg.save_cache()

            async def enviar_update(uid_target, rival_id):
                inter = lg.DATA_CACHE["search_interactions"].pop(uid_target, None)
                if not inter:
                    return

                rival_member = interaction.guild.get_member(int(rival_id))
                if not rival_member:
                    return

                user_data = lg.DATA_CACHE["users"][str(rival_member.id)]

                preview = lg.generar_preview_desde_equipped(
                    rival_member,
                    user_data,
                    user_data.get("equipped", {})
                )
                file = discord.File(preview, filename="perfil.png")

                try:
                    await inter.followup.send(
                        f"🎯 **Rival encontrado: {rival_member.display_name}**\n\n"
                        f"Ve al canal {channel.mention} para preparar el locke.",
                        file=file,
                        ephemeral=True
                    )
                except Exception as e:
                    print("ERROR UPDATE MATCH:", e)

            await enviar_update(p1, p2)
            await enviar_update(p2, p1)

            return
        
        await interaction.response.send_message(
            "🔎 Buscando rival...",
            view=BuscandoRivalView(uid),
            ephemeral=True
        )

    @discord.ui.button(
        label="Sesión privada",
        style=discord.ButtonStyle.secondary,
        emoji="🎮",
        custom_id="inicio_sesion_privada"
    )
    async def sesion_privada(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not lg.is_elite(interaction.user):
            await interaction.response.send_message(
                "💎 Crear sesiones privadas es una función exclusiva de usuarios **Élite**. Más información en el canal【📋】información",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(SesionPrivadaModal())

    @discord.ui.button(
        label="Tienda",
        style=discord.ButtonStyle.primary,
        custom_id="inicio_tienda"
    )
    async def abrir_tienda(self, interaction: discord.Interaction, button: discord.ui.Button):

        user_id = interaction.user.id
        uid = str(user_id)

        data = lg.DATA_CACHE
        users = data["users"]

        if uid not in users:
            await interaction.response.send_message(
                "❌ No tienes perfil creado.",
                ephemeral=True
            )
            return

        user = users[uid]

        lg.ensure_inventory(user)
        lg.ensure_monedas(user)

        monedas = user.get("monedas_dual", 0)
        monedas_elite = user.get("monedas_elite", 0)

        await interaction.response.send_message(
            f"🏪 **Tienda Dual**\n\n"
            f"🪙 **Monedas Dual:** {monedas}\n"
            f"💎 **Monedas Élite:** {monedas_elite}\n\n"
            f"Selecciona una máquina:",
            view=TiendaView(user_id),
            ephemeral=True
        )

    @discord.ui.button(
        label="Abrir ticket",
        style=discord.ButtonStyle.danger,
        custom_id="inicio_ticket"
    )
    async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())
    
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
        data = lg.DATA_CACHE
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
        nivel = user.get("nivel", 0)
        exp = user.get("exp", 0)
        nombre = user.get("trainer_name", member.display_name)

        genero = equipped.get("avatar") or user.get("gender", "—")
        pokemon = equipped.get("pokemon") or user.get("pokemon")
        ui_skin = equipped.get("ui_skin_card", "default")

        preview = lg.generar_preview_desde_equipped(
            member,
            user,
            equipped
        )

        file = discord.File(preview, filename="perfil.png")

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

        data = lg.DATA_CACHE
        user = data["users"][str(interaction.user.id)]
        lg.ensure_inventory(user)

        view = EditarPerfilView(interaction.user.id)

        preview = lg.generar_preview_desde_equipped(
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
        img = lg.generar_tarjeta_entrenador(
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
            sprite_url = lg.get_pokemon_sprite(user["starter"])
            if sprite_url:
                pokemon_sprite = requests.get(sprite_url).content

        trainer_avatar = None
        if user["genero"]:
            trainer_avatar = lg.get_trainer_avatar(user["genero"])

        img = lg.generar_tarjeta_entrenador(
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
            discord.SelectOption(label="Rojo", value="Rojo"),
            discord.SelectOption(label="Verde", value="Verde")
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
        options=[discord.SelectOption(label=name.capitalize(), value=name) for name in lg.STARTERS.keys()]
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
        data = lg.DATA_CACHE
        users = data["users"]
        uid = str(member.id)

        # 🚫 evitar crear perfil dos veces
        if uid in users:
            await interaction.response.send_message(
                "❌ Ya tienes un perfil creado.",
                ephemeral=True
            )
            return

        avatar_equipped = user["genero"]

        starter = lg.apply_shiny_if_lucky(user["starter"].lower())

        users[uid] = {
            "pokemon": starter,
            "starter": starter,
            "nivel": None,
            "exp": users.get(uid, {}).get("exp", 0),
            "trainer_name": user["nombre"],
            "gender": user["genero"],
            "available": False,
            "equipped": {
                "avatar": avatar_equipped,
                "pokemon": user["starter"].lower(),
                "ui_skin_card": "default",
                "ui_skin_team": "default"
            },
            "updated_at": str(datetime.datetime.utcnow())
        }

        lg.ensure_inventory(users[uid])

        # ✨ dar insignia si el starter es shiny
        if "_shiny" in starter:
            await lg.give_badge(member, users[uid], "shiny")

        tipo = lg.STARTERS.get(starter)
        skin = lg.TYPE_TO_SKIN.get(tipo)

        if skin and skin not in users[uid]["inventory"]["ui_skins"]:
            users[uid]["inventory"]["ui_skins"].append(skin)

        await lg.save_cache()

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

        await lg.apply_level_change(interaction.user, users[uid], 0)
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

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

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("quitavida")
        await cmd(ctx)

    # ⚔️ SUMAR VICTORIA
    @discord.ui.button(
        label="Sumar victoria",
        style=discord.ButtonStyle.success,
        emoji="⚔️",
        custom_id="panel_sumar_punto"
    )
    async def sumar_punto(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("sumapunto")
        await cmd(ctx)

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

        sid, s = lg.obtener_sesion_por_canal(interaction.channel.id)
        if not s:
            return

        team = s["teams"].get(str(interaction.user.id), [])

        if not team:
            await interaction.response.send_message(
                "❌ No tienes Pokémon en el equipo.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Selecciona el Pokémon a quitar:",
            view=QuitarPokemonView(team, sid),
            ephemeral=True
        )


    @discord.ui.button(
    label="Evolucionar",
    style=discord.ButtonStyle.secondary,  # luego explico color
    emoji="✨",
    custom_id="panel_evolucionar"
    )
    async def evolucionar(self, interaction: discord.Interaction, button: discord.ui.Button):

        sid, s = lg.obtener_sesion_por_canal(interaction.channel.id)
        if not s:
            return

        team = s["teams"].get(str(interaction.user.id), [])

        # 🔎 filtrar los que pueden evolucionar
        evolucionables = [p for p in team if lg.puede_evolucionar(p)]

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

        # 🛑 TERMINAR SESIÓN
    @discord.ui.button(
        label="Terminar sesión",
        style=discord.ButtonStyle.danger,
        emoji="🛑",
        custom_id="panel_terminar_sesion",
    )
    async def terminar_sesion(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "⚠️ **Advertencia**\nAsegúrate de que habéis terminado la sesión.\n**No hay vuelta atrás.**",
            view=ConfirmarTerminarSesionView(),
            ephemeral=True
        )
    
    @discord.ui.button(
        label="Voz",
        style=discord.ButtonStyle.primary,
        emoji="🎤",
        custom_id="panel_voz",
        row=1
    )
    async def voz_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        sid, s = lg.obtener_sesion_por_canal(interaction.channel.id)
        if not s:
            return

        # 🟢 NO EXISTE → crear
        if not s.get("voice_channel"):

            await interaction.response.defer()

            ctx = await interaction.client.get_context(interaction.message)
            ctx.author = interaction.user
            ctx.channel = interaction.channel

            cmd = interaction.client.get_command("voz")
            await cmd(ctx)

            # 🔄 VOLVER A LEER SESIÓN (CLAVE)
            sid, s = lg.obtener_sesion_por_canal(interaction.channel.id)

            if s.get("voice_channel"):
                button.label = "Cerrar voz"
                button.style = discord.ButtonStyle.danger
                button.emoji = "🔇"

                await interaction.message.edit(view=self)

        # 🔴 YA EXISTE → borrar
        else:

            vc = interaction.guild.get_channel(s["voice_channel"])

            if vc:
                try:
                    await vc.delete(reason="Cerrado desde botón")
                except:
                    pass

            # limpiar estado
            s["voice_channel"] = None
            s["voice_last_active"] = None
            s["voice_warn_3"] = False
            s["voice_warn_2"] = False
            s["voice_warn_1"] = False

            await lg.save_cache()

            await interaction.response.send_message(
                "🔇 Canal de voz cerrado.",
                ephemeral=True
            )

            button.label = "Voz"
            button.style = discord.ButtonStyle.primary
            button.emoji = "🎤"

            await interaction.message.edit(view=self)
    @discord.ui.button(
        label="Ruleta",
        style=discord.ButtonStyle.secondary,
        emoji="🎡",
        custom_id="panel_ruleta",
        row=1
    )
    async def ruleta(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "🎡 **Sistema de ruleta**",
            view=RuletaStartView(interaction.user.id),
            ephemeral=True
        )
    
    @discord.ui.button(
        label="Stats Pokémon",
        style=discord.ButtonStyle.secondary,
        emoji="📊",
        custom_id="panel_stats_pokemon",
        row=1
    )
    async def stats_pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "🔎 **Consulta de Pokémon**",
            view=StatsPokemonStartView(interaction.user.id),
            ephemeral=True
        )
    
class ConfirmarTerminarSesionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Sí, terminar", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("terminarsesion")
        await cmd(ctx)

        try:
            await interaction.delete_original_response()
        except:
            pass

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()

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
        await interaction.delete_original_response()

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
        lock = lg.get_session_lock(sid)

        async with lock:
            data = lg.DATA_CACHE
            s = data["sessions"][sid]

            uid = str(interaction.user.id)
            team = s["teams"][uid]

            # 👇 IMPORTANTE usar original
            idx = team.index(pokemon_original)

            nuevo_nombre = f"{evolucion}_shiny" if shiny else evolucion
            team[idx] = nuevo_nombre

            nombre_final = evolucion.capitalize() + (" ✨" if shiny else "")

            lg.log_event(
                s,
                f"{interaction.user.display_name} evoluciona {pokemon_original} → {nuevo_nombre}"
            )

            await lg.save_cache()

        await lg.refrescar_collages(s, interaction.guild, sid)

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

class QuitarPokemonSelect(discord.ui.Select):
    def __init__(self, team, sid):
        options = [
            discord.SelectOption(label=p.capitalize(), value=p)
            for p in team
        ]

        super().__init__(
            placeholder="Selecciona el Pokémon a quitar",
            options=options
        )

        self.sid = sid

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer()
        await interaction.delete_original_response()

        pokemon = self.values[0]
        sid = self.sid

        lock = lg.get_session_lock(sid)

        async with lock:
            data = lg.DATA_CACHE
            s = data["sessions"][sid]

            uid = str(interaction.user.id)
            team = s["teams"][uid]

            if pokemon not in team:
                return

            team.remove(pokemon)

            lg.log_event(
                s,
                f"{interaction.user.display_name} quita {pokemon}"
            )

            await lg.save_cache()

        await lg.refrescar_collages(s, interaction.guild, sid)

        msg = await interaction.channel.send(
            f"➖ **{pokemon.capitalize()}** eliminado del equipo."
        )

        await asyncio.sleep(5)

        try:
            await msg.delete()
        except:
            pass

class QuitarPokemonView(discord.ui.View):
    def __init__(self, team, sid):
        super().__init__(timeout=60)
        self.add_item(QuitarPokemonSelect(team, sid))

class AddPokemonModal(discord.ui.Modal, title="Añadir Pokémon"):

    pokemon = discord.ui.TextInput(
        label="Nombre del Pokémon",
        placeholder="Ej: charmander  |  charmander_shiny"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        sid, s = lg.obtener_sesion_por_canal(ctx.channel.id)
        if not s:
            return

        lock = lg.get_session_lock(sid)

        async with lock:
            data = lg.DATA_CACHE
            s = data["sessions"][sid]

            uid = str(ctx.author.id)
            team = s["teams"][uid]

            if len(team) >= 6:
                await ctx.send("❌ Tu equipo ya tiene 6 Pokémon.", delete_after=5)
                return

            nombre = lg.normalize_pokemon_name(self.pokemon.value)

            # 🔍 detectar shiny
            if nombre.endswith("_shiny"):
                base_name = nombre.replace("_shiny", "")
                shiny = True
            else:
                base_name = nombre
                shiny = False

            if not lg.get_pokemon_id(base_name):
                await ctx.send("❌ Pokémon no válido.", delete_after=5)
                return

            if nombre in team:
                await ctx.send("❌ Ese Pokémon ya está en tu equipo.", delete_after=5)
                return

            team.append(nombre)

            lg.log_event(s, f"{ctx.author.display_name} añade {nombre}")
            await lg.save_cache()

        await lg.refrescar_collages(s, ctx.guild, sid)

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

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("quitapoke")
        await cmd(ctx, self.pokemon.value.lower())

class EvolucionarModal(discord.ui.Modal, title="Evolucionar Pokémon"):

    actual = discord.ui.TextInput(label="Pokémon actual")
    evolucion = discord.ui.TextInput(label="Evolución")

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer()

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        sid, s = lg.obtener_sesion_por_canal(ctx.channel.id)
        if not s:
            return

        lock = lg.get_session_lock(sid)

        async with lock:
            data = lg.DATA_CACHE
            s = data["sessions"][sid]

            uid = str(ctx.author.id)
            team = s["teams"].get(uid, [])

            actual = self.actual.value.lower()
            evolucion = self.evolucion.value.lower()

            if actual not in team:
                await ctx.send("❌ Ese Pokémon no está en tu equipo.", delete_after=6)
                return

            if not lg.get_pokemon_id(evolucion):
                await ctx.send("❌ Evolución no válida.", delete_after=6)
                return

            index = team.index(actual)
            team[index] = evolucion

            lg.log_event(s, f"{ctx.author.display_name} evoluciona {actual} → {evolucion}")

            await lg.save_cache()

        await lg.refrescar_collages(s, ctx.guild, sid)

        await ctx.send(
            f"✨ **{actual.capitalize()} ha evolucionado a {evolucion.capitalize()}!**",
            delete_after=6
        )

class BuscandoRivalView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Cancelar búsqueda", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):

        uid = str(interaction.user.id)

        if uid != self.user_id:
            await interaction.response.send_message("❌ Este panel no es tuyo.", ephemeral=True)
            return

        lg.remove_from_queue(uid)
        lg.set_user_available(uid, False)
        await lg.save_cache()

        await interaction.response.edit_message(
            content="🔴 Has cancelado la búsqueda.",
            view=None
        )

class RivalEncontradoView(discord.ui.View):
    def __init__(self, user_id, rival_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.rival_id = rival_id

    @discord.ui.button(label="Aceptar y continuar", style=discord.ButtonStyle.success, emoji="🤝")
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):

        uid = str(interaction.user.id)

        if uid != self.user_id:
            await interaction.response.send_message("❌ Este panel no es tuyo.", ephemeral=True)
            return

        # 🔹 crear canal
        channel = await lg.create_prelocke_channel(
            interaction.guild,
            self.user_id,
            self.rival_id
        )

        await interaction.response.edit_message(
            content=f"📩 Ve al canal {channel.mention} para preparar el locke.",
            view=None
        )

        await channel.send(
            "## 🤝 Preparación del DualLocke\n\n"
            "Aquí acordaréis los detalles antes de crear la sesión.\n"
            "Próximamente aparecerá el formulario."
        )

class PrelockeView(discord.ui.View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = match_id

    @discord.ui.button(label="📝 Rellenar datos", style=discord.ButtonStyle.primary)
    async def rellenar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            PrelockeModal(self.match_id)
        )

    @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):

        uid = str(interaction.user.id)

        ok, done = lg.confirm_prelocke(self.match_id, uid)

        if not ok:
            await interaction.response.send_message("❌ Error.", ephemeral=True)
            return

        if not done:
            await interaction.response.send_message(
                "🕓 Confirmación registrada. Esperando al rival.",
                ephemeral=True
            )
            return

        # 🔥 LOS DOS CONFIRMARON
        pl = lg.get_prelocke(self.match_id)

        data = pl.get("data")
        if not data:
            await interaction.response.send_message(
                "❌ Debéis rellenar el formulario primero.",
                ephemeral=True
            )
            return

        p1, p2 = pl["players"]

        guild = interaction.guild
        staff_channel = discord.utils.get(guild.text_channels, name="【🔒】administración")

        if staff_channel:
            m1 = guild.get_member(int(p1))
            m2 = guild.get_member(int(p2))

            await staff_channel.send(
            "📨 **Solicitud de DualLocke**\n\n"
            f"👥 {m1.display_name} vs {m2.display_name}\n"
            f"🔹 Discord: {m1.name} vs {m2.name}\n"
            f"🎮 Juego: {data['game']}\n"
            f"⚙️ Modalidad: {data['type']}\n"
            f"❤️ Vidas: {data['lives']}"
        )

        # 🧠 CAMBIAR ESTADO ANTES DE BORRAR
        pl["status"] = "waiting_session"
        await lg.save_cache()

        # 🚫 quitar disponibilidad
        for pid in [p1, p2]:
            lg.set_user_available(pid, False)

        lg.remove_from_queue(p1)
        lg.remove_from_queue(p2)

        # 🧹 ahora sí borrar prelocke
        lg.clear_prelocke(self.match_id)
        await lg.save_cache()

        await interaction.channel.delete()

class ConfirmarPrelockeView(discord.ui.View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = match_id

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):

        import logic as lg

        ok, done = lg.confirm_prelocke(self.match_id, str(interaction.user.id))

        if not ok:
            await interaction.response.send_message("❌ Error.", ephemeral=True)
            return

        if not done:
            await interaction.response.send_message(
                "🕓 Confirmación registrada. Esperando al rival…",
                ephemeral=True
            )
            return

        # 🔥 LOS DOS HAN CONFIRMADO
        pl = lg.get_prelocke(self.match_id)
        data = pl["data"]
        p1, p2 = pl["players"]

        await interaction.response.send_message(
            "📨 Datos enviados a staff. Espera a que creen la sesión.",
            ephemeral=True
        )

        lg.clear_prelocke(self.match_id)

class PrelockeModal(discord.ui.Modal, title="Datos del DualLocke"):

    juego = discord.ui.TextInput(label="Juego")
    tipo = discord.ui.TextInput(label="Modalidad")
    vidas = discord.ui.TextInput(label="Vidas iniciales")

    def __init__(self, match_id):
        super().__init__()
        self.match_id = match_id

    async def on_submit(self, interaction: discord.Interaction):

        data = {
            "game": self.juego.value,
            "type": self.tipo.value,
            "lives": self.vidas.value
        }

        pl = lg.get_prelocke(self.match_id)
        if pl:
            pl["data"] = data

        embed = discord.Embed(
            title="📋 Datos del DualLocke",
            description=(
                f"🎮 Juego: **{data['game']}**\n"
                f"⚙️ Modalidad: **{data['type']}**\n"
                f"❤️ Vidas: **{data['lives']}**"
            ),
            color=discord.Color.blue()
        )

        await interaction.channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Datos actualizados.",
            ephemeral=True
        )

class ClasificacionMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mi clasificación", style=discord.ButtonStyle.primary)
    async def mi_clasif(self, interaction: discord.Interaction, button: discord.ui.Button):

        ranking = lg.get_sorted_ranking(interaction.guild)
        pos_global = lg.get_user_position(ranking, interaction.user.id)

        if pos_global is None:
            await interaction.response.send_message(
                "❌ No estás en la clasificación.",
                ephemeral=True
            )
            return

        league = ranking[pos_global]["rank"]

        view = MiClasificacionView(league, page=0)

        # 👇 IMPORTANTE: defer para que render controle todo
        await interaction.response.defer()
        await view.render(interaction)


    @discord.ui.button(label="Top global", style=discord.ButtonStyle.secondary)
    async def top_global(self, interaction: discord.Interaction, button: discord.ui.Button):

        view = TopGlobalView(0)
        await view.render(interaction)


    @discord.ui.button(label="Buscar jugador", style=discord.ButtonStyle.secondary)
    async def buscar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuscarJugadorModal())

class MiClasificacionView(discord.ui.View):
    def __init__(self, league, page=0):
        super().__init__(timeout=None)
        self.league = league
        self.page = page
        self.per_page = 20

    async def render(self, interaction):
        ranking = lg.get_sorted_ranking(interaction.guild)
        liga = [r for r in ranking if r["rank"] == self.league]

        total_pages = max(1, (len(liga)-1)//self.per_page + 1)
        self.page = max(0, min(self.page, total_pages-1))

        start = self.page * self.per_page
        end = start + self.per_page
        chunk = liga[start:end]

        lineas = []
        for i, r in enumerate(chunk, start=start+1):

            member = r.get("member")
            if not member:
                continue

            nombre = lg.ranking_name(member)
            nombre = nombre.replace("\n", " ").strip()

            nivel = r.get("nivel") or 0

            if member.id == interaction.user.id:
                lineas.append(f"{i}. **{nombre}** — Nivel {nivel}")
            else:
                lineas.append(f"{i}. {nombre} — Nivel {nivel}")

        header = f"## 🏆 Liga {self.league} — Página {self.page+1}/{total_pages}\n"
        texto = header + "\n".join(lineas)

        self.prev.disabled = self.page == 0
        self.next.disabled = self.page >= total_pages-1

        miembros = [r["member"] for r in chunk]
        view = crear_view_clasificacion(miembros, self, row=0)

        try:
            await interaction.response.edit_message(
                content=texto,
                attachments=[],
                view=view
            )
        except:
            await interaction.edit_original_response(
                content=texto,
                attachments=[],
                view=view
            )



    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary, row = 1)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.render(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary, row = 1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.render(interaction)

    @discord.ui.button(label="Top de mi liga", style=discord.ButtonStyle.primary, row = 1)
    async def top_liga(self, interaction: discord.Interaction, button: discord.ui.Button):

        ranking = lg.get_sorted_ranking(interaction.guild)
        liga = [r for r in ranking if r["rank"] == self.league][:20]

        texto = f"## 🏆 Top Liga {self.league}\n\n"

        for i, r in enumerate(liga, start=1):

            nombre = lg.ranking_name(r["member"])

            texto += f"{i}. {nombre} — Nivel {r['nivel']}\n"

        miembros = [r["member"] for r in liga]
        view = crear_view_clasificacion(miembros, self, row=0)

        await interaction.response.edit_message(
            content=texto,
            attachments=[],
            view=view
        )


    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.danger, row = 1)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="## 📊 Clasificación",
            attachments=[],
            view=ClasificacionMainView()
        )

class TopLigaView(discord.ui.View):
    def __init__(self, league, page=0):
        super().__init__(timeout=None)
        self.league = league
        self.page = page
        self.per_page = 20

    async def render(self, interaction):
        ranking = lg.get_sorted_ranking(interaction.guild)
        liga = [r for r in ranking if r["rank"] == self.league]

        total_pages = max(1, (len(liga)-1) // self.per_page + 1)
        page = max(0, min(self.page, total_pages-1))

        start = page * self.per_page
        end = start + self.per_page
        chunk = liga[start:end]

        texto = f"## 🏆 Top Liga {self.league} — Página {page+1}/{total_pages}\n\n"

        for i, r in enumerate(chunk, start=start+1):
            texto += f"{i}. {r['member'].display_name} — Nivel {r['nivel']}\n"

        await interaction.response.edit_message(
            content=texto,
            attachments=[],
            view=self
        )

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.render(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.render(interaction)

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.danger)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MiClasificacionView(self.league, 0)
        await view.render(interaction)

class VolverClasifView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="## 📊 Clasificación",
            attachments=[],  # 👈 limpia imágenes
            view=ClasificacionMainView()
        )

class TopGlobalView(discord.ui.View):
    def __init__(self, league_index=0):
        super().__init__(timeout=None)
        self.leagues = lg.get_all_leagues_desc()
        self.index = league_index

    async def render(self, interaction):
        league = self.leagues[self.index]

        ranking = lg.get_sorted_ranking(interaction.guild)
        liga = [r for r in ranking if r["rank"] == league][:20]

        texto = f"## 🌍 Top — Liga {league}\n\n"

        for i, r in enumerate(liga, start=1):

            nombre = lg.ranking_name(r["member"])

            texto += f"{i}. {nombre} — Nivel {r['nivel']}\n"

        # 👇 límites de navegación
        self.prev_league.disabled = self.index >= len(self.leagues)-1
        self.next_league.disabled = self.index <= 0

        miembros = [r["member"] for r in liga]
        view = crear_view_clasificacion(miembros, self, row=1)

        await interaction.response.edit_message(
            content=texto,
            attachments=[],
            view=view
        )


    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def prev_league(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        await self.render(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def next_league(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        await self.render(interaction)

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.danger)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="## 📊 Clasificación",
            attachments=[],
            view=ClasificacionMainView()
        )

class BuscarJugadorModal(discord.ui.Modal, title="Buscar jugador"):

    nombre = discord.ui.TextInput(label="Nombre o entrenador")

    async def on_submit(self, interaction: discord.Interaction):

        member, user = lg.find_user_by_name(interaction.guild, self.nombre.value)

        if not member:
            await interaction.response.send_message("❌ No encontrado.", ephemeral=True)
            return

        preview = lg.generar_preview_desde_equipped(
            member,
            user,
            user.get("equipped", {})
        )

        file = discord.File(preview, filename="perfil.png")

        await interaction.response.edit_message(
            content=f"🔎 Resultado: **{member.display_name}**",
            attachments=[file],
            view=VolverClasifView()
        )

class BotonVerPerfil(discord.ui.Button):
    def __init__(self, member_id: int):
        super().__init__(
            label="Ver perfil",
            style=discord.ButtonStyle.secondary,
            emoji="👤"
        )
        self.member_id = member_id

    async def callback(self, interaction: discord.Interaction):
        await abrir_perfil_desde_id(interaction, self.member_id)

class ClasificacionInteractivaView(discord.ui.View):

    def __init__(self, miembros):
        super().__init__(timeout=300)

        for m in miembros:
            self.add_item(BotonVerPerfil(m.id))

class SelectVerPerfil(discord.ui.Select):
    def __init__(self, miembros, base_view, row=1):

        self.base_view = base_view  # 👈 guardamos la vista original

        options = [
            discord.SelectOption(
                label=m.display_name[:100],
                value=str(m.id)
            )
            for m in miembros[:25]
        ]

        super().__init__(
            placeholder="👤 Ver perfil",
            options=options,
            min_values=1,
            max_values=1,
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        member_id = int(self.values[0])
        await abrir_perfil_desde_id(interaction, member_id, self.base_view)

class PerfilSoloLecturaView(discord.ui.View):
    def __init__(self, previous_view):
        super().__init__(timeout=None)
        self.previous_view = previous_view

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):

        # 👇 Truco: usamos edit_message pero llamamos a render
        await self.previous_view.render(interaction)

class TicketModal(discord.ui.Modal, title="Abrir incidencia"):

    mensaje = discord.ui.TextInput(
        label="Describe el problema o sugerencia",
        style=discord.TextStyle.paragraph,
        placeholder="Explica qué ha pasado o qué propones...",
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        canal_staff = discord.utils.get(
            interaction.guild.text_channels,
            name="【🔒】administración"
        )

        embed = discord.Embed(
            title="🎫 Nuevo ticket",
            description=self.mensaje.value,
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.set_author(
            name=f"{interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(name="Estado", value="🟡 Abierto", inline=False)

        await canal_staff.send(embed=embed, view=TicketAdminView())

        await interaction.response.send_message(
            "✅ Tu incidencia ha sido enviada al staff.",
            ephemeral=True
        )

class TicketAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Asignarme",
        style=discord.ButtonStyle.primary,
        emoji="🧑‍💼",
        custom_id="ticket_asignar"
    )
    async def asignar(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = interaction.message.embeds[0]

        # 🔒 si ya está asignado
        for field in embed.fields:
            if field.name == "Asignado a":
                await interaction.response.send_message(
                    "⚠️ Este ticket ya está asignado.",
                    ephemeral=True
                )
                return

        embed.add_field(
            name="Asignado a",
            value=interaction.user.mention,
            inline=False
        )
        embed.color = discord.Color.green()
        embed.set_field_at(0, name="Estado", value="🟢 Asignado", inline=False)

        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(
            "🧩 Te has asignado este ticket.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Cerrar ticket",
        style=discord.ButtonStyle.danger,
        emoji="✅",
        custom_id="ticket_cerrar"
    )
    async def cerrar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "🗑️ Ticket cerrado.",
            ephemeral=True
        )

        await interaction.message.delete()

class SeleccionarUISlotView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.parent_view = parent_view

    @discord.ui.button(label="Tarjeta entrenador", style=discord.ButtonStyle.primary)
    async def card(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=SeleccionarItemView(self.parent_view, "ui_skins_card")
        )

    @discord.ui.button(label="Tarjeta equipo", style=discord.ButtonStyle.secondary)
    async def team(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=SeleccionarItemView(self.parent_view, "ui_skins_team")
        )

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.parent_view)

class AdminUserEditModal(discord.ui.Modal, title="Editar usuario"):

    nombre = discord.ui.TextInput(
        label="Usuario",
        placeholder="Jufa"
    )

    campo = discord.ui.TextInput(
        label="Campo",
        placeholder="trainer_name | nivel | exp | pokemon | monedas_dual | available"
    )

    valor = discord.ui.TextInput(
        label="Valor",
        placeholder="Nuevo valor"
    )

    async def on_submit(self, interaction: discord.Interaction):

        member, user = lg.find_user_by_name(
            interaction.guild,
            self.nombre.value
        )

        if not user:
            await interaction.response.send_message("❌ No encontrado", ephemeral=True)
            return

        campo = self.campo.value.strip()
        raw_valor = self.valor.value.strip()

        # 🔹 PARSER SEGURO
        valor = raw_valor

        # bool primero
        if isinstance(raw_valor, str) and raw_valor.lower() in ["true", "false"]:
            valor = raw_valor.lower() == "true"

        else:
            # intentar int
            try:
                valor = int(raw_valor)
            except:
                valor = raw_valor

        user[campo] = valor

        # 🔥 SI CAMBIA NIVEL → pipeline completo
        if campo == "nivel":
            await lg.apply_level_change(member, user, int(valor))

        lg.ensure_inventory(user)

        await lg.save_cache()

        await interaction.response.send_message(
            f"✅ {campo} actualizado a {valor}",
            ephemeral=True
        )

class AdminInventoryModal(discord.ui.Modal, title="Editar inventario"):

    nombre = discord.ui.TextInput(label="Usuario")

    accion = discord.ui.TextInput(
        label="Acción",
        placeholder="add o remove"
    )

    categoria = discord.ui.TextInput(
        label="Categoría",
        placeholder="pokemons | avatars | ui_skins | badges"
    )

    item = discord.ui.TextInput(
        label="Item",
        placeholder="pikachu"
    )

    async def on_submit(self, interaction: discord.Interaction):

        member, user = lg.find_user_by_name(
            interaction.guild,
            self.nombre.value
        )

        if not user:
            await interaction.response.send_message("❌ No encontrado", ephemeral=True)
            return

        lg.ensure_inventory(user)

        accion = self.accion.value.lower()
        cat = lg.normalize_category(self.categoria.value)
        item = self.item.value.lower()

        if accion == "add":
            if item not in user["inventory"][cat]:
                user["inventory"][cat].append(item)

        elif accion == "remove":
            if item in user["inventory"][cat]:
                user["inventory"][cat].remove(item)

        await lg.save_cache()
        await interaction.response.send_message("✅ Inventario actualizado", ephemeral=True)

class AdminSessionModal(discord.ui.Modal, title="Editar sesión"):

    canal = discord.ui.TextInput(
        label="Nombre del canal",
        placeholder="Ej: jufa vs pepe"
    )

    jugador = discord.ui.TextInput(
        label="Jugador",
        placeholder="1 o 2"
    )

    cambios = discord.ui.TextInput(
        label="Cambios",
        style=discord.TextStyle.paragraph,
        placeholder="lives=5\nscore=2"
    )

    async def on_submit(self, interaction: discord.Interaction):

        session = None
        sid = None

        for k, s in lg.DATA_CACHE["sessions"].items():
            ch = interaction.guild.get_channel(s["s_channel"])
            if ch and ch.name.lower() == self.canal.value.lower():
                session = s
                sid = k
                break

        if not session:
            await interaction.response.send_message("❌ Sesión no encontrada", ephemeral=True)
            return

        uid = session["player1"] if self.jugador.value == "1" else session["player2"]

        for linea in self.cambios.value.split("\n"):
            if "=" not in linea:
                continue

            k, v = linea.split("=")
            k = k.strip()
            v = int(v.strip())

            if k in session:
                session[k][uid] = v

        await lg.save_cache()

        await lg.refrescar_sesion_embed(sid, interaction.guild)

        await interaction.response.send_message(
            "✅ Sesión actualizada",
            ephemeral=True
        )

class AdminExpModal(discord.ui.Modal, title="Dar EXP"):

    nombre = discord.ui.TextInput(
        label="Usuario",
        placeholder="Nombre de Discord o entrenador"
    )

    cantidad = discord.ui.TextInput(
        label="Cantidad de EXP",
        placeholder="Ej: 500"
    )

    async def on_submit(self, interaction: discord.Interaction):

        # 🔎 buscar por nombre (recicla tu función)
        member, user = lg.find_user_by_name(
            interaction.guild,
            self.nombre.value
        )

        if not member or not user:
            await interaction.response.send_message(
                "❌ Usuario no encontrado",
                ephemeral=True
            )
            return

        # 🔢 convertir exp
        try:
            amount = int(self.cantidad.value)
        except:
            await interaction.response.send_message(
                "❌ Cantidad inválida",
                ephemeral=True
            )
            return

        # 🚀 usar tu sistema actual de exp
        await lg.add_exp(member, amount)

        await interaction.response.send_message(
            f"📈 {amount} EXP añadida a {member.display_name}",
            ephemeral=True
        )

class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="👤 Usuarios", style=discord.ButtonStyle.primary)
    async def usuarios(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminUserEditModal())

    @discord.ui.button(label="🎒 Inventario", style=discord.ButtonStyle.secondary)
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminInventoryModal())

    @discord.ui.button(label="🧩 Sesiones", style=discord.ButtonStyle.secondary)
    async def sesiones(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminSessionModal())

    @discord.ui.button(label="📈 Dar EXP", style=discord.ButtonStyle.success)
    async def exp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminExpModal())
    
    @discord.ui.button(label="🆕 Crear sesión", style=discord.ButtonStyle.primary)
    async def crear_sesion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminCrearSesionModal())

    @discord.ui.button(label="♻️ Resetear jugador", style=discord.ButtonStyle.danger)
    async def reset_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdminResetUserModal())

class AdminCrearSesionModal(discord.ui.Modal, title="Crear sesión manual"):

    jugador1 = discord.ui.TextInput(label="Jugador 1")
    jugador2 = discord.ui.TextInput(label="Jugador 2")
    juego = discord.ui.TextInput(label="Juego")
    tipo = discord.ui.TextInput(label="Tipo")
    vidas = discord.ui.TextInput(label="Vidas")

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        # 🔎 buscar por nombre de discord
        def buscar(nombre):
            nombre = nombre.lower()

            for m in interaction.guild.members:
                if m.display_name.lower() == nombre or m.name.lower() == nombre:
                    return m

            return None

        m1 = buscar(self.jugador1.value)
        m2 = buscar(self.jugador2.value)

        if not m1 or not m2:
            await interaction.followup.send(
                "❌ No se pudo encontrar uno de los jugadores.",
                ephemeral=True
            )
            return

        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("crearsesion")

        await cmd(
            ctx,
            m1,
            m2,
            self.juego.value,
            self.tipo.value,
            int(self.vidas.value)
        )

        await interaction.followup.send(
            "✅ Sesión creada manualmente",
            ephemeral=True
        )

class AdminResetUserModal(discord.ui.Modal, title="Resetear jugador"):

    nombre = discord.ui.TextInput(
        label="Usuario",
        placeholder="Nombre o entrenador"
    )

    async def on_submit(self, interaction: discord.Interaction):

        member, user = lg.find_user_by_name(
            interaction.guild,
            self.nombre.value
        )

        if not member or not user:
            await interaction.response.send_message(
                "❌ Usuario no encontrado",
                ephemeral=True
            )
            return

        uid = str(member.id)

        starter = user.get("starter")

        # 🔥 calcular skin del starter
        tipo = lg.STARTERS.get(starter)
        starter_skin = lg.TYPE_TO_SKIN.get(tipo)

        inventory = {
            "avatars": ["Rojo", "Verde"],
            "pokemons": [starter],
            "ui_skins": ["default"],
            "badges": []
        }

        # 👉 añadir skin si existe
        if starter_skin:
            inventory["ui_skins"].append(starter_skin)

        # 🧠 reset datos
        lg.DATA_CACHE["users"][uid] = {
            "pokemon": starter,
            "starter": starter,
            "nivel": 0,
            "exp": 0,
            "trainer_name": member.display_name,
            "gender": user.get("gender"),
            "available": False,
            "equipped": {
                "avatar": user.get("equipped", {}).get("avatar"),
                "pokemon": starter,
                "ui_skin_card": "default",
                "ui_skin_team": "default"
            },
            "inventory": inventory
        }

        # 🎖️ reset roles → solo Joven
        rank_roles = list(lg.RANK_LEVELS.values())

        roles_to_remove = [r for r in member.roles if r.name in rank_roles]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        joven_role = discord.utils.get(interaction.guild.roles, name="Joven")
        if joven_role:
            await member.add_roles(joven_role)

        await lg.save_cache()

        await interaction.response.send_message(
            f"♻️ {member.display_name} reseteado completamente",
            ephemeral=True
        )

class SeleccionarBadgeEquipView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.parent_view = parent_view

        user = lg.DATA_CACHE["users"][str(parent_view.user_id)]
        lg.ensure_inventory(user)

        inventory_badges = user["inventory"]["badges"]
        equipped = parent_view.temp_equipped.get("badges", [])

        opciones = []

        for badge_id in inventory_badges:
            if badge_id not in equipped:
                badge_data = lg.BADGES.get(badge_id, {})
                label = badge_data.get("name", badge_id)

                opciones.append(
                    discord.SelectOption(
                        label=label,
                        value=badge_id
                    )
                )

        if opciones:
            self.add_item(BadgeEquipSelect(opciones, parent_view))

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.parent_view)

class BadgeEquipSelect(discord.ui.Select):
    def __init__(self, options, parent_view):
        super().__init__(placeholder="Selecciona insignia", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):

        badge_id = self.values[0]

        equipped = self.parent_view.temp_equipped.setdefault("badges", [])

        if len(equipped) >= 12:
            await interaction.response.send_message(
                "❌ Máximo 12 insignias equipadas.",
                ephemeral=True
            )
            return

        equipped.append(badge_id)

        await interaction.response.edit_message(view=None)
        await self.parent_view.refrescar_preview(interaction)

class SeleccionarBadgeRemoveView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.parent_view = parent_view

        equipped = parent_view.temp_equipped.get("badges", [])

        opciones = []

        for badge_id in equipped:
            badge_data = lg.BADGES.get(badge_id, {})
            label = badge_data.get("name", badge_id)

            opciones.append(
                discord.SelectOption(
                    label=label,
                    value=badge_id
                )
            )

        if opciones:
            self.add_item(BadgeRemoveSelect(opciones, parent_view))

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=self.parent_view)

class BadgeRemoveSelect(discord.ui.Select):
    def __init__(self, options, parent_view):
        super().__init__(placeholder="Quitar insignia", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):

        badge_id = self.values[0]

        equipped = self.parent_view.temp_equipped.setdefault("badges", [])

        if badge_id in equipped:
            equipped.remove(badge_id)

        await interaction.response.edit_message(view=None)
        await self.parent_view.refrescar_preview(interaction)

class MenuInsigniasView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=120)
        self.parent_view = parent_view

    @discord.ui.button(label="➕ Añadir insignia", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=SeleccionarBadgeEquipView(self.parent_view)
        )

    @discord.ui.button(label="➖ Quitar insignia", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=SeleccionarBadgeRemoveView(self.parent_view)
        )

    @discord.ui.button(label="⬅ Volver", style=discord.ButtonStyle.secondary)
    async def volver(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            view=self.parent_view
        )

class TiendaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

        # cargar tienda elite
        tienda_elite = lg.load_tienda_elite()

        if tienda_elite["items"]:
            for item in tienda_elite["items"]:
                self.add_item(
                    EliteItemButton(item, user_id)
                )

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Esta tienda no es tuya.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Máquina Pokémon (1)🪙", style=discord.ButtonStyle.primary)
    async def maquina_pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        ok, result = await lg.tirar_maquina(interaction.user, "pokemon_machine")

        if not ok:
            await interaction.followup.send(
            traducir_error(result),
            ephemeral=True
        )
            return

        # 🎨 Mostrar bonito (sin _shiny)
        if result.endswith("_shiny"):
            display = result.replace("_shiny", "").capitalize() + " ✨"
        else:
            display = result.capitalize()

        monedas_restantes = lg.DATA_CACHE["users"][str(self.user_id)]["monedas_dual"]

        await interaction.edit_original_response(
            content=(
                f"🏪 **Tienda Dual**\n\n"
                f"🎉 ¡Te ha tocado **{display}**!\n\n"
                f"🪙 **Monedas Dual:** {monedas_restantes}\n\n"
            ),
            view=TiendaView(self.user_id)
        )
    @discord.ui.button(label="Máquina Avatar (1)🪙", style=discord.ButtonStyle.secondary)
    async def maquina_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):

        ok, result = await lg.tirar_maquina(interaction.user, "avatar_machine")

        if not ok:
            await interaction.response.send_message(
                traducir_error(result),
                ephemeral=True
            )
            return

        monedas_restantes = lg.DATA_CACHE["users"][str(self.user_id)]["monedas_dual"]

        await interaction.response.edit_message(
            content=(
                f"🏪 **Tienda Dual**\n\n"
                f"🎉 ¡Te ha tocado el avatar **{result}**!\n\n"
                f"🪙 **Monedas Dual:** {monedas_restantes}\n\n"
            ),
            view=TiendaView(self.user_id)
        )
    
class EliteItemButton(discord.ui.Button):

    def __init__(self, item, user_id):

        self.item = item
        self.user_id = user_id

        if item["type"] == "ui_skin":
            label = lg.SKIN_DISPLAY_NAMES.get(
                item["id"],
                item["id"].replace("_", " ").capitalize()
            )

        elif item["type"] == "badge":
            badge = lg.BADGES.get(item["id"], {})
            label = badge.get("name", item["id"].replace("_", " ").capitalize())

        else:
            label = item["id"].replace("_", " ").capitalize()

        super().__init__(
        label=f"{label} (1)💎",
        style=discord.ButtonStyle.success,
        row=1
    )

    async def callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Esta tienda no es tuya.",
                ephemeral=True
            )
            return

        item = self.item

        user = lg.DATA_CACHE["users"].get(str(self.user_id))

        mapping = {
            "pokemon": "pokemons",
            "avatar": "avatars",
            "badge": "badges",
            "ui_skin": "ui_skins"
        }

        categoria = mapping.get(item["type"])

        if item["id"] in user["inventory"][categoria]:

            await interaction.response.send_message(
                "❌ Ya tienes este objeto.",
                ephemeral=True
            )
            return


        texto = (
            f"💎 **Tienda Élite**\n\n"
            f"Objeto seleccionado:\n"
            f"**{item['id'].capitalize()}**\n\n"
            f"Coste: **1 Moneda Élite**\n\n"
            f"¿Confirmar compra?"
        )

        file = None

        if item["type"] == "pokemon":

            sprite = lg.get_pokemon_sprite(item["id"])

            if sprite:
                img = requests.get(sprite).content

                file = discord.File(
                    io.BytesIO(img),
                    filename="preview.png"
    )

        elif item["type"] == "avatar":

            avatar_bytes = lg.get_trainer_avatar(item["id"])

            if avatar_bytes:
                file = discord.File(
                    io.BytesIO(avatar_bytes),
                    filename="avatar.png"
                )

        elif item["type"] == "badge":

            path = f"assets/badges/{item['id']}.png"

            try:
                file = discord.File(path, filename="badge.png")
            except:
                pass

        elif item["type"] == "ui_skin":

            fake_user = {
                "trainer_name": "",
                "nivel": 0,
                "exp": 0,
                "rank": None,
                "top": None,
                "gender": None,
                "inventory": {
                    "badges": []
                }
            }

            equipped = {
                "avatar": None,
                "pokemon": None,
                "badges": [],
                "ui_skin_card": item["id"]
            }

            preview = lg.generar_preview_desde_equipped(
                interaction.user,
                fake_user,
                equipped
            )

            file = discord.File(preview, filename="preview.png")

        await interaction.response.edit_message(
            content=texto,
            attachments=[file] if file else [],
            view=EliteConfirmView(self.user_id, item)
        )

class EliteConfirmView(discord.ui.View):

    def __init__(self, user_id, item):
        super().__init__(timeout=60)

        self.user_id = user_id
        self.item = item

    @discord.ui.button(label="✅ Comprar", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.user_id:
            return

        user = lg.DATA_CACHE["users"].get(str(self.user_id))

        lg.ensure_inventory(user)
        lg.ensure_monedas(user)

        if user["monedas_elite"] < 1:

            await interaction.response.edit_message(
                content=(
                    f"🏪 **Tienda Dual**\n\n"
                    f"🪙 **Monedas Dual:** {user.get('monedas_dual',0)}\n"
                    f"💎 **Monedas Élite:** {user.get('monedas_elite',0)}\n\n"
                    f"❌ **No tienes monedas élite.**\n"
                    f"Puedes conseguirlas apoyando el servidor.\n"
                    f"Más información en el canal 【📋】información.\n\n"
                    f"Selecciona una máquina:"
                ),
                attachments=[],
                view=TiendaView(self.user_id)
            )
            return

        tipo = self.item["type"]
        objeto = self.item["id"]

        mapping = {
            "pokemon": "pokemons",
            "avatar": "avatars",
            "badge": "badges",
            "ui_skin": "ui_skins"
        }

        categoria = mapping.get(tipo)

        if objeto in user["inventory"][categoria]:
            await interaction.response.edit_message(
                content="❌ Ya tienes este objeto.",
                view=None
            )
            return

        user["monedas_elite"] -= 1
        user["inventory"][categoria].append(objeto)

        await lg.save_cache()

        monedas_dual = user.get("monedas_dual",0)
        monedas_elite = user.get("monedas_elite",0)

        await interaction.response.edit_message(
            content=(
                f"🏪 **Tienda Dual**\n\n"
                f"🪙 **Monedas Dual:** {monedas_dual}\n"
                f"💎 **Monedas Élite:** {monedas_elite}\n\n"
                f"✨ Has comprado **{objeto.capitalize()}**\n\n"
                f"Selecciona una máquina:"
            ),
            attachments=[],
            view=TiendaView(self.user_id)
        )

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.user_id:
            return

        user = lg.DATA_CACHE["users"].get(str(self.user_id))
        monedas_dual = user.get("monedas_dual", 0)
        monedas_elite = user.get("monedas_elite", 0)

        await interaction.response.edit_message(
            content=(
                f"🏪 **Tienda Dual**\n\n"
                f"🪙 Monedas Dual: **{monedas_dual}**\n"
                f"💎 Monedas Élite: **{monedas_elite}**\n\n"
                f"Selecciona una máquina:"
            ),
            attachments=[],
            view=TiendaView(self.user_id)
        )

class CerrarEphemeralView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger)
    async def cerrar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        try:
            await interaction.delete_original_response()
        except:
            pass

class RuletaStartView(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🎡 Crear ruleta", style=discord.ButtonStyle.primary)
    async def crear(self, interaction: discord.Interaction, button: discord.ui.Button):

        # 🔒 SOLO ELITE
        if not lg.is_elite(interaction.user):
            await interaction.response.send_message(
                "💎 La ruleta personalizada es exclusiva para usuarios **Élite**.",
                ephemeral=True
            )
            return

        # 🔒 SOLO QUIEN ABRIÓ EL PANEL
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Solo quien creó la ruleta puede usarla.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(RuletaModal(self.user_id))

class RuletaModal(discord.ui.Modal):

    def __init__(self, user_id):
        super().__init__(title="Opciones de la ruleta")

        self.user_id = user_id

        self.opciones = discord.ui.TextInput(
            label="Opciones (separadas por coma)",
            placeholder="charmander, squirtle, bulbasaur",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=200
        )

        self.add_item(self.opciones)

    async def on_submit(self, interaction: discord.Interaction):

        opciones = [o.strip() for o in self.opciones.value.split(",") if o.strip()]

        if len(opciones) < 2:
            await interaction.response.send_message(
                "❌ Necesitas al menos **2 opciones**.",
                ephemeral=True
            )
            return

        if len(opciones) > 10:
            await interaction.response.send_message(
                "❌ Máximo **10 opciones**.",
                ephemeral=True
            )
            return

        texto = "\n".join([f"• {o}" for o in opciones])

        view = RuletaSpinView(opciones)

        await interaction.response.send_message(
            f"🎡 **Ruleta creada**\n\n{texto}\n\n",
            view=view
        )

class RuletaSpinView(discord.ui.View):

    def __init__(self, opciones):
        super().__init__(timeout=120)
        self.opciones = opciones

    @discord.ui.button(label="🎡 Girar", style=discord.ButtonStyle.success)
    async def girar(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        # borrar opciones y mostrar girando
        await interaction.edit_original_response(
            content="🎡 Girando...",
            view=None
        )

        await asyncio.sleep(2)

        resultado = random.choice(self.opciones)

        msg = await interaction.edit_original_response(
            content=f"🏆 **Resultado:** {resultado}"
        )

        await asyncio.sleep(10)

        try:
            await msg.delete()
        except:
            pass

class StatsPokemonStartView(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🔎 Buscar Pokémon", style=discord.ButtonStyle.primary)
    async def buscar(self, interaction: discord.Interaction, button: discord.ui.Button):

        # 🔒 SOLO ELITE
        if not lg.is_elite(interaction.user):
            await interaction.response.send_message(
                "💎 Esta función es exclusiva para usuarios **Élite**.",
                ephemeral=True
            )
            return

        # 🔒 SOLO QUIEN ABRIÓ EL PANEL
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Solo quien ejecutó el comando puede usarlo.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(StatsPokemonModal())

class StatsPokemonModal(discord.ui.Modal, title="Buscar Pokémon"):

    pokemon = discord.ui.TextInput(
        label="Nombre del Pokémon",
        placeholder="Ejemplo: gastly",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        nombre = lg.normalize_pokemon_name(self.pokemon.value)

        try:
            r = requests.get(
                f"https://pokeapi.co/api/v2/pokemon/{nombre}",
                timeout=10
            )

            if r.status_code != 200:
                raise Exception()

            data = r.json()

            # tipos en español
            tipos = [
                TYPE_ES.get(t["type"]["name"], t["type"]["name"].capitalize())
                for t in data["types"]
            ]
            tipos_texto = " / ".join(tipos)

            # stats base
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

            hp = stats.get("hp", 0)
            atk = stats.get("attack", 0)
            deff = stats.get("defense", 0)
            spa = stats.get("special-attack", 0)
            spd = stats.get("special-defense", 0)
            spe = stats.get("speed", 0)

            evo_texto = "No evoluciona"

            try:

                species = requests.get(
                    f"https://pokeapi.co/api/v2/pokemon-species/{nombre}",
                    timeout=10
                ).json()

                evo_chain_url = species["evolution_chain"]["url"]

                evo_data = requests.get(evo_chain_url, timeout=10).json()

                chain = evo_data["chain"]

                evoluciones = []

                def buscar(node):

                    base = node["species"]["name"]

                    if base == nombre:

                        for evo in node["evolves_to"]:

                            evo_name = evo["species"]["name"].capitalize()
                            d = evo["evolution_details"][0] if evo["evolution_details"] else None

                            if not d:
                                evoluciones.append(f"Evoluciona a {evo_name}")
                                continue

                            # NIVEL
                            if d["min_level"]:
                                evoluciones.append(f"Nivel {d['min_level']} → {evo_name}")

                            # OBJETO
                            elif d["item"]:
                                item = traducir_item(d["item"]["name"])
                                evoluciones.append(f"Usar {item} → {evo_name}")

                            # INTERCAMBIO
                            elif d["trigger"]["name"] == "trade":

                                if d["held_item"]:
                                    item = traducir_item(d["held_item"]["name"])
                                    evoluciones.append(f"Intercambio con {item} → {evo_name}")

                                else:
                                    evoluciones.append(f"Intercambio → {evo_name}")

                            # AMISTAD
                            elif d["min_happiness"]:
                                evoluciones.append(f"Amistad alta → {evo_name}")

                            # MOVIMIENTO
                            elif d["known_move"]:
                                move = d["known_move"]["name"].replace("-", " ").capitalize()
                                evoluciones.append(f"Aprender {move} → {evo_name}")

                            # TIPO DE MOVIMIENTO (Sylveon)
                            elif d["known_move_type"]:
                                tipo = TYPE_ES.get(d["known_move_type"]["name"], d["known_move_type"]["name"])
                                evoluciones.append(f"Con movimiento tipo {tipo} y amistad alta → {evo_name}")

                            # STATS (Tyrogue)
                            elif d["relative_physical_stats"] == 1:
                                evoluciones.append(f"Ataque > Defensa → {evo_name}")

                            elif d["relative_physical_stats"] == -1:
                                evoluciones.append(f"Ataque < Defensa → {evo_name}")

                            elif d["relative_physical_stats"] == 0:
                                evoluciones.append(f"Ataque = Defensa → {evo_name}")

                            # BELLEZA
                            elif d["min_beauty"]:
                                evoluciones.append(f"Belleza alta → {evo_name}")

                            # UBICACIÓN (Leafeon / Glaceon)
                            elif d["location"]:

                                loc = d["location"]["name"]

                                if "moss" in loc:
                                    evoluciones.append(f"Subir nivel cerca de Roca Musgo → {evo_name}")

                                elif "ice" in loc:
                                    evoluciones.append(f"Subir nivel cerca de Roca Hielo → {evo_name}")

                                else:
                                    loc = loc.replace("-", " ").capitalize()
                                    evoluciones.append(f"Subir nivel en {loc} → {evo_name}")

                            # HORA
                            elif d["time_of_day"]:

                                if d["time_of_day"] == "day":
                                    evoluciones.append(f"Subir nivel de día → {evo_name}")

                                elif d["time_of_day"] == "night":
                                    evoluciones.append(f"Subir nivel de noche → {evo_name}")

                            # POKÉMON EN EQUIPO
                            elif d["party_species"]:
                                p = d["party_species"]["name"].capitalize()
                                evoluciones.append(f"Con {p} en el equipo → {evo_name}")

                            # TIPO EN EQUIPO
                            elif d["party_type"]:
                                tipo = TYPE_ES.get(d["party_type"]["name"], d["party_type"]["name"])
                                evoluciones.append(f"Con Pokémon tipo {tipo} en el equipo → {evo_name}")

                            # INKAY
                            elif d["turn_upside_down"]:
                                evoluciones.append(f"Subir nivel con la consola invertida → {evo_name}")

                            else:
                                evoluciones.append(f"Evoluciona a {evo_name}")

                    for e in node["evolves_to"]:
                        buscar(e)

                buscar(chain)

                if evoluciones:
                    evo_texto = "\n".join(evoluciones)

            except:
                pass

            # mensaje final
            mensaje = (
                f"📊 **{nombre.capitalize()}**\n\n"
                f"**Tipo:** {tipos_texto}\n\n"
                f"**Evolución:**\n{evo_texto}\n\n"
                f"**Stats base:**\n"
                f"HP: {hp}\n"
                f"ATK: {atk}\n"
                f"DEF: {deff}\n"
                f"SPA: {spa}\n"
                f"SPD: {spd}\n"
                f"SPE: {spe}"
            )

            await interaction.response.send_message(mensaje)

            msg = await interaction.original_response()

            await asyncio.sleep(30)

            try:
                await msg.delete()
            except:
                pass

        except:
            await interaction.response.send_message(
                "❌ Pokémon no encontrado.",
                ephemeral=True
            )
            return

class SesionPrivadaModal(discord.ui.Modal, title="Crear sesión privada"):

    rival = discord.ui.TextInput(
        label="Rival",
        placeholder="Nombre de Discord"
    )

    juego = discord.ui.TextInput(
        label="Juego",
        placeholder="Ej: Pokemon Esmeralda"
    )

    tipo_locke = discord.ui.TextInput(
        label="Tipo de locke",
        placeholder="Ej: Hardcore / Random"
    )

    vidas = discord.ui.TextInput(
        label="Número de vidas",
        placeholder="Ej: 3",
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        rival = None
        nombre = self.rival.value.lower()

        for m in guild.members:
            if m.display_name.lower() == nombre or m.name.lower() == nombre:
                rival = m
                break

        if not rival:
            await interaction.followup.send(
                "❌ Rival no encontrado.",
                ephemeral=True
            )
            return


        # 🔒 comprobar sesión privada existente
        for s in lg.DATA_CACHE["sessions"].values():

            if s.get("status") != "active":
                continue

            channel = guild.get_channel(s.get("s_channel"))

            if channel and channel.name.startswith("privado-"):
                if str(interaction.user.id) in (s["player1"], s["player2"]):

                    await interaction.followup.send(
                        "❌ Ya tienes una sesión privada activa.",
                        ephemeral=True
                    )
                    return


        try:
            vidas = int(self.vidas.value)
        except:
            await interaction.followup.send(
                "❌ Número de vidas inválido.",
                ephemeral=True
            )
            return


        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.channel = interaction.channel

        cmd = interaction.client.get_command("crearsesion")

        await cmd(
            ctx,
            interaction.user,
            rival,
            self.juego.value,
            self.tipo_locke.value,
            vidas,
            privada=True
        )

        # buscar la sesión recién creada
        session_id = max(lg.DATA_CACHE["sessions"].keys(), key=int)
        session = lg.DATA_CACHE["sessions"][session_id]

        channel = guild.get_channel(session["s_channel"])

        view = AceptarSesionPrivadaView(rival.id, session_id)

class AceptarSesionPrivadaView(discord.ui.View):

    def __init__(self, rival_id, session_id):
        super().__init__(timeout=None)
        self.rival_id = rival_id
        self.session_id = session_id

    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.success)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.rival_id:
            await interaction.response.send_message(
                "❌ Solo el rival puede aceptar.",
                ephemeral=True
            )
            return

        # borrar mensaje confirmación
        await interaction.message.delete()

        await interaction.response.send_message(
            "✅ Sesión aceptada. ¡Podéis empezar!",
            ephemeral=True
        )

    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.danger)
    async def rechazar(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.rival_id:
            await interaction.response.send_message(
                "❌ Solo el rival puede rechazar.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        await interaction.response.send_message(
            "❌ Sesión rechazada.",
            ephemeral=True
        )

        await canal.delete(reason="Sesión privada rechazada")

class SolicitarRomModal(discord.ui.Modal, title="Solicitar ROM para DualLocke"):

    rom = discord.ui.TextInput(
        label="¿Qué ROM necesitas?",
        placeholder="Ej: Pokémon Rubi Omega / Sol / Platino...",
        required=True
    )

    mensaje = discord.ui.TextInput(
        label="Detalles (opcional)",
        style=discord.TextStyle.paragraph,
        placeholder="Puedes dejar detalles aquí",
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):

        canal_staff = discord.utils.get(
            interaction.guild.text_channels,
            name="【🔒】administración"
        )

        embed = discord.Embed(
            title="💾 Solicitud de ROM",
            description=f"**ROM solicitada:**\n{self.rom.value}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )

        if self.mensaje.value:
            embed.add_field(
                name="Detalles",
                value=self.mensaje.value,
                inline=False
            )

        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="Estado",
            value="🟡 Pendiente",
            inline=False
        )

        await canal_staff.send(embed=embed, view=TicketAdminView())

        await interaction.response.send_message(
            "📨 Tu solicitud de ROM ha sido enviada al staff.",
            ephemeral=True
        )

class PanelRomsView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Solicitar ROM",
        style=discord.ButtonStyle.primary,
        emoji="💾",
        custom_id="rom_solicitar"
    )
    async def solicitar_rom(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(SolicitarRomModal())

def ranking_name(member):

    name = member.display_name

    if lg.is_elite(member):
        name = f"{name} 💎"

    return name

def traducir_item(item):

    if item in ITEM_ES:
        return ITEM_ES[item]

    return item.replace("-", " ").capitalize()

def traducir_error(code):
    mensajes = {
        "no_user": "❌ Usuario no encontrado.",
        "no_coins": "🪙 No tienes Monedas Dual.",
        "empty_machine": "⚙️ Esta máquina está vacía.",
        "no_more_items": "📦 Ya tienes todos los objetos disponibles.",
        "invalid_machine": "❌ Máquina inválida."
    }
    return mensajes.get(code, "❌ Ha ocurrido un error.")

def crear_view_clasificacion(miembros, base_view, row=1):

    # eliminar selector anterior si existe
    for item in list(base_view.children):
        if isinstance(item, SelectVerPerfil):
            base_view.remove_item(item)

    if miembros:
        base_view.add_item(
            SelectVerPerfil(miembros, base_view, row=row)
        )

    return base_view

async def abrir_perfil_desde_id(interaction, member_id: int, previous_view):

    member = interaction.guild.get_member(member_id)

    if not member:
        await interaction.response.send_message("❌ Usuario no encontrado", ephemeral=True)
        return

    data = lg.DATA_CACHE["users"]
    uid = str(member.id)

    if uid not in data:
        await interaction.response.send_message("❌ Este usuario no tiene perfil", ephemeral=True)
        return

    user = data[uid]
    equipped = user.get("equipped", {})

    img = lg.generar_preview_desde_equipped(member, user, equipped)
    file = discord.File(img, filename="perfil.png")

    view = PerfilSoloLecturaView(previous_view)

    await interaction.response.edit_message(
        content=None,
        attachments=[file],
        view=view
    )

async def enviar_panel_bienvenida(bot):
    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🙋‍♂️】bienvenido")

    if not canal:
        print("Canal bienvenido no encontrado")
        return

    texto = (
        "## Bienvenido/a al servidor\n\n"
        "En este server, podrás tener tu propio perfil con el cual entrarás en la Liga Dualocke.\n"
        "Cuando crees tu perfil, te recomendamos que lo primero que hagas sea leer el canal de Documentación, donde tendras acceso al tutorial del servidor y a las normas del mismo.\n"
        "Esperamos que disfrutes de la liga.\n"
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

async def enviar_panel_perfil(bot):
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

async def enviar_panel_inicio(bot):
    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🔰】inicio")

    if not canal:
        print("Canal inicio no encontrado")
        return

    texto = (
        "## 💻 Panel principal\n\n"
        "Usa los botones para navegar por el sistema."
    )

    panel_msg = None

    async for msg in canal.history(limit=20):
        if msg.author == bot.user and msg.components:
            panel_msg = msg
            break

    # ✅ si ya existe → no hacer nada
    if panel_msg:
        print("Panel inicio ya existente")
        return

    # ✅ si no existe → crear
    mensaje = await canal.send(texto, view=PanelInicioView())
    await mensaje.pin()

    
    lg.DATA_CACHE["panel_inicio_msg"] = mensaje.id
    await lg.save_cache()

    print("Panel inicio enviado")

async def send_or_edit_ephemeral(interaction, content=None, embed=None, view=None):
    try:
        await interaction.response.edit_message(
            content=content,
            embed=embed,
            view=view
        )
    except discord.InteractionResponded:
        await interaction.edit_original_response(
            content=content,
            embed=embed,
            view=view
        )

async def enviar_panel_roms(bot):

    await bot.wait_until_ready()

    guild = bot.guilds[0]
    canal = discord.utils.get(guild.text_channels, name="【🎮】roms")

    if not canal:
        print("Canal roms no encontrado")
        return

    texto = (
        "## 💾 Solicitud de ROM\n\n"
        "Si necesitas una ROM para jugar tu dualocke, solicitala aquí"
    )

    async for msg in canal.history(limit=10):
        if msg.author == bot.user and msg.components:
            return

    mensaje = await canal.send(
        texto,
        view=PanelRomsView()
    )

    await mensaje.pin()

    print("Panel ROMs enviado")
