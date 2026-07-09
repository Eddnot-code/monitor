# PriceWatch v3.0 — Loja Integrada + SIGE Cloud — 2026-07-09
"""
PriceWatch - Backend API Server
Musical Presentes - musicalpresentesonline.com.br
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os, threading, time, requests
from datetime import datetime, timedelta
from scraper import CompetitorScraper
from loja_integrada import LojaIntegradaAPI
from telegram_alerter import TelegramAlerter
from analyzer import PriceAnalyzer

app = Flask(__name__)
CORS(app)

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
DATA_PATH   = os.path.join(BASE_DIR, 'data')

SCRAPE_INTERVAL_HOURS = 6
_scrape_lock = threading.Lock()
_is_scraping = False

SIGE_HEADERS = {
    "Authorization-token": "a8f322ba60dcbc9124171063b6bd56a3dd355e146a50cb6863079d7d568d27d092d9d02ad70dd0ccb08bc268edcbd5ab2e22ce51672c95da7c63eaa34e8951fe26c8d74948478485a1438c04441810b9c7b5dfc5c0a4985b0051558dc6bdf20001beb52853b7cf3414768c80118826136838b785225e78d1d595d8f7f17ff524",
    "User": "marketing@musicalpresentesonline.com.br",
    "App": "API"
}

SIGE_TERMOS = [
    "violao", "guitarra", "baixo", "teclado", "bateria",
    "microfone", "amplificador", "caixa", "pedaleira", "fone",
    "saxofone", "trompete", "cavaquinho", "ukulele", "violino",
    "acordeon", "percussao", "pandeiro", "cajon", "interface"
]

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

def get_sige_prices():
    precos = {}
    for termo in SIGE_TERMOS:
        try:
            r = requests.get(
                "https://api.sigecloud.com.br/request/produtos/pesquisar",
                params={"nome": termo},
                headers=SIGE_HEADERS,
                timeout=15
            )
            if r.status_code == 200:
                for p in r.json():
                    codigo = p.get("Codigo", "")
                    if not codigo:
                        continue
                    preco = p.get("PrecoVenda") or (p.get("PrecosTabelas") or [{}])[0].get("PrecoVenda")
                    if preco and 10 < preco < 50000:
                        precos[codigo] = preco
            time.sleep(0.3)
        except Exception as e:
            print(f"[sige] Erro {termo}: {e}")
    print(f"[sige] {len(precos)} precos carregados")
    return precos

def sync_products():
    cfg = load_config()
    print("[sync] Buscando produtos da Loja Integrada...")
    api = LojaIntegradaAPI(
        cfg['loja_integrada']['chave_api'],
        cfg['loja_integrada']['chave_aplicacao']
    )
    li_products = api.get_products()
    print(f"[sync] {len(li_products)} produtos da LI")

    print("[sync] Buscando precos do SIGE Cloud...")
    sige_precos = get_sige_prices()

    produtos_finais = []
    matched = 0
    for p in li_products:
        sku   = str(p.get('sku', ''))
        preco = sige_precos.get(sku)
        if preco:
            matched += 1
        if p.get('nome'):
            produtos_finais.append({
                "id":    p.get('id'),
                "sku":   sku,
                "nome":  p.get('nome', ''),
                "preco": preco,
                "ativo": p.get('ativo', True),
                "url":   p.get('url', ''),
            })

    produtos_validos = [p for p in produtos_finais if p.get('preco') and p.get('nome')]
    save_data('products.json', produtos_validos)
    print(f"[sync] {len(produtos_validos)} produtos com preco ({matched} cruzados LI+SIGE)")
    return produtos_validos

def run_scrape_and_alert():
    global _is_scraping
    try:
        cfg     = load_config()
        scraper = CompetitorScraper(cfg['competitors'])
        results = scraper.scrape_all()
        save_data('competitors.json', results)

        products = load_data('products.json')
        if not products or not any(p.get('preco') for p in (products if isinstance(products, list) else [])):
            print("[scheduler] Sem produtos com preco — sincronizando LI+SIGE...")
            products = sync_products()

        analyzer = PriceAnalyzer()
        alerts   = analyzer.generate_alerts(products, results, cfg['alert_thresholds'])
        save_data('alerts.json', alerts)
        save_data('last_run.json', {'timestamp': datetime.now().isoformat(), 'alerts': len(alerts)})

        if alerts and cfg['telegram']['enabled']:
            tg   = TelegramAlerter(cfg['telegram'])
            sent = tg.send_alerts(alerts)
            print(f"[{datetime.now()}] {len(alerts)} alertas, {sent} enviados")
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
    finally:
        _is_scraping = False

def maybe_run_scrape(force=False):
    global _is_scraping
    last_run   = load_data('last_run.json') or {}
    last_ts    = last_run.get('timestamp')
    should_run = force
    if not should_run:
        if not last_ts:
            should_run = True
        else:
            last_dt = datetime.fromisoformat(last_ts)
            if datetime.now() - last_dt >= timedelta(hours=SCRAPE_INTERVAL_HOURS):
                should_run = True
    if should_run and not _is_scraping:
        with _scrape_lock:
            if _is_scraping:
                return False
            _is_scraping = True
        t = threading.Thread(target=run_scrape_and_alert, daemon=True)
        t.start()
        return True
    return False

@app.route('/')
def home():
    return jsonify({'app': 'PriceWatch — Musical Presentes', 'status': 'online', 'time': datetime.now().isoformat()})

@app.route('/api/status')
def status():
    products  = load_data('products.json')
    comp      = load_data('competitors.json')
    alerts    = load_data('alerts.json') or []
    last_run  = load_data('last_run.json') or {}
    com_preco = len([p for p in products if p.get('preco')]) if isinstance(products, list) else 0
    return jsonify({
        'status':              'ok',
        'timestamp':           datetime.now().isoformat(),
        'products_loaded':     len(products) if isinstance(products, list) else 0,
        'products_com_preco':  com_preco,
        'competitors_scraped': len(comp),
        'alerts':              len(alerts),
        'last_run':            last_run,
        'is_scraping':         _is_scraping,
    })

@app.route('/api/products/sync/now', methods=['GET', 'POST'])
def sync_now():
    produtos  = sync_products()
    com_preco = len([p for p in produtos if p.get('preco')])
    return jsonify({'total': len(produtos), 'com_preco': com_preco, 'timestamp': datetime.now().isoformat()})

@app.route('/api/products/sige/sync', methods=['GET', 'POST'])
def sync_sige_sync():
    todos = {}
    for termo in SIGE_TERMOS:
        try:
            r = requests.get(
                "https://api.sigecloud.com.br/request/produtos/pesquisar",
                params={"nome": termo}, headers=SIGE_HEADERS, timeout=15
            )
            if r.status_code == 200:
                for p in r.json():
                    codigo = p.get("Codigo", "")
                    if not codigo: continue
                    preco = p.get("PrecoVenda") or (p.get("PrecosTabelas") or [{}])[0].get("PrecoVenda")
                    if preco and 10 < preco < 50000:
                        todos[codigo] = {"id": codigo, "sku": codigo, "nome": p.get("Nome",""), "preco": preco, "ativo": True, "url": "https://www.musicalpresentesonline.com.br/buscar?q="+p.get("Nome","").replace(" ","+")}
            time.sleep(0.3)
        except Exception as e:
            print(f"[sige] Erro {termo}: {e}")
    produtos = list(todos.values())
    save_data('products.json', produtos)
    return jsonify({'synced': len(produtos), 'timestamp': datetime.now().isoformat()})

@app.route('/api/products')
def get_products():
    cfg = load_config()
    api = LojaIntegradaAPI(cfg['loja_integrada']['chave_api'], cfg['loja_integrada']['chave_aplicacao'])
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
    if not products or not competitors: return jsonify([])
    return jsonify(PriceAnalyzer().compare(products, competitors))

@app.route('/api/alerts')
def get_alerts():
    return jsonify(load_data('alerts.json') or [])

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    started = maybe_run_scrape(force=True)
    return jsonify({'status': 'iniciado' if started else 'ja_em_andamento', 'timestamp': datetime.now().isoformat()})

@app.route('/api/scrape/sync', methods=['POST'])
def trigger_scrape_sync():
    global _is_scraping
    _is_scraping = False
    n = run_scrape_and_alert()
    return jsonify({'scraped': 7, 'alerts': n, 'timestamp': datetime.now().isoformat()})

@app.route('/api/cron', methods=['GET', 'POST', 'HEAD'])
def cron_endpoint():
    started  = maybe_run_scrape(force=False)
    last_run = load_data('last_run.json') or {}
    return jsonify({'status': 'ok', 'scrape_started': started, 'last_run': last_run, 'timestamp': datetime.now().isoformat()})

@app.route('/api/telegram/test', methods=['POST', 'GET'])
def test_telegram():
    cfg = load_config()
    tg  = TelegramAlerter(cfg['telegram'])
    tg.enabled = True
    ok = tg.broadcast("✅ PriceWatch online na nuvem!\nMusical Presentes · Ipatinga, MG\n\nSistema rodando 24h no Railway.\nAlertas automaticos a cada 6 horas.")
    return jsonify({'sent': ok > 0})

@app.route('/api/update-price', methods=['POST'])
def update_price():
    body = request.json
    cfg  = load_config()
    api  = LojaIntegradaAPI(cfg['loja_integrada']['chave_api'], cfg['loja_integrada']['chave_aplicacao'])
    return jsonify(api.update_price(body['product_id'], body['new_price']))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"PriceWatch iniciado — porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
