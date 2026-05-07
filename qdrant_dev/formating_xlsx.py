import re
from pathlib import Path

import pandas as pd


ARQUIVO_ENTRADA = "digital_states.xls"
ARQUIVO_SAIDA = "digital_states_tratado.xlsx"


def valor_para_texto(valor):
    if pd.isna(valor):
        return ""

    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))

    return str(valor).strip()


def eh_estado_vazio(valor):
    texto = valor_para_texto(valor)
    return bool(re.fullmatch(r"\?\d+", texto))


def tratar_arquivo_excel(caminho_entrada, caminho_saida):
    caminho_entrada = Path(caminho_entrada)

    df = pd.read_excel(
        caminho_entrada,
        header=None,
        dtype=object
    )

    linha_cabecalho = None
    col_digital_set = None
    col_digital_states = None

    for idx, row in df.iterrows():
        valores = [valor_para_texto(v).lower() for v in row]

        if "digital state set" in valores and "digital states" in valores:
            linha_cabecalho = idx
            col_digital_set = valores.index("digital state set")
            col_digital_states = valores.index("digital states")
            break

    if linha_cabecalho is None:
        raise ValueError("Não encontrei o cabeçalho com 'Digital State Set' e 'Digital States'.")

    linha_indices = linha_cabecalho + 1
    resultado = []

    for i in range(linha_cabecalho + 2, len(df)):
        row = df.iloc[i]

        digital_set = valor_para_texto(row[col_digital_set])

        if not digital_set:
            continue

        estados_formatados = []

        for col in range(col_digital_states, len(df.columns)):
            valor_estado = row[col]
            texto_estado = valor_para_texto(valor_estado)

            if not texto_estado:
                continue

            if eh_estado_vazio(texto_estado):
                continue

            indice_cabecalho = valor_para_texto(df.iloc[linha_indices, col])

            if indice_cabecalho:
                indice = indice_cabecalho
            else:
                indice = str(col - col_digital_states)

            estados_formatados.append(f"{indice} = {texto_estado}")

        resultado.append({
            "Digital Set": digital_set,
            "Digital States": ", ".join(estados_formatados)
        })

    df_saida = pd.DataFrame(resultado)

    df_saida.to_excel(caminho_saida, index=False)

    print(f"Arquivo gerado com sucesso: {caminho_saida}")


if __name__ == "__main__":
    tratar_arquivo_excel(ARQUIVO_ENTRADA, ARQUIVO_SAIDA)