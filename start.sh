#!/usr/bin/env bash
mkdir -p "$HOME/.config/himalaya"
printf '[account]\nname = "%s"\nimap_host = "%s"\nimap_port = "%s"\nimap_username = "%s"\nimap_password = "%s"\nimap_auth_type = "password"\n' "$HIMALAYA_IMAP_HOST" "$HIMALAYA_IMAP_PORT" "$HIMALAYA_IMAP_USER" "$HIMALAYA_IMAP_PASS" > "$HOME/.config/himalaya/config.toml"
exec gunicorn -b 0.0.0.0:$PORT app:app
