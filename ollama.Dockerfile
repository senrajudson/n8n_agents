FROM ollama/ollama:latest

RUN ollama serve & sleep 5 && \
    ollama pull nomic-embed-text-v2-moe && \
    ollama pull gemma4:e4b