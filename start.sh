#!/usr/bin/env bash
mkdir -p "$HOME/.config/himalaya"
printf '[account]
name = "default"
imap_host = ""
imap_port = 
imap_username = ""
imap_password = ""
imap_auth_type = "password"
' "$HIMALAYA_IMAP_HOST" "$HIMALAYA_IMAP_PORT" "$HIMALAYA_IMAP_USER" "$HIMALAYA_IMAP_PASS" > "$HOME/.config/himalaya/config.toml"
exec gunicorn -b 0.0.0.0:$PORT app:app
