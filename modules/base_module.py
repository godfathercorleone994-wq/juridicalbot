from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database.operations import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class BaseModule:
    def __init__(self, app):
        self.app = app
        self.db = DatabaseManager()
        self.handlers = []
    
    def register_module(self, application):
        """Registra todos os handlers no aplicativo"""
        for handler in self.handlers:
            application.add_handler(handler)
    
    def add_handler(self, handler):
        """Adiciona handler à lista"""
        self.handlers.append(handler)
    
    def check_subscription(self, user_id):
        """Verifica se usuário tem assinatura ativa"""
        return self.db.check_user_subscription(user_id)
    
    def get_user_usage(self, user_id):
        """Obtém uso mensal do usuário"""
        return self.db.get_user_usage(user_id) 
