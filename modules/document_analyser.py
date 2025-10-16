import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from modules.base_module import BaseModule
import google.generativeai as genai

logger = logging.getLogger(__name__)

class DocumentAnalyzer(BaseModule):
    def __init__(self, app):
        super().__init__(app)
        # Configurar a API do Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        self.setup_handlers()

    def setup_handlers(self):
        """Configura handlers para análise de documentos"""
        self.add_handler(CommandHandler("analisar", self.analyze_document))
        self.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))

    async def analyze_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia o processo de análise de documento"""
        user_id = update.effective_user.id
        
        # Verificar assinatura
        if not self.check_subscription(user_id):
            await update.message.reply_text(
                "❌ Você excedeu seu limite de consultas gratuitas deste mês. "
                "Assine o plano Premium para consultas ilimitadas.\n\n"
                "Use /planos para ver os planos disponíveis."
            )
            return

        # Verificar se há documento para analisar
        if not update.message.document:
            await update.message.reply_text(
                "📄 Por favor, envie o documento que deseja analisar. "
                "Formatos suportados: PDF, TXT, DOCX."
            )
            return

        # Processar o documento
        await self.handle_document(update, context)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa o documento enviado"""
        user_id = update.effective_user.id
        
        # Verificar assinatura
        if not self.check_subscription(user_id):
            await update.message.reply_text(
                "❌ Você excedeu seu limite de consultas gratuitas deste mês. "
                "Assine o plano Premium para consultas ilimitadas.\n\n"
                "Use /planos para ver os planos disponíveis."
            )
            return

        # Verificar se é um documento
        if not update.message.document:
            return

        document = update.message.document
        file_extension = document.file_name.split('.')[-1].lower() if document.file_name else ''

        # Verificar formato
        if file_extension not in ['pdf', 'txt', 'docx']:
            await update.message.reply_text(
                "❌ Formato não suportado. Envie um arquivo PDF, TXT ou DOCX."
            )
            return

        # Baixar o arquivo
        file = await document.get_file()
        file_path = f"temp_{user_id}_{document.file_name}"
        await file.download_to_drive(file_path)

        # Processar o arquivo
        try:
            # Ler o conteúdo do arquivo (simplificado para txt, para outros formatos precisaria de bibliotecas extras)
            if file_extension == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # Para PDF e DOCX, vamos usar uma abordagem simplificada (em produção, use bibliotecas como PyPDF2, python-docx)
                content = f"Conteúdo do arquivo {document.file_name} (formato {file_extension}) não pode ser lido nesta versão. Em breve, suporte completo."

            # Se o conteúdo for muito longo, truncar (limite do Gemini)
            if len(content) > 10000:
                content = content[:10000] + "... [conteúdo truncado]"

            # Analisar com Gemini
            analysis = await self.analyze_with_gemini(content)

            # Incrementar uso
            self.db.increment_usage(user_id)

            # Enviar resposta
            await update.message.reply_text(
                f"📊 **Análise do Documento**\n\n{analysis}",
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Erro ao analisar documento: {e}")
            await update.message.reply_text(
                "❌ Ocorreu um erro ao analisar o documento. Tente novamente."
            )
        finally:
            # Limpar arquivo temporário
            if os.path.exists(file_path):
                os.remove(file_path)

    async def analyze_with_gemini(self, text: str) -> str:
        """Analisa o texto com a API do Gemini"""
        prompt = """
        Você é um assistente jurídico especializado em direito brasileiro. 
        Analise o documento fornecido e forneça:

        1. **Resumo Executivo**: Um breve resumo do documento.
        2. **Pontos Críticos**: Identifique pontos que necessitam de atenção jurídica.
        3. **Recomendações**: Sugestões de melhorias ou ajustes.
        4. **Referências Legais**: Indique leis ou jurisprudências aplicáveis.

        Mantenha a resposta em português e estruturada de forma clara.
        """

        try:
            response = self.model.generate_content(prompt + text)
            return response.text
        except Exception as e:
            logger.error(f"Erro na API do Gemini: {e}")
            return "Erro na análise com IA. Tente novamente mais tarde."

def register_module(app):
    """Função de registro do módulo"""
    DocumentAnalyzer(app)
