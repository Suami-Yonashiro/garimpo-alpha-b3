# Imagem reproduzivel do projeto. Usa uv (gerenciador rapido) sobre Python 3.11.
FROM python:3.11-slim

# uv: instalador/gerenciador de dependencias (copiado da imagem oficial)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 1) Copia so o manifesto primeiro -> aproveita cache de camada do Docker
COPY pyproject.toml ./
# Instala o nucleo de dependencias no ambiente do sistema do container
RUN uv pip install --system -r pyproject.toml

# 2) Copia o resto do codigo
COPY . .

# Comando padrao (ajustado quando houver um entrypoint real de pipeline)
CMD ["python", "-c", "from src.config import settings; print('Garimpo Alpha B3 — ambiente OK')"]
