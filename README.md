# DownloadXMLNf-e

Ferramenta desktop para Windows/Linux que estou desenvolvendo para **baixar NF-e modelo 55 destinadas a um CNPJ**, usando o serviço oficial **Distribuição DF-e (NFeDistribuicaoDFe)** e certificado digital A1.

A comunicação fiscal é feita com o projeto open source [NFePHP/SPED-NFe](https://github.com/nfephp-org/sped-nfe). A interface desktop é em Python/Tkinter.

> Este projeto substitui a versão anterior que automatizava um site de terceiros com Selenium. A proposta agora é consultar diretamente o serviço oficial da NF-e.

## O que a ferramenta faz

- seleciona certificado A1 `.pfx` ou `.p12`;
- consulta NF-e modelo 55 destinadas ao CNPJ;
- controla automaticamente o último NSU;
- continua as próximas consultas a partir do NSU salvo;
- descompacta os `docZip` retornados;
- separa XML completo, resumo de NF-e e eventos;
- evita depender de Chrome, ChromeDriver ou sites de terceiros;
- limita cada sincronização a 12 consultas, com intervalo de 2 segundos entre lotes.

## Como funciona

```
Certificado A1 + CNPJ
        ↓
NFePHP/SPED-NFe
        ↓
NFeDistribuicaoDFe
        ↓
ultNSU → novos documentos → maxNSU
        ↓
docZip
        ↓
xml/      XML completo (procNFe)
resumos/  resNFe
eventos/  eventos
```

O NSU não é o número da nota. Ele é o número sequencial usado pela Distribuição DF-e. Na primeira execução a ferramenta começa em `000000000000000`; depois grava o `ultNSU` em um arquivo de estado oculto na pasta escolhida.

## Requisitos

- Python 3.10 ou superior;
- PHP 8.1 ou superior, com extensões exigidas pelo NFePHP;
- Composer;
- certificado digital A1 válido;
- acesso à internet.

## Instalação

Clone o projeto:

```bash
git clone https://github.com/JannioFSantos/DownloadXMLNf-e.git
cd DownloadXMLNf-e
```

Instale o backend fiscal:

```bash
composer install
```

Execute:

```bash
python app.py
```

Na tela, informe o CNPJ, UF, certificado A1, senha e pasta onde deseja armazenar os XMLs. Depois clique em **Sincronizar NF-e**.

## Estrutura

```
DownloadXMLNf-e/
├── app.py
├── composer.json
├── requirements.txt
├── php/
│   └── distribuicao.php
└── README.md
```

## Manifestação do destinatário

Quando a Distribuição DF-e entrega apenas `resNFe`, o XML completo pode depender da manifestação do destinatário. Nesta primeira versão eu **não automatizei a manifestação**, para evitar registrar um evento fiscal sem uma ação explícita do usuário.

Os resumos ficam na pasta `resumos/` para uma futura tela de manifestação.

## Limites da Distribuição DF-e

O serviço deve ser consultado respeitando as regras da SEFAZ. A aplicação interrompe o ciclo quando recebe retorno sem novos documentos ou consumo indevido e mantém o último NSU para a próxima sincronização.

A Distribuição DF-e não deve ser tratada como backup histórico ilimitado. Documentos ficam disponíveis conforme as regras vigentes do Ambiente Nacional.

## Segurança

Não envie certificados A1, senhas ou XMLs reais para o GitHub. Os padrões `*.pfx` e `*.p12` estão no `.gitignore`.

A senha do certificado é passada ao processo PHP somente durante a execução e não é gravada pelo aplicativo.

## Base técnica

- [NFePHP/SPED-NFe](https://github.com/nfephp-org/sped-nfe)
- Serviço NFeDistribuicaoDFe / Distribuição de Documentos Fiscais Eletrônicos
- NF-e modelo 55

## Autor

**Jannio F. Santos**

GitHub: [@JannioFSantos](https://github.com/JannioFSantos)

## Aviso

Projeto open source em desenvolvimento. Antes de usar em produção, valide o comportamento com seu certificado, regras fiscais aplicáveis e documentação vigente da NF-e.
