from pymongo import MongoClient
from datetime import datetime, timedelta
import os

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.juridical_bot
    
    # Coleções
    @property
    def users(self):
        return self.db.users
    
    @property
    def subscriptions(self):
        return self.db.subscriptions
    
    @property
    def legal_documents(self):
        return self.db.legal_documents
    
    @property
    def user_usage(self):
        return self.db.user_usage
    
    def init_user(self, user_id, username, first_name):
        """Inicializa usuário no sistema"""
        user_data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'subscription_plan': 'free',
            'joined_date': datetime.utcnow(),
            'monthly_usage': 0
        }
        self.users.update_one(
            {'user_id': user_id},
            {'$setOnInsert': user_data},
            upsert=True
        )
    
    def check_user_subscription(self, user_id):
        """Verifica assinatura do usuário"""
        user = self.users.find_one({'user_id': user_id})
        if not user:
            return False
        
        if user['subscription_plan'] == 'free':
            return self.check_free_usage(user_id)
        
        return user['subscription_plan'] in ['premium', 'enterprise']
    
    def check_free_usage(self, user_id):
        """Verifica se usuário free não excedeu limite"""
        usage = self.user_usage.find_one({
            'user_id': user_id,
            'month': datetime.utcnow().month,
            'year': datetime.utcnow().year
        })
        
        free_limit = 10  # 10 consultas gratuitas por mês
        current_usage = usage['count'] if usage else 0
        
        return current_usage < free_limit
    
    def increment_usage(self, user_id):
        """Incrementa contador de uso"""
        self.user_usage.update_one(
            {
                'user_id': user_id,
                'month': datetime.utcnow().month,
                'year': datetime.utcnow().year
            },
            {'$inc': {'count': 1}},
            upsert=True
        )
