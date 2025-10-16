import os
import logging
from pymongo import MongoClient
from database.operations import DatabaseManager
import google.generativeai as genai

logger = logging.getLogger(__name__)

class LegalAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')

    def search_legal_references(self, query: str, max_results: int = 5):
        """Busca referências legais na base de dados"""
        # Busca textual simples (em produção, usar índice de texto completo)
        results = self.db.legal_documents.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(max_results)

        return list(results)

    async def analyze_with_legal_context(self, question: str, user_id: int) -> str:
        """Analisa questão jurídica com contexto da base legal"""
        # Verificar assinatura para acesso à base legal completa
        user_plan = self.db.get_user_plan(user_id)
        
        # Buscar referências relevantes
        legal_refs = self.search_legal_references(question)
        
        # Construir contexto legal
        legal_context = ""
        if legal_refs:
            legal_context = "Referências Legais Encontradas:\n"
            for ref in legal_refs:
                legal_context += f"- {ref['title']}: {ref['content'][:200]}...\n\n"

        # Se usuário free, limitar contexto
        if user_plan == 'free' and len(legal_refs) > 2:
            legal_context = "Referências Legais (limitadas no plano Free):\n"
            for ref in legal_refs[:2]:
                legal_context += f"- {ref['title']}\n"
            legal_context += "\n*Assine o Premium para acesso completo à base legal.*\n\n"

        prompt = f"""
        Você é um assistente jurídico especializado em direito brasileiro.
        Use o contexto legal abaixo para responder à questão do usuário.

        {legal_context}

        Questão: {question}

        Forneça uma resposta:
        1. **Resposta Direta**: Responda objetivamente.
        2. **Fundamentação**: Baseie-se na legislação e jurisprudência.
        3. **Próximos Passos**: Oriente sobre ações possíveis.

        Mantenha a resposta em português e estruturada.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Erro na análise legal: {e}")
            return "Erro na consulta à base legal. Tente novamente."

    def add_legal_document(self, title: str, content: str, doc_type: str, tags: list):
        """Adiciona documento à base legal"""
        self.db.legal_documents.insert_one({
            'title': title,
            'content': content,
            'type': doc_type,  # lei, jurisprudencia, doutrina, etc.
            'tags': tags,
            'added_date': datetime.utcnow()
        })

    def get_legal_document(self, doc_id: str):
        """Recupera documento legal por ID"""
        return self.db.legal_documents.find_one({'_id': doc_id})
