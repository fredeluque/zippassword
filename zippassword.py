#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
zippassword.py
Brute-force extractor for ZIP/RAR from terminal (Windows).
Soporta fuerza bruta y wordlists usando WinRAR/7-Zip.
"""

import argparse
import itertools
import os
import sys
import time
import string
import threading
from datetime import timedelta
import subprocess
import shutil

ASCII_HEADER = """
\033[32m  ___________ _____   _____ _____            _____ _  ________ _____  
 |___  /_   _|  __ \ / ____|  __ \     /\   / ____| |/ /  ____|  __ \ 
    / /  | | | |__) | |    | |__) |   /  \ | |    | ' /| |__  | |__) |
   / /   | | |  ___/| |    |  _  /   / /\ \| |    |  < |  __| |  _  / 
  / /__ _| |_| |    | |____| | \ \  / ____ \ |____| . \| |____| | \ \ 
 /_____|_____|_|     \_____|_|  \_\/_/    \_\_____|_|\_\______|_|  \_\\
\033[0m
\033[2m 
  Z I P   P A S S W O R D   —  Fuerza Bruta / Wordlist
  Recuperación de archivos (ZIP / RAR) — Uso responsable
    by: @fredeluque\033[0m
"""

# ---------------------------
# Helpers
# ---------------------------
def human(n):
    return f"{n:,}"

def format_td(seconds):
    if seconds is None or seconds == float('inf'):
        return "∞"
    try:
        return str(timedelta(seconds=int(seconds)))
    except Exception:
        return "??:??:??"

# ---------------------------
# Extracción usando WinRAR / 7z
# ---------------------------
import shutil
import subprocess

def try_extract(archivo, destino, clave):
    """
    Intentar extraer usando la mejor herramienta disponible:
      - Para .zip: preferir 7z o WinRAR
      - Para .rar: preferir rar (o WinRAR) luego 7z
    Devuelve True si la extracción tuvo éxito, False si la contraseña es incorrecta,
    y False además si no se pudo extraer (se imprimirá depuración).
    """
    archivo = os.path.abspath(archivo)
    destino = os.path.abspath(destino)
    os.makedirs(destino, exist_ok=True)

    # candidatos (rutas comunes incluidas)
    rar_candidates = [
        "rar", "Rar.exe", "WinRAR.exe",
        r"C:\Program Files\WinRAR\Rar.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\Rar.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe"
    ]
    sevenz_candidates = [
        "7z", "7z.exe",
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe"
    ]
    winrar_candidates = [
        "WinRAR.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe"
    ]

    def find_executable(candidates):
        for c in candidates:
            if os.path.isabs(c) and os.path.isfile(c):
                return c
            path = shutil.which(c)
            if path:
                return path
        return None

    def run_cmd(cmd):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
            out = (proc.stdout or "") + (proc.stderr or "")
            return out.lower(), proc.returncode
        except FileNotFoundError:
            return None, None
        except Exception as e:
            return f"exception: {e}", None

    # patrones en español/inglés para éxito / contraseña incorrecta
    success_patterns = ["all ok", "done", "everything is ok", "everything is ok", "extracción correcta", "completado", "archivo extraído", "extraction complete"]
    wrong_password_patterns = ["wrong password", "wrong password for file", "can not open encrypted archive", "contraseña incorrecta", "contraseña errónea", "contraseña equivocada", "wrong password"]

    ext = os.path.splitext(archivo)[1].lower()

    # lista de intentos según la extensión (orden de preferencia)
    attempts = []
    if ext == ".zip":
        # preferir 7z, luego WinRAR (que suele manejar ambos), finalmente rar (menos ideal para zip)
        attempts = [
            ("7z", sevenz_candidates, lambda exe: [exe, "x", f"-p{clave}", archivo, f"-o{destino}", "-y"]),
            ("winrar", winrar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
            ("rar", rar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
        ]
    elif ext == ".rar":
        # preferir rar (o WinRAR), luego 7z
        attempts = [
            ("rar", rar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
            ("winrar", winrar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
            ("7z", sevenz_candidates, lambda exe: [exe, "x", f"-p{clave}", archivo, f"-o{destino}", "-y"]),
        ]
    else:
        # archivo sin extensión reconocida: probar 7z y WinRAR y rar
        attempts = [
            ("7z", sevenz_candidates, lambda exe: [exe, "x", f"-p{clave}", archivo, f"-o{destino}", "-y"]),
            ("winrar", winrar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
            ("rar", rar_candidates, lambda exe: [exe, "x", f"-p{clave}", "-y", archivo, destino]),
        ]

    # Intentar cada herramienta en orden
    for name, candidates, build_cmd in attempts:
        exe = find_executable(candidates)
        if not exe:
            # no disponible, saltar
            continue
        cmd = build_cmd(exe)
        out, rc = run_cmd(cmd)
        if out is None:
            # fallo al ejecutar (p.ej. no encontrada), seguir probando
            continue
        # buscar patrones de éxito o fallo
        for pat in success_patterns:
            if pat in out:
                return True
        for pat in wrong_password_patterns:
            if pat in out:
                return False
        # si no hay patrones claros, imprimimos depuración y seguimos probando otras herramientas
        print(f"\n[Depuración: herramienta {name} ({exe}) devolvió sin patrones claros]\nreturncode={rc}\n{out}\n")
        # seguir al siguiente intento

    # Si hemos llegado aquí no se pudo extraer con ninguna herramienta
    print("⚠️  No se pudo extraer el archivo con las herramientas disponibles (o contraseña incorrecta).")
    print("Comprueba que tienes 7-Zip o WinRAR instalados y en PATH, o pásame la salida de depuración anterior.")
    return False

# ---------------------------
# Ataque por wordlist
# ---------------------------
def wordlist_attack(archivo, destino, wordlist_path, stop_event, show_every=200):
    if not os.path.isfile(wordlist_path):
        print(f"Error: wordlist no encontrada: {wordlist_path}")
        return None, 0

    with open(wordlist_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"\nComenzando ataque por wordlist: {wordlist_path} (Total: {total_lines})")
    start = time.time()
    tried = 0

    for line_no, raw in enumerate(lines, start=1):
        if stop_event.is_set():
            print("\nDetenido por el usuario.")
            return None, tried

        clave = raw.strip()
        if not clave:
            continue
        tried += 1

        if tried % show_every == 0 or tried == 1:
            elapsed = time.time() - start
            speed = tried / (elapsed if elapsed > 0 else 1)
            pct = (line_no / total_lines) * 100
            print(f"\rProbadas: {human(line_no)}/{human(total_lines)} ({pct:.2f}%) | {speed:.1f} pwd/s | último: {clave}", end="", flush=True)

        try:
            if try_extract(archivo, destino, clave):
                elapsed = time.time() - start
                print("\n\n✅ ¡Contraseña encontrada en wordlist!")
                print(f"   Contraseña: {clave}")
                print(f"   Intentos: {human(tried)}  Tiempo: {format_td(elapsed)}  Velocidad: {speed:.1f} pwd/s")
                return clave, tried
        except KeyboardInterrupt:
            stop_event.set()
            print("\n\n✋ Interrupción por teclado (Ctrl+C). Finalizando...")
            return None, tried

    print("\n\n✖️  No se encontró la contraseña en la wordlist.")
    return None, tried

# ---------------------------
# Fuerza bruta
# ---------------------------
def brute_force(archivo, destino, charset, length, stop_event, show_every=200):
    total = len(charset) ** length
    print(f"\nComenzando fuerza bruta: charset={len(charset)}, longitud={length}, total={human(total)}")
    start = time.time()
    tried = 0

    for combo in itertools.product(charset, repeat=length):
        if stop_event.is_set():
            print("\nDetenido por el usuario.")
            return None, tried
        clave = "".join(combo)
        tried += 1

        if tried % show_every == 0 or tried == 1:
            elapsed = time.time() - start
            speed = tried / (elapsed if elapsed > 0 else 1)
            pct = (tried / total) * 100
            print(f"\rProbadas: {human(tried)}/{human(total)} ({pct:.2f}%) | {speed:.1f} pwd/s | último: {clave}", end="", flush=True)

        if try_extract(archivo, destino, clave):
            elapsed = time.time() - start
            print("\n\n✅ ¡Contraseña encontrada por fuerza bruta!")
            print(f"   Contraseña: {clave}")
            print(f"   Intentos: {human(tried)}  Tiempo: {format_td(elapsed)}  Velocidad: {speed:.1f} pwd/s")
            return clave, tried

    print("\n\n✖️  No se encontró la contraseña en fuerza bruta.")
    return None, tried

# ---------------------------
# Parser y main
# ---------------------------
def build_argparser():
    p = argparse.ArgumentParser(description="ZIP/RAR Password Recovery (Windows, Brute-force + Wordlist)")
    p.add_argument("-o", "--options", action="store_true", help="Mostrar opciones y ejemplos")
    p.add_argument("-lm", "--lower", action="store_true", help="Incluir minúsculas a-z")
    p.add_argument("-lM", "--upper", action="store_true", help="Incluir MAYÚSCULAS A-Z")
    p.add_argument("-n", "--numbers", action="store_true", help="Incluir números 0-9")
    p.add_argument("-s", "--special", action="store_true", help="Incluir caracteres especiales")
    p.add_argument("-c", "--custom", type=str, default=None, help="Charset personalizado")
    p.add_argument("-L", "--length", type=int, default=4, help="Longitud exacta para fuerza bruta")
    p.add_argument("-e", "--entrada", type=str, required=False, help=".zip o .rar")
    p.add_argument("-d", "--dest", type=str, default=".", help="Directorio de extracción")
    p.add_argument("-W", "--wordlist", type=str, default=None, help="Fichero .txt con posibles contraseñas")
    p.add_argument("--show-every", type=int, default=200, help="Actualizar consola cada N intentos")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    return p

def print_options_and_examples():
    txt = """
Opciones disponibles:
  -o, --options       Mostrar este mensaje
  -lm, --lower        Incluir minúsculas a-z
  -lM, --upper        Incluir MAYÚSCULAS A-Z
  -n, --numbers       Incluir números 0-9
  -s, --special       Incluir caracteres especiales
  -c, --custom <str>  Charset personalizado
  -L, --length <n>    Longitud exacta (para fuerza bruta)
  -e, --entrada <f>   Archivo .zip/.rar
  -d, --dest <dir>    Directorio de extracción
  -W, --wordlist FILE Probar contraseñas desde un fichero .txt
  --show-every <n>    Actualizar consola cada n intentos
  -v, --verbose       Verbose

Ejemplos:
  ./zippassword.py -W passwords.txt -e secreto.zip -d salida
  ./zippassword.py -lm -n -L 4 -W passwords.txt -e secreto.zip -d salida
"""
    print(txt)

def main():
    print(ASCII_HEADER)
    parser = build_argparser()
    args = parser.parse_args()

    if args.options and not args.entrada:
        print_options_and_examples()
        return

    if not args.entrada:
        parser.print_help()
        return

    archivo = args.entrada
    destino = args.dest

    if not os.path.exists(archivo):
        print(f"Error: archivo de entrada no encontrado: {archivo}")
        sys.exit(1)
    if not os.path.isdir(destino):
        os.makedirs(destino, exist_ok=True)
        print(f"Creando directorio destino: {destino}")

    stop_event = threading.Event()

    # Ataque por wordlist
    if args.wordlist:
        clave, tried = wordlist_attack(archivo, destino, args.wordlist, stop_event, show_every=args.show_every)
        if clave or stop_event.is_set():
            return

    # Preparar charset fuerza bruta
    charset = ""
    if args.custom:
        charset = args.custom
    else:
        if args.lower:
            charset += string.ascii_lowercase
        if args.upper:
            charset += string.ascii_uppercase
        if args.numbers:
            charset += string.digits
        if args.special:
            charset += string.punctuation

    if not charset:
        print("No se seleccionó charset para fuerza bruta. Usa -lm -lM -n -s o -c.")
        return

    if args.length < 1:
        print("Longitud debe ser >= 1")
        return

    brute_force(archivo, destino, charset, args.length, stop_event, show_every=args.show_every)

if __name__ == "__main__":
    main()
