from datetime import datetime
from .models import DatabaseManager

class DatabaseManager(DatabaseManager):
    def get_user_plan(self, user_id: int) -> str:
        """Obtém o plano do usuário"""
        user = self.users.find_one({'user_id': user_id})
        return user.get('subscription_plan', 'free') if user else 'free'

    def get_user_data(self, user_id: int) -> dict:
        """Obtém todos os dados do usuário"""
        user = self.users.find_one({'user_id': user_id})
        if not user:
            return {
                'subscription_plan': 'free',
                'joined_date': datetime.utcnow(),
                'monthly_usage': 0
            }
        return user

    def update_user_plan(self, user_id: int, plan: str):
        """Atualiza plano do usuário"""
        self.users.update_one(
            {'user_id': user_id},
            {'$set': {'subscription_plan': plan}}
        )
