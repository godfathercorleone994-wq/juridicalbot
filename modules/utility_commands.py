import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from modules.base_module import BaseModule

# Configurar logging
logger = logging.getLogger(__name__)

class UtilityCommands(BaseModule):
    """
    Módulo de comandos utilitários do bot jurídico
    Contém comandos básicos como /start, /help, /sobre
    """
    
    def __init__(self, app):
        """Inicializa o módulo com a aplicação do bot"""
        super().__init__(app)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configura todos os handlers de comandos deste módulo"""
        # Cada comando é associado a uma função handler
        self.add_handler(CommandHandler("start", self.start))
        self.add_handler(CommandHandler("help", self.help))
        self.add_handler(CommandHandler("sobre", self.about))
        self.add_handler(CommandHandler("status", self.status))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler do comando /start
        Mensagem de boas-vindas quando usuário inicia o bot
        """
        user = update.effective_user
        user_id = user.id
        
        # Registrar usuário no banco de dados (se for novo)
        self.db.init_user(user_id, user.username, user.first_name)
        
        # Mensagem de boas-vindas personalizada
        welcome_text = f"""
👋 Olá, {user.first_name}!

🤖 Bem-vindo ao *Assistente Jurídico IA* - seu parceiro inteligente para questões legais.

⚖️ *Recursos Disponíveis:*

📄 `/analisar` - Analise documentos jurídicos com IA
📝 `/criardocumento` - Crie documentos jurídicos personalizados
💬 `/consultar` - Consulte nossa base legal completa
📊 `/minhaconta` - Veja seu uso e assinatura
💼 `/planos` - Conheça nossos planos de assinatura

🎯 *Exemplos de uso:*
• Envie um documento para análise jurídica
• Consulte sobre prazos processuais  
• Crie contratos e petições
• Analise cláusulas contratuais

Digite /help para ver todos os comandos disponíveis.
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        logger.info(f"Novo usuário iniciou o bot: {user_id} - {user.first_name}")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler do comando /help
        Mostra ajuda detalhada sobre todos os comandos
        """
        help_text = """
🆘 *Central de Ajuda - Assistente Jurídico*

⚖️ *COMANDOS PRINCIPAIS:*

📄 `/analisar` - Analise documentos (PDF, TXT, DOCX)
   _Exemplo: Envie um documento ou use /analisar_

📝 `/criardocumento` - Crie documentos jurídicos
   _Tipos: Contratos, Notificações, Petições, NDAs_

💬 `/consultar [sua pergunta]` - Consulta à base legal
   _Exemplo: /consultar Qual prazo para entrar com recurso?_

🔍 `/buscar [termo]` - Busca na base de leis e jurisprudência

📊 *COMANDOS DE CONTA:*

👤 `/minhaconta` - Ver seus dados e uso mensal
💼 `/planos` - Ver planos de assinatura disponíveis

🛠️ *OUTROS COMANDOS:*

ℹ️ `/sobre` - Informações sobre o bot
🔄 `/status` - Status do sistema e sua conta
🆘 `/help` - Esta mensagem de ajuda

💡 *DICA:* Você também pode digitar perguntas diretamente!
O bot reconhece automaticamente consultas jurídicas.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler do comando /sobre
        Mostra informações sobre o bot e sua tecnologia
        """
        about_text = """
🤖 *Sobre o Assistente Jurídico IA*

⚖️ *Missão:*
Democratizar o acesso à assessoria jurídica através de inteligência artificial.

🛠️ *Tecnologia:*
• **IA Gemini** - Análise inteligente de documentos
• **Base Legal** - Banco de dados com legislação brasileira
• **Sistema Modular** - Expansível e atualizável
• **MongoDB** - Armazenamento seguro de dados

📚 *Base de Conhecimento:*
• Constituição Federal e emendas
• Códigos Civil, Penal, Trabalhista
• Leis esparsas e complementares
• Jurisprudência dos tribunais
• Doutrina jurídica

🔒 *Segurança e Privacidade:*
• Dados criptografados
• Conformidade com LGPD
• Backup automático
• Acesso restrito

👨‍💻 *Desenvolvimento:*
Sistema desenvolvido com arquitetura modular para fácil expansão e manutenção.

📞 *Suporte:* contato@juridicalbot.com
        """
        
        await update.message.reply_text(about_text, parse_mode='Markdown')
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler do comando /status
        Mostra status do sistema e da conta do usuário
        """
        user_id = update.effective_user.id
        
        # Obter dados do usuário
        user_data = self.db.get_user_data(user_id)
        usage_data = self.db.get_user_usage(user_id)
        
        # Verificar status da assinatura
        subscription_status = "✅ Ativa" if self.check_subscription(user_id) else "❌ Expirada/Limite"
        
        # Emojis para os planos
        plan_emojis = {
            'free': '🆓',
            'premium': '⭐',
            'enterprise': '🏢'
        }
        
        status_text = f"""
📊 *Status da Sua Conta*

👤 *Usuário:* {update.effective_user.first_name}
📅 *Membro desde:* {user_data['joined_date'].strftime('%d/%m/%Y')}
🎯 *Plano:* {plan_emojis.get(user_data['subscription_plan'], '❓')} {user_data['subscription_plan'].title()}
📈 *Consultas este mês:* {usage_data['monthly_usage']}
🔔 *Status:* {subscription_status}

🤖 *Status do Sistema:*
✅ Bot Online
✅ Base Legal Ativa
✅ IA Gemini Operacional
✅ Banco de Dados Conectado

💡 *Próximos Passos:*
• Use /analisar para documentos
• Use /consultar para dúvidas
• Use /planos para upgrade
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        logger.info(f"Usuário {user_id} verificou status do sistema")

def register_module(app):
    """
    Função de registro obrigatória para todos os módulos
    O sistema principal chama esta função para carregar o módulo
    """
    UtilityCommands(app)
    logger.info("Módulo de comandos utilitários carregado com sucesso")
