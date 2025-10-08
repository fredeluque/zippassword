# zippassword

Brute-force extractor for ZIP/RAR desde terminal — **uso responsable**.

> ⚠️ **Advertencia legal**: Esta herramienta está diseñada para uso legítimo (recuperar tus archivos) y educativo. No uses esta herramienta para acceder a archivos ajenos sin permiso. El autor no se hace responsable de usos ilícitos.

## Contenido de este README
- Descripción
- Funcionalidad
- Requisitos del sistema
- Instalación
- Añadir WinRAR / 7-Zip al PATH (Windows)
- Uso (ejemplos)
- Opciones disponibles
- Formato de wordlist
- Sugerencias y troubleshooting
- Compatibilidad / notas por SO
- Contribuir
- Licencia

## Descripción
zippassword es un script en Python que intenta recuperar la contraseña de archivos comprimidos (.zip o .rar) mediante:
  - probar una wordlist (fichero .txt con posibles contraseñas, una por línea), y/o
  - realizar una fuerza bruta sobre un charset y longitud indicados.
En Windows el script usa WinRAR o 7‑Zip (si están disponibles) para extraer, lo que evita limitaciones del módulo zipfile de Python (por ejemplo con métodos de compresión o cifrados no soportados).

## Funcionalidad principal
- Probar contraseñas desde un fichero (--wordlist / -W).
- Hacer fuerza bruta con combinaciones (opciones --lower, --upper, --numbers, --special, --custom y --length).
- Extraer el contenido cuando se encuentra la contraseña (usa WinRAR/7z en Windows).
- Mensajes de progreso y estimaciones (ETA).
- Mensajes diagnósticos para ayudar con problemas de compresión/cifrado.

## Requisitos del sistema
- Python 3.8+
- Espacio en disco suficiente para extraer contenidos
- (Opcional pero recomendado en Windows) WinRAR o 7‑Zip instalados y accesibles desde la línea de comandos (en PATH).
- (Opcional) pyzipper y/o rarfile si quieres que Python intente extracciones directamente en entornos no‑Windows (no obligatorio en la versión Windows que usa WinRAR/7z).
- Contenido del requirements.txt sugerido:
  ```bash
  rarfile>=4.0        # opcional (RAR via Python)
  pyzipper>=1.0       # opcional (ZIP con AES desde Python)
Instalación de dependencias (opcional):
  ```bash
  pip install -r requirements.txt
  # o individualmente:
  pip install rarfile pyzipper
```

##Añadir WinRAR o 7‑Zip al PATH (Windows)
- Para que el script pueda invocar rar/WinRAR.exe o 7z:
- Busca la carpeta de instalación:
- WinRAR típico: C:\Program Files\WinRAR o C:\Program Files (x86)\WinRAR
- 7‑Zip típico: C:\Program Files\7-Zip o C:\Program Files (x86)\7-Zip
- Copia la ruta (p. ej. C:\Program Files\WinRAR).
- Abre "Editar las variables de entorno del sistema":
- Pulsa Win + S → escribe Editar las variables de entorno del sistema → Abrir.
- Haz clic en Variables de entorno…
- En Variables del sistema, selecciona Path → Editar… → Nuevo → pega la ruta.
- Acepta y cierra las ventanas.
- Reinicia cualquier terminal o editor (VSCode) para que detecte la nueva variable PATH.
- Verifica en una nueva terminal:
```bash
  where rar
  where winrar
  where 7z
```
## Uso - Ejemplos
```bash
python zippassword.py -o
# o
python zippassword.py --help
```
- Probar una wordlist:
```bash
python zippassword.py -W passwords.txt -e secreto.zip -d salida
```
- Probar wordlist y, si no se encuentra, continuar con fuerza bruta (minúsculas + números, longitud 4):
```bash
python zippassword.py -W passwords.txt -lm -n -L 4 -e secreto.zip -d salida
```
- Force brute con charset personalizado:
```bash
python zippassword.py -c "abc123!@" -L 4 -e secreto.zip -d salida
```
- Mostrar progreso más frecuente (útil para pruebas):
```bash
python zippassword.py -W prueba.txt -e secreto.zip -d salida --show-every 1
```

## Opciones
-o, --options : Mostrar opciones y ejemplos.
-W, --wordlist FILE : Fichero .txt con posibles contraseñas (una por línea). Se prueba antes de la fuerza bruta.
-e, --entrada FILE : Archivo comprimido de entrada (.zip o .rar).
-d, --dest DIR : Carpeta de destino para extracción (por defecto: .).
-lm, --lower : Incluir letras minúsculas a‑z en el charset.
-lM, --upper : Incluir letras MAYÚSCULAS A‑Z.
-n, --numbers : Incluir números 0‑9.
-s, --special : Incluir caracteres especiales (punctuation).
-c, --custom STR : Charset personalizado (si se usa ignora las anteriores).
-L, --length N : Longitud exacta a probar (obligatorio para fuerza bruta).
--show-every N : Actualizar consola cada N intentos (por defecto 200).
-v, --verbose : Salida más detallada.

