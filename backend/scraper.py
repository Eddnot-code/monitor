"""
Scraper de concorrentes — lojas de instrumentos musicais
"""

import requests
from bs4 import BeautifulSoup
import re, time, random, sys
from datetime import datetime
from typing import Optional

# Fix encoding no Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def clean_price(text: str) -> Optional[float]:
    """Extrai valor numerico de strings como R$ 3.990,00"""
    if not text:
        return None
    # Remove tudo exceto digitos e virgula
    text = re.sub(r'[^\d,]', '', text.replace('.', ''))
    text = text.replace(',', '.')
    try:
        val = float(text)
        # Filtra precos absurdos (acima de R$100.000 provavelmente erro)
        if val > 100000 or val < 5:
            return None
        return val
    except ValueError:
        return None


def extract_price_from_soup(soup) -> Optional[float]:
    """Tenta varios seletores para encontrar o preco correto"""

    # 1. Meta itemprop price (mais confiavel)
    meta = soup.find('meta', itemprop='price')
    if meta and meta.get('content'):
        try:
            val = float(meta['content'])
            if 5 < val < 100000:
                return val
        except:
            pass

    # 2. JSON-LD structured data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            import json
            data = json.loads(script.string or '{}')
            # Pode ser lista ou dict
            if isinstance(data, list):
                data = data[0] if data else {}
            price = None
            if 'offers' in data:
                offers = data['offers']
                if isinstance(offers, list):
                    price = offers[0].get('price')
                else:
                    price = offers.get('price')
            elif 'price' in data:
                price = data['price']
            if price:
                val = float(str(price).replace(',', '.'))
                if 5 < val < 100000:
                    return val
        except:
            pass

    # 3. Seletores CSS especificos por plataforma
    selectors = [
        # Loja Integrada
        '.fbits-produto-preco-por',
        '.preco-atual',
        '.precoPor',
        'span.preco-venda',
        # WooCommerce
        '.woocommerce-Price-amount.amount',
        'p.price > span.amount',
        'ins .woocommerce-Price-amount',
        # Genericos
        '[itemprop="price"]',
        '.product-price',
        '.price-box .price',
        '.selling-price',
        '.preco-por strong',
        '.produto-preco strong',
    ]

    for sel in selectors:
        try:
            el = soup.select_one(sel)
            if not el:
                continue
            # Pega o content ou o texto
            content = el.get('content') or el.get_text(strip=True)
            # Verifica se tem R$ ou numero
            if not re.search(r'[\d,]', content):
                continue
            price = clean_price(content)
            if price:
                return price
        except:
            pass

    return None


class CompetitorScraper:
    def __init__(self, competitors_config: list):
        self.competitors = competitors_config
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def scrape_url(self, url: str) -> Optional[float]:
        """Scrape preco de uma URL"""
        try:
            time.sleep(random.uniform(2.0, 4.0))
            r = self.session.get(url, timeout=20, allow_redirects=True)
            if r.status_code != 200:
                return None
            r.encoding = r.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')
            return extract_price_from_soup(soup)
        except Exception as e:
            print(f'[scraper] Erro em {url}: {e}')
            return None

    def scrape_all(self) -> dict:
        """Scrapes todos os produtos de todos os concorrentes"""
        results = {}
        timestamp = datetime.now().isoformat()

        for competitor in self.competitors:
            name = competitor['name']
            results[name] = {
                'name':      name,
                'url':       competitor.get('base_url', ''),
                'local':     competitor.get('local', False),
                'timestamp': timestamp,
                'products':  {},
            }

            for product in competitor.get('products', []):
                sku   = product['sku']
                url   = product['url']
                price = self.scrape_url(url)
                results[name]['products'][sku] = {
                    'sku':   sku,
                    'name':  product['name'],
                    'url':   url,
                    'price': price,
                    'found': price is not None,
                }
                status = f'R$ {price:.2f}' if price else 'nao encontrado'
                print(f'[{name}] {product["name"]}: {status}')

        return results
