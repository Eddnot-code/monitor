"""
Analisador de precos e gerador de alertas
Cruza produtos da loja com concorrentes por nome (fuzzy match)
"""

from datetime import datetime
from typing import Optional
import re


def normalize(text: str) -> str:
    """Normaliza texto para comparacao: remove acentos, lowercase, espacos extras"""
    text = text.upper()
    subs = {
        'Ã':'A','Á':'A','À':'A','Â':'A','Ä':'A',
        'É':'E','Ê':'E','È':'E','Ë':'E',
        'Í':'I','Î':'I','Ì':'I','Ï':'I',
        'Õ':'O','Ó':'O','Ô':'O','Ò':'O','Ö':'O',
        'Ú':'U','Û':'U','Ù':'U','Ü':'U',
        'Ç':'C','Ñ':'N',
    }
    for k, v in subs.items():
        text = text.replace(k, v)
    text = re.sub(r'[^A-Z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_keywords(nome: str) -> set:
    """Extrai palavras-chave relevantes do nome do produto"""
    n = normalize(nome)
    # Remove palavras genericas
    stop = {'DE','DA','DO','COM','SEM','PARA','E','A','O','EM','NO','NA','C','S'}
    words = set(w for w in n.split() if len(w) > 2 and w not in stop)
    return words


def match_score(nome_loja: str, nome_comp: str) -> float:
    """
    Calcula score de similaridade entre dois nomes de produto (0 a 1)
    Score >= 0.5 considera match
    """
    kw_loja = extract_keywords(nome_loja)
    kw_comp = extract_keywords(nome_comp)
    if not kw_loja or not kw_comp:
        return 0.0
    intersect = kw_loja & kw_comp
    union     = kw_loja | kw_comp
    return len(intersect) / len(union)


class PriceAnalyzer:

    def compare(self, my_products: list, competitors: dict) -> list:
        """Cruza produtos da loja com precos dos concorrentes por nome"""
        results = []

        for product in my_products:
            my_price = product.get('preco')
            nome     = product.get('nome', '')
            if not my_price or not nome or my_price < 10:
                continue

            # Busca matches nos concorrentes por nome
            comp_prices = []
            for comp_name, comp_data in competitors.items():
                for sku, cp in comp_data.get('products', {}).items():
                    if not cp.get('price'):
                        continue
                    score = match_score(nome, cp.get('name', ''))
                    if score >= 0.45:
                        comp_prices.append({
                            'competitor': comp_name,
                            'price':      cp['price'],
                            'url':        cp.get('url', ''),
                            'local':      comp_data.get('local', False),
                            'score':      score,
                        })

            if not comp_prices:
                continue

            comp_prices_sorted = sorted(comp_prices, key=lambda x: x['price'])
            min_comp = comp_prices_sorted[0]['price']
            max_comp = comp_prices_sorted[-1]['price']
            avg_comp = round(sum(c['price'] for c in comp_prices) / len(comp_prices), 2)

            diff_min = round(my_price - min_comp, 2)
            diff_pct = round((diff_min / min_comp) * 100, 1)

            all_prices = sorted([my_price] + [c['price'] for c in comp_prices])
            position   = all_prices.index(my_price) + 1

            status = 'ok'
            if diff_pct > 15:   status = 'caro'
            elif diff_pct > 5:  status = 'atencao'
            elif diff_pct < -5: status = 'mais_barato'

            results.append({
                'id':          product.get('id'),
                'sku':         product.get('sku', ''),
                'name':        nome,
                'my_price':    my_price,
                'min_comp':    min_comp,
                'max_comp':    max_comp,
                'avg_comp':    avg_comp,
                'diff_min':    diff_min,
                'diff_pct':    diff_pct,
                'position':    position,
                'total':       len(comp_prices) + 1,
                'status':      status,
                'competitors': comp_prices_sorted,
                'updated_at':  datetime.now().isoformat(),
            })

        return results

    def generate_alerts(self, my_products: list, competitors: dict, thresholds: dict) -> list:
        """Gera alertas quando criterios sao atingidos"""
        comparison = self.compare(my_products, competitors)
        alerts     = []

        for item in comparison:
            diff_pct = item.get('diff_pct')
            if diff_pct is None:
                continue

            # Alerta: muito mais caro
            if diff_pct >= thresholds.get('expensive_pct', 10):
                cheaper = [c for c in item['competitors'] if c['price'] < item['my_price']]
                local   = [c for c in cheaper if c.get('local')]
                alerts.append({
                    'type':               'expensive',
                    'severity':           'high' if diff_pct >= 20 else 'medium',
                    'product':            item['name'],
                    'sku':                item['sku'],
                    'my_price':           item['my_price'],
                    'min_price':          item['min_comp'],
                    'diff_pct':           diff_pct,
                    'cheaper_stores':     cheaper,
                    'has_local_cheaper':  len(local) > 0,
                    'message': (
                        f"🔴 ALERTA — PriceWatch\n"
                        f"Musical Presentes · {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                        f"📦 {item['name'][:60]}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"Seu preco:  R$ {item['my_price']:,.2f}\n"
                        f"Mais barato: R$ {item['min_comp']:,.2f} ({diff_pct:+.1f}%)\n"
                        + (''.join(f"\n  • {c['competitor']}: R$ {c['price']:,.2f}{' 📍LOCAL' if c['local'] else ''}" for c in cheaper[:3]))
                        + (f"\n\n⚠️ Concorrente LOCAL mais barato!" if local else "")
                        + f"\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"musicalpresentesonline.com.br"
                    ),
                    'timestamp': datetime.now().isoformat(),
                })

            # Alerta: voce e o mais barato
            elif diff_pct <= thresholds.get('cheapest_pct', -10):
                alerts.append({
                    'type':      'cheapest',
                    'severity':  'info',
                    'product':   item['name'],
                    'sku':       item['sku'],
                    'my_price':  item['my_price'],
                    'avg_price': item['avg_comp'],
                    'diff_pct':  diff_pct,
                    'message': (
                        f"💚 OPORTUNIDADE — PriceWatch\n"
                        f"Musical Presentes · {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                        f"📦 {item['name'][:60]}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"Voce e o MAIS BARATO!\n"
                        f"Seu preco:   R$ {item['my_price']:,.2f}\n"
                        f"Media mercado: R$ {item['avg_comp']:,.2f}\n"
                        f"Margem possivel: R$ {item['avg_comp'] - item['my_price']:,.2f}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"musicalpresentesonline.com.br"
                    ),
                    'timestamp': datetime.now().isoformat(),
                })

        return alerts

    def suggest_price(self, my_price: float, competitors: list, strategy: str = 'competitive') -> Optional[float]:
        if not competitors:
            return None
        prices = sorted(c['price'] for c in competitors)
        if strategy == 'cheapest':    return round(prices[0] * 0.98, 2)
        elif strategy == 'competitive': return round(prices[0] * 1.01, 2)
        elif strategy == 'average':   return round(sum(prices)/len(prices) * 0.99, 2)
        return None
