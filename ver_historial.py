import streamlit as st
import csv
import os
import json
import datetime
import calendar
from collections import defaultdict

PEDIDOS_FILE = "pedidos.csv"

def leer_csv(file, fieldnames=None):
    if not os.path.exists(file):
        return []
    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# =======================
# Interfaz Streamlit
# =======================
st.title("📜 Historial y Agenda de Pedidos")

# Leer pedidos
pedidos = leer_csv(PEDIDOS_FILE, fieldnames=[
    "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total"
])

if not pedidos:
    st.warning("⚠️ No hay pedidos registrados todavía.")
    st.stop()

# Convertir fechas
for p in pedidos:
    try:
        p["fecha_creacion_dt"] = datetime.datetime.strptime(p["fecha_creacion"], "%d-%m-%Y %H:%M:%S")
    except:
        p["fecha_creacion_dt"] = None

    try:
        p["fecha_evento_dt"] = datetime.datetime.strptime(p["fecha_evento"], "%d-%m-%Y")
    except:
        p["fecha_evento_dt"] = None

# =======================
# Fechas de referencia
# =======================
hoy = datetime.date.today()
inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())   # lunes
fin_semana = inicio_semana + datetime.timedelta(days=6)       # domingo

# =======================
# Sección 1: Eventos de esta semana
# =======================
st.header("📅 Eventos de esta semana")
eventos_semana = [
    p for p in pedidos
    if p["fecha_evento_dt"] and inicio_semana <= p["fecha_evento_dt"].date() <= fin_semana
]

if eventos_semana:
    for p in eventos_semana:
        with st.expander(f"📝 {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
            st.write(f"📅 Creado: {p['fecha_creacion']}")
            st.write(f"💰 Total: **${p['total']}**")
            try:
                st.table(json.loads(p["items"]))
            except:
                st.text(p["items"])
else:
    st.info("✅ No hay eventos programados para esta semana.")

# =======================
# Sección 2: Resumen mensual de eventos pasados
# =======================
st.header("📊 Resumen por mes (eventos pasados)")
pasados = [p for p in pedidos if p["fecha_evento_dt"] and p["fecha_evento_dt"].date() < hoy]

if pasados:
    resumen_mensual = defaultdict(float)
    for p in pasados:
        mes = p["fecha_evento_dt"].strftime("%B %Y")  # Ej: Agosto 2025
        resumen_mensual[mes] += float(p["total"])

    for mes, total in resumen_mensual.items():
        st.write(f"📌 {mes}: **${total:.2f}** en eventos")
else:
    st.info("Aún no hay eventos pasados registrados.")

# =======================
# Sección 3: Eventos futuros (después de esta semana)
# =======================
st.header("🚀 Eventos futuros")
futuros = [p for p in pedidos if p["fecha_evento_dt"] and p["fecha_evento_dt"].date() > fin_semana]

if futuros:
    for p in futuros:
        with st.expander(f"📝 {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
            st.write(f"📅 Creado: {p['fecha_creacion']}")
            st.write(f"💰 Total: **${p['total']}**")
            try:
                st.table(json.loads(p["items"]))
            except:
                st.text(p["items"])
else:
    st.info("⚠️ No hay eventos futuros programados más allá de esta semana.")

# =======================
# Sección 4: Buscar cliente
# =======================
st.header("🔍 Buscar cliente")

nombre_busqueda = st.text_input("Escribe el nombre del cliente:")

if nombre_busqueda:
    resultados = [p for p in pedidos if nombre_busqueda.lower() in p["nombre_cliente"].lower()]

    if resultados:
        st.success(f"✅ Se encontraron {len(resultados)} pedidos para '{nombre_busqueda}'")

        for p in resultados:
            tipo = "📅 Futuro" if p["fecha_evento_dt"] and p["fecha_evento_dt"].date() >= hoy else "⏳ Pasado"
            with st.expander(f"{tipo} - {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
                st.write(f"📅 Creado: {p['fecha_creacion']}")
                st.write(f"💰 Total: **${p['total']}**")
                try:
                    st.table(json.loads(p["items"]))
                except:
                    st.text(p["items"])
    else:
        st.warning(f"⚠️ No se encontraron pedidos para '{nombre_busqueda}'")


# =======================
# Sección 5: Buscar por ID de pedido
# =======================
st.header("🔎 Buscar por ID de pedido")

id_busqueda = st.text_input("Escribe el ID del pedido:")

if id_busqueda:
    resultados_id = [p for p in pedidos if p["id_pedido"] == id_busqueda]

    if resultados_id:
        st.success(f"✅ Se encontró el pedido con ID '{id_busqueda}'")

        for p in resultados_id:
            tipo = "📅 Futuro" if p["fecha_evento_dt"] and p["fecha_evento_dt"].date() >= hoy else "⏳ Pasado"
            with st.expander(f"{tipo} - {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
                st.write(f"📅 Creado: {p['fecha_creacion']}")
                st.write(f"💰 Total: **${p['total']}**")
                try:
                    st.table(json.loads(p["items"]))
                except:
                    st.text(p["items"])
    else:
        st.warning(f"⚠️ No se encontró ningún pedido con el ID '{id_busqueda}'")