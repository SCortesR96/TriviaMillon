FROM node:20-alpine AS alpine_vendor
WORKDIR /vendor
COPY package.json package-lock.json* ./
RUN npm install
RUN mkdir -p dist && cp node_modules/alpinejs/dist/cdn.min.js dist/alpine.min.js

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Tailwind CSS: CLI standalone (binario autocontenido), no depende de Node en runtime.
RUN curl -sLo /usr/local/bin/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=alpine_vendor /vendor/dist/alpine.min.js static/vendor/alpine.min.js

RUN tailwindcss -i tailwind/input.css -o static/dist/output.css --minify

# SECRET_KEY real solo se inyecta en runtime (Dokploy); este valor de build no se usa despues.
RUN SECRET_KEY=collectstatic-build-only python manage.py collectstatic --noinput

EXPOSE 8000
# migrate corre en cada arranque del contenedor (solo aqui: docker-compose.yml pisa este CMD
# en dev con runserver, asi que esto nunca se ejecuta en local). exec para que daphne quede
# como PID 1 y reciba bien las señales de apagado.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec daphne -b 0.0.0.0 -p 8000 config.asgi:application"]
