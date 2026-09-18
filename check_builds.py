import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://libretro.com"

def get_latest_builds():
    # Obtém a data de hoje (Formato: AAAA-MM-DD)
    hoje = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"Buscando atualizações de hoje ({hoje}) na central do Libretro...")
    
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Não foi possível acessar a página. Status: {response.status_code}")
        return [], hoje
    
    soup = BeautifulSoup(response.text, 'html.parser')
    arquivos_encontrados = []
    
    # Varre todos os links da página procurando os APKs do dia
    for link in soup.find_all('a', href=True):
        href = link['href']
        filename = os.path.basename(href)
        
        # Filtra arquivos que começam com a data de hoje e terminam em .apk
        if filename.startswith(hoje) and filename.endswith('.apk'):
            full_url = href if href.startswith('http') else os.path.join(URL, href)
            arquivos_encontrados.append({
                'name': filename,
                'url': full_url
            })
            
    return arquivos_encontrados, hoje

def main():
    builds, data_versao = get_latest_builds()
    
    if not builds:
        print("Nenhuma build lançada hoje até o momento.")
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("novas_builds=false\n")
        return

    print(f"Sucesso! Encontrados {len(builds)} arquivos para centralizar. Baixando...")
    os.makedirs("downloads", exist_ok=True)
    
    for build in builds:
        print(f"-> {build['name']}")
        r = requests.get(build['url'], stream=True)
        if r.status_code == 200:
            with open(f"downloads/{build['name']}", 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("novas_builds=true\n")
            f.write(f"tag_name=v{data_versao}\n")

if __name__ == "__main__":
    main()
