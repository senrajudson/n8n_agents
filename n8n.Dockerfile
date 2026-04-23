FROM n8nio/n8n:latest

# Mudamos para root para ter permissão de instalar pacotes npm
USER root

# Instalamos o nó da comunidade do Google Cloud Pub/Sub
RUN npm install -g n8n-nodes-gcp-pubsub

# Voltamos para o usuário padrão do n8n por segurança
USER node

# cat ./backup/postgres/n8n_2026-04-23_09-15-49.sql | docker exec -i n8n_postgres psql -U n8n -d n8n