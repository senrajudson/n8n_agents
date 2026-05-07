import os
import re
from pathlib import Path
from uuid import uuid5, NAMESPACE_DNS

import pandas as pd
import requests
from qdrant_client import QdrantClient, models


ARQUIVO_EXCEL = os.getenv("ARQUIVO_EXCEL", "data/digital_states_tratado.xlsx")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "digital_state_sets")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text-v2-moe")

RECRIAR_COLLECTION = os.getenv("RECRIAR_COLLECTION", "true").lower() == "true"

BATCH_SIZE = 32


def limpar_texto(valor):
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def gerar_id_estavel(digital_set):
    return str(uuid5(NAMESPACE_DNS, f"digital-state-set::{digital_set}"))


def extrair_indices_states(digital_states):
    resultado = []

    partes = [p.strip() for p in digital_states.split(",") if p.strip()]

    for parte in partes:
        match = re.match(r"^(\d+)\s*=\s*(.+)$", parte)

        if not match:
            continue

        indice = int(match.group(1))
        valor = match.group(2).strip()

        resultado.append({
            "indice": indice,
            "valor": valor
        })

    return resultado


def montar_page_content(digital_set, digital_states):
    return (
        f"search_document: Digital State Set: {digital_set}\n"
        f"Nome do Digital Set: {digital_set}\n"
        f"Estados digitais configurados: {digital_states}\n"
        f"Use este documento para responder consultas sobre o digital set {digital_set}."
    )


def carregar_documentos_excel(caminho_excel):
    caminho = Path(caminho_excel)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_excel(caminho, dtype=str).fillna("")

    colunas_esperadas = {"Digital Set", "Digital States"}

    if not colunas_esperadas.issubset(set(df.columns)):
        raise ValueError(
            "O Excel precisa ter as colunas 'Digital Set' e 'Digital States'. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    documentos = []

    for _, row in df.iterrows():
        digital_set = limpar_texto(row["Digital Set"])
        digital_states = limpar_texto(row["Digital States"])

        if not digital_set:
            continue

        page_content = montar_page_content(digital_set, digital_states)
        states_parseados = extrair_indices_states(digital_states)

        metadata = {
            "digital_set": digital_set,
            "digital_states": digital_states,
            "states": states_parseados,
            "source": Path(ARQUIVO_EXCEL).name,
            "tipo": "digital_state_set"
        }

        payload = {
            "content": page_content,
            "page_content": page_content,
            "metadata": metadata,
            "digital_set": digital_set,
            "digital_states": digital_states,
            "tipo": "digital_state_set",
            "source": Path(ARQUIVO_EXCEL).name
        }

        documentos.append({
            "id": gerar_id_estavel(digital_set),
            "page_content": page_content,
            "payload": payload
        })

    return documentos


def gerar_embeddings_ollama(textos):
    url = f"{OLLAMA_URL.rstrip('/')}/api/embed"

    body = {
        "model": EMBED_MODEL,
        "input": textos
    }

    response = requests.post(url, json=body, timeout=300)
    response.raise_for_status()

    data = response.json()

    embeddings = data.get("embeddings")

    if not embeddings:
        raise ValueError(f"Ollama não retornou embeddings. Resposta: {data}")

    return embeddings


def dividir_em_lotes(lista, tamanho):
    for i in range(0, len(lista), tamanho):
        yield lista[i:i + tamanho]


def criar_collection(client, tamanho_vetor):
    if client.collection_exists(COLLECTION_NAME):
        if RECRIAR_COLLECTION:
            client.delete_collection(COLLECTION_NAME)
        else:
            return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=tamanho_vetor,
            distance=models.Distance.COSINE
        )
    )


def criar_indices_payload(client):
    indices = [
        "digital_set",
        "tipo",
        "source",
        "metadata.digital_set",
        "metadata.tipo"
    ]

    for campo in indices:
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=campo,
                field_schema=models.PayloadSchemaType.KEYWORD
            )
        except Exception:
            pass


def ingerir_documentos(documentos):
    if not documentos:
        raise ValueError("Nenhum documento válido encontrado para ingestão.")

    client = QdrantClient(
        url=QDRANT_URL,
        timeout=300
    )

    primeiro_embedding = gerar_embeddings_ollama([documentos[0]["page_content"]])[0]
    tamanho_vetor = len(primeiro_embedding)

    criar_collection(client, tamanho_vetor)
    criar_indices_payload(client)

    total = 0

    for lote in dividir_em_lotes(documentos, BATCH_SIZE):
        textos = [doc["page_content"] for doc in lote]
        embeddings = gerar_embeddings_ollama(textos)

        pontos = []

        for doc, embedding in zip(lote, embeddings):
            pontos.append(
                models.PointStruct(
                    id=doc["id"],
                    vector=embedding,
                    payload=doc["payload"]
                )
            )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=pontos
        )

        total += len(pontos)
        print(f"Ingeridos {total}/{len(documentos)} documentos")

    print("Ingestão finalizada.")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Modelo de embedding: {EMBED_MODEL}")
    print(f"Dimensão do vetor: {tamanho_vetor}")


def testar_busca():
    client = QdrantClient(url=QDRANT_URL)

    pergunta = "search_query: quais são os estados do BatchAct?"
    vetor = gerar_embeddings_ollama([pergunta])[0]

    resultado = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vetor,
        limit=5,
        with_payload=True
    ).points

    print("\nTeste de busca:")
    for ponto in resultado:
        payload = ponto.payload or {}

        print("-" * 80)
        print(f"Score: {ponto.score}")
        print(f"Digital Set: {payload.get('digital_set')}")
        print(f"Digital States: {payload.get('digital_states')}")


if __name__ == "__main__":
    docs = carregar_documentos_excel(ARQUIVO_EXCEL)
    ingerir_documentos(docs)
    testar_busca()