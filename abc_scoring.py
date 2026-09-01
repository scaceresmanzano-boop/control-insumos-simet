"""Clasificación ABC multicriterio — pesos AHP + corte por percentil de ranking.

Fórmulas fuente (hoja "Catálogo de Insumos" de Control_Insumos_Consolidado_SIMET-USACH.xlsx):
  Puntaje ponderado = w_costo*norm(costo) + w_frec*norm(frecuencia)
                       + w_impacto*(impacto-1)/4 + w_tr*norm(tiempo_reposicion)
  norm(x) = (x - min) / (max - min) sobre el conjunto de insumos con los 4 criterios
            completos (0 si max == min); impacto operacional usa escala fija 1-5.
  Ranking = orden descendente de puntaje ponderado (empates por menor ID).
  Clase ABC por PERCENTIL DE POSICIÓN en el ranking (no por % acumulado del puntaje):
    - rank <= ROUNDUP(0.20 * n) -> A   (20% superior)
    - rank <= ROUNDUP(0.50 * n) -> B   (siguiente 30%)
    - resto -> C                       (50% restante)
  donde n = cantidad de insumos con los 4 criterios completos.
Insumos con algún criterio en blanco quedan sin puntaje ni clase (None), igual que
la celda vacía en el Excel.
"""
import math

# Pesos AHP del capítulo 4 de la tesis (deben sumar 1.0).
PESOS_DEFECTO = {
    "costo": 0.0411,
    "frecuencia": 0.3129,
    "impacto": 0.5691,
    "tiempo_reposicion": 0.0769,
}

FACTOR_SEGURIDAD_POR_CLASE = {"A": 0.5, "B": 0.3, "C": 0.15}


def _normalizar(valor, minimo, maximo):
    if maximo == minimo:
        return 0.0
    return (valor - minimo) / (maximo - minimo)


def calcular_clasificacion_abc(insumos, pesos=None):
    """insumos: iterable de dicts/Rows con id, costo_unitario, frecuencia_uso_mensual,
    impacto_operacional, tiempo_reposicion_dias.
    Devuelve lista de dicts {id, puntaje_ponderado, clase_abc, factor_seguridad} para
    TODOS los insumos recibidos (valores en None si falta algún criterio)."""
    pesos = pesos or PESOS_DEFECTO
    if abs(sum(pesos.values()) - 1.0) > 1e-6:
        raise ValueError("Los pesos deben sumar 1.0")

    completos = [
        i for i in insumos
        if i["costo_unitario"] is not None
        and i["frecuencia_uso_mensual"] is not None
        and i["impacto_operacional"] is not None
        and i["tiempo_reposicion_dias"] is not None
    ]

    resultados = {
        i["id"]: {"id": i["id"], "puntaje_ponderado": None, "clase_abc": None, "factor_seguridad": None}
        for i in insumos
    }

    if not completos:
        return list(resultados.values())

    costos = [i["costo_unitario"] for i in completos]
    frecs = [i["frecuencia_uso_mensual"] for i in completos]
    trs = [i["tiempo_reposicion_dias"] for i in completos]
    min_c, max_c = min(costos), max(costos)
    min_f, max_f = min(frecs), max(frecs)
    min_t, max_t = min(trs), max(trs)

    puntajes = []
    for i in completos:
        norm_costo = _normalizar(i["costo_unitario"], min_c, max_c)
        norm_frec = _normalizar(i["frecuencia_uso_mensual"], min_f, max_f)
        norm_impacto = (i["impacto_operacional"] - 1) / 4
        norm_tr = _normalizar(i["tiempo_reposicion_dias"], min_t, max_t)
        puntaje = (
            pesos["costo"] * norm_costo
            + pesos["frecuencia"] * norm_frec
            + pesos["impacto"] * norm_impacto
            + pesos["tiempo_reposicion"] * norm_tr
        )
        puntajes.append({"id": i["id"], "puntaje_ponderado": puntaje})

    # Ranking descendente por puntaje (empate: ID más chico primero, estable).
    puntajes.sort(key=lambda p: (-p["puntaje_ponderado"], p["id"]))

    n = len(puntajes)
    umbral_a = math.ceil(0.20 * n)
    umbral_b = math.ceil(0.50 * n)

    for rank, p in enumerate(puntajes, start=1):
        if rank <= umbral_a:
            clase = "A"
        elif rank <= umbral_b:
            clase = "B"
        else:
            clase = "C"
        resultados[p["id"]] = {
            "id": p["id"],
            "puntaje_ponderado": p["puntaje_ponderado"],
            "clase_abc": clase,
            "factor_seguridad": FACTOR_SEGURIDAD_POR_CLASE[clase],
        }

    return list(resultados.values())
