import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes

# Configurar logger específico para erros
error_logger = logging.getLogger('error_handler')

class ErrorHandler:
    """
    Sistema centralizado de tratamento de erros
    Captura e registra todas as exceções não tratadas
    """
    
    def __init__(self, admin_ids):
        self.admin_ids = admin_ids
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler global de erros - captura todas as exceções não tratadas
        """
        # Log do erro completo
        error_logger.error(f"Exception while handling an update: {context.error}")
        
        # Traceback detalhado para debugging
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)
        
        error_logger.error(f"Traceback: {tb_string}")
        
        # Notificar administradores sobre erros críticos
        await self.notify_admins(context, tb_string)
        
        # Responder ao usuário com mensagem amigável
        if update and update.effective_message:
            user_friendly_message = """
❌ Ops! Ocorreu um erro inesperado.

Nossa equipe já foi notificada e está trabalhando na solução.

Enquanto isso, você pode:
• Tentar novamente em alguns instantes
• Usar outro comando disponível
• Contatar suporte se o problema persistir

Pedimos desculpas pelo inconveniente.
            """
            await update.effective_message.reply_text(user_friendly_message)
    
    async def notify_admins(self, context: ContextTypes.DEFAULT_TYPE, traceback_text: str):
        """
        Notifica administradores sobre erros críticos
        """
        error_message = f"""
🚨 *ERRO NO SISTEMA JURÍDICO*

💥 *Exceção:* {type(context.error).__name__}
📝 *Mensagem:* {str(context.error)}

🕒 *Hora:* {context.error.__traceback__.tb_frame.f_code.co_filename if context.error.__traceback__ else 'N/A'}

🔧 *Ação necessária:* Verificar logs para detalhes completos
        """
        
        # Enviar para todos os administradores
        for admin_id in self.admin_ids:
            try:
                # Enviar mensagem resumida pelo Telegram
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=error_message,
                    parse_mode='Markdown'
                )
                
                # Log completo no console/log file
                error_logger.error(f"Error details sent to admin {admin_id}")
                
            except Exception as e:
                error_logger.error(f"Failed to notify admin {admin_id}: {e}")
