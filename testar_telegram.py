"""
Teste do bot Telegram — rode este arquivo para confirmar a conexao
"""
import requests, json

TOKEN   = "8394491554:AAE65U2uhjmssegA5DbbfvTcPAP8UdZYLkc"
CHAT_ID = "665712154"

print("Testando conexao com o bot Telegram...")

r = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": (
            "✅ PriceWatch conectado!\n"
            "Musical Presentes · Ipatinga, MG\n\n"
            "🎸 Sistema de monitoramento ativo\n"
            "📦 1.082 produtos monitorados\n"
            "🏪 7 concorrentes rastreados\n"
            "📍 ShopMusic (local) em prioridade\n\n"
            "Você receberá alertas aqui automaticamente!"
        )
    },
    timeout=15
)

d = r.json()
if d.get("ok"):
    print("✅ Mensagem enviada com sucesso! Verifique o Telegram.")
else:
    print("❌ Erro:", d.get("description"))
