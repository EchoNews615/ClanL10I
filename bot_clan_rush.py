import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import re
from datetime import datetime, timedelta
import json
import aiohttp

# ============================================
# ⛏️ BOT DO CLAN 147 - MINECRAFT BEDWARS
# ============================================

# ============================================
# 🔧 CONFIGURAÇÕES DA API BASE44
# ============================================

API_BASE_URL = "https://app.base44.com/api/apps/69262cc75415469b118ed899"
API_KEY = "27958a48b4ce49be959dfd60cbfdf11f"

# ============================================
# 📡 FUNÇÕES DE INTEGRAÇÃO COM O SITE BASE44
# ============================================

async def api_request(entity_name, method='GET', data=None, entity_id=None):
    """Faz requisições para a API do Base44"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "api_key": API_KEY,
                "Content-Type": "application/json"
            }
            
            url = f"{API_BASE_URL}/entities/{entity_name}"
            if entity_id:
                url = f"{url}/{entity_id}"
            
            if method.upper() == 'GET':
                async with session.get(url, headers=headers, params=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        print(f"❌ API Error GET: {resp.status}")
                        return None
                        
            elif method.upper() == 'POST':
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
                    else:
                        print(f"❌ API Error POST: {resp.status} - {await resp.text()}")
                        return None
                        
            elif method.upper() == 'PUT':
                async with session.put(url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        print(f"❌ API Error PUT: {resp.status}")
                        return None
                        
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None

async def buscar_membro_por_discord_id(discord_id):
    """Busca um membro pelo discord_id"""
    try:
        result = await api_request("Membro", "GET", {"discord_id": str(discord_id)})
        if result and len(result) > 0:
            return result[0]
        return None
    except:
        return None

async def registrar_membro(discord_id, username, avatar_url, cargo="🆕 Novato"):
    """Registra ou atualiza um membro no site"""
    membro_existente = await buscar_membro_por_discord_id(discord_id)
    
    dados = {
        "discord_id": str(discord_id),
        "discord_username": username,
        "discord_avatar": avatar_url,
        "cargo_servidor": cargo,
        "status": "ativo"
    }
    
    if membro_existente:
        result = await api_request("Membro", "PUT", dados, membro_existente['id'])
        print(f"[API] ✅ Membro atualizado: {username}")
    else:
        dados.update({
            "data_entrada": datetime.utcnow().isoformat(),
            "avisos": 0,
            "tickets_abertos": 0,
            "tickets_atendidos": 0,
            "xp": 0,
            "nivel": 1,
            "vitorias_bedwars": 0,
            "derrotas_bedwars": 0,
            "camas_destruidas": 0,
            "kills": 0,
            "deaths": 0
        })
        result = await api_request("Membro", "POST", dados)
        print(f"[API] ✅ Novo membro registrado: {username}")
    
    return result

async def atualizar_membro(discord_id, dados_atualizacao):
    """Atualiza dados de um membro específico"""
    membro = await buscar_membro_por_discord_id(discord_id)
    if membro:
        result = await api_request("Membro", "PUT", dados_atualizacao, membro['id'])
        print(f"[API] ✅ Membro atualizado: {discord_id}")
        return result
    return None

async def incrementar_avisos(discord_id):
    """Incrementa o contador de avisos de um membro"""
    membro = await buscar_membro_por_discord_id(discord_id)
    if membro:
        novos_avisos = (membro.get('avisos', 0) or 0) + 1
        await api_request("Membro", "PUT", {"avisos": novos_avisos}, membro['id'])
        print(f"[API] ⚠️ Avisos incrementados para {discord_id}: {novos_avisos}")
        return novos_avisos
    return 0

async def registrar_historico(discord_id, tipo, descricao, moderador_id=None, moderador_nome=None, detalhes=None):
    """Registra um evento no histórico do membro"""
    dados = {
        "discord_id": str(discord_id),
        "tipo": tipo,
        "descricao": descricao,
        "data_evento": datetime.utcnow().isoformat()
    }
    
    if moderador_id:
        dados["moderador_id"] = str(moderador_id)
    if moderador_nome:
        dados["moderador_nome"] = moderador_nome
    if detalhes:
        dados["detalhes"] = detalhes
    
    result = await api_request("HistoricoMembro", "POST", dados)
    print(f"[API] 📝 Histórico registrado: {tipo} - {descricao}")
    return result

async def registrar_ticket(ticket_id, usuario_id, usuario_nome, usuario_avatar=None, status="aberto", categoria="suporte"):
    """Registra um ticket no site"""
    dados = {
        "ticket_id": str(ticket_id),
        "usuario_id": str(usuario_id),
        "usuario_nome": usuario_nome,
        "status": status,
        "categoria": categoria,
        "prioridade": "media",
        "data_abertura": datetime.utcnow().isoformat()
    }
    
    if usuario_avatar:
        dados["usuario_avatar"] = usuario_avatar
    
    result = await api_request("Ticket", "POST", dados)
    print(f"[API] 🎫 Ticket registrado: {ticket_id} - {status}")
    
    membro = await buscar_membro_por_discord_id(usuario_id)
    if membro:
        tickets_abertos = (membro.get('tickets_abertos', 0) or 0) + 1
        await api_request("Membro", "PUT", {"tickets_abertos": tickets_abertos}, membro['id'])
    
    return result

async def buscar_ticket_por_id(ticket_id):
    """Busca um ticket pelo ticket_id"""
    try:
        result = await api_request("Ticket", "GET", {"ticket_id": str(ticket_id)})
        if result and len(result) > 0:
            return result[0]
        return None
    except:
        return None

async def atualizar_ticket(ticket_id, dados_atualizacao):
    """Atualiza um ticket existente"""
    ticket = await buscar_ticket_por_id(ticket_id)
    if ticket:
        result = await api_request("Ticket", "PUT", dados_atualizacao, ticket['id'])
        print(f"[API] 🎫 Ticket atualizado: {ticket_id}")
        return result
    return None

async def atualizar_contador_staff(staff_id, staff_nome=None):
    """Incrementa contador de tickets atendidos do staff"""
    membro = await buscar_membro_por_discord_id(staff_id)
    if membro:
        tickets_atendidos = (membro.get('tickets_atendidos', 0) or 0) + 1
        await api_request("Membro", "PUT", {"tickets_atendidos": tickets_atendidos}, membro['id'])
        print(f"[API] 👤 Staff {staff_id} atendeu mais um ticket: {tickets_atendidos}")
        return tickets_atendidos
    return 0

async def atualizar_status_membro(discord_id, status):
    """Atualiza o status de um membro"""
    membro = await buscar_membro_por_discord_id(discord_id)
    if membro:
        await api_request("Membro", "PUT", {"status": status}, membro['id'])
        print(f"[API] 🔄 Status atualizado para {discord_id}: {status}")

async def atualizar_cargo_membro(discord_id, novo_cargo):
    """Atualiza o cargo de um membro no site"""
    membro = await buscar_membro_por_discord_id(discord_id)
    if membro:
        await api_request("Membro", "PUT", {"cargo_servidor": novo_cargo}, membro['id'])
        print(f"[API] 🎭 Cargo atualizado para {discord_id}: {novo_cargo}")

# ============================================
# 🤖 CONFIGURAÇÃO DO BOT
# ============================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ============================================
# 📋 CONFIGURAÇÕES
# ============================================

# Sistema de avisos por usuário
user_warnings = {}  # {user_id: {"count": int, "last_warning": datetime}}

# Tickets ativos (para controle de tempo)
active_tickets = {}  # {channel_id: {"created_at": datetime, "user_id": int, "claimed_by": None}}

PALAVROES = [
    # Palavrões comuns
    'caralho', 'porra', 'merda', 'fdp', 'filho da puta', 'puta', 'putinha', 'putaria',
    'viado', 'veado', 'viado', 'arrombado', 'arrombada', 'cuzao', 'cuzão', 'cu',
    'buceta', 'boceta', 'piroca', 'pica', 'rola', 'cacete', 'caraio',
    
    # Ofensas pessoais
    'desgraça', 'desgraca', 'desgraçado', 'idiota', 'imbecil', 'otario', 'otário',
    'babaca', 'bosta', 'lixo', 'inutil', 'inútil', 'retardado', 'retardada',
    'burro', 'burra', 'animal', 'mongol', 'mongoloide', 'doente', 'maluco',
    
    # Xingamentos compostos
    'pau no cu', 'vai se foder', 'foda-se', 'fodase', 'vai tomar no cu',
    'tomar no cu', 'tmnc', 'vsf', 'tnc', 'pqp', 'krl', 'vtnc', 'fdp',
    'fds', 'pnc', 'kct', 'vsfmlk', 'filha da puta', 'puta que pariu',
    
    # Variações
    'fude', 'fuder', 'fudido', 'fudida', 'fudeu', 'foder',
    'corno', 'corna', 'chifrudo', 'gado', 'trouxa', 'otaria',
    'vagabundo', 'vagabunda', 'vadia', 'vadio', 'safado', 'safada',
    'nojento', 'nojenta', 'podre', 'fedido', 'fedida',
    
    # Homofóbicos/discriminatórios (proibido)
    'gay', 'bicha', 'bichona', 'sapatao', 'sapatão', 'traveco',
    'macaco', 'preto', 'negro', 'crioulo', 'favelado',
    
    # Família
    'sua mae', 'sua mãe', 'tua mae', 'tua mãe', 'mae', 'mãe',
    
    # Mais variações gamer/internet
    'noob', 'lixao', 'lixão', 'trash', 'cancer', 'cancêr', 'aids',
    'autista', 'down', 'mongol', 'aborto', 'aberração',
    
    # Com caracteres especiais (bypass attempts)
    'c4ralho', 'p0rra', 'm3rda', 'put4', 'v1ado', 'buc3ta',
    'arr0mbado', 'cuz4o', 'id1ota', 'imb3cil', 'b4baca'
]

CORES = {
    'principal': 0x55FF55,  # Verde Minecraft
    'sucesso': 0x00AA00,    # Verde escuro
    'erro': 0xAA0000,       # Vermelho escuro
    'info': 0x55FFFF,       # Aqua/Cyan
    'aviso': 0xFFAA00,      # Dourado
    'diamante': 0x55FFFF,   # Azul diamante
    'esmeralda': 0x00AA00,  # Verde esmeralda
    'ouro': 0xFFAA00,       # Dourado
    'redstone': 0xAA0000,   # Vermelho redstone
    'lapis': 0x5555FF       # Azul lapis
}

# Cargos que podem ver tickets
CARGOS_TICKET = ['👑 Líder', '⚔️ Sub-Líder', '🎯 Recrutador']

# ============================================
# 🚀 EVENTO DE INICIALIZAÇÃO
# ============================================

@bot.event
async def on_ready():
    print(f'''
    ╔═══════════════════════════════════════════════════╗
    ║                                                   ║
    ║   ⛏️  BOT CLAN 147 - MINECRAFT BEDWARS  ⛏️       ║
    ║                                                   ║
    ╠═══════════════════════════════════════════════════╣
    ║                                                   ║
    ║   🟢 STATUS: ONLINE                               ║
    ║   🤖 Bot: {bot.user.name:<30}       ║
    ║   🆔 ID: {bot.user.id}                        ║
    ║   🌐 Servidores: {len(bot.guilds):<5}                         ║
    ║                                                   ║
    ║   ⚔️  Dominando o Bedwars desde sempre!          ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝
    ''')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="⛏️ Bedwars | Clan 147"
        )
    )
    check_ticket_expiry.start()  # Inicia verificação de tickets
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados!")
    except Exception as e:
        print(f"❌ Erro ao sincronizar: {e}")

# ============================================
# ⏰ TASK: VERIFICAR TICKETS EXPIRADOS (5 HORAS)
# ============================================

@tasks.loop(minutes=5)
async def check_ticket_expiry():
    now = datetime.utcnow()
    expired = []
    
    for channel_id, ticket_info in active_tickets.items():
        # Se passou 5 horas desde a criação
        if now - ticket_info["created_at"] > timedelta(hours=5):
            expired.append(channel_id)
    
    for channel_id in expired:
        try:
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="⏰ Ticket Expirado",
                    description="Este ticket foi fechado automaticamente após 5 horas.",
                    color=CORES['aviso']
                )
                await channel.send(embed=embed)
                await asyncio.sleep(5)
                await channel.delete()
            del active_tickets[channel_id]
        except:
            if channel_id in active_tickets:
                del active_tickets[channel_id]

# ============================================
# 🏗️ COMANDO DE SETUP DO SERVIDOR
# ============================================

@bot.tree.command(name="setup", description="🏗️ Configura o servidor completo do Clan 147")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    
    status_embed = discord.Embed(
        title="🏗️ Configurando Servidor Clan 147...",
        description="Aguarde enquanto criamos tudo...",
        color=CORES['principal']
    )
    status_msg = await interaction.followup.send(embed=status_embed, ephemeral=True)
    
    # Deletar canais e categorias existentes (opcional)
    # for channel in guild.channels:
    #     try:
    #         await channel.delete()
    #     except:
    #         pass
    
    # ========== CARGOS (ESTILO MINECRAFT) ==========
    cargos_config = [
        {"name": "👑 Líder", "color": discord.Color.from_rgb(255, 170, 0), "hoist": True, "permissions": discord.Permissions.all()},  # Dourado
        {"name": "⚔️ Sub-Líder", "color": discord.Color.from_rgb(170, 0, 0), "hoist": True},  # Vermelho escuro
        {"name": "💻 Sub-Líder Dev", "color": discord.Color.from_rgb(170, 0, 170), "hoist": True, "permissions": discord.Permissions.all()},  # Roxo - DEV com todas as perms
        {"name": "🎯 Recrutador", "color": discord.Color.from_rgb(255, 85, 85), "hoist": True},  # Vermelho claro
        {"name": "🛡️ Moderador", "color": discord.Color.from_rgb(85, 85, 255), "hoist": True},  # Azul
        {"name": "💎 Diamante", "color": discord.Color.from_rgb(85, 255, 255), "hoist": True},  # Cyan diamante
        {"name": "🟢 Esmeralda", "color": discord.Color.from_rgb(0, 170, 0), "hoist": True},  # Verde esmeralda
        {"name": "🟡 Ouro", "color": discord.Color.from_rgb(255, 170, 0), "hoist": True},  # Dourado
        {"name": "⚪ Ferro", "color": discord.Color.from_rgb(170, 170, 170), "hoist": True},  # Cinza
        {"name": "🪨 Pedra", "color": discord.Color.from_rgb(85, 85, 85), "hoist": True},  # Cinza escuro
        {"name": "🆕 Novato", "color": discord.Color.from_rgb(85, 85, 85), "hoist": True},  # Cinza
        {"name": "🔇 Mutado", "color": discord.Color.from_rgb(170, 0, 0), "hoist": False},  # Vermelho
    ]
    
    cargos_criados = {}
    for cargo_info in cargos_config:
        cargo = await guild.create_role(
            name=cargo_info["name"],
            color=cargo_info.get("color", discord.Color.default()),
            hoist=cargo_info.get("hoist", False),
            permissions=cargo_info.get("permissions", discord.Permissions.none())
        )
        cargos_criados[cargo_info["name"]] = cargo
    
    # ========== CATEGORIAS E CANAIS (ESTILO MINECRAFT BW) ==========
    
    # ⛏️ INFORMAÇÕES
    cat_info = await guild.create_category("⛏️ ═══ INFORMAÇÕES ═══")
    await guild.create_text_channel("📜┃regras", category=cat_info, 
        topic="⚠️ Regras do Clan 147 - Leia antes de jogar!")
    await guild.create_text_channel("📣┃anúncios", category=cat_info,
        topic="📢 Anúncios importantes do clan")
    await guild.create_text_channel("🎉┃bem-vindo", category=cat_info,
        topic="👋 Boas-vindas aos novos guerreiros!")
    await guild.create_text_channel("📊┃status-mc", category=cat_info,
        topic="🖥️ Status dos servidores de Minecraft")
    await guild.create_text_channel("🏆┃ranking", category=cat_info,
        topic="🥇 Ranking dos melhores jogadores")
    
    # 💬 COMUNIDADE GERAL
    cat_comunidade = await guild.create_category("💬 ═══ COMUNIDADE ═══")
    await guild.create_text_channel("💬┃bate-papo", category=cat_comunidade,
        topic="🗣️ Converse com a galera do clan!")
    await guild.create_text_channel("🎮┃bedwars-talk", category=cat_comunidade,
        topic="🛏️ Discussões sobre Bedwars")
    await guild.create_text_channel("💡┃estratégias", category=cat_comunidade,
        topic="🧠 Compartilhe suas táticas de BW")
    await guild.create_text_channel("🤖┃comandos", category=cat_comunidade,
        topic="🤖 Use comandos do bot aqui")
    
    # 🖼️ MÍDIA
    cat_midia = await guild.create_category("🖼️ ═══ MÍDIA ═══")
    await guild.create_text_channel("📸┃screenshots", category=cat_midia,
        topic="📷 Poste suas melhores screenshots!")
    await guild.create_text_channel("🎬┃videos", category=cat_midia,
        topic="🎥 Compartilhe seus vídeos e clips")
    await guild.create_text_channel("😂┃memes", category=cat_midia,
        topic="🤣 Memes de Minecraft e Bedwars")
    await guild.create_text_channel("🎨┃fan-art", category=cat_midia,
        topic="🖌️ Artes e criações da comunidade")
    
    # 🎯 RECRUTAMENTO
    cat_recrutamento = await guild.create_category("🎯 ═══ RECRUTAMENTO ═══")
    await guild.create_text_channel("📝┃como-entrar", category=cat_recrutamento,
        topic="📋 Informações para entrar no Clan 147")
    await guild.create_text_channel("📋┃formulários", category=cat_recrutamento,
        topic="✍️ Envie seu formulário de entrada")
    await guild.create_text_channel("✅┃aprovados", category=cat_recrutamento,
        topic="🎉 Novos membros aprovados!")
    await guild.create_text_channel("❌┃recusados", category=cat_recrutamento,
        topic="😢 Candidatos recusados")
    
    # 🎫 SUPORTE
    cat_suporte = await guild.create_category("🎫 ═══ SUPORTE ═══")
    await guild.create_text_channel("🎫┃abrir-ticket", category=cat_suporte,
        topic="🆘 Clique para abrir um ticket de suporte")
    await guild.create_text_channel("❓┃dúvidas", category=cat_suporte,
        topic="❔ Tire suas dúvidas aqui")
    await guild.create_text_channel("🐛┃bugs", category=cat_suporte,
        topic="🪲 Reporte bugs encontrados")
    
    # 🔊 CANAIS DE VOZ - GERAL
    cat_voz = await guild.create_category("🔊 ═══ VOZ GERAL ═══")
    await guild.create_voice_channel("🎙️ Lobby Principal", category=cat_voz)
    await guild.create_voice_channel("💬 Bate-papo 1", category=cat_voz)
    await guild.create_voice_channel("💬 Bate-papo 2", category=cat_voz)
    await guild.create_voice_channel("🎵 Música", category=cat_voz)
    await guild.create_voice_channel("💤 AFK", category=cat_voz)
    
    # ⚔️ CANAIS DE VOZ - BEDWARS
    cat_voz_bw = await guild.create_category("⚔️ ═══ VOZ BEDWARS ═══")
    await guild.create_voice_channel("🛏️ Bedwars Solo", category=cat_voz_bw)
    await guild.create_voice_channel("👥 Bedwars Duo", category=cat_voz_bw)
    await guild.create_voice_channel("👨‍👩‍👧‍👦 Bedwars Trio", category=cat_voz_bw)
    await guild.create_voice_channel("🏆 Bedwars Squad", category=cat_voz_bw)
    await guild.create_voice_channel("⚔️ Ranked", category=cat_voz_bw)
    await guild.create_voice_channel("🎯 Treino PvP", category=cat_voz_bw)
    
    # 🎯 CANAIS DE VOZ - RECRUTAMENTO
    cat_voz_rec = await guild.create_category("🎯 ═══ VOZ RECRUTAMENTO ═══")
    overwrites_rec = {
        guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
        cargos_criados["👑 Líder"]: discord.PermissionOverwrite(connect=True, speak=True, mute_members=True),
        cargos_criados["⚔️ Sub-Líder"]: discord.PermissionOverwrite(connect=True, speak=True, mute_members=True),
        cargos_criados["🎯 Recrutador"]: discord.PermissionOverwrite(connect=True, speak=True, mute_members=True),
    }
    await guild.create_voice_channel("📝 Entrevista 1", category=cat_voz_rec, overwrites=overwrites_rec)
    await guild.create_voice_channel("📝 Entrevista 2", category=cat_voz_rec, overwrites=overwrites_rec)
    await guild.create_voice_channel("📝 Entrevista 3", category=cat_voz_rec, overwrites=overwrites_rec)
    
    # 👑 STAFF (PRIVADO)
    cat_staff = await guild.create_category("👑 ═══ STAFF ═══")
    overwrites_staff = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        cargos_criados["👑 Líder"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        cargos_criados["⚔️ Sub-Líder"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        cargos_criados["🎯 Recrutador"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        cargos_criados["🛡️ Moderador"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    await guild.create_text_channel("📋┃logs", category=cat_staff, overwrites=overwrites_staff,
        topic="📊 Logs de ações do servidor")
    await guild.create_text_channel("💬┃staff-chat", category=cat_staff, overwrites=overwrites_staff,
        topic="💬 Chat exclusivo da staff")
    await guild.create_text_channel("⚠️┃punições", category=cat_staff, overwrites=overwrites_staff,
        topic="🔨 Registro de punições")
    await guild.create_text_channel("🎫┃tickets-admin", category=cat_staff, overwrites=overwrites_staff,
        topic="🎫 Gerenciamento de tickets - STAFF ONLY")
    await guild.create_text_channel("📝┃recrutamento-admin", category=cat_staff, overwrites=overwrites_staff,
        topic="🎯 Decisões de recrutamento")
    
    # 🔒 ADMIN (APENAS LÍDERES)
    cat_admin = await guild.create_category("🔒 ═══ ADMINISTRAÇÃO ═══")
    overwrites_admin = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        cargos_criados["👑 Líder"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        cargos_criados["⚔️ Sub-Líder"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    await guild.create_text_channel("👑┃líderes", category=cat_admin, overwrites=overwrites_admin,
        topic="👑 Chat exclusivo dos líderes")
    await guild.create_text_channel("📊┃finanças", category=cat_admin, overwrites=overwrites_admin,
        topic="💰 Gestão financeira do clan")
    await guild.create_text_channel("🗓️┃planejamento", category=cat_admin, overwrites=overwrites_admin,
        topic="📅 Planejamento de eventos e estratégias")
    await guild.create_voice_channel("🔒 Reunião Admin", category=cat_admin, overwrites=overwrites_admin)
    
    # Embed de sucesso
    success_embed = discord.Embed(
        title="⛏️ Servidor Configurado com Sucesso!",
        description=f"""
        **O servidor do Clan 147 está pronto para dominar o Bedwars!**
        
        📁 **Categorias criadas:** 10
        💬 **Canais de texto:** 25+
        🔊 **Canais de voz:** 15+
        🎭 **Cargos criados:** {len(cargos_config)}
        
        **📋 Próximos passos:**
        • Use `/regras` para enviar as regras
        • Use `/ticket` no canal de suporte
        • Use `/recrutamento` no canal de recrutamento
        
        **⚔️ Bom jogo!**
        """,
        color=CORES['esmeralda']
    )
    success_embed.set_thumbnail(url="https://i.imgur.com/JfEfT9Q.png")
    success_embed.set_footer(text="⛏️ Clan 147 - Dominando o Bedwars!")
    await status_msg.edit(embed=success_embed)

# ============================================
# 📜 COMANDO DE REGRAS
# ============================================

@bot.tree.command(name="regras", description="📜 Envia as regras do servidor")
@app_commands.checks.has_permissions(administrator=True)
async def regras(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⛏️ REGRAS DO CLAN 147 - BEDWARS",
        description="**Leia TODAS as regras antes de jogar!**",
        color=CORES['diamante']
    )
    embed.add_field(
        name="1️⃣ Respeito Acima de Tudo",
        value="Respeite TODOS os membros. Xingamentos, ofensas ou discriminação resultam em punição.",
        inline=False
    )
    embed.add_field(
        name="2️⃣ Sem Spam ou Flood",
        value="Não faça spam de mensagens, links, emojis ou menções repetidas.",
        inline=False
    )
    embed.add_field(
        name="3️⃣ Conteúdo Apropriado",
        value="Proibido conteúdo +18, gore, violência ou material inapropriado.",
        inline=False
    )
    embed.add_field(
        name="4️⃣ Sem Hacks ou Cheats",
        value="Hacks, cheats, exploits ou qualquer trapaça = BAN PERMANENTE.",
        inline=False
    )
    embed.add_field(
        name="5️⃣ Use os Canais Certos",
        value="Cada canal tem seu propósito. Mídia no canal de mídia, etc.",
        inline=False
    )
    embed.add_field(
        name="6️⃣ Obedeça a Staff",
        value="Decisões da staff são finais. Reclamações via ticket.",
        inline=False
    )
    embed.add_field(
        name="7️⃣ Sem Divulgação",
        value="Proibido divulgar outros servidores, clans ou conteúdo externo.",
        inline=False
    )
    embed.add_field(
        name="⚠️ Sistema de Punições (Xingamentos)",
        value="🟡 1º → Aviso | 🟠 2º → Último Aviso | 🔴 3º → MUTE 1H | ⛔ 4º → MUTE 4H + Reset",
        inline=False
    )
    embed.add_field(
        name="🔨 Punições Gerais",
        value="Aviso → Mute → Kick → Ban Temporário → Ban Permanente",
        inline=False
    )
    embed.set_thumbnail(url="https://i.imgur.com/JfEfT9Q.png")
    embed.set_image(url="https://i.imgur.com/8QGK3Pj.png")  # Banner Minecraft
    embed.set_footer(text="⛏️ Ao participar do servidor, você concorda com estas regras! | Clan 147")
    
    await interaction.response.send_message("✅ Regras enviadas!", ephemeral=True)
    await interaction.channel.send(embed=embed)

# ============================================
# 🛡️ SISTEMA ANTI-XINGAMENTO AVANÇADO
# ============================================
# 1º xingamento: Aviso (restam 2)
# 2º xingamento: Aviso (restam 1)
# 3º xingamento: Mute 1 hora
# 4º xingamento: Mute 4 horas
# Depois reinicia o contador

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Verificar palavrões
    conteudo_lower = message.content.lower()
    # Remover caracteres especiais para detectar bypass
    conteudo_clean = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', '', conteudo_lower)
    
    for palavrao in PALAVROES:
        if palavrao in conteudo_lower or palavrao in conteudo_clean:
            await message.delete()
            
            user_id = message.author.id
            
            # Inicializar ou atualizar contador do usuário
            if user_id not in user_warnings:
                user_warnings[user_id] = {"count": 0, "last_warning": datetime.utcnow()}
            
            user_warnings[user_id]["count"] += 1
            user_warnings[user_id]["last_warning"] = datetime.utcnow()
            count = user_warnings[user_id]["count"]
            
            # Determinar punição baseada no número de infrações
            if count == 1:
                # 1º xingamento - Aviso
                aviso_embed = discord.Embed(
                    title="⚠️ AVISO - Linguagem Inapropriada",
                    description=f"""
                    {message.author.mention}, sua mensagem foi removida!
                    
                    ⛏️ **Infrações:** {count}/4
                    ⏳ **Avisos restantes:** 2
                    
                    *Próxima infração: mais um aviso*
                    """,
                    color=CORES['aviso']
                )
                aviso_embed.set_footer(text="🛡️ Sistema Anti-Xingamento | Clan 147")
                
            elif count == 2:
                # 2º xingamento - Último aviso
                aviso_embed = discord.Embed(
                    title="🔶 ÚLTIMO AVISO!",
                    description=f"""
                    {message.author.mention}, CUIDADO!
                    
                    ⛏️ **Infrações:** {count}/4
                    ⏳ **Avisos restantes:** 1
                    
                    ⚠️ *Próxima infração: MUTE DE 1 HORA!*
                    """,
                    color=CORES['aviso']
                )
                aviso_embed.set_footer(text="🛡️ A coisa está ficando séria...")
                
            elif count == 3:
                # 3º xingamento - Mute 1 hora
                try:
                    await message.author.timeout(timedelta(hours=1), reason="Anti-xingamento: 3ª infração")
                except:
                    pass
                    
                aviso_embed = discord.Embed(
                    title="🔴 MUTADO POR 1 HORA!",
                    description=f"""
                    {message.author.mention} foi **MUTADO**!
                    
                    ⛏️ **Infrações:** {count}/4
                    ⏰ **Duração:** 1 hora
                    
                    ⚠️ *Próxima infração: MUTE DE 4 HORAS!*
                    """,
                    color=CORES['erro']
                )
                aviso_embed.set_footer(text="🛡️ Aprenda a respeitar os membros!")
                
            else:  # count >= 4
                # 4º xingamento - Mute 4 horas e reinicia contador
                try:
                    await message.author.timeout(timedelta(hours=4), reason="Anti-xingamento: 4ª infração")
                except:
                    pass
                    
                aviso_embed = discord.Embed(
                    title="🔴 MUTADO POR 4 HORAS!",
                    description=f"""
                    {message.author.mention} foi **MUTADO SEVERAMENTE**!
                    
                    ⛏️ **Infrações:** {count}/4
                    ⏰ **Duração:** 4 horas
                    
                    ✅ *Contador reiniciado após essa punição*
                    """,
                    color=CORES['erro']
                )
                aviso_embed.set_footer(text="🛡️ Respeite as regras do Clan 147!")
                
                # Reiniciar contador
                user_warnings[user_id]["count"] = 0
            
            aviso_msg = await message.channel.send(embed=aviso_embed)
            await asyncio.sleep(15)
            await aviso_msg.delete()
            
            # ENVIAR PARA O SITE - Registrar no histórico
            await registrar_historico(
                discord_id=message.author.id,
                tipo="xingamento",
                descricao=f"Xingamento detectado ({count}/4)",
                mensagem_original=message.content[:200],
                canal=message.channel.name,
                duracao="1 hora" if count == 3 else "4 horas" if count >= 4 else None
            )
            
            # Log para staff
            for channel in message.guild.text_channels:
                if "logs" in channel.name:
                    log_embed = discord.Embed(
                        title="🔴 Xingamento Detectado",
                        color=CORES['erro'],
                        timestamp=datetime.utcnow()
                    )
                    log_embed.add_field(name="👤 Usuário", value=f"{message.author} ({message.author.id})")
                    log_embed.add_field(name="📊 Infração", value=f"{count}/4")
                    log_embed.add_field(name="📍 Canal", value=message.channel.mention)
                    log_embed.add_field(name="💬 Mensagem", value=f"||{message.content[:100]}||", inline=False)
                    
                    if count == 3:
                        log_embed.add_field(name="⚡ Ação", value="Mute 1 hora", inline=False)
                    elif count >= 4:
                        log_embed.add_field(name="⚡ Ação", value="Mute 4 horas + Reset", inline=False)
                    
                    await channel.send(embed=log_embed)
                    break
            return
    
    await bot.process_commands(message)

# ============================================
# 🎫 SISTEMA DE TICKETS AVANÇADO
# ============================================
# - Apenas Líderes, Sub-Líderes e Recrutadores veem tickets
# - Notificação no canal admin quando alguém abre ticket
# - Staff precisa "aceitar" o ticket antes de atender
# - Ticket fecha automaticamente após 5 horas
# - DM ao usuário quando ticket é aceito/fechado

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket", emoji="⛏️")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # Verificar se já tem ticket aberto
        for channel in guild.text_channels:
            if f"ticket-{user.id}" in channel.name:
                await interaction.response.send_message(
                    f"❌ Você já tem um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return
        
        # Criar categoria de tickets se não existir
        ticket_category = discord.utils.get(guild.categories, name="🎫 ═══ TICKETS ABERTOS ═══")
        if not ticket_category:
            ticket_category = await guild.create_category("🎫 ═══ TICKETS ABERTOS ═══")
        
        # Permissões do canal - APENAS STAFF ESPECÍFICA
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        # Adicionar apenas cargos específicos (Líder, Sub-Líder, Recrutador)
        for role in guild.roles:
            if any(cargo in role.name for cargo in CARGOS_TICKET):
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        # Criar canal do ticket
        ticket_channel = await guild.create_text_channel(
            name=f"🎫┃ticket-{user.name}",
            category=ticket_category,
            overwrites=overwrites
        )
        
        # Registrar ticket ativo
        active_tickets[ticket_channel.id] = {
            "created_at": datetime.utcnow(),
            "user_id": user.id,
            "claimed_by": None
        }
        
        # Embed inicial do ticket
        embed = discord.Embed(
            title="⛏️ Ticket Aberto - Clan 147",
            description=f"""
            Olá {user.mention}! Bem-vindo ao suporte do **Clan 147**!
            
            🎮 **Descreva seu problema ou dúvida abaixo.**
            
            ⏰ **Aguarde um membro da staff aceitar seu ticket.**
            Este ticket será fechado automaticamente em **5 horas**.
            
            📋 **Informações:**
            • Seja claro e objetivo
            • Envie prints se necessário
            • Aguarde pacientemente
            """,
            color=CORES['diamante']
        )
        embed.set_footer(text=f"⏰ Ticket expira em 5 horas | ID: {user.id}")
        embed.set_thumbnail(url="https://i.imgur.com/JfEfT9Q.png")  # Ícone Minecraft
        
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(
            f"✅ Ticket criado: {ticket_channel.mention}\n⏰ Um membro da staff irá aceitar em breve!",
            ephemeral=True
        )
        
        # ENVIAR PARA O SITE - Registrar ticket
        await registrar_ticket(
            ticket_id=str(ticket_channel.id),
            usuario_id=user.id,
            usuario_nome=user.name,
            status="aberto"
        )
        
        # Registrar no histórico do usuário
        await registrar_historico(
            discord_id=user.id,
            tipo="ticket_aberto",
            descricao=f"Abriu um ticket de suporte"
        )
        
        # NOTIFICAR NO CANAL DE TICKETS-ADMIN
        for channel in guild.text_channels:
            if "tickets-admin" in channel.name:
                admin_embed = discord.Embed(
                    title="🆕 NOVO TICKET ABERTO!",
                    description=f"""
                    **Um novo ticket foi aberto e aguarda atendimento!**
                    
                    👤 **Usuário:** {user.mention} ({user.name})
                    🆔 **ID:** {user.id}
                    📍 **Canal:** {ticket_channel.mention}
                    ⏰ **Aberto em:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC
                    
                    **Clique no botão abaixo para aceitar o ticket!**
                    """,
                    color=CORES['aviso']
                )
                admin_embed.set_thumbnail(url=user.display_avatar.url)
                await channel.send(embed=admin_embed, view=AcceptTicketView(ticket_channel.id, user.id))
                break

class AcceptTicketView(discord.ui.View):
    def __init__(self, channel_id: int, user_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.user_id = user_id
    
    @discord.ui.button(label="✅ Aceitar Ticket", style=discord.ButtonStyle.success, custom_id="accept_ticket")
    async def accept_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar se tem cargo de staff
        has_permission = False
        for role in interaction.user.roles:
            if any(cargo in role.name for cargo in CARGOS_TICKET):
                has_permission = True
                break
        
        if not has_permission:
            await interaction.response.send_message("❌ Você não tem permissão para aceitar tickets!", ephemeral=True)
            return
        
        # Verificar se ticket ainda existe
        ticket_channel = interaction.guild.get_channel(self.channel_id)
        if not ticket_channel:
            await interaction.response.send_message("❌ Este ticket não existe mais!", ephemeral=True)
            # Remover mensagem de admin
            await interaction.message.delete()
            return
        
        # Verificar se já foi aceito
        if self.channel_id in active_tickets and active_tickets[self.channel_id]["claimed_by"]:
            await interaction.response.send_message("❌ Este ticket já foi aceito por outro membro!", ephemeral=True)
            return
        
        # Marcar como aceito
        if self.channel_id in active_tickets:
            active_tickets[self.channel_id]["claimed_by"] = interaction.user.id
        
        # Notificar no canal do ticket
        accept_embed = discord.Embed(
            title="✅ Ticket Aceito!",
            description=f"""
            {interaction.user.mention} aceitou este ticket!
            
            👤 **Atendente:** {interaction.user.name}
            ⏰ **Aceito em:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC
            
            *O atendente irá te ajudar em breve!*
            """,
            color=CORES['sucesso']
        )
        await ticket_channel.send(embed=accept_embed)
        
        # Enviar DM para o usuário
        user = interaction.guild.get_member(self.user_id)
        if user:
            try:
                dm_embed = discord.Embed(
                    title="🎫 Seu Ticket Foi Aceito!",
                    description=f"""
                    Olá! Seu ticket no **Clan 147** foi aceito!
                    
                    👤 **Atendente:** {interaction.user.name}
                    📍 **Canal:** {ticket_channel.mention}
                    
                    Volte ao servidor para continuar a conversa!
                    """,
                    color=CORES['sucesso']
                )
                await user.send(embed=dm_embed)
            except:
                pass  # Usuário com DM fechada
        
        # Atualizar mensagem de admin (desabilitar botão)
        for item in self.children:
            item.disabled = True
            item.label = f"✅ Aceito por {interaction.user.name}"
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(f"✅ Você aceitou o ticket! Vá para {ticket_channel.mention}", ephemeral=True)
        
        # ENVIAR PARA O SITE - Atualizar contador do staff
        await atualizar_contador_staff(interaction.user.id)
    
    @discord.ui.button(label="❌ Recusar/Fechar", style=discord.ButtonStyle.danger, custom_id="reject_ticket")
    async def reject_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar permissão
        has_permission = False
        for role in interaction.user.roles:
            if any(cargo in role.name for cargo in CARGOS_TICKET):
                has_permission = True
                break
        
        if not has_permission:
            await interaction.response.send_message("❌ Você não tem permissão!", ephemeral=True)
            return
        
        ticket_channel = interaction.guild.get_channel(self.channel_id)
        
        # Notificar usuário por DM
        user = interaction.guild.get_member(self.user_id)
        if user:
            try:
                dm_embed = discord.Embed(
                    title="🎫 Seu Ticket Foi Fechado",
                    description=f"""
                    Seu ticket no **Clan 147** foi fechado por {interaction.user.name}.
                    
                    Se ainda precisar de ajuda, abra um novo ticket!
                    """,
                    color=CORES['erro']
                )
                await user.send(embed=dm_embed)
            except:
                pass
        
        # Deletar canal se existir
        if ticket_channel:
            await ticket_channel.delete()
        
        # Remover dos tickets ativos
        if self.channel_id in active_tickets:
            del active_tickets[self.channel_id]
        
        # Atualizar mensagem
        for item in self.children:
            item.disabled = True
        self.children[1].label = f"❌ Fechado por {interaction.user.name}"
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message("✅ Ticket fechado!", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apenas staff ou dono do ticket pode fechar
        channel_name = interaction.channel.name
        
        # Remover dos tickets ativos
        if interaction.channel.id in active_tickets:
            del active_tickets[interaction.channel.id]
        
        embed = discord.Embed(
            title="🔒 Ticket Fechado",
            description=f"""
            Este ticket foi fechado por {interaction.user.mention}.
            
            **O canal será deletado em 10 segundos...**
            """,
            color=CORES['erro']
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(10)
        await interaction.channel.delete()

@bot.tree.command(name="ticket", description="🎫 Envia painel de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⛏️ Central de Suporte - Clan 147",
        description="""
        **🎮 Precisa de ajuda no Clan 147?**
        
        Clique no botão abaixo para abrir um ticket!
        
        📌 **Use tickets para:**
        • 🔴 Reportar jogadores
        • ❓ Tirar dúvidas sobre o clan
        • 🐛 Reportar bugs
        • 💡 Dar sugestões
        • ⚠️ Fazer denúncias
        • 🎯 Dúvidas sobre recrutamento
        
        ⏰ **Tickets fecham automaticamente após 5 horas!**
        """,
        color=CORES['diamante']
    )
    embed.set_thumbnail(url="https://i.imgur.com/JfEfT9Q.png")
    embed.set_footer(text="⛏️ Clan 147 - Dominando o Bedwars!")
    
    await interaction.response.send_message("✅ Painel de tickets enviado!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=TicketView())

# ============================================
# 📝 SISTEMA DE RECRUTAMENTO
# ============================================

class RecrutamentoModal(discord.ui.Modal, title="📝 Formulário de Entrada - Clan 147"):
    nome_minecraft = discord.ui.TextInput(
        label="Nome no Minecraft",
        placeholder="Seu nick exato no jogo",
        required=True,
        max_length=16
    )
    
    idade = discord.ui.TextInput(
        label="Sua Idade",
        placeholder="Ex: 16",
        required=True,
        max_length=2
    )
    
    tempo_jogando = discord.ui.TextInput(
        label="Há quanto tempo joga Minecraft?",
        placeholder="Ex: 3 anos",
        required=True,
        max_length=50
    )
    
    porque_entrar = discord.ui.TextInput(
        label="Por que quer entrar no Clan 147?",
        style=discord.TextStyle.paragraph,
        placeholder="Conte um pouco sobre você e por que quer fazer parte do clan...",
        required=True,
        max_length=500
    )
    
    habilidades = discord.ui.TextInput(
        label="Suas habilidades no jogo",
        style=discord.TextStyle.paragraph,
        placeholder="PvP, construção, redstone, farms, etc...",
        required=True,
        max_length=300
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Enviar para canal de formulários
        for channel in interaction.guild.text_channels:
            if "formulários" in channel.name or "formularios" in channel.name:
                embed = discord.Embed(
                    title="📝 Nova Solicitação de Entrada",
                    color=CORES['info'],
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="👤 Discord", value=f"{interaction.user.mention}\n{interaction.user}", inline=True)
                embed.add_field(name="🎮 Nick Minecraft", value=self.nome_minecraft.value, inline=True)
                embed.add_field(name="📅 Idade", value=self.idade.value, inline=True)
                embed.add_field(name="⏰ Tempo de Jogo", value=self.tempo_jogando.value, inline=True)
                embed.add_field(name="❓ Por que quer entrar", value=self.porque_entrar.value, inline=False)
                embed.add_field(name="⚔️ Habilidades", value=self.habilidades.value, inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text=f"ID: {interaction.user.id}")
                
                await channel.send(embed=embed, view=RecrutamentoDecisaoView(interaction.user.id))
                break
        
        await interaction.response.send_message(
            "✅ Seu formulário foi enviado! Aguarde a análise da staff.",
            ephemeral=True
        )

class RecrutamentoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📝 Preencher Formulário", style=discord.ButtonStyle.success, custom_id="fill_form")
    async def fill_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RecrutamentoModal())

class RecrutamentoDecisaoView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success, custom_id="approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        member = interaction.guild.get_member(self.user_id)
        if member:
            # Dar cargo de membro
            for role in interaction.guild.roles:
                if "Membro" in role.name and "VIP" not in role.name:
                    await member.add_roles(role)
                    break
            
            # Remover cargo de novato
            for role in member.roles:
                if "Novato" in role.name:
                    await member.remove_roles(role)
            
            # Anunciar aprovação
            for channel in interaction.guild.text_channels:
                if "aprovados" in channel.name:
                    embed = discord.Embed(
                        title="🎉 Novo Membro Aprovado!",
                        description=f"Bem-vindo ao Clan 147, {member.mention}!",
                        color=CORES['sucesso']
                    )
                    await channel.send(embed=embed)
                    break
            
            try:
                await member.send(f"🎉 Parabéns! Você foi **APROVADO** no Clan 147!")
            except:
                pass
        
        await interaction.response.send_message("✅ Membro aprovado!", ephemeral=True)
        
        # Desabilitar botões
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
            return
        
        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("😔 Infelizmente sua solicitação para o Clan 147 foi recusada. Você pode tentar novamente no futuro!")
            except:
                pass
        
        await interaction.response.send_message("❌ Membro recusado!", ephemeral=True)
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

@bot.tree.command(name="recrutamento", description="📝 Envia painel de recrutamento")
@app_commands.checks.has_permissions(administrator=True)
async def recrutamento_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎯 Recrutamento - Clan 147",
        description="""
        **Quer fazer parte do melhor clan?**
        
        📋 **Requisitos:**
        • Ter no mínimo 14 anos
        • Ser ativo no servidor
        • Ter experiência em Minecraft
        • Respeitar todos os membros
        • Participar de eventos
        
        ⚔️ **O que oferecemos:**
        • Comunidade ativa e unida
        • Eventos semanais
        • Ajuda com builds e farms
        • Proteção de territórios
        • Muita diversão!
        
        **Clique no botão abaixo para se candidatar!**
        """,
        color=CORES['principal']
    )
    embed.set_footer(text="Boa sorte! 🍀")
    
    await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=RecrutamentoView())

# ============================================
# 👋 SISTEMA DE BOAS-VINDAS
# ============================================

@bot.event
async def on_member_join(member):
    # Dar cargo de novato
    for role in member.guild.roles:
        if "Novato" in role.name:
            await member.add_roles(role)
            break
    
    # ENVIAR PARA O SITE - Registrar novo membro
    await registrar_membro(
        discord_id=member.id,
        username=str(member),
        avatar_url=str(member.display_avatar.url),
        cargo="🆕 Novato"
    )
    
    # Registrar entrada no histórico
    await registrar_historico(
        discord_id=member.id,
        tipo="entrada",
        descricao=f"Entrou no servidor do Clan 147"
    )
    
    # Enviar mensagem de boas-vindas
    for channel in member.guild.text_channels:
        if "bem-vindo" in channel.name:
            embed = discord.Embed(
                title="⛏️ Novo Guerreiro Chegou!",
                description=f"""
                **Bem-vindo ao Clan 147, {member.mention}!**
                
                🛏️ Somos o melhor clan de **Bedwars** do servidor!
                
                ⚔️ **Comece sua jornada:**
                • 📜 Leia as regras em #📜┃regras
                • 📝 Candidate-se em #📝┃como-entrar
                • 💬 Converse em #💬┃bate-papo
                • 🎮 Entre nos canais de voz para jogar!
                
                **🏆 Prepare-se para dominar o Bedwars!**
                """,
                color=CORES['esmeralda']
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_image(url="https://i.imgur.com/8QGK3Pj.png")
            embed.set_footer(text=f"⛏️ Membro #{member.guild.member_count} | Clan 147")
            await channel.send(embed=embed)
            break

@bot.event
async def on_member_remove(member):
    # ENVIAR PARA O SITE - Registrar saída
    await registrar_historico(
        discord_id=member.id,
        tipo="saida",
        descricao=f"Saiu do servidor do Clan 147"
    )
    
    for channel in member.guild.text_channels:
        if "logs" in channel.name:
            embed = discord.Embed(
                title="👋 Membro Saiu",
                description=f"**{member}** saiu do servidor.",
                color=CORES['aviso'],
                timestamp=datetime.utcnow()
            )
            await channel.send(embed=embed)
            break

# ============================================
# 🔨 COMANDOS DE MODERAÇÃO
# ============================================

@bot.tree.command(name="kick", description="🔨 Expulsa um membro")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Você não pode expulsar este membro!", ephemeral=True)
        return
    
    await membro.kick(reason=motivo)
    
    embed = discord.Embed(
        title="🔨 Membro Expulso",
        color=CORES['erro']
    )
    embed.add_field(name="Usuário", value=f"{membro} ({membro.id})")
    embed.add_field(name="Moderador", value=interaction.user.mention)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="🔨 Bane um membro")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não especificado"):
    if membro.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Você não pode banir este membro!", ephemeral=True)
        return
    
    await membro.ban(reason=motivo)
    
    embed = discord.Embed(
        title="🔨 Membro Banido",
        color=CORES['erro']
    )
    embed.add_field(name="Usuário", value=f"{membro} ({membro.id})")
    embed.add_field(name="Moderador", value=interaction.user.mention)
    embed.add_field(name="Motivo", value=motivo, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="mute", description="🔇 Muta um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, membro: discord.Member, minutos: int = 10, motivo: str = "Não especificado"):
    from datetime import timedelta
    
    await membro.timeout(timedelta(minutes=minutos), reason=motivo)
    
    embed = discord.Embed(
        title="🔇 Membro Mutado",
        color=CORES['aviso']
    )
    embed.add_field(name="Usuário", value=membro.mention)
    embed.add_field(name="Duração", value=f"{minutos} minutos")
    embed.add_field(name="Motivo", value=motivo, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unmute", description="🔊 Desmuta um membro")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, membro: discord.Member):
    await membro.timeout(None)
    await interaction.response.send_message(f"✅ {membro.mention} foi desmutado!")

@bot.tree.command(name="limpar", description="🧹 Limpa mensagens do canal")
@app_commands.checks.has_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int = 10):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"✅ {len(deleted)} mensagens deletadas!", ephemeral=True)

# ============================================
# 📊 COMANDOS INFORMATIVOS
# ============================================

@bot.tree.command(name="serverinfo", description="📊 Informações do servidor")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=CORES['info']
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="👑 Dono", value=guild.owner.mention)
    embed.add_field(name="👥 Membros", value=guild.member_count)
    embed.add_field(name="💬 Canais", value=len(guild.channels))
    embed.add_field(name="🎭 Cargos", value=len(guild.roles))
    embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="🆔 ID", value=guild.id)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="👤 Informações de um usuário")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    
    embed = discord.Embed(
        title=f"👤 {membro.name}",
        color=membro.top_role.color
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="📛 Nome", value=membro)
    embed.add_field(name="🆔 ID", value=membro.id)
    embed.add_field(name="📅 Entrou", value=membro.joined_at.strftime("%d/%m/%Y"))
    embed.add_field(name="📅 Conta criada", value=membro.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="🎭 Cargo mais alto", value=membro.top_role.mention)
    embed.add_field(name="🎭 Cargos", value=len(membro.roles) - 1)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="🖼️ Mostra o avatar de um usuário")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    
    embed = discord.Embed(
        title=f"🖼️ Avatar de {membro.name}",
        color=CORES['info']
    )
    embed.set_image(url=membro.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

# ============================================
# 🎮 COMANDOS DIVERTIDOS
# ============================================

@bot.tree.command(name="say", description="💬 Faz o bot falar")
@app_commands.checks.has_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, mensagem: str):
    await interaction.response.send_message("✅ Mensagem enviada!", ephemeral=True)
    await interaction.channel.send(mensagem)

@bot.tree.command(name="embed", description="📝 Cria um embed personalizado")
@app_commands.checks.has_permissions(manage_messages=True)
async def embed_cmd(interaction: discord.Interaction, titulo: str, descricao: str, cor: str = "roxo"):
    cores_map = {
        "roxo": CORES['principal'],
        "verde": CORES['sucesso'],
        "vermelho": CORES['erro'],
        "azul": CORES['info'],
        "amarelo": CORES['aviso']
    }
    
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=cores_map.get(cor.lower(), CORES['principal'])
    )
    
    await interaction.response.send_message("✅ Embed enviado!", ephemeral=True)
    await interaction.channel.send(embed=embed)

# ============================================
# 🔄 REGISTRAR VIEWS PERSISTENTES
# ============================================

@bot.event
async def setup_hook():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(RecrutamentoView())

# ============================================
# 🚀 INICIAR BOT
# ============================================

# Coloque seu token aqui
TOKEN = "MTQ0Mjk4NjY4ODg2NjY4MDk3Mg.G1eC-4.aZgAhtxCsNlbXmZppMe02eY1IcVxo2yCRengQs"

if __name__ == "__main__":
    bot.run(TOKEN)
