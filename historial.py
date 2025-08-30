import csv
import os
import uuid
import datetime
import json

PEDIDOS_FILE = "pedidos.csv"

def leer_csv(file, fieldnames=None):
    if not os.path.exists(file):
        if fieldnames:
            with open(file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return []
    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def escribir_csv(file, data, fieldnames):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def guardar_pedido(cliente, items):
    """
    Guarda un pedido en pedidos.csv
    - cliente: dict con datos del cliente
    - items: lista de ítems (dicts con descripcion, cantidad, precio_unitario)
    """

    pedidos = leer_csv(PEDIDOS_FILE, fieldnames=[
        "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total"
    ])

    total = sum(float(it["precio_unitario"]) * int(it["cantidad"]) for it in items)

    pedido = {
        "id_pedido": str(uuid.uuid4()),
        "fecha_creacion": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "id_cliente": cliente.get("id",""),
        "nombre_cliente": cliente.get("cliente",""),
        "fecha_evento": cliente.get("fecha_evento",""),
        "items": json.dumps(items, ensure_ascii=False),
        "total": f"{total:.2f}"
    }

    pedidos.append(pedido)
    escribir_csv(PEDIDOS_FILE, pedidos, fieldnames=[
        "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total"
    ])

    return pedido
