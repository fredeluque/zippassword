# zippassword

Brute-force extractor for ZIP/RAR desde terminal — **uso responsable**.

> ⚠️ **Advertencia legal**: Esta herramienta está diseñada para uso legítimo (recuperar tus archivos) y educativo. No uses esta herramienta para acceder a archivos ajenos sin permiso. El autor no se hace responsable de usos ilícitos.

## Qué hace
Script en Python que prueba combinaciones de contraseñas para intentar extraer un archivo ZIP o RAR.

## Requisitos
- Python 3.8+
- (Opcional) `pip install -r requirements.txt` para soporte RAR (`rarfile`).

## Ejemplos de uso
```bash
./zippassword.py -lm -lM -n -s -e secreto.zip -d salida -L 4
./zippassword.py --lower --numbers --entrada=archivo.zip --length=3
