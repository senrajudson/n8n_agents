FROM n8nio/n8n:latest

# Mudamos para root para ter permissão de instalar pacotes npm
USER root

# Instalamos o nó da comunidade do Google Cloud Pub/Sub
RUN npm install -g n8n-nodes-gcp-pubsub

# Voltamos para o usuário padrão do n8n por segurança
USER node