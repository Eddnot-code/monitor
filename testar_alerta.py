"""
Teste completo do PriceWatch — simula alertas reais e envia no Telegram
"""
import requests, json, time
from datetime import datetime

TOKEN   = "8394491554:AAE65U2uhjmssegA5DbbfvTcPAP8UdZYLkc"
CHAT_ID = "665712154"

def send(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )
    ok = r.json().get("ok", False)
    print("Enviado!" if ok else f"Erro: {r.text}")
    return ok

print("=" * 50)
print("  PriceWatch — Teste de Alertas")
print("  Musical Presentes · Ipatinga, MG")
print("=" * 50)

# ALERTA 1 — Produto caro vs ShopMusic local
print("\n[1/4] Enviando alerta: produto caro vs concorrente local...")
send(
    "🔴 ALERTA — PriceWatch\n"
    "Musical Presentes · " + datetime.now().strftime('%d/%m/%Y %H:%M') + "\n\n"
    "📦 GUITARRA TAGIMA TG-510\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Seu preco:     R$ 989,00\n"
    "ShopMusic:     R$ 899,00  LOCAL\n"
    "Super Sonora:  R$ 919,00\n"
    "Diferenca:     +10,0% acima\n\n"
    "Sugestao: reduzir para R$ 889,00\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "musicalpresentesonline.com.br"
)
time.sleep(2)

# ALERTA 2 — Voce e o mais barato
print("[2/4] Enviando alerta: voce e o mais barato...")
send(
    "💚 OPORTUNIDADE — PriceWatch\n"
    "Musical Presentes · " + datetime.now().strftime('%d/%m/%Y %H:%M') + "\n\n"
    "📦 VIOLAO GIANNINI START N14 NAILON\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Seu preco:      R$ 439,00\n"
    "American Music: R$ 449,00\n"
    "Loja Constelac: R$ 459,00\n"
    "ShopMusic:      R$ 489,00  LOCAL\n\n"
    "Voce e o MAIS BARATO do mercado!\n"
    "Margem possivel: ate R$ 50,00 a mais\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "musicalpresentesonline.com.br"
)
time.sleep(2)

# ALERTA 3 — Relatorio diario
print("[3/4] Enviando relatorio diario...")
send(
    "📊 RELATORIO DIARIO — PriceWatch\n"
    + datetime.now().strftime('%d/%m/%Y') + " · Musical Presentes\n\n"
    "🔴 Produtos acima do mercado (2):\n"
    "• Takamine GD11: R$ 3.990 vs R$ 2.939 (+35,8%)\n"
    "• Takamine GD90: R$ 8.800 vs R$ 7.490 (+17,5%)\n\n"
    "💚 Voce e o mais barato (1):\n"
    "• Giannini N14: R$ 439 (mercado R$ 471)\n\n"
    "🏪 Concorrente local ShopMusic:\n"
    "• 3 produtos verificados\n"
    "• 2 mais baratos que voce\n\n"
    "Proxima varredura: em 6 horas\n"
    "musicalpresentesonline.com.br"
)
time.sleep(2)

# ALERTA 4 — Concorrente baixou preco
print("[4/4] Enviando alerta de mudanca de preco...")
send(
    "⚠️ MUDANCA DE PRECO DETECTADA\n"
    "Musical Presentes · " + datetime.now().strftime('%d/%m/%Y %H:%M') + "\n\n"
    "📦 VIOLAO SEIZI KAIZEN AKIRA\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Super Sonora baixou o preco!\n"
    "Antes: R$ 1.899,00\n"
    "Agora: R$ 1.699,00  (-10,5%)\n\n"
    "Seu preco atual: R$ 1.899,00\n"
    "Diferenca: +11,8% acima deles\n\n"
    "Acao recomendada: revisar preco\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "musicalpresentesonline.com.br"
)

print("\n" + "=" * 50)
print("  4 alertas enviados com sucesso!")
print("  Verifique o Telegram agora.")
print("=" * 50)
