import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

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
    
    # Lista para armazenar apenas arquivos com data no nome (padrão AAAA-MM-DD-...)
    arquivos_datados = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.endswith('.apk'):
            # Verifica se o arquivo começa com uma estrutura de data (ex: 2026-09-26)
            partes = href.split('-')
            if len(partes) >= 3 and partes[0].isdigit() and len(partes[0]) == 4:
                arquivos_datados.append(href)

    if not arquivos_datados:
        print("⚠️ Nenhum arquivo APK datado foi encontrado.")
        return None

    # Descobre qual é a data mais recente disponível na lista
    # Como a lista é em ordem cronológica, pegamos a data do último item
    ultima_data_str = "-".join(arquivos_datados[-1].split('-')[:3])
    print(f"📅 Data mais recente detectada no servidor: {ultima_data_str}")

    # Filtra os arquivos específicos dessa data mais recente
    alvos = {
        "universal": f"{ultima_data_str}-RetroArch.apk",
        "arm64": f"{ultima_data_str}-RetroArch_aarch64.apk",
        "arm32": f"{ultima_data_str}-RetroArch_ra32.apk"
    }

    # Baixa apenas os 3 arquivos correspondentes
    for arquitetura, nome_arquivo in alvos.items():
        if nome_arquivo in arquivos_datados:
            url_download = urljoin(url_pagina, nome_arquivo)
            caminho_salvar = os.path.join(pasta_destino, nome_arquivo)
            print(f"⬇️ Baixando ({arquitetura}): {nome_arquivo}...")
            
            try:
                with requests.get(url_download, stream=True) as r:
                    r.raise_for_status()
                    with open(caminho_salvar, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"✅ Download concluído: {nome_arquivo}")
            except Exception as e:
                print(f"❌ Erro ao baixar {nome_arquivo}: {e}")
        else:
            print(f"⚠️ Arquivo esperado não encontrado: {nome_arquivo}")

    # Retorna a data encontrada para ser usada como nome da Tag no GitHub Releases
    return ultima_data_str

if __name__ == "__main__":
    data_detectada = extrair_e_baixar_apks(URL_ALVO)
    # Escreve a data em um arquivo temporário para o GitHub Actions ler depois
    if data_detectada:
        with open("tag_name.txt", "w") as f:
            f.write(data_detectada)
