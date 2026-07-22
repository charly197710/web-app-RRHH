import subprocess, os, pathlib, sys

def main():
    out_dir = pathlib.Path("./cvs")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Asumimos que el usuario ya configuró su cuenta con la skill hymalaya
    # Ejecutamos: hymalaya fetch --since 3 --download-attachments --dest ./cvs
    subprocess.run(["himalaya", "fetch", "--since", "3", "--download-attachments", "--dest", str(out_dir)], check=False)

if __name__ == "__main__":
    main()