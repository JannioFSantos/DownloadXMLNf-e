# Downloader Automático de NF-e

Este programa permite baixar XMLs de Notas Fiscais Eletrônicas (NF-e) do site [www.meudanfe.com.br](https://www.meudanfe.com.br) usando automação web com Selenium. A aplicação possui interface gráfica moderna com barra de progresso em tempo real.



## 🎯 XPaths Utilizados

A automação utiliza os seguintes XPaths específicos do site meudanfe.com.br:

- **Campo de pesquisa**: `//*[@id="searchTxt"]`
- **Botão de consulta**: `//*[@id="searchBtn"]`
- **Botão de download XML**: `//*[@id="downloadXmlBtn"]/span` (
- **Botão de nova consulta**: `//*[@id="newSearchBtn"]/span`


## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:

```pip install -r requirements.txt
```

# DownloadXMLNf-e
