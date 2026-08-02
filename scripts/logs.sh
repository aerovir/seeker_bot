#!/usr/bin/env bash
# Seeker Bot — SSH Log Reader
# Использование: ./scripts/logs.sh [options]
#
# Требует настроенного SSH-хоста в ~/.ssh/config или передачи параметров.
#
# Примеры:
#   ./scripts/logs.sh                            # последние 50 строк
#   ./scripts/logs.sh -n 100                     # последние 100 строк
#   ./scripts/logs.sh -n 50 -l ERROR             # последние 50 ERROR-записей
#   ./scripts/logs.sh -f                         # follow (tail -f)
#   ./scripts/logs.sh -s                         # статистика ошибок
#   ./scripts/logs.sh -c bot                     # логи конкретного Docker-контейнера
#   ./scripts/logs.sh -c bot -n 100 -f           # tail -f последних 100 строк бота
#   ./scripts/logs.sh -d                         # вывод в Markdown (для Claude)
#
# Конфигурация: скопировать и отредактировать /etc/ssh/ssh_config.d/seeker_bot.conf
#   Host seeker-bot
#       HostName <IP>
#       User <username>
#       Port 22
#       IdentityFile ~/.ssh/seeker_bot_deploy
#       StrictHostKeyChecking accept-new

set -euo pipefail

# --- Конфигурация (заполнить после получения доступа) ---
SSH_HOST="${SEEKER_SSH_HOST:-}"
SSH_USER="${SEEKER_SSH_USER:-}"
SSH_PORT="${SEEKER_SSH_PORT:-22}"
SSH_KEY="${SEEKER_SSH_KEY:-}"
LOG_DIR="/var/log/seeker_bot"
COMPOSE_DIR="/opt/seeker_bot"

# --- Параметры ---
LINES=50
LEVEL=""
FOLLOW=false
STATS=false
DOCKER_CONTAINER=""
MARKDOWN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n) LINES="$2"; shift 2 ;;
        -l) LEVEL="$2"; shift 2 ;;
        -f) FOLLOW=true; shift ;;
        -s) STATS=true; shift ;;
        -c) DOCKER_CONTAINER="$2"; shift 2 ;;
        -d) MARKDOWN=true; shift ;;
        -h|--help)
            sed -n '3,20p' "$0" | sed 's/^# //'
            exit 0
            ;;
        *) echo "Неизвестный аргумент: $1"; exit 1 ;;
    esac
done

# --- Проверка SSH-доступа ---
check_ssh() {
    if [[ -z "$SSH_HOST" ]]; then
        # Пробуем через ~/.ssh/config
        if ssh -G seeker-bot 2>/dev/null | grep -q "^hostname "; then
            SSH_HOST="seeker-bot"
        else
            echo "❌ SSH-хост не настроен."
            echo ""
            echo "Настройка:"
            echo '  export SEEKER_SSH_HOST="<IP-адрес>"'
            echo '  export SEEKER_SSH_USER="<username>"'
            echo '  export SEEKER_SSH_KEY="~/.ssh/seeker_bot_deploy"'
            echo ""
            echo "Или добавьте в ~/.ssh/config:"
            echo "  Host seeker-bot"
            echo "      HostName <IP-адрес>"
            echo "      User <username>"
            echo "      IdentityFile ~/.ssh/seeker_bot_deploy"
            exit 1
        fi
    fi

    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SSH_HOST" "echo ok" 2>/dev/null; then
        echo "❌ SSH-соединение не удалось. Проверьте доступ к $SSH_HOST"
        exit 1
    fi
}

# --- Docker compose logs ---
fetch_docker_logs() {
    local container="$1"
    local lines="$2"
    local follow_flag=""
    $FOLLOW && follow_flag="-f"

    if $FOLLOW; then
        ssh "$SSH_HOST" "cd $COMPOSE_DIR && docker compose logs $follow_flag --tail=$lines $container"
    else
        ssh "$SSH_HOST" "cd $COMPOSE_DIR && docker compose logs --tail=$lines $container 2>&1 | head -$lines"
    fi
}

# --- Файловые логи ---
fetch_file_logs() {
    local lines="$1"
    local level="$2"
    local follow_flag=""
    $FOLLOW && follow_flag="-f"

    if [[ -n "$level" ]]; then
        if $FOLLOW; then
            ssh "$SSH_HOST" "tail $follow_flag -n $lines $LOG_DIR/seeker_bot.log | grep -iE '\[$level\]|level=.$level.'" 2>/dev/null
        else
            ssh "$SSH_HOST" "grep -iE '\[$level\]|level=.$level.' $LOG_DIR/seeker_bot.log | tail -n $lines" 2>/dev/null
        fi
    else
        if $FOLLOW; then
            ssh "$SSH_HOST" "tail $follow_flag -n $lines $LOG_DIR/seeker_bot.log"
        else
            ssh "$SSH_HOST" "tail -n $lines $LOG_DIR/seeker_bot.log"
        fi
    fi
}

# --- Статистика ---
fetch_stats() {
    echo "📊 Seeker Bot — статистика логов"
    echo ""

    local total
    total=$(ssh "$SSH_HOST" "wc -l < $LOG_DIR/seeker_bot.log 2>/dev/null || echo 0")
    echo "📝 Всего строк в логе: $total"

    local errors
    errors=$(ssh "$SSH_HOST" "grep -cE 'ERROR|level=.error.' $LOG_DIR/seeker_bot.log 2>/dev/null || echo 0")
    echo "❌ Ошибок всего: $errors"

    local warnings
    warnings=$(ssh "$SSH_HOST" "grep -cE 'WARNING|level=.warning.' $LOG_DIR/seeker_bot.log 2>/dev/null || echo 0")
    echo "⚠️  Предупреждений: $warnings"

    local errors_hour
    errors_hour=$(ssh "$SSH_HOST" "grep -E 'ERROR|level=.error.' $LOG_DIR/seeker_bot.log 2>/dev/null | tail -100 | wc -l")
    echo "🚨 Ошибок за последние 100 строк: $errors_hour"

    echo ""
    echo "📦 Docker контейнеры:"
    ssh "$SSH_HOST" "cd $COMPOSE_DIR && docker compose ps --format 'table {{.Name}}\t{{.Status}}' 2>/dev/null || echo '  (Docker не запущен)'"

    echo ""
    echo "💾 Диск:"
    ssh "$SSH_HOST" "df -h $LOG_DIR 2>/dev/null | tail -1 || echo '  (нет данных)'"

    echo ""
    echo "🔄 Последние источники:"
    ssh "$SSH_HOST" "grep -E 'pipeline_start|pipeline_complete' $LOG_DIR/seeker_bot.log 2>/dev/null | tail -5 || echo '  (нет данных)'"
}

# --- Markdown-отчёт ---
fetch_markdown() {
    local lines="$1"

    echo "# Seeker Bot — Отчёт"
    echo ""

    echo "## Система"
    echo '```'
    ssh "$SSH_HOST" "uname -a && echo '---' && free -h && echo '---' && df -h / | tail -1" 2>/dev/null
    echo '```'
    echo ""

    echo "## Docker"
    echo '```'
    ssh "$SSH_HOST" "cd $COMPOSE_DIR && docker compose ps --format 'table {{.Name}}\t{{.Status}}'" 2>/dev/null
    echo '```'
    echo ""

    echo "## Последние $lines строк лога"
    echo '```'
    ssh "$SSH_HOST" "tail -n $lines $LOG_DIR/seeker_bot.log" 2>/dev/null
    echo '```'
    echo ""

    echo "## Последние ошибки"
    echo '```'
    ssh "$SSH_HOST" "grep -E 'ERROR|level=.error.' $LOG_DIR/seeker_bot.log 2>/dev/null | tail -10" 2>/dev/null || echo "  (нет ошибок)"
    echo '```'
}

# --- Главная ---
main() {
    check_ssh

    if [[ -n "$DOCKER_CONTAINER" ]]; then
        fetch_docker_logs "$DOCKER_CONTAINER" "$LINES"
    elif $STATS; then
        fetch_stats
    elif $MARKDOWN; then
        fetch_markdown "$LINES"
    else
        fetch_file_logs "$LINES" "$LEVEL"
    fi
}

main
