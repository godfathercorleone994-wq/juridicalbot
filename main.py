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

# Configuração de logging para Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()  # Render captura logs do stdout
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class JuridicalBot:
    """
    Classe principal do Bot Jurídico
    """
    
    def __init__(self):
        """Inicializa o bot com configurações do ambiente"""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.port = int(os.getenv('PORT', 10000))
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado")
        
        # Criar aplicação do Telegram
        self.application = Application.builder().token(self.token).build()
        self.modules = []
        
        logger.info("Bot jurídico inicializado - Modo Render")
    
    def load_modules(self):
        """
        Carrega automaticamente todos os módulos da pasta 'modules'
        """
        try:
            package_path = 'modules'
            package = importlib.import_module(package_path)
            
            for _, name, ispkg in pkgutil.iter_modules(package.__path__):
                if not ispkg and name != 'base_module':
                    try:
                        module = importlib.import_module(f'{package_path}.{name}')
                        if hasattr(module, 'register_module'):
                            module.register_module(self.application)
                            self.modules.append(name)
                            logger.info(f'✅ Módulo {name} carregado')
                    except Exception as e:
                        logger.error(f'❌ Erro no módulo {name}: {e}')
                        
            logger.info(f'Total de {len(self.modules)} módulos carregados')
            
        except Exception as e:
            logger.error(f'Erro crítico ao carregar módulos: {e}')
            raise
    
    def setup_webhook(self):
        """
        Configura webhook para o Render
        """
        webhook_url = f"{self.webhook_url}/{self.token}"
        
        # Configurar webhook no Telegram
        success = self.application.bot.set_webhook(webhook_url)
        if success:
            logger.info(f'✅ Webhook configurado: {webhook_url}')
        else:
            logger.error(f'❌ Falha ao configurar webhook: {webhook_url}')
        
        return success

# Instância global do bot
try:
    bot = JuridicalBot()
    bot.load_modules()
except Exception as e:
    logger.error(f"Falha na inicialização do bot: {e}")
    bot = None

@app.route('/')
def index():
    """Rota raiz para health check"""
    if bot:
        return {
            'status': 'online',
            'service': 'Juridical Bot',
            'modules': len(bot.modules),
            'webhook': 'active' if bot.webhook_url else 'inactive'
        }
    return {'status': 'error', 'message': 'Bot não inicializado'}

@app.route('/health')
def health_check():
    """Rota de health check para monitoramento"""
    if not bot:
        return {'status': 'error'}, 500
    
    return {
        'status': 'healthy',
        'modules_loaded': bot.modules,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }

@app.route(f'/webhook', methods=['POST'])
def webhook():
    """
    Endpoint do webhook - Render não permite URLs dinâmicas no path principal
    """
    if not bot:
        return 'Bot não inicializado', 500
    
    try:
        # Verificar se é um update do Telegram
        if request.is_json:
            update = Update.de_json(request.get_json(), bot.application.bot)
            bot.application.process_update(update)
            return 'ok'
        else:
            return 'Invalid content type', 400
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configurar webhook manualmente"""
    if not bot:
        return 'Bot não inicializado', 500
    
    success = bot.setup_webhook()
    return f'Webhook configurado: {success}'

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    """Remover webhook"""
    if not bot:
        return 'Bot não inicializado', 500
    
    success = bot.application.bot.delete_webhook()
    return f'Webhook removido: {success}'

def initialize_bot():
    """Função de inicialização para o Render"""
    global bot
    if bot and bot.webhook_url:
        bot.setup_webhook()

# Inicializar quando o módulo for carregado
initialize_bot()

if __name__ == '__main__':
    """
    Ponto de entrada para desenvolvimento local
    No Render, o Gunicorn usará o objeto `app` diretamente
    """
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port)
