#!/usr/bin/env bash
# Install himalaya if not present
if ! command -v himalaya &> /dev/null; then
    echo "Himalaya not found, installing..."
    HIMALAYA_VERSION=1.2.0
    curl -L -o /tmp/himalaya.tgz https://github.com/pimalaya/himalaya/releases/download/v${HIMALAYA_VERSION}/himalaya.x86_64-linux.tgz || { echo "Failed to download himalaya"; exit 1; }
    tar -xzf /tmp/himalaya.tgz -C /usr/local/bin himalaya || { echo "Failed to extract himalaya"; exit 1; }
    chmod +x /usr/local/bin/himalaya || { echo "Failed to chmod himalaya"; exit 1; }
    echo "Himalaya installed at $(which himalaya)"
else
    echo "Himalaya already present at $(which himalaya)"
fi
himalaya --version

mkdir -p "$HOME/.config/himalaya"
printf '[account]\nname = "default"\nimap_host = "%s"\nimap_port = %s\nimap_username = "%s"\nimap_password = "%s"\nimap_auth_type = "password"\n' "$HIMALAYA_IMAP_HOST" "$HIMALAYA_IMAP_PORT" "$HIMALAYA_IMAP_USER" "$HIMALAYA_IMAP_PASS" > "$HOME/.config/himalaya/config.toml"

exec gunicorn -b 0.0.0.0:$PORT app:app
