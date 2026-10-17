"""Copia a central/contenido/ los archivos de una o más colas locales y arma contenido/cola.json.

Uso:  python preparar_contenido.py <cola1.json> [<cola2.json> ...]
Cada cola es una lista de {fecha, hora, file (ruta local), txt}, como las de PUBLICACIONES.
No borra lo ya publicado: agrega y reemplaza por (fecha, hora).
"""
import json
import os
import re
import shutil
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.abspath(__file__))
CONT = os.path.join(RAIZ, 'contenido')
MEDIA = os.path.join(CONT, 'media')


def limpio(nombre):
    s = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s)


def main(rutas):
    os.makedirs(MEDIA, exist_ok=True)
    ruta_cola = os.path.join(CONT, 'cola.json')
    cola = {}
    if os.path.exists(ruta_cola):
        for p in json.load(open(ruta_cola, encoding='utf-8')):
            cola[(p['fecha'], p['hora'])] = p
    for r in rutas:
        for p in json.load(open(r, encoding='utf-8')):
            carpeta = limpio(os.path.basename(os.path.dirname(p['file'])))
            destino = os.path.join(MEDIA, carpeta, limpio(os.path.basename(p['file'])))
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copy2(p['file'], destino)
            rel = os.path.relpath(destino, CONT).replace('\\', '/')
            cola[(p['fecha'], p['hora'])] = dict(fecha=p['fecha'], hora=p['hora'], archivo=rel, txt=p['txt'].rstrip())
    orden = sorted(cola.values(), key=lambda p: (p['fecha'][6:], p['fecha'][3:5], p['fecha'][:2], p['hora']))
    json.dump(orden, open(ruta_cola, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(orden)} publicaciones en contenido/cola.json')


if __name__ == '__main__':
    main(sys.argv[1:])
