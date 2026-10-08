# Agente de Pesquisa de Carteira (STUDIO DENIM)

Site estático (GitHub Pages) para consultar a carteira de pedidos: busca direta, painel com filtro de mês e lista de pedidos atrasados.

## Arquivos

- `index.html` — a página inteira (HTML, CSS e JavaScript em um arquivo).
- `carteira.enc.json` — a carteira **criptografada** (AES-256-GCM; chave derivada da senha de entrada por PBKDF2-SHA256). Sem a senha, o conteúdo não pode ser lido.
- `tools/atualizar_carteira.py` — converte a planilha `carteira_….xlsx` e regrava `carteira.enc.json`.

## Atualizar a carteira

```bash
pip install openpyxl cryptography
CARTEIRA_SENHA='a senha de entrada' python3 tools/atualizar_carteira.py caminho/carteira_XXXX.xlsx <mtime_em_ms> carteira.enc.json
git add carteira.enc.json && git commit -m "Atualiza carteira" && git push
```

A senha nunca é gravada no repositório. Para trocar a senha, apague `carteira.enc.json` e gere-o de novo com a senha nova.

## Observações

- Só entram no arquivo as colunas usadas pelo site (Pedido, Emissão, Embarque, Cliente, Cliente Remessa, Pedido Cliente, Cond Pgto, Prazo Medio, Situação, Sit Linha, Motivo Cancel Linha, Notas Fiscais, Datas, Descrição, Quantidade, qtde_faturada, Saldo, Valor Unitário Liquido, Valor Total).
- A página aberta confere a cada 10 minutos se há carteira nova.
