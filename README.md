# 🎸 PriceWatch — Musical Presentes
**Monitor de Preços · Análise de Concorrência · Alertas WhatsApp**

---

## 📁 Estrutura do Projeto

```
pricewatch/
├── backend/
│   ├── server.py          ← Servidor Flask (API principal)
│   ├── loja_integrada.py  ← Cliente API Loja Integrada
│   ├── scraper.py         ← Coleta de preços dos concorrentes
│   ├── analyzer.py        ← Análise e geração de alertas
│   ├── whatsapp.py        ← Envio de alertas via WhatsApp
│   └── requirements.txt   ← Dependências Python
├── frontend/
│   └── index.html         ← Dashboard completo (abre no navegador)
├── config/
│   └── config.json        ← ⚙️ ARQUIVO PRINCIPAL DE CONFIGURAÇÃO
└── data/                  ← Dados coletados (gerado automaticamente)
    ├── products.json
    ├── competitors.json
    └── alerts.json
```

---

## 🚀 Instalação

### 1. Pré-requisitos
- Python 3.11+
- pip

### 2. Instalar dependências
```bash
cd pricewatch/backend
pip install -r requirements.txt
```

### 3. Configurar API Keys (config/config.json)

Abra `config/config.json` e preencha:

```json
{
  "loja_integrada": {
    "chave_api": "a11542bc1dda66018ff6",       ← já está aqui
    "chave_aplicacao": "COLE_AQUI_O_EMAIL"      ← aguardando 72h
  }
}
```

### 4. Iniciar o servidor
```bash
cd pricewatch/backend
python server.py
```

### 5. Abrir o dashboard
Abra `frontend/index.html` no navegador.
O dashboard já funciona com dados de demonstração enquanto o backend não está ativo.

---

## ⚡ Uso

### Via Dashboard
1. Abra `frontend/index.html` no navegador
2. Clique **"Escanear Concorrentes"** para coletar preços
3. Acesse **Análise Competitiva** para ver comparações
4. Configure WhatsApp em **WhatsApp** → salve as credenciais
5. Defina os limites de alerta em **Configurações**

### Via API (linha de comando)
```bash
# Buscar produtos da sua loja
curl http://localhost:5000/api/products

# Disparar scraping dos concorrentes
curl -X POST http://localhost:5000/api/scrape

# Ver comparação completa
curl http://localhost:5000/api/comparison

# Ver alertas gerados
curl http://localhost:5000/api/alerts

# Atualizar preço de um produto
curl -X POST http://localhost:5000/api/update-price \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "new_price": 3290.00}'
```

---

## 📱 Configurar WhatsApp

### Opção 1 — Z-API (Recomendado, R$49/mês)
1. Acesse https://z-api.io e crie uma conta
2. Crie uma instância e conecte seu WhatsApp via QR Code
3. Copie o **Instance ID** e o **Token**
4. Cole no dashboard em **WhatsApp** → Configuração
5. Adicione o número destino: `5531999852104` (formato sem + e sem espaço)

### Opção 2 — Evolution API (Gratuito, self-hosted)
1. Clone: `git clone https://github.com/EvolutionAPI/evolution-api`
2. Siga o README do repositório para instalar
3. No config.json, altere `provider` para `"evolution"` e defina `base_url`

---

## 🏪 Concorrentes Monitorados

| Loja               | Tipo     | Cidade           | Prioridade |
|--------------------|----------|------------------|------------|
| ShopMusic          | Local    | Ipatinga, MG     | 🔴 Alta    |
| Super Sonora       | Nacional | Online           | 🟡 Média   |
| Loja Constelação   | Nacional | Online           | 🟡 Média   |
| Guarani Musical    | Nacional | Online           | 🟡 Média   |
| American Musical   | Nacional | Online           | 🟢 Normal  |
| BH Guitar          | Nacional | BH, MG           | 🟢 Normal  |
| Mundomax           | Nacional | Online           | 🟢 Normal  |

---

## 🔑 Quando a chave de aplicação chegar

1. Abra `config/config.json`
2. Substitua `"COLE_AQUI_QUANDO_CHEGAR_O_EMAIL"` pela chave recebida
3. Reinicie o servidor: `python server.py`
4. Clique **"Atualizar Produtos"** no dashboard — seus produtos reais serão carregados

---

## 📊 Lógica de Alertas

| Status         | Condição                              | Cor    |
|----------------|---------------------------------------|--------|
| Mais barato    | > 10% abaixo da média                 | 🟢 Verde |
| OK             | Dentro da faixa competitiva           | ⚪ Cinza |
| Atenção        | 5–10% acima do menor concorrente      | 🟡 Amber |
| Caro           | > 10% acima do menor concorrente      | 🔴 Vermelho |

---

## 🔄 Agendamento Automático

O servidor roda scraping automático a cada **6 horas**.
Para alterar, edite `config.json`:
```json
"scraping": { "interval_hours": 6 }
```

---

## 📞 Suporte

- **Loja:** musicalpresentesonline.com.br
- **WhatsApp:** (31) 99885-2104
- **Telefone:** (33) 3271-2912
