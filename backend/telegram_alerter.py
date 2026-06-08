"""
Telegram Alerter — PriceWatch Musical Presentes
Gratuito, oficial, sem aprovação necessária.
"""

import requests
from datetime import datetime


class TelegramAlerter:
    def __init__(self, config: dict):
        self.token    = config.get("bot_token", "")
        self.chat_ids = config.get("chat_ids", [])   # lista de IDs que recebem alertas
        self.enabled  = config.get("enabled", False)
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id: str, text: str) -> bool:
        if not self.enabled:
            print(f"[Telegram] DESATIVADO — mensagem para {chat_id}:\n{text}")
            return False
        try:
            r = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id":    chat_id,
                    "text":       text,
                    "parse_mode": "Markdown",
                },
                timeout=15,
            )
            ok = r.json().get("ok", False)
            print(f"[Telegram] {'OK' if ok else 'ERRO'} → {chat_id}")
            return ok
        except Exception as e:
            print(f"[Telegram] Erro: {e}")
            return False

    def broadcast(self, text: str) -> int:
        """Envia para todos os chat_ids configurados"""
        sent = 0
        for cid in self.chat_ids:
            if self.send_message(cid, text):
                sent += 1
        return sent

    def send_alerts(self, alerts: list) -> int:
        sent = 0
        for a in alerts:
            if a.get("severity") not in ("high", "medium") and a.get("type") != "cheapest":
                continue
            msg = self._format_alert(a)
            sent += self.broadcast(msg)
        return sent

    def send_daily_report(self, comparison: list) -> bool:
        expensive = [p for p in comparison if p.get("status") == "caro"]
        cheaper   = [p for p in comparison if p.get("status") == "mais_barato"]
        lines = [
            f"📊 *Relatório Diário — Musical Presentes*",
            f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n",
        ]
        if expensive:
            lines.append("🔴 *Produtos acima do mercado:*")
            for p in expensive[:5]:
                lines.append(f"• {p['name']}: R${p['my_price']:,.0f} → min R${p['min_comp']:,.0f} ({p['diff_pct']:+.0f}%)")
        if cheaper:
            lines.append("\n💚 *Você é o mais barato:*")
            for p in cheaper[:5]:
                lines.append(f"• {p['name']}: R${p['my_price']:,.0f}")
        lines.append(f"\n_PriceWatch · musicalpresentesonline.com.br_")
        return self.broadcast("\n".join(lines)) > 0

    def _format_alert(self, a: dict) -> str:
        if a["type"] == "expensive":
            local_warn = "\n🏪 *Concorrente LOCAL mais barato!*" if a.get("has_local_cheaper") else ""
            cheaper_list = ""
            for c in a.get("cheaper_stores", [])[:3]:
                cheaper_list += f"\n  • {c['competitor']}: R${c['price']:,.0f}"
            return (
                f"🔔 *PriceWatch — Musical Presentes*\n"
                f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n"
                f"📦 *{a['product']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Seu preço:  R${a['my_price']:,.2f}\n"
                f"Mais barato: R${a['min_price']:,.2f} ({a['diff_pct']:+.1f}%)\n"
                f"{cheaper_list}{local_warn}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"_musicalpresentesonline.com.br_"
            )
        else:
            return (
                f"💚 *Oportunidade — Musical Presentes*\n"
                f"_{datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n"
                f"📦 *{a['product']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Você é o *mais barato!*\n"
                f"Seu preço:   R${a['my_price']:,.2f}\n"
                f"Média mercado: R${a.get('avg_price',0):,.2f}\n"
                f"Margem possível: R${a.get('avg_price',0) - a['my_price']:,.2f}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"_musicalpresentesonline.com.br_"
            )
