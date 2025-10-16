import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from modules.base_module import BaseModule

logger = logging.getLogger(__name__)

class UtilityCommands(BaseModule):
    def __init__(self):
        super().__init__()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.add_handler(CommandHandler("start", self.start))
        self.add_handler(CommandHandler("help", self.help))
        self.add_handler(CommandHandler("sobre", self.about))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🤖 Bot Jurídico Iniciado!")
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📚 Ajuda: Use /start para começar")
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⚖️ Bot Jurídico com IA")

def register_module(app):
    """Função de registro - interface padrão para todos os módulos"""
    UtilityCommands().register_module(app)
