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

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class JuridicalBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        self.application = Application.builder().token(self.token).build()
        self.modules = []
        
    def load_modules(self):
        """Carrega todos os módulos automaticamente"""
        package_path = 'modules'
        package = importlib.import_module(package_path)
        
        for _, name, ispkg in pkgutil.iter_modules(package.__path__):
            if not ispkg and name != 'base_module':
                try:
                    module = importlib.import_module(f'{package_path}.{name}')
                    if hasattr(module, 'register_module'):
                        module.register_module(self.application)
                        self.modules.append(name)
                        logger.info(f'Módulo {name} carregado com sucesso')
                except Exception as e:
                    logger.error(f'Erro ao carregar módulo {name}: {e}')
    
    def setup_webhook(self):
        """Configura o webhook para o Render"""
        self.application.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv('PORT', 5000)),
            url_path=self.token,
            webhook_url=f"{self.webhook_url}/{self.token}"
        )

# Instância global do bot
bot = JuridicalBot()

@app.route('/')
def index():
    return 'Bot Jurídico Online!'

@app.route(f'/{bot.token}', methods=['POST'])
def webhook():
    """Endpoint do webhook"""
    update = Update.de_json(request.get_json(), bot.application.bot)
    bot.application.process_update(update)
    return 'ok'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configurar webhook manualmente"""
    webhook_url = f"{bot.webhook_url}/{bot.token}"
    success = bot.application.bot.set_webhook(webhook_url)
    return f'Webhook configurado: {success}'

if __name__ == '__main__':
    # Carregar módulos
    bot.load_modules()
    
    # Configurar webhook no startup
    webhook_url = f"{bot.webhook_url}/{bot.token}"
    bot.application.bot.set_webhook(webhook_url)
    
    # Iniciar Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
