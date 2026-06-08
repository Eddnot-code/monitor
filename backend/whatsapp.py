"""
WhatsApp Alerter — via Z-API (solução brasileira)
Alternativa: Evolution API (self-hosted, gratuito)

Z-API: https://z-api.io
  - Plano gratuito disponível para testes
  - Plano pago a partir de R$49/mês
  - Sem necessidade de aprovação Meta

Evolution API (self-hosted):
  - Gratuito e open source
  - Requer servidor próprio
  - https://github.com/EvolutionAPI/evolution-api
"""

import requests
from datetime import datetime


class WhatsAppAlerter:
    def __init__(self, config: dict):
        self.provider  = config.get("provider", "zapi")  # "zapi" | "evolution"
        self.instance  = config.get("instance_id", "")
        self.token     = config.get("token", "")
        self.numbers   = config.get("numbers", [])        # lista de números destino
        self.base_url  = config.get("base_url", "")       # Evolution API URL se self-hosted
        self.enabled   = config.get("enabled", False)

    # ── Z-API ─────────────────────────────────────────────────────────────

    def _send_zapi(self, number: str, message: str) -> dict:
        """
        Envia via Z-API
        Endpoint: POST https://api.z-api.io/instances/{instance}/token/{token}/send-text
        """
        url = f"https://api.z-api.io/instances/{self.instance}/token/{self.token}/send-text"
        payload = {
            "phone":   number.replace("+", "").replace("-", "").replace(" ", ""),
            "message": message,
        }
        r = requests.post(url, json=payload, timeout=15)
        return r.json()

    # ── Evolution API ──────────────────────────────────────────────────────

    def _send_evolution(self, number: str, message: str) -> dict:
        """
        Envia via Evolution API (self-hosted)
        Endpoint: POST {base_url}/message/sendText/{instance}
        """
        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {"apikey": self.token}
        payload = {
            "number": number,
            "options": {"delay": 1200, "presence": "composing"},
            "textMessage": {"text": message},
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        return r.json()

    # ── Public ─────────────────────────────────────────────────────────────

    def send_message(self, number: str, message: str) -> bool:
        """Envia mensagem para um número"""
        if not self.enabled:
            print(f"[WhatsApp] DESATIVADO — mensagem para {number}:\n{message}")
            return False
        try:
            if self.provider == "zapi":
                result = self._send_zapi(number, message)
            else:
                result = self._send_evolution(number, message)
            print(f"[WhatsApp] Enviado para {number}: {result}")
            return True
        except Exception as e:
            print(f"[WhatsApp] Erro ao enviar para {number}: {e}")
            return False

    def send_alerts(self, alerts: list[dict]) -> int:
        """Envia todos os alertas para todos os números configurados"""
        sent = 0
        for alert in alerts:
            if alert.get("severity") not in ("high", "medium") and alert.get("type") != "cheapest":
                continue
            message = alert.get("message", "")
            for number in self.numbers:
                if self.send_message(number, message):
                    sent += 1
        return sent

    def send_daily_report(self, comparison: list[dict]) -> bool:
        """Envia resumo diário com top variações"""
        expensive = [p for p in comparison if p.get("status") == "caro"]
        cheaper   = [p for p in comparison if p.get("status") == "mais_barato"]

        lines = [
            f"📊 *Relatório Diário — Musical Presentes*",
            f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n",
        ]

        if expensive:
            lines.append("🔴 *Produtos acima do mercado:*")
            for p in expensive[:5]:
                lines.append(f"• {p['name']}: R${p['my_price']:,.0f} (min concorrente R${p['min_comp']:,.0f}, {p['diff_pct']:+.0f}%)")

        if cheaper:
            lines.append("\n💚 *Você é o mais barato:*")
            for p in cheaper[:5]:
                lines.append(f"• {p['name']}: R${p['my_price']:,.0f}")

        lines.append(f"\n_PriceWatch · musicalpresentesonline.com.br_")
        message = "\n".join(lines)

        success = False
        for number in self.numbers:
            if self.send_message(number, message):
                success = True
        return success
