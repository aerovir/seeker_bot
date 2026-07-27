#!/usr/bin/env bash
# Seeker Bot — Server Setup Script
# Запускать на VPS однократно при первом развёртывании.
# Копирует ключи, настраивает логи, директории, cron.
#
# Использование:
#   scp scripts/setup-server.sh user@host:/tmp/
#   ssh user@host "bash /tmp/setup-server.sh"

set -euo pipefail

echo "🚀 Seeker Bot — настройка сервера"
echo ""

# --- 1. Системные пакеты ---
echo "📦 Установка системных пакетов..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    docker.io \
    docker-compose-v2 \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    iotop \
    cron \
    logrotate \
    || true

sudo systemctl enable --now docker

# --- 2. Директории ---
echo "📁 Создание директорий..."
sudo mkdir -p /opt/seeker_bot
sudo mkdir -p /var/log/seeker_bot
sudo mkdir -p /var/log/nginx

# Права: пользователь в группе docker может писать логи
sudo chmod 755 /var/log/seeker_bot

# --- 3. Настройка logrotate ---
echo "🔄 Настройка logrotate..."
sudo tee /etc/logrotate.d/seeker_bot > /dev/null << 'EOF'
/var/log/seeker_bot/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    dateext
    maxsize 50M
}
EOF

sudo logrotate -f /etc/logrotate.d/seeker_bot || true

# --- 4. Настройка Docker compose ---
echo "🐳 Настройка Docker Compose..."
if [[ ! -f /opt/seeker_bot/docker-compose.yml ]]; then
    echo "⚠️  /opt/seeker_bot/docker-compose.yml не найден."
    echo "   Скопируйте файлы проекта на сервер:"
    echo "   rsync -avz --exclude='node_modules' --exclude='.venv' --exclude='.git' ./ user@host:/opt/seeker_bot/"
    echo ""
fi

# --- 5. Пользователь для деплоя ---
echo "👤 Настройка пользователя для деплоя..."
if id "deploy" &>/dev/null; then
    echo "   Пользователь deploy уже существует"
else
    sudo useradd -m -s /bin/bash deploy
    sudo usermod -aG docker deploy
    echo "   Создан пользователь deploy (в группе docker)"
    echo ""
    echo "   Добавьте SSH-ключ для деплоя:"
    echo "   ssh-copy-id deploy@<IP>"
fi

# --- 6. Docker Compose alias ---
echo "📋 Добавление alias в bashrc..."
for user_home in /root /home/deploy /home/*; do
    if [[ -f "$user_home/.bashrc" ]]; then
        if ! grep -q "seeker" "$user_home/.bashrc" 2>/dev/null; then
            echo "alias dc='docker compose'" >> "$user_home/.bashrc"
            echo "alias seeker-logs='tail -f /var/log/seeker_bot/seeker_bot.log'" >> "$user_home/.bashrc"
            echo "alias seeker-errors='grep ERROR /var/log/seeker_bot/seeker_bot.log | tail -50'" >> "$user_home/.bashrc"
        fi
    fi
done

# --- 7. Итог ---
echo ""
echo "✅ Настройка сервера завершена!"
echo ""
echo "📌 Путь к проекту: /opt/seeker_bot"
echo "📌 Путь к логам:   /var/log/seeker_bot/"
echo "📌 Logrotate:       /etc/logrotate.d/seeker_bot (ежедневно, 14 дней)"
echo ""
echo "Полезные команды на сервере:"
echo "  seeker-logs          — tail -f лога"
echo "  seeker-errors        — последние 50 ошибок"
echo "  docker compose ps    — статус контейнеров"
echo "  docker compose logs -f bot  — логи бота (через Docker)"
echo ""
echo "Где взять проект:"
echo "  git clone git@github.com:aerovir/seeker_bot.git /opt/seeker_bot"
echo "  cd /opt/seeker_bot && docker compose up -d"
