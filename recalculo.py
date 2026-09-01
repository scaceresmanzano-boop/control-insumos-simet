"""Recalcula, para todo el catálogo, la clasificación ABC y el stock mínimo derivado,
y guarda ambos resultados. Se llama después de cualquier edición que pueda afectarlos
(agregar insumo, editar criterios ABC, editar unidades por cambio, etc.)."""
from abc_scoring import calcular_clasificacion_abc
from stock_calc import calcular_stock_minimo

import db


def recalcular_catalogo(conn):
    insumos = db.list_insumos(conn)
    clasificacion = calcular_clasificacion_abc(insumos)
    por_id = {i["id"]: i for i in insumos}

    resultados = []
    for c in clasificacion:
        insumo = por_id[c["id"]]
        stock_minimo = calcular_stock_minimo(
            insumo["frecuencia_uso_mensual"],
            insumo["tiempo_reposicion_dias"],
            c["factor_seguridad"],
            insumo["unidades_por_cambio"],
        )
        resultados.append({
            "id": c["id"],
            "puntaje_ponderado": c["puntaje_ponderado"],
            "clase_abc": c["clase_abc"],
            "stock_minimo": stock_minimo,
        })

    db.update_scores_masivo(conn, resultados)
    return resultados
