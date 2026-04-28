# Usa a imagem oficial do Ollama como base
FROM ollama/ollama:latest

# Configura o modelo: Pull -> Create Alias -> Remove Original -> Cleanup
RUN ollama serve & sleep 5 && \
    # 1. Baixa o modelo original do Hugging Face
    # ollama pull hf.co/Ian-Liu/Qwen2-VL-2B-OCR-Q4_K_M-GGUF && \
    # # 2. Cria o alias amigável
    # echo "FROM hf.co/Ian-Liu/Qwen2-VL-2B-OCR-Q4_K_M-GGUF" > Modelfile && \
    # ollama create qwen2vl-jackchew-2b -f Modelfile && \
    # # 3. LIMPEZA: Remove o nome gigante original e o arquivo temporário
    # ollama rm hf.co/Ian-Liu/Qwen2-VL-2B-OCR-Q4_K_M-GGUF && \
    # ollama rm qwen-ocr && \
    # rm Modelfile && \
    # 4. Baixa os outros modelos de texto necessários
    ollama pull qwen3.5:4b