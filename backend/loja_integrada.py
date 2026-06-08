"""
Loja Integrada API Client
"""

import requests

BASE_URL = "https://api.awsli.com.br/v1"


class LojaIntegradaAPI:
    def __init__(self, chave_api: str, chave_aplicacao: str):
        self.auth = {
            "chave_api": chave_api,
            "chave_aplicacao": chave_aplicacao,
        }

    def _get(self, endpoint: str, params: dict = None) -> dict:
        p = {**self.auth, **(params or {})}
        r = requests.get(f"{BASE_URL}/{endpoint}/", params=p, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_products(self, limit: int = 200) -> list:
        products = []
        offset = 0
        while True:
            resp = self._get("produto", {"limit": 50, "offset": offset, "ativo": "true"})
            objects = resp.get("objects", [])
            if not objects:
                break
            for obj in objects:
                if not obj or not obj.get("nome"):
                    continue

                # Categorias pode ser lista de strings ou lista de dicts
                cats_raw = obj.get("categorias", [])
                categorias = []
                for c in cats_raw:
                    if isinstance(c, dict):
                        categorias.append(c.get("nome", ""))
                    elif isinstance(c, str):
                        categorias.append(c)

                preco = obj.get("preco_promocional") or obj.get("preco_cheio") or obj.get("preco")

                products.append({
                    "id":        obj.get("id"),
                    "sku":       obj.get("sku", ""),
                    "nome":      obj.get("nome", ""),
                    "preco":     preco,
                    "ativo":     obj.get("ativo", True),
                    "categorias": categorias,
                    "url":       obj.get("url", ""),
                    "marca":     obj.get("marca", {}).get("nome") if isinstance(obj.get("marca"), dict) else "",
                })

            offset += 50
            if not resp.get("meta", {}).get("next"):
                break
            if offset >= limit:
                break

        return products

    def get_product(self, product_id: int) -> dict:
        return self._get(f"produto/{product_id}")

    def update_price(self, product_id: int, new_price: float) -> dict:
        r = requests.put(
            f"{BASE_URL}/produto/{product_id}/",
            params=self.auth,
            json={"preco_venda": new_price},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def get_categories(self) -> list:
        resp = self._get("categoria")
        return resp.get("objects", [])
