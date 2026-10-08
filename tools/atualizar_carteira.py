#!/usr/bin/env python3
"""Converte a planilha de carteira (.xlsx) e grava carteira.enc.json criptografado.

Uso:
    CARTEIRA_SENHA='...' python3 tools/atualizar_carteira.py <carteira.xlsx> <mtime_ms> [saida]

- So entram no arquivo as colunas usadas pelo site (lista COLS).
- O conteudo e cifrado com AES-256-GCM; a chave vem da senha por PBKDF2-SHA256.
- A senha nunca e gravada: informe-a pela variavel de ambiente CARTEIRA_SENHA.
Requer: openpyxl, cryptography.
"""
import sys, os, json, base64, datetime
import openpyxl
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

COLS = ['Pedido', 'Emissão', 'Embarque', 'Cliente', 'Cliente Remessa', 'Pedido Cliente', 'Cond Pgto',
        'Prazo Medio', 'Situação', 'Sit Linha', 'Motivo Cancel Linha', 'Notas Fiscais', 'Datas',
        'Descrição', 'Quantidade', 'qtde_faturada', 'Saldo', 'Valor Unitário Liquido', 'Valor Total']
NEED = ['Pedido', 'Embarque', 'Cliente', 'Sit Linha', 'Saldo', 'Quantidade', 'Valor Unitário Liquido']
ITER = 250000


def ler_planilha(src):
    wb = openpyxl.load_workbook(src, data_only=True)
    best = None
    for ws in wb:
        rows = list(ws.iter_rows(values_only=True))
        for hi, r in enumerate(rows[:6]):
            names = [str(c).strip() if c is not None else '' for c in r]
            n = sum(1 for c in COLS if c in names)
            if best is None or n > best[0]:
                best = (n, ws.title, hi, names, rows)
    n, title, hi, names, rows = best
    if not all(c in names for c in NEED):
        sys.exit('ERRO: colunas da carteira nao encontradas')
    idx = [names.index(c) if c in names else -1 for c in COLS]

    def conv(v):
        if isinstance(v, (datetime.datetime, datetime.date)):
            return v.strftime('%Y-%m-%d')
        if v is None:
            return ''
        if isinstance(v, float):
            return round(v, 4)
        if isinstance(v, str):
            return v.strip()
        return v

    out = []
    for r in rows[hi + 1:]:
        if all(v is None or v == '' for v in r):
            continue
        out.append([conv(r[i]) if i >= 0 else '' for i in idx])
    if not out:
        sys.exit('ERRO: planilha sem linhas')
    return title, out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, mtime_ms = sys.argv[1], int(sys.argv[2])
    dest = sys.argv[3] if len(sys.argv) > 3 else 'carteira.enc.json'
    senha = os.environ.get('CARTEIRA_SENHA', '')
    if not senha:
        sys.exit('ERRO: defina a variavel de ambiente CARTEIRA_SENHA')
    title, linhas = ler_planilha(src)
    iso = lambda d: d.isoformat(timespec='seconds').replace('+00:00', 'Z')
    utc = datetime.timezone.utc
    meta = {'arquivo': os.path.basename(src),
            'modificadoEm': iso(datetime.datetime.fromtimestamp(mtime_ms / 1000, utc)),
            'atualizadoEm': iso(datetime.datetime.now(utc))}
    salt = None
    if os.path.exists(dest):  # mantem o mesmo sal para a mesma senha continuar valendo
        try:
            salt = base64.b64decode(json.load(open(dest, encoding='utf-8'))['salt'])
        except Exception:
            salt = None
    if not salt:
        salt = os.urandom(16)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(senha.encode('utf-8'))
    iv = os.urandom(12)
    plain = json.dumps({'meta': meta, 'linhas': linhas}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    ct = AESGCM(key).encrypt(iv, plain, None)
    b64 = lambda b: base64.b64encode(b).decode('ascii')
    doc = {'v': 1, 'kdf': 'PBKDF2-SHA256', 'cifra': 'AES-256-GCM', 'iter': ITER, 'versao': str(mtime_ms),
           'arquivo': meta['arquivo'], 'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct)}
    json.dump(doc, open(dest, 'w', encoding='utf-8'))
    print('aba', title, '| linhas', len(linhas), '| arquivo', meta['arquivo'], '| gravado', dest)


if __name__ == '__main__':
    main()
