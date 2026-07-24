#!/usr/bin/env bash

# Add user's local bin to PATH (where pip installs scripts)
export PATH="$PATH:$HOME/.local/bin"

# Ensure config directory exists
mkdir -p "$HOME/.config/himalaya"

# Write config from environment variables
cat > "$HOME/.config/himalaya/config.toml" <<'EOF'
[account]
name = "default"
imap_host = "$HIMALAYA_IMAP_HOST"
imap_port = $HIMALAYA_IMAP_PORT
imap_username = "$HIMALAYA_IMAP_USER"
imap_password = "$HIMALAYA_IMAP_PASS"
auth_type = "password"
EOF
exec gunicorn -b 0.0.0.0:$PORT app:app
