"""Publicador en la nube de Eurochimo: Facebook (página) + Instagram, sin depender del PC.

Lee contenido/cola.json (lista de {fecha "dd/mm/aaaa", hora "14"|"18", archivo, txt}) y publica
lo que ya venció y aún no figura en contenido/publicados.json. Pensado para correr cada 15 min
en GitHub Actions; también se puede probar en el PC con --simular.

Variables de entorno (secretos de GitHub, nunca en el código):
  META_PAGE_ID, META_PAGE_TOKEN   página de Facebook "Eurochimo" y su token de página (larga duración)
  IG_USER_ID                      cuenta de Instagram profesional vinculada (europachina.cl)
  MEDIA_BASE_URL                  URL pública donde están los archivos de contenido/ (p. ej. raw de GitHub)

Uso:  python publicar.py [--simular] [--ahora "dd/mm/aaaa HH:MM"]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

RAIZ = os.path.dirname(os.path.abspath(__file__))
COLA = os.path.join(RAIZ, 'contenido', 'cola.json')
HECHOS = os.path.join(RAIZ, 'contenido', 'publicados.json')
TZ = ZoneInfo('America/Santiago')
GRAPH = 'https://graph.facebook.com/v21.0'
VENTANA = timedelta(hours=3)  # no publicar algo que se atrasó más de esto (evita ráfagas tras una caída)


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return defecto


def clave(p):
    return f"{p['fecha']} {p['hora']} {p['archivo']}"


def guardar(hechos):
    with open(HECHOS, 'w', encoding='utf-8') as f:
        json.dump(hechos, f, ensure_ascii=False, indent=1)


def vencidas(cola, hechos, ahora):
    out = []
    for p in cola:
        hora = p['hora'] if ':' in p['hora'] else f"{p['hora']}:00"  # "14" o "12:40"
        cuando = datetime.strptime(f"{p['fecha']} {hora}", '%d/%m/%Y %H:%M').replace(tzinfo=TZ)
        completa = 'instagram' in hechos.get(clave(p), {})
        if not completa and cuando <= ahora < cuando + VENTANA:
            out.append(p)
    return out


def graph(metodo, ruta, **params):
    r = requests.request(metodo, f'{GRAPH}/{ruta}', data=params, timeout=120)
    j = r.json()
    if r.status_code >= 400 or 'error' in j:
        raise RuntimeError(f'{ruta}: {j.get("error", j)}')
    return j


def token_pagina():
    """El secreto puede ser el token del usuario del sistema: de él se obtiene el token de la página."""
    if not os.environ.get('_TOKEN_PAGINA'):
        j = requests.get(f"{GRAPH}/{os.environ['META_PAGE_ID']}",
                         params={'fields': 'access_token', 'access_token': os.environ['META_PAGE_TOKEN']},
                         timeout=60).json()
        os.environ['_TOKEN_PAGINA'] = j.get('access_token') or os.environ['META_PAGE_TOKEN']
    return os.environ['_TOKEN_PAGINA']


def publicar_facebook(p, url, es_video):
    pid, tok = os.environ['META_PAGE_ID'], token_pagina()
    if es_video:
        return graph('POST', f'{pid}/videos', file_url=url, description=p['txt'], access_token=tok)['id']
    return graph('POST', f'{pid}/photos', url=url, caption=p['txt'], access_token=tok)['id']


def id_instagram():
    """IG_USER_ID si está definido; si no, la cuenta de Instagram vinculada a la página."""
    if os.environ.get('IG_USER_ID'):
        return os.environ['IG_USER_ID']
    j = requests.get(f"{GRAPH}/{os.environ['META_PAGE_ID']}",
                     params={'fields': 'instagram_business_account', 'access_token': os.environ['META_PAGE_TOKEN']},
                     timeout=60).json()
    if 'instagram_business_account' not in j:
        raise RuntimeError(f'La página no tiene Instagram vinculado: {j}')
    os.environ['IG_USER_ID'] = j['instagram_business_account']['id']
    return os.environ['IG_USER_ID']


def publicar_instagram(p, url, es_video):
    ig, tok = id_instagram(), os.environ['META_PAGE_TOKEN']
    datos = {'caption': p['txt'], 'access_token': tok}
    if es_video:
        datos.update(media_type='REELS', video_url=url, share_to_feed='true')
    else:
        datos.update(image_url=url)
    cont = graph('POST', f'{ig}/media', **datos)['id']
    for _ in range(40):  # los reels tardan en procesarse
        estado = requests.get(f'{GRAPH}/{cont}', params={'fields': 'status_code', 'access_token': tok}, timeout=60).json()
        if estado.get('status_code') == 'FINISHED':
            break
        if estado.get('status_code') == 'ERROR':
            raise RuntimeError(f'Instagram rechazó el archivo: {estado}')
        time.sleep(15)
    return graph('POST', f'{ig}/media_publish', creation_id=cont, access_token=tok)['id']


def verificar():
    """Prueba los accesos sin publicar nada: página, token de página e Instagram vinculado."""
    tok = token_pagina()
    pag = requests.get(f"{GRAPH}/{os.environ['META_PAGE_ID']}", params={'fields': 'name', 'access_token': tok}, timeout=60).json()
    if 'error' in pag:
        raise RuntimeError(f'Página: {pag["error"]}')
    print(f"Página OK: {pag['name']} (token de página {'obtenido' if tok != os.environ['META_PAGE_TOKEN'] else 'NO obtenido'})")
    ig = id_instagram()
    cuenta = requests.get(f'{GRAPH}/{ig}', params={'fields': 'username', 'access_token': os.environ['META_PAGE_TOKEN']}, timeout=60).json()
    if 'error' in cuenta:
        raise RuntimeError(f'Instagram: {cuenta["error"]}')
    print(f"Instagram OK: @{cuenta['username']} (id {ig})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--simular', action='store_true', help='solo muestra qué publicaría')
    ap.add_argument('--ahora', help='fecha/hora a simular, "dd/mm/aaaa HH:MM"')
    ap.add_argument('--verificar', action='store_true', help='prueba los accesos a Meta sin publicar')
    a = ap.parse_args()
    if a.verificar:
        verificar()
        return
    ahora = (datetime.strptime(a.ahora, '%d/%m/%Y %H:%M').replace(tzinfo=TZ) if a.ahora
             else datetime.now(TZ))
    cola, hechos = cargar(COLA, []), cargar(HECHOS, {})
    pendientes = vencidas(cola, hechos, ahora)
    print(f'{ahora:%d/%m/%Y %H:%M} — {len(pendientes)} publicación(es) por hacer')
    base = os.environ.get('MEDIA_BASE_URL', '').rstrip('/')
    errores = 0
    for p in pendientes:
        es_video = p['archivo'].lower().endswith('.mp4')
        url = f"{base}/{quote(p['archivo'])}"
        print(f"  → {p['fecha']} {p['hora']} h {p['archivo']} ({'reel' if es_video else 'imagen'})")
        if a.simular:
            continue
        reg = hechos.setdefault(clave(p), {})
        try:
            # se guarda cada red apenas sale, para que un reintento no duplique la que ya se publicó
            if 'facebook' not in reg:
                reg['facebook'] = publicar_facebook(p, url, es_video)
                guardar(hechos)
            if 'instagram' not in reg:
                reg['instagram'] = publicar_instagram(p, url, es_video)
            reg['hora'] = datetime.now(TZ).isoformat()
            guardar(hechos)
            print(f"    publicado (FB {reg['facebook']}, IG {reg['instagram']})")
        except Exception as e:  # sigue con las demás y deja el error visible en el log
            errores += 1
            print(f'    ERROR: {e}')
    sys.exit(1 if errores else 0)


if __name__ == '__main__':
    main()
