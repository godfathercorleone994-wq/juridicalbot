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

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variável global para a aplicação
application = None

def initialize_bot():
    """Inicializa o bot de forma segura"""
    global application
    
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN não configurado")
            return False
        
        # Criar aplicação - método correto para versão 20.x
        application = Application.builder().token(token).build()
        
        # Carregar módulos
        load_modules(application)
        
        logger.info("✅ Bot inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        return False

def load_modules(app):
    """Carrega todos os módulos automaticamente"""
    try:
        package_path = 'modules'
        package = importlib.import_module(package_path)
        modules_loaded = []
        
        for _, name, ispkg in pkgutil.iter_modules(package.__path__):
            if not ispkg and name != 'base_module':
                try:
                    module = importlib.import_module(f'{package_path}.{name}')
                    if hasattr(module, 'register_module'):
                        module.register_module(app)
                        modules_loaded.append(name)
                        logger.info(f'✅ Módulo {name} carregado')
                except Exception as e:
                    logger.error(f'❌ Erro no módulo {name}: {e}')
        
        logger.info(f'🎯 {len(modules_loaded)} módulos carregados: {modules_loaded}')
        
    except Exception as e:
        logger.error(f'❌ Erro ao carregar módulos: {e}')

# Inicializar o bot ao importar
bot_initialized = initialize_bot()

@app.route('/')
def home():
    return '🤖 Bot Jurídico Online! Use /start no Telegram.'

@app.route('/health')
def health():
    status = "healthy" if application else "unhealthy"
    return {'status': status, 'bot_initialized': bot_initialized}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para receber atualizações do Telegram"""
    if not application:
        return 'Bot não inicializado', 500
        
    try:
        # Processar a atualização do Telegram
        update = Update.de_json(request.get_json(), application.bot)
        application.process_update(update)
        return 'ok'
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return 'error', 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Configurar webhook no Telegram"""
    if not application:
        return 'Bot não inicializado', 500
        
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        return 'WEBHOOK_URL não configurada', 500
        
    full_webhook_url = f"{webhook_url}/webhook"
    
    try:
        success = application.bot.set_webhook(full_webhook_url)
        logger.info(f"🌐 Webhook configurado: {success} - URL: {full_webhook_url}")
        return f'Webhook configurado: {success} - URL: {full_webhook_url}'
    except Exception as e:
        logger.error(f"❌ Erro ao configurar webhook: {e}")
        return f'Erro: {e}', 500

@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    """Remover webhook (útil para testes)"""
    if not application:
        return 'Bot não inicializado', 500
        
    try:
        success = application.bot.delete_webhook()
        logger.info(f"🗑️ Webhook removido: {success}")
        return f'Webhook removido: {success}'
    except Exception as e:
        logger.error(f"❌ Erro ao remover webhook: {e}")
        return f'Erro: {e}', 500

# Configurar webhook automaticamente ao iniciar
if bot_initialized and application:
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        try:
            full_url = f"{webhook_url}/webhook"
            application.bot.set_webhook(full_url)
            logger.info(f"🚀 Webhook automático configurado: {full_url}")
        except Exception as e:
            logger.error(f"❌ Erro no webhook automático: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port)
