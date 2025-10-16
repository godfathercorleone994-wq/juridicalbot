import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from modules.base_module import BaseModule
from legal_database.legal_analyzer import LegalAnalyzer

logger = logging.getLogger(__name__)

class LegalConsult(BaseModule):
    def __init__(self, app):
        super().__init__(app)
        self.legal_analyzer = LegalAnalyzer()
        self.setup_handlers()

    def setup_handlers(self):
        """Configura handlers para consulta legal"""
        self.add_handler(CommandHandler("consultar", self.legal_query))
        self.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_query))

    async def legal_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia consulta à base legal"""
        user_id = update.effective_user.id
        
        # Verificar assinatura
        if not self.check_subscription(user_id):
            await update.message.reply_text(
                "❌ Você excedeu seu limite de consultas gratuitas deste mês. "
                "Assine o plano Premium para consultas ilimitadas.\n\n"
                "Use /planos para ver os planos disponíveis."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "💬 Digite sua consulta jurídica após o comando:\n"
                "Ex: /consultar Qual o prazo para entrada de recurso em ação trabalhista?"
            )
            return

        query = ' '.join(context.args)
        await self.process_legal_query(update, query, user_id)

    async def handle_text_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa consultas em texto livre (se começar com palavra-chave)"""
        user_id = update.effective_user.id
        text = update.message.text

        # Verificar se é uma consulta jurídica (palavras-chave)
        legal_keywords = ['lei ', 'direito ', 'jurídico', 'processo', 'recurso', 'contrato', 'penal', 'trabalhista']
        
        if any(keyword in text.lower() for keyword in legal_keywords):
            if not self.check_subscription(user_id):
                await update.message.reply_text(
                    "❌ Você excedeu seu limite de consultas gratuitas. Use /planos para upgrade."
                )
                return

            await self.process_legal_query(update, text, user_id)

    async def process_legal_query(self, update: Update, query: str, user_id: int):
        """Processa a consulta jurídica"""
        # Indicar que está processando
        processing_msg = await update.message.reply_text("🔍 Consultando base legal...")

        try:
            # Analisar com contexto legal
            response = await self.legal_analyzer.analyze_with_legal_context(query, user_id)

            # Incrementar uso
            self.db.increment_usage(user_id)

            # Enviar resposta
            await processing_msg.edit_text(
                f"⚖️ **Consulta Jurídica**\n\n"
                f"**Pergunta:** {query}\n\n"
                f"**Resposta:**\n{response}",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro na consulta legal: {e}")
            await processing_msg.edit_text(
                "❌ Ocorreu um erro na consulta. Tente novamente mais tarde."
            )

def register_module(app):
    """Função de registro do módulo"""
    LegalConsult(app)
