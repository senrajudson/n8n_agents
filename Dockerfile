# Usa a imagem oficial do Ollama como base
FROM ollama/ollama:latest

# Inicia o servidor em background, aguarda 5 segundos para ele inicializar 
# e então faz o download do modelo Llama 3 para dentro da imagem.
RUN ollama serve & sleep 5 && \
    ollama pull llama3.1:8b && \
    ollama pull llama3.2:1b && \
    ollama pull llama3.2:3b && \
    ollama pull qwen3.5:0.8b && \
    ollama pull qwen3.5:2b && \
    ollama pull qwen3.5:4b && \
    ollama pull deepseek-r1:8b