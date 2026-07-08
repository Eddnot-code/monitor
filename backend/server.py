@app.route('/api/products/sige', methods=['POST', 'GET'])
def sync_sige_products():
    """Sincroniza produtos direto da API SIGE Cloud"""
    SIGE_HEADERS = {
        "Authorization-token": "a8f322ba60dcbc9124171063b6bd56a3dd355e146a50cb6863079d7d568d27d092d9d02ad70dd0ccb08bc268edcbd5ab2e22ce51672c95da7c63eaa34e8951fe26c8d74948478485a1438c04441810b9c7b5dfc5c0a4985b0051558dc6bdf20001beb52853b7cf3414768c80118826136838b785225e78d1d595d8f7f17ff524",
        "User": "marketing@musicalpresentesonline.com.br",
        "App": "API"
    }
    TERMOS = [
        "violao","guitarra","baixo","teclado","bateria",
        "microfone","amplificador","caixa","pedaleira","fone",
        "saxofone","trompete","cavaquinho","ukulele","violino",
        "acordeon","percussao","pandeiro","cajon","interface"
    ]
    todos = {}
    for termo in TERMOS:
        try:
            r = requests.get(
                "https://api.sigecloud.com.br/request/produtos/pesquisar",
                params={"nome": termo},
                headers=SIGE_HEADERS,
                timeout=15
            )
            if r.status_code == 200:
                for p in r.json():
                    codigo = p.get("Codigo","")
                    if not codigo:
                        continue
                    preco = p.get("PrecoVenda") or (p.get("PrecosTabelas") or [{}])[0].get("PrecoVenda")
                    if not preco or not (10 < preco < 50000):
                        continue
                    todos[codigo] = {
                        "id": codigo, "sku": codigo,
                        "nome": p.get("Nome",""),
                        "preco": preco, "ativo": True,
                        "url": f"https://www.musicalpresentesonline.com.br/buscar?q={p.get('Nome','').replace(' ','+')}",
                    }
            time.sleep(0.3)
        except Exception as e:
            print(f"[sige] Erro {termo}: {e}")
    produtos = list(todos.values())
    save_data('products.json', produtos)
    print(f"[sige] {len(produtos)} produtos sincronizados")
    return jsonify({'synced': len(produtos), 'timestamp': datetime.now().isoformat()})
