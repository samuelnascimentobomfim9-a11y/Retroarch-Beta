import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL_ALVO = "https://buildbot.libretro.com/nightly/android/"

def extrair_e_baixar_apks(url_pagina, pasta_destino="apks_baixados"):
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    print(f"🔍 Conectando ao site: {url_pagina}...")
    try:
        resposta = requests.get(url_pagina)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao acessar o site: {e}")
        return None

    soup = BeautifulSoup(resposta.text, 'html.parser')
    arquivos_datados = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.apk'):
            # Filtra arquivos que começam com o ano atual (ex: 2026-)
            if href.startswith("2026-"):
                arquivos_datados.append(href)

    if not arquivos_datados:
        print("⚠️ Nenhum arquivo APK datado de 2026 foi encontrado.")
        return None

    # Ordena a lista para garantir a ordem cronológica e pega o último (mais recente)
    arquivos_datados.sort()
    ultimo_arquivo = arquivos_datados[-1]
    
    # Extrai a data cortando os primeiros 10 caracteres (padrão: AAAA-MM-DD)
    ultima_data_str = ultimo_arquivo[:10]
    print(f"📅 Data mais recente detectada no servidor: {ultima_data_str}")

    # Define os três alvos específicos solicitados para essa data
    alvos = {
        "universal": f"{ultima_data_str}-RetroArch.apk",
        "arm64": f"{ultima_data_str}-RetroArch_aarch64.apk",
        "arm32": f"{ultima_data_str}-RetroArch_ra32.apk"
    }

    baixou_algo = False
    for arquitetura, nome_arquivo in alvos.items():
        url_download = urljoin(url_pagina, nome_arquivo)
        caminho_salvar = os.path.join(pasta_destino, nome_arquivo)
        print(f"⬇️ Baixando ({arquitetura}): {nome_arquivo}...")
        
        try:
            with requests.get(url_download, stream=True) as r:
                if r.status_code == 200:
                    with open(caminho_salvar, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Download concluído: {nome_arquivo}")
                    baixou_algo = True
                else:
                    print(f"⚠️ Arquivo não encontrado no servidor: {nome_arquivo}")
        except Exception as e:
            print(f"❌ Erro ao baixar {nome_arquivo}: {e}")

    return ultima_data_str if baixou_algo else None

if __name__ == "__main__":
    data_detectada = extrair_e_baixar_apks(URL_ALVO)
    if data_detectada:
        with open("tag_name.txt", "w") as f:
            f.write(data_detectada)
