#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
zippassword.py
Brute-force extractor for ZIP/RAR from terminal.
Usage examples:
  ./zippassword.py -o                    # muestra opciones / ayuda breve
  ./zippassword.py -lm -lM -n -s -e file.zip -d outdir -L 4
  ./zippassword.py --lower --upper --numbers --special --entrada file.zip --dest outdir --length 4
"""

import argparse
import itertools
import os
import sys
import time
import zipfile
import threading
from math import ceil

try:
    import rarfile
    RAR_AVAILABLE = True
except Exception:
    RAR_AVAILABLE = False

import string
from datetime import timedelta

# ---------------------------
# ASCII HEADER (bonito)
# ---------------------------
ASCII_HEADER = r"""
  ______  _  ______                       _               
 |___  / | |/ / ___|  ___  ___  ___  ___ | |__   ___ _ __ 
    / /  | ' / |  _  / __|/ _ \/ __|/ _ \| '_ \ / _ \ '__|
   / /_  | . \ |_| | \__ \  __/\__ \ (_) | |_) |  __/ |   
  /____| |_|\_\____| |___/\___||___/\___/|_.__/ \___|_|   
                                                         
    Descompresor por Fuerza Bruta — Uso responsable
"""

# ---------------------------
# Helpers
# ---------------------------
def human(n):
    """Formatea número con separadores de miles."""
    return f"{n:,}"

def format_td(seconds):
    if seconds == float('inf') or seconds is None:
        return "∞"
    try:
        return str(timedelta(seconds=int(seconds)))
    except Exception:
        return "??:??:??"

# ---------------------------
# Intentar extracción
# ---------------------------
def try_extract(archivo, destino, clave):
    """Devuelve True si la contraseña fue correcta y extracción ha sido posible."""
    try:
        if archivo.lower().endswith(".zip"):
            with zipfile.ZipFile(archivo) as zf:
                # zipfile necesita bytes para pwd
                zf.extractall(destino, pwd=clave.encode('utf-8'))
            return True
        elif archivo.lower().endswith(".rar"):
            if not RAR_AVAILABLE:
                return False
            with rarfile.RarFile(archivo) as rf:
                rf.extractall(destino, pwd=clave)
            return True
    except Exception:
        return False
    return False

# ---------------------------
# Brute-force main
# ---------------------------
def brute_force(archivo, destino, charset, length, stop_event, show_every=200):
    total = len(charset) ** length
    print(f"\nComenzando fuerza bruta: charset={len(charset)} chars, longitud={length}, total={human(total)}\n")
    start = time.time()
    tried = 0
    last_time = start
    samples_per_sec = 0.0

    # early check: avoid extremely grandes sin confirmación (solo advertencia)
    if total > 100_000_000:
        print("⚠️  Atención: el número total de combinaciones es muy grande. Esto puede tardar muchísimo.")
        print("    (Presiona Ctrl+C para cancelar)\n")

    it = itertools.product(charset, repeat=length)
    try:
        for combo in it:
            if stop_event.is_set():
                print("\nDetenido por el usuario.")
                return None, tried
            clave = "".join(combo)
            tried += 1

            # medir velocidad cada cierto número
            if tried % show_every == 0 or tried == 1:
                now = time.time()
                elapsed = now - start
                samples_per_sec = tried / (elapsed if elapsed > 0 else 1)
                remaining = total - tried
                eta = remaining / (samples_per_sec if samples_per_sec > 0 else 1)
                pct = (tried / total) * 100
                print(f"\rProbadas: {human(tried)} / {human(total)} ({pct:.2f}%) | {samples_per_sec:.1f} pwd/s | ETA {format_td(eta)} | último: {clave}", end="", flush=True)

            # intentar extracción
            if try_extract(archivo, destino, clave):
                elapsed = time.time() - start
                print("\n\n✅ ¡Contraseña encontrada!")
                print(f"   Contraseña: {clave}")
                print(f"   Intentos: {human(tried)}  Tiempo: {format_td(elapsed)}  Velocidad: {samples_per_sec:.1f} pwd/s")
                return clave, tried

        print("\n\n✖️  No se encontró la contraseña en el espacio de búsqueda indicado.")
        return None, tried

    except KeyboardInterrupt:
        stop_event.set()
        print("\n\n✋ Interrupción por teclado (Ctrl+C). Finalizando...")
        return None, tried

# ---------------------------
# CLI / Main
# ---------------------------
def build_argparser():
    p = argparse.ArgumentParser(
        prog="zippassword.py",
        description="Herramienta de fuerza bruta para extraer ZIP/RAR (uso responsable)."
    )

    # Options flags inspired by your sample: -lm (letras minusculas), -lM (letras Mayúsculas), -n (números), -s (especiales), -o (show options)
    p.add_argument("-o", "--options", action="store_true",
                   help="Mostrar lista de opciones disponibles y ejemplos.")
    p.add_argument("-lm", "--lower", action="store_true",
                   help="Incluir letras minúsculas a-z en el charset.")
    p.add_argument("-lM", "--upper", action="store_true",
                   help="Incluir letras MAYÚSCULAS A-Z en el charset.")
    p.add_argument("-n", "--numbers", action="store_true",
                   help="Incluir números 0-9 en el charset.")
    p.add_argument("-s", "--special", action="store_true",
                   help="Incluir caracteres especiales (string.punctuation) en el charset.")
    p.add_argument("-c", "--custom", type=str, default=None,
                   help="Charset personalizado (cadena de caracteres). Si se usa, ignora las opciones anteriores.")
    p.add_argument("-L", "--length", type=int, default=4,
                   help="Longitud exacta de la contraseña a probar (ej: 4). Obligatorio para fuerza bruta.")
    p.add_argument("-e", "--entrada", type=str, required=False,
                   help="Archivo comprimido de entrada (.zip o .rar).")
    p.add_argument("-d", "--dest", type=str, default=".",
                   help="Carpeta de destino donde extraer si se encuentra la contraseña. (por defecto: directorio actual)")
    p.add_argument("--show-every", type=int, default=200,
                   help="Frecuencia de actualización en consola (cada N intentos).")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Salida más detallada.")
    return p

def print_options_and_examples():
    txt = """
Opciones disponibles:
  -o, --options       Mostrar este mensaje de opciones/ejemplos.
  -lm, --lower        Incluir letras minúsculas a-z.
  -lM, --upper        Incluir letras MAYÚSCULAS A-Z.
  -n, --numbers       Incluir números 0-9.
  -s, --special       Incluir caracteres especiales (puntuación).
  -c, --custom <str>  Charset personalizado (si se usa ignora los anteriores).
  -L, --length <n>    Longitud exacta de la contraseña a probar (obligatorio para fuerza bruta).
  -e, --entrada <f>   Archivo comprimido de entrada (.zip o .rar).
  -d, --dest <dir>    Carpeta de destino donde extraer (por defecto: .).
  --show-every <n>    Actualizar consola cada n intentos.
  -v, --verbose       Verbose.

Ejemplos:
  ./zippassword.py -lm -lM -n -s -e secreto.zip -d salida -L 4
  ./zippassword.py --lower --numbers --entrada=archivo.zip --length=3
"""
    print(txt)

def main():
    print(ASCII_HEADER)
    parser = build_argparser()
    args = parser.parse_args()

    # if user asked to see options
    if args.options and not args.entrada:
        print_options_and_examples()
        return

    # If no entrada provided, print help (or options) and exit
    if not args.entrada:
        parser.print_help()
        print("\nEjemplo rápido: ./zippassword.py -lm -n -e fichero.zip -d ./out -L 4\n")
        return

    archivo = args.entrada
    destino = args.dest

    if not os.path.exists(archivo):
        print(f"Error: archivo de entrada no encontrado: {archivo}")
        sys.exit(1)
    if not os.path.isdir(destino):
        try:
            os.makedirs(destino, exist_ok=True)
            print(f"Creando directorio destino: {destino}")
        except Exception as e:
            print(f"Error creando directorio destino: {e}")
            sys.exit(1)

    # Construir charset
    if args.custom:
        charset = args.custom
    else:
        charset = ""
        if args.lower:
            charset += string.ascii_lowercase
        if args.upper:
            charset += string.ascii_uppercase
        if args.numbers:
            charset += string.digits
        if args.special:
            charset += string.punctuation

    if not charset:
        print("Error: no se ha seleccionado ningún conjunto de caracteres. Usa -lm -lM -n -s o -c para especificarlo.")
        sys.exit(1)

    length = args.length
    if length < 1:
        print("Error: longitud debe ser >= 1.")
        sys.exit(1)

    total = len(charset) ** length
    print(f"Archivo: {archivo}")
    print(f"Destino: {destino}")
    print(f"Charset ({len(charset)}): {charset if args.verbose else ''.join(sorted(set(charset)))}")
    print(f"Longitud: {length}  => Total combinaciones: {human(total)}\n")

    # Warn about rar availability
    if archivo.lower().endswith(".rar") and not RAR_AVAILABLE:
        print("⚠️  Archivo RAR detectado pero la librería 'rarfile' no está disponible o no se puede usar.")
        print("    Instala 'pip install rarfile' y asegúrate de tener 'unrar' o 'rar' en PATH.")
        print("    Abortando.")
        sys.exit(1)

    # Safety/legal note
    print("Nota: Asegúrate de tener permiso para acceder a este archivo. No uses esta herramienta de forma ilegal.\n")

    # confirm if very big?
    if total > 10_000_000:
        print("AVISO: el espacio de búsqueda es muy grande y puede tardar MUCHO tiempo.")
        print("Puedes cancelar en cualquier momento con Ctrl+C.\n")

    stop_event = threading.Event()
    clave, intentos = brute_force(archivo, destino, charset, length, stop_event, show_every=args.show_every)

    if clave:
        print(f"\nSe extrajo correctamente con la contraseña: {clave}")
    else:
        print(f"\nNo se obtuvo la contraseña (se probaron {human(intentos)} combinaciones).")

if __name__ == "__main__":
    main()