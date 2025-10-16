import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes
from dotenv import load_dotenv
import importlib
import pkgutil

# Carregar variáveis de ambiente
load_dotenv()

# Configuração avançada de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Log no console
        logging.FileHandler('bot.log')  # Log em arquivo
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class JuridicalBot:
    """
    Classe principal do Bot Jurídico
    Gerencia inicialização, módulos e webhook
    """
    
    def __init__(self):
        """Inicializa o bot com configurações do ambiente"""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
        
        # Criar aplicação do Telegram
        self.application = Application.builder().token(self.token).build()
        self.modules = []
        
        # Configurar handler de erros global
        from utils.error_handler import ErrorHandler
        self.error_handler = ErrorHandler(self.admin_ids)
        self.application.add_error_handler(self.error_handler.error_handler)
        
        logger.info("Bot jurídico inicializado")
    
    def load_modules(self):
        """
        Carrega automaticamente todos os módulos da pasta 'modules'
        Sistema modular permite adicionar funcionalidades sem alterar código principal
        """
        package_path = 'modules'
        
        try:
            package = importlib.import_module(package_path)
            
            # Iterar por todos os módulos na pasta
            for _, name, ispkg in pkgutil.iter_modules(package.__path__):
                # Ignorar pacotes e o módulo base
                if not ispkg and name != 'base_module':
                    try:
                        # Importar módulo dinamicamente
                        module = importlib.import_module(f'{package_path}.{name}')
                        
                        # Verificar se módulo tem função de registro
                        if hasattr(module, 'register_module'):
                            module.register_module(self.application)
                            self.modules.append(name)
                            logger.info(f'✅ Módulo {name} carregado com sucesso')
                        else:
                            logger.warning(f'⚠️ Módulo {name} não tem função register_module')
                            
                    except Exception as e:
                        logger.error(f'❌ Erro ao carregar módulo {name}: {e}')
                        
            logger.info(f'Total de {len(self.modules)} módulos carregados: {", ".join(self.modules)}')
            
        except ImportError as e:
            logger.error(f'Erro ao importar pacote de módulos: {e}')
    
    def setup_webhook(self):
        """
        Configura webhook para deploy no Render
        O Render requer webhook em vez de polling
        """
        self.application.run_webhook(
            listen="0.0.0.0",  # Ouvir em todas as interfaces
            port=int(os.getenv('PORT', 5000)),  # Porta do Render
            url_path=self.token,  # URL path único para o bot
            webhook_url=f"{self.webhook_url}/{self.token}"  # URL completa do webhook
        )

# Instância global do bot - única para toda aplicação
bot = JuridicalBot()

@app.route('/')
def index():
    """Rota raiz - saúde da aplicação"""
    return '🤖 Bot Jurídico Online - Sistema Operacional'

@app.route('/health')
def health_check():
    """Rota de health check para monitoramento"""
    return {
        'status': 'online',
        'modules_loaded': len(bot.modules),
        'modules': bot.modules
    }

@app.route(f'/{bot.token}', methods=['POST'])
def webhook():
    """
    Endpoint principal do webhook do Telegram
    Todas as mensagens do Telegram chegam aqui
    """
    try:
        # Processar update recebido do Telegram
        update = Update.de_json(request.get_json(), bot.application.bot)
        bot.application.process_update(update)
        return 'ok'
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """
    Rota para configurar webhook manualmente
    Útil para debugging e setup inicial
    """
    webhook_url = f"{bot.webhook_url}/{bot.token}"
    success = bot.application.bot.set_webhook(webhook_url)
    
    logger.info(f"Webhook configurado: {success} - URL: {webhook_url}")
    return f'Webhook configurado: {success} - URL: {webhook_url}'

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    """Remove webhook (útil para desenvolvimento local)"""
    success = bot.application.bot.delete_webhook()
    logger.info(f"Webhook removido: {success}")
    return f'Webhook removido: {success}'

if __name__ == '__main__':
    """
    Ponto de entrada da aplicação
    Executado quando o script é iniciado diretamente
    """
    # Carregar todos os módulos automaticamente
    bot.load_modules()
    
    # Configurar webhook no startup
    webhook_url = f"{bot.webhook_url}/{bot.token}"
    bot.application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook configurado no startup: {webhook_url}")
    
    # Iniciar servidor Flask (para Render)
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    
    app.run(host='0.0.0.0', port=port)
