#!/usr/bin/env bash
mkdir -p "$HOME/.config/himalaya"
cat > "$HOME/.config/himalaya/config.toml" <<EOF
[[account]]
name = "default"
imap_host = "$HIMALAYA_IMAP_HOST"
imap_port = $HIMALAYA_IMAP_PORT
imap_username = "$HIMALAYA_IMAP_USER"
imap_password = "$HIMALAYA_IMAP_PASS"
imap_auth_type = "password"
EOF
exec gunicorn -b 0.0.0.0:$PORT app:app