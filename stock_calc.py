"""Stock mínimo y alertas — fórmulas de la hoja "Catálogo de Insumos" del Excel consolidado.

Stock mínimo = CEILING((frecuencia_mensual/30 * tiempo_reposicion_dias) * (1 + factor_seguridad),
                        unidades_por_cambio)
  Redondea hacia arriba al múltiplo exacto del tamaño del set de reposición (unidades_por_cambio).
  Si unidades_por_cambio = 1, equivale a redondear al entero superior.
  Requiere frecuencia, tiempo_reposicion, factor_seguridad (viene de la clase ABC) y
  unidades_por_cambio > 0; si falta alguno, el stock mínimo queda indefinido (None).

Alerta de nivel de stock: "REPONER AHORA" si stock_actual <= stock_minimo, si no "OK".

Alerta de ventana de compra: proyecta la fecha en que el stock caerá al mínimo
(hoy + días restantes al ritmo de consumo mensual/30) y compara el día del mes con
la ventana de facturación SDT-USACH (día 1 al 20). Si el día proyectado cae después
del 20, la alerta es "FUERA DE VENTANA".
"""
import math
from datetime import timedelta

VENTANA_SDT_ULTIMO_DIA = 20


def calcular_stock_minimo(frecuencia_uso_mensual, tiempo_reposicion_dias, factor_seguridad, unidades_por_cambio):
    if (
        frecuencia_uso_mensual is None
        or tiempo_reposicion_dias is None
        or factor_seguridad is None
        or not unidades_por_cambio
    ):
        return None
    bruto = (frecuencia_uso_mensual / 30 * tiempo_reposicion_dias) * (1 + factor_seguridad)
    return math.ceil(bruto / unidades_por_cambio) * unidades_por_cambio


def calcular_alertas(stock_actual, stock_minimo, frecuencia_uso_mensual, hoy):
    """Devuelve dict: alerta_nivel, fecha_proyectada, dia_proyectado, alerta_ventana.
    Los campos de ventana quedan en None si no hay stock_minimo o frecuencia."""
    if stock_minimo is None:
        return {
            "alerta_nivel": None, "fecha_proyectada": None,
            "dia_proyectado": None, "alerta_ventana": None,
        }

    alerta_nivel = "REPONER AHORA" if stock_actual <= stock_minimo else "OK"

    if not frecuencia_uso_mensual:
        return {
            "alerta_nivel": alerta_nivel, "fecha_proyectada": None,
            "dia_proyectado": None, "alerta_ventana": None,
        }

    dias_restantes = max(0.0, (stock_actual - stock_minimo) / (frecuencia_uso_mensual / 30))
    fecha_proyectada = hoy + timedelta(days=dias_restantes)
    dia_proyectado = fecha_proyectada.day
    alerta_ventana = "FUERA DE VENTANA" if dia_proyectado > VENTANA_SDT_ULTIMO_DIA else "DENTRO DE VENTANA"

    return {
        "alerta_nivel": alerta_nivel,
        "fecha_proyectada": fecha_proyectada,
        "dia_proyectado": dia_proyectado,
        "alerta_ventana": alerta_ventana,
    }
