import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from modules.base_module import BaseModule

logger = logging.getLogger(__name__)

# Estados da conversação
SELECT_DOC_TYPE, PROVIDE_DETAILS = range(2)

class DocumentCreator(BaseModule):
    def __init__(self, app):
        super().__init__(app)
        self.setup_handlers()

    def setup_handlers(self):
        """Configura handlers para criação de documentos"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('criardocumento', self.start_creation)],
            states={
                SELECT_DOC_TYPE: [
                    CallbackQueryHandler(self.select_doc_type, pattern='^doc_')
                ],
                PROVIDE_DETAILS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.provide_details)
                ],
            },
            fallbacks=[CommandHandler('cancelar', self.cancel_creation)]
        )
        self.add_handler(conv_handler)

    async def start_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia o processo de criação de documento"""
        user_id = update.effective_user.id

        # Verificar assinatura (apenas premium e enterprise podem criar documentos)
        if not self.check_subscription(user_id) or self.db.get_user_plan(user_id) == 'free':
            await update.message.reply_text(
                "❌ Criação de documentos é exclusiva para assinantes Premium e Enterprise.\n\n"
                "Use /planos para upgrade."
            )
            return ConversationHandler.END

        keyboard = [
            [InlineKeyboardButton("📄 Contrato de Prestação de Serviços", callback_data='doc_contrato_servicos')],
            [InlineKeyboardButton("📝 Notificação Extrajudicial", callback_data='doc_notificacao')],
            [InlineKeyboardButton("🏛️ Petição Inicial", callback_data='doc_peticao')],
            [InlineKeyboardButton("🔒 Termo de Confidencialidade", callback_data='doc_nda')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📋 Selecione o tipo de documento que deseja criar:",
            reply_markup=reply_markup
        )

        return SELECT_DOC_TYPE

    async def select_doc_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa a seleção do tipo de documento"""
        query = update.callback_query
        await query.answer()

        doc_type = query.data
        context.user_data['doc_type'] = doc_type

        # Mapear tipos para prompts
        prompts = {
            'doc_contrato_servicos': "Forneça os detalhes para o Contrato de Prestação de Serviços:\n\n- Nomes das partes\n- Objeto do contrato\n- Valor e forma de pagamento\n- Prazo de execução\n- Outras cláusulas importantes",
            'doc_notificacao': "Forneça os detalhes para a Notificação Extrajudicial:\n\n- Nome do destinatário\n- Endereço completo\n- Objeto da notificação\n- Prazo para cumprimento\n- Fundamentos legais",
            'doc_peticao': "Forneça os detalhes para a Petição Inicial:\n\n- Nome do autor e réu\n- Endereços completos\n- Descrição dos fatos\n- Pedidos\n- Fundamentos legais",
            'doc_nda': "Forneça os detalhes para o Termo de Confidencialidade:\n\n- Nomes das partes\n- Objeto da confidencialidade\n- Prazo de vigência\n- Exceções à confidencialidade"
        }

        await query.edit_message_text(
            f"📝 {prompts[doc_type]}\n\n"
            "Digite todas as informações solicitadas em uma única mensagem:"
        )

        return PROVIDE_DETAILS

    async def provide_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa os detalhes fornecidos e gera o documento"""
        user_id = update.effective_user.id
        details = update.message.text
        doc_type = context.user_data['doc_type']

        # Gerar documento (simulação - em produção, integrar com template engine e Gemini)
        document_content = await self.generate_document(doc_type, details)

        # Incrementar uso
        self.db.increment_usage(user_id)

        # Enviar documento
        await update.message.reply_text(
            f"✅ Documento gerado com sucesso!\n\n"
            f"📄 Conteúdo:\n\n{document_content}\n\n"
            f"*Nota: Este é um documento gerado automaticamente. "
            f"Recomendamos consultar um advogado para validação.*",
            parse_mode='Markdown'
        )

        return ConversationHandler.END

    async def generate_document(self, doc_type: str, details: str) -> str:
        """Gera o documento com base no tipo e detalhes"""
        # Em produção, usar templates e IA para refinar
        doc_templates = {
            'doc_contrato_servicos': f"CONTRATO DE PRESTAÇÃO DE SERVIÇOS\n\nBaseado nas informações: {details}",
            'doc_notificacao': f"NOTIFICAÇÃO EXTRAJUDICIAL\n\nBaseado nas informações: {details}",
            'doc_peticao': f"PEIÇÃO INICIAL\n\nBaseado nas informações: {details}",
            'doc_nda': f"TERMO DE CONFIDENCIALIDADE\n\nBaseado nas informações: {details}"
        }

        return doc_templates.get(doc_type, "Tipo de documento não reconhecido.")

    async def cancel_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela a criação do documento"""
        await update.message.reply_text(
            "❌ Criação de documento cancelada."
        )
        return ConversationHandler.END

def register_module(app):
    """Função de registro do módulo"""
    DocumentCreator(app)
