import subprocess, os, pathlib, sys

def main():
    # Ensure config directory exists
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "himalaya")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.toml")
    # Write config if not already present (or overwrite)
    with open(config_path, "w") as f:
        f.write(f'''[account]
name = "default"
imap_host = "{os.environ.get('HIMALAYA_IMAP_HOST', '')}"
imap_port = {os.environ.get('HIMALAYA_IMAP_PORT', '')}
imap_username = "{os.environ.get('HIMALAYA_IMAP_USER', '')}"
imap_password = "{os.environ.get('HIMALAYA_IMAP_PASS', '')}"
auth_type = "password"
''')
    out_dir = pathlib.Path("./cvs")
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["himalaya", "fetch", "--since", "3", "--download-attachments", "--dest", str(out_dir)], check=False)

if __name__ == "__main__":
    main()
