"""Genera etiquetas con código de barras (Code128) para pegar en los insumos,
compaginadas en hojas tamaño carta/A4 listas para imprimir (PDF)."""
from io import BytesIO

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

DPI = 150
PAGINA_ANCHO = int(210 / 25.4 * DPI)   # A4 horizontal (mm -> px)
PAGINA_ALTO = int(297 / 25.4 * DPI)
MARGEN = 40
COLUMNAS = 3
FILAS = 7
CELDA_ANCHO = (PAGINA_ANCHO - 2 * MARGEN) // COLUMNAS
CELDA_ALTO = (PAGINA_ALTO - 2 * MARGEN) // FILAS


def _fuente(tamano):
    try:
        return ImageFont.truetype("arial.ttf", tamano)
    except OSError:
        return ImageFont.load_default()


def _etiqueta(nombre, codigo):
    celda = Image.new("RGB", (CELDA_ANCHO, CELDA_ALTO), "white")
    draw = ImageDraw.Draw(celda)

    bc = barcode.get("code128", codigo, writer=ImageWriter())
    buf = BytesIO()
    bc.write(buf, options={"write_text": False, "module_height": 9.0, "quiet_zone": 1.5})
    buf.seek(0)
    barcode_img = Image.open(buf).convert("RGB")

    escala = (CELDA_ANCHO - 10) / barcode_img.width
    barcode_img = barcode_img.resize(
        (int(barcode_img.width * escala), min(int(barcode_img.height * escala), CELDA_ALTO - 60))
    )

    nombre_corto = nombre if len(nombre) <= 40 else nombre[:37] + "..."
    fuente_nombre = _fuente(13)
    fuente_codigo = _fuente(12)

    draw.text((CELDA_ANCHO / 2, 6), nombre_corto, font=fuente_nombre, fill="black", anchor="ma")
    barcode_y = 28
    celda.paste(barcode_img, ((CELDA_ANCHO - barcode_img.width) // 2, barcode_y))
    draw.text(
        (CELDA_ANCHO / 2, barcode_y + barcode_img.height + 4),
        codigo, font=fuente_codigo, fill="black", anchor="ma",
    )
    draw.rectangle([0, 0, CELDA_ANCHO - 1, CELDA_ALTO - 1], outline="lightgray")
    return celda


def generar_pdf_etiquetas(insumos):
    """insumos: iterable de dicts/Rows con 'nombre' y 'codigo' (se omiten los sin código).
    Devuelve los bytes de un PDF con una etiqueta por insumo, en hojas A4."""
    items = [i for i in insumos if i["codigo"]]
    if not items:
        return None

    paginas = []
    pagina = None
    for idx, item in enumerate(items):
        pos_en_pagina = idx % (COLUMNAS * FILAS)
        if pos_en_pagina == 0:
            pagina = Image.new("RGB", (PAGINA_ANCHO, PAGINA_ALTO), "white")
            paginas.append(pagina)
        fila, col = divmod(pos_en_pagina, COLUMNAS)
        x = MARGEN + col * CELDA_ANCHO
        y = MARGEN + fila * CELDA_ALTO
        pagina.paste(_etiqueta(item["nombre"], item["codigo"]), (x, y))

    buffer = BytesIO()
    paginas[0].save(buffer, format="PDF", save_all=True, append_images=paginas[1:])
    return buffer.getvalue()
