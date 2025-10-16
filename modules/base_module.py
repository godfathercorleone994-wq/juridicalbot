from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
import logging

logger = logging.getLogger(__name__)

class BaseModule:
    def __init__(self):
        self.handlers = []
    
    def register_module(self, application):
        """Registra todos os handlers no aplicativo"""
        for handler in self.handlers:
            application.add_handler(handler)
        logger.info(f"✅ Módulo {self.__class__.__name__} registrado")
    
    def add_handler(self, handler):
        """Adiciona handler à lista"""
        self.handlers.append(handler)
