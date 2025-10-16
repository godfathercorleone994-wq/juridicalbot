from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from modules.base_module import BaseModule
from database.operations import DatabaseManager

class SubscriptionManager(BaseModule):
    def __init__(self, app):
        super().__init__(app)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configura handlers de assinatura"""
        self.add_handler(CommandHandler('planos', self.show_plans))
        self.add_handler(CommandHandler('minhaconta', self.my_account))
        self.add_handler(CallbackQueryHandler(self.handle_subscription, pattern='^subscription_'))
    
    async def show_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra planos de assinatura"""
        keyboard = [
            [InlineKeyboardButton("🆓 Plano Free (10 consultas/mês)", callback_data='subscription_free')],
            [InlineKeyboardButton("⭐ Premium (R$ 29,90/mês)", callback_data='subscription_premium')],
            [InlineKeyboardButton("🏢 Enterprise (R$ 99,90/mês)", callback_data='subscription_enterprise')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
📋 **Planos de Assinatura**

🆓 **Free**
• 10 consultas por mês
• Análise básica de documentos
• Acesso limitado à base legal

⭐ **Premium** - R$ 29,90/mês
• Consultas ilimitadas
• Análise avançada com IA
• Acesso completo à base legal
• Criação de documentos

🏢 **Enterprise** - R$ 99,90/mês
• Todos os benefícios Premium
• Suporte prioritário
• Integração personalizada
        """
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def my_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra informações da conta do usuário"""
        user_id = update.effective_user.id
        user_data = self.db.get_user_data(user_id)
        usage_data = self.db.get_user_usage(user_id)
        
        plan_emoji = {
            'free': '🆓',
            'premium': '⭐', 
            'enterprise': '🏢'
        }
        
        text = f"""
👤 **Minha Conta**

📊 **Plano Atual:** {plan_emoji.get(user_data['subscription_plan'], '❓')} {user_data['subscription_plan'].title()}
📈 **Consultas este mês:** {usage_data['monthly_usage']}
📅 **Membro desde:** {user_data['joined_date'].strftime('%d/%m/%Y')}
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa seleção de plano"""
        query = update.callback_query
        await query.answer()
        
        plan = query.data.split('_')[1]
        
        if plan == 'free':
            await query.edit_message_text(
                "✅ Você já está no plano Free! Use /minhaconta para ver seu uso."
            )
        else:
            # Em produção, integrar com gateway de pagamento
            await query.edit_message_text(
                f"💳 *Plano {plan.title()}*\n\n"
                f"Para assinar o plano {plan}, entre em contato conosco para "
                f"finalizar o pagamento e ativação.\n\n"
                "📧 contato@juridicalbot.com",
                parse_mode='Markdown'
            )

def register_module(app):
    """Função de registro do módulo"""
    SubscriptionManager(app)
