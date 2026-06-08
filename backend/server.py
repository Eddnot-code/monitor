"""
PriceWatch - Backend API Server
Musical Presentes - musicalpresentesonline.com.br
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os, threading, time
from datetime import datetime
from scraper import CompetitorScraper
from loja_integrada import LojaIntegradaAPI
from telegram_alerter import TelegramAlerter
from analyzer import PriceAnalyzer

app = Flask(__name__)
CORS(app)

# Paths — funciona tanto local quanto Railway
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
DATA_PATH   = os.path.join(BASE_DIR, 'data')

def load_config():
    with open(CONFIG_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_data(filename, data):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(os.path.join(DATA_PATH, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data(filename):
    path = os.path.join(DATA_PATH, filename)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def run_scrape_and_alert():
    try:
        cfg     = load_config()
        scraper = CompetitorScraper(cfg['competitors'])
        results = scraper.scrape_all()
        save_data('competitors.json', results)

        products = load_data('products.json')
        if not products:
            print("[scheduler] Nenhum produto — carregando da API...")
            api = LojaIntegradaAPI(
                cfg['loja_integrada']['chave_api'],
                cfg['loja_integrada']['chave_aplicacao']
            )
            products = api.get_products()
            save_data('products.json', products)

        analyzer = PriceAnalyzer()
        alerts   = analyzer.generate_alerts(products, results, cfg['alert_thresholds'])
        save_data('alerts.json', alerts)

        if alerts and cfg['telegram']['enabled']:
            tg   = TelegramAlerter(cfg['telegram'])
            sent = tg.send_alerts(alerts)
            print(f"[{datetime.now()}] {len(alerts)} alertas, {sent} enviados no Telegram")

            if datetime.now().hour == 9:
                comparison = analyzer.compare(products, results)
                tg.send_daily_report(comparison)
        else:
            print(f"[{datetime.now()}] Scraping OK — {len(alerts)} alertas")

        return len(alerts)
    except Exception as e:
        print(f"[{datetime.now()}] Erro: {e}")
        import traceback; traceback.print_exc()
        return 0

@app.route('/')
def home():
    return jsonify({
        'app':    'PriceWatch — Musical Presentes',
        'status': 'online',
        'time':   datetime.now().isoformat()
    })

@app.route('/api/status')
def status():
    products    = load_data('products.json')
    competitors = load_data('competitors.json')
    alerts      = load_data('alerts.json') or []
    return jsonify({
        'status':              'ok',
        'timestamp':           datetime.now().isoformat(),
        'products_loaded':     len(products) if isinstance(products, list) else 0,
        'competitors_scraped': len(competitors),
        'alerts':              len(alerts),
    })

@app.route('/api/products')
def get_products():
    cfg = load_config()
    api = LojaIntegradaAPI(
        cfg['loja_integrada']['chave_api'],
        cfg['loja_integrada']['chave_aplicacao']
    )
    products = api.get_products()
    save_data('products.json', products)
    return jsonify({'loaded': len(products)})

@app.route('/api/competitors')
def get_competitors():
    return jsonify(load_data('competitors.json'))

@app.route('/api/comparison')
def get_comparison():
    products    = load_data('products.json')
    competitors = load_data('competitors.json')
    if not products or not competitors:
        return jsonify([])
    analyzer = PriceAnalyzer()
    return jsonify(analyzer.compare(products, competitors))

@app.route('/api/alerts')
def get_alerts():
    return jsonify(load_data('alerts.json') or [])

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    t = threading.Thread(target=run_scrape_and_alert, daemon=True)
    t.start()
    return jsonify({'status': 'iniciado', 'timestamp': datetime.now().isoformat()})

@app.route('/api/scrape/sync', methods=['POST'])
def trigger_scrape_sync():
    n      = run_scrape_and_alert()
    alerts = load_data('alerts.json') or []
    return jsonify({'scraped': 7, 'alerts': n, 'timestamp': datetime.now().isoformat()})

@app.route('/api/telegram/test', methods=['POST'])
def test_telegram():
    cfg = load_config()
    tg  = TelegramAlerter(cfg['telegram'])
    tg.enabled = True
    ok = tg.broadcast(
        "✅ PriceWatch online na nuvem!\n"
        "Musical Presentes · Ipatinga, MG\n\n"
        "Sistema rodando 24h no Railway.\n"
        "Alertas automaticos a cada 6 horas."
    )
    return jsonify({'sent': ok > 0})

@app.route('/api/update-price', methods=['POST'])
def update_price():
    body = request.json
    cfg  = load_config()
    api  = LojaIntegradaAPI(
        cfg['loja_integrada']['chave_api'],
        cfg['loja_integrada']['chave_aplicacao']
    )
    return jsonify(api.update_price(body['product_id'], body['new_price']))

def scheduler():
    time.sleep(60)  # aguarda 1 min antes do primeiro ciclo
    while True:
        print(f"[{datetime.now()}] Iniciando varredura automatica...")
        run_scrape_and_alert()
        time.sleep(6 * 3600)

if __name__ == '__main__':
    t = threading.Thread(target=scheduler, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 5000))
    print(f"PriceWatch iniciado — porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
