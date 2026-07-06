# SkillTree AI backend — Django ASGI (Daphne) + Celery share this one image.
FROM python:3.12-slim

# docker CLI so the Celery worker can run the code-executor sandboxes
# (talks to the host daemon via the mounted /var/run/docker.sock).
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Default = web server. Worker/beat override `command` in docker-compose.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && daphne -b 0.0.0.0 -p 8000 core.asgi:application"]
