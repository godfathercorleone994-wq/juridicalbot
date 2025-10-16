import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from modules.base_module import BaseModule

logger = logging.getLogger(__name__)

class AdminTools(BaseModule):
    """
    Módulo de ferramentas administrativas
    Acesso restrito a administradores para gerenciar o sistema
    """
    
    def __init__(self, app):
        """Inicializa o módulo administrativo"""
        super().__init__(app)
        # Lista de IDs de administradores (definidos no .env)
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configura handlers para comandos administrativos"""
        # Comandos restritos a administradores
        self.add_handler(CommandHandler("admin", self.admin_panel))
        self.add_handler(CommandHandler("stats", self.system_stats))
        self.add_handler(CommandHandler("broadcast", self.broadcast_message))
        self.add_handler(CommandHandler("userinfo", self.user_info))
    
    def is_admin(self, user_id: int) -> bool:
        """Verifica se o usuário é administrador"""
        return user_id in self.admin_ids
    
    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Painel administrativo principal
        Mostra opções de administração disponíveis
        """
        user_id = update.effective_user.id
        
        # Verificar permissões de administrador
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Acesso restrito a administradores.")
            logger.warning(f"Tentativa de acesso não autorizado ao admin: {user_id}")
            return
        
        admin_text = """
🛠️ *Painel Administrativo*

📊 `/stats` - Estatísticas do sistema
📢 `/broadcast [mensagem]` - Enviar mensagem para todos os usuários
👤 `/userinfo [id]` - Informações detalhadas de usuário
📈 `/usage` - Relatório de uso do sistema

🔧 *Ferramentas da Base Legal:*
📚 `/addlaw [titulo] [conteudo]` - Adicionar lei à base
🔍 `/searchindex [termo]` - Buscar na base legal
📥 `/importlaws` - Importar leis em lote

💾 *Backup e Manutenção:*
🔄 `/backup` - Criar backup do banco
🧹 `/cleanup` - Limpar dados temporários
        """
        
        await update.message.reply_text(admin_text, parse_mode='Markdown')
        logger.info(f"Administrador {user_id} acessou o painel")
    
    async def system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Mostra estatísticas detalhadas do sistema
        Total de usuários, uso, planos, etc.
        """
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Acesso restrito a administradores.")
            return
        
        try:
            # Coletar estatísticas do banco de dados
            total_users = self.db.users.count_documents({})
            premium_users = self.db.users.count_documents({'subscription_plan': 'premium'})
            enterprise_users = self.db.users.count_documents({'subscription_plan': 'enterprise'})
            free_users = self.db.users.count_documents({'subscription_plan': 'free'})
            
            # Estatísticas de uso do mês atual
            from datetime import datetime
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            monthly_usage = self.db.user_usage.aggregate([
                {
                    '$match': {
                        'month': current_month,
                        'year': current_year
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_usage': {'$sum': '$count'}
                    }
                }
            ])
            
            total_monthly_usage = list(monthly_usage)
            usage_count = total_monthly_usage[0]['total_usage'] if total_monthly_usage else 0
            
            # Estatísticas da base legal
            legal_docs_count = self.db.legal_documents.count_documents({})
            
            stats_text = f"""
📊 *Estatísticas do Sistema - {datetime.utcnow().strftime("%d/%m/%Y")}*

👥 *Usuários:*
• **Total:** {total_users} usuários
• 🆓 **Free:** {free_users} ({free_users/total_users*100:.1f}%)
• ⭐ **Premium:** {premium_users} ({premium_users/total_users*100:.1f}%)
• 🏢 **Enterprise:** {enterprise_users} ({enterprise_users/total_users*100:.1f}%)

📈 *Uso Este Mês:*
• **Total de consultas:** {usage_count}
• **Média por usuário:** {usage_count/total_users:.1f}

📚 *Base Legal:*
• **Documentos armazenados:** {legal_docs_count}
• **Leis, jurisprudências e doutrinas**

🟢 *Status do Sistema:* Operacional
            """
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            logger.info(f"Administrador {user_id} verificou estatísticas do sistema")
            
        except Exception as e:
            error_msg = f"❌ Erro ao coletar estatísticas: {str(e)}"
            await update.message.reply_text(error_msg)
            logger.error(f"Erro em system_stats: {e}")
    
    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Envia mensagem para todos os usuários do sistema
        Útil para anuncios e atualizações
        """
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Acesso restrito a administradores.")
            return
        
        # Verificar se há mensagem para broadcast
        if not context.args:
            await update.message.reply_text(
                "📢 Uso: /broadcast [sua mensagem]\n\n"
                "Exemplo: /broadcast Nova atualização disponível!"
            )
            return
        
        broadcast_message = ' '.join(context.args)
        
        # Confirmar broadcast
        confirmation_text = f"""
📢 *CONFIRMAR BROADCAST*

💬 *Mensagem:*
{broadcast_message}

👥 *Destinatários:* Todos os usuários do sistema

⚠️ *Esta ação não pode ser desfeita.*

Digite CONFIRMAR para enviar ou CANCELAR para abortar.
        """
        
        await update.message.reply_text(confirmation_text, parse_mode='Markdown')
        
        # Armazenar mensagem temporariamente para confirmação
        context.user_data['pending_broadcast'] = broadcast_message
    
    async def user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Mostra informações detalhadas de um usuário específico
        """
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Acesso restrito a administradores.")
            return
        
        # Verificar se foi fornecido ID de usuário
        if not context.args:
            await update.message.reply_text("👤 Uso: /userinfo [id_do_usuario]")
            return
        
        try:
            target_user_id = int(context.args[0])
            user_data = self.db.get_user_data(target_user_id)
            
            if not user_data:
                await update.message.reply_text("❌ Usuário não encontrado.")
                return
            
            # Formatar informações do usuário
            user_info_text = f"""
👤 *Informações do Usuário*

🆔 *ID:* {target_user_id}
📛 *Nome:* {user_data.get('first_name', 'N/A')}
🔖 *Username:* @{user_data.get('username', 'N/A')}
🎯 *Plano:* {user_data.get('subscription_plan', 'free').title()}
📅 *Cadastro:* {user_data.get('joined_date', 'N/A').strftime('%d/%m/%Y')}
📊 *Uso Mensal:* {user_data.get('monthly_usage', 0)}

💾 *Atividade Recente:* Disponível no log do sistema
            """
            
            await update.message.reply_text(user_info_text, parse_mode='Markdown')
            logger.info(f"Administrador {user_id} consultou info do usuário {target_user_id}")
            
        except ValueError:
            await update.message.reply_text("❌ ID de usuário inválido. Deve ser numérico.")
        except Exception as e:
            error_msg = f"❌ Erro ao buscar informações: {str(e)}"
            await update.message.reply_text(error_msg)
            logger.error(f"Erro em user_info: {e}")

def register_module(app):
    """
    Função de registro do módulo administrativo
    """
    AdminTools(app)
    logger.info("Módulo de ferramentas administrativas carregado com sucesso")
