# 🤖 PI Chat - Assistente Virtual do PIMS

O **PI Chat** é um assistente virtual integrado ao Google Chat Workspace, desenvolvido para acelerar e simplificar o diagnóstico da infraestrutura e dos dados industriais (PI System) da Aperam.

Em vez de abrir painéis complexos para consultas rápidas, basta perguntar ao bot em linguagem natural!

---

## 🚀 O que ele pode fazer?

Atualmente, o agente possui duas grandes frentes de atuação:

### 1. 🔍 Status do PIMS e Servidores
O bot consegue analisar o estado da infraestrutura, investigando quedas, lentidão e logs de erro na PI Web API.
* **Exemplos de uso:**
  > *"A API caiu?"*
  > *"O servidor do PIMS está lento hoje?"*
  > *"Verifique a saúde da PI Web API."*

### 2. 🏷️ Consulta de Tags do PI System
Busca instantânea de detalhes técnicos de tags, retornando metadados, descrições e o `InstrumentTag` configurado.
* **Prefixos suportados:** `UTI`, `ACI`, `RED`, `LFS`, `LFI`, `CPD`.
* **Exemplos de uso:**
  > *"Qual a descrição da tag LFI_RB3_PESO_BOBINA?"*
  > *"Me traga os detalhes da UTI_TEMP_ZONA1."*
  > *"LFI_RB3_VEL_PROUM_FORNO"* *(Você pode enviar apenas o nome da tag)*

---

## 💬 Como utilizar

1. Abra o seu **Google Chat** (via navegador, app desktop ou celular).
2. Clique em **"Novo Chat"** e pesquise por **PI Chat**.
3. Envie um "Olá" para iniciar a conversa e o bot guiará você!

> **Dica:** O bot possui memória de contexto! Você pode fazer perguntas sequenciais (ex: *"Qual a descrição dessa tag?"* e depois *"E qual o instrument tag dela?"*).

---

## 🛠️ Arquitetura e Tecnologias

Este projeto foi construído focado em segurança, rodando seus modelos de IA localmente na infraestrutura da empresa:

* **Frontend / Interface:** Google Chat API integrada via Google Cloud Pub/Sub.
* **Orquestração e Fluxos:** [n8n](https://n8n.io/)
* **Inteligência Artificial (LLM):** `Llama 3.1 (8B)` hospedado localmente via Ollama (Hardware acelerado com GPU).
* **Memória de Conversação:** Redis.
* **Banco de Dados (n8n):** PostgreSQL 16.

---

## ⚙️ Como rodar / Manutenção SRE

Para subir o ambiente de desenvolvimento/produção localmente:

1. Clone este repositório.
2. Crie ou ajuste o arquivo `.env` na raiz do projeto com as credenciais necessárias (`POSTGRES_USER`, `N8N_ENCRYPTION_KEY`, etc.).
3. Inicie os contêineres:
   ```bash
   docker compose up -d