import streamlit as st
import csv
import os
import json
import datetime
from collections import defaultdict

PEDIDOS_FILE = "pedidos.csv"

# =======================
# Funciones auxiliares
# =======================
def leer_csv(file, fieldnames=None):
    if not os.path.exists(file):
        return []
    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def guardar_csv(file, data, fieldnames):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            clean_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(clean_row)

# =======================
# Interfaz Streamlit
# =======================
st.title("📜 Historial y Agenda de Pedidos")

# Leer pedidos
pedidos = leer_csv(PEDIDOS_FILE, fieldnames=[
    "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
])

# Si faltan estados, se asignan como "cotizacion"
for p in pedidos:
    if "estado" not in p or not p["estado"]:
        p["estado"] = "cotizacion"

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
    if p["estado"] == "confirmado" and p["fecha_evento_dt"] and inicio_semana <= p["fecha_evento_dt"].date() <= fin_semana
]

if eventos_semana:
    for p in eventos_semana:
        with st.expander(f"📝 {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
            st.write(f"📅 Creado: {p['fecha_creacion']}")
            st.write(f"💰 Total: **${p['total']}**")
            st.write(f"📌 Estado: **{p['estado']}**")
            try:
                st.table(json.loads(p["items"]))
            except:
                st.text(p["items"])

            if p["estado"] == "confirmado":
                if st.button(f"❌ Cancelar evento {p['id_pedido']}", key=f"cancel_semana_{p['id_pedido']}"):
                    p["estado"] = "cotizacion"
                    guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                        "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                    ])
                    st.warning(f"El pedido {p['id_pedido']} ha sido regresado a cotización ⚠️")
                    st.rerun()
else:
    st.info("✅ No hay eventos programados para esta semana.")

# =======================
# Sección 2: Resumen mensual de eventos pasados
# =======================
st.header("📊 Resumen por mes (eventos pasados)")
pasados = [
    p for p in pedidos
    if p["estado"] in ["confirmado", "recogido"]
    and p["fecha_evento_dt"]
    and p["fecha_evento_dt"].date() < hoy
]

if pasados:
    # Agrupar por mes
    pedidos_por_mes = defaultdict(list)
    totales_por_mes = defaultdict(float)

    for p in pasados:
        mes = p["fecha_evento_dt"].strftime("%B %Y")
        pedidos_por_mes[mes].append(p)
        totales_por_mes[mes] += float(p["total"])

    # Mostrar mes por mes
    for mes in sorted(pedidos_por_mes.keys(), key=lambda x: datetime.datetime.strptime(x, "%B %Y"), reverse=True):
        st.subheader(f"📌 {mes} — Total: **${totales_por_mes[mes]:.2f}**")

        for p in pedidos_por_mes[mes]:
            with st.expander(f"⏳ {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
                st.write(f"📅 Creado: {p['fecha_creacion']}")
                st.write(f"💰 Total: **${p['total']}**")
                st.write(f"📌 Estado: **{p['estado']}**")
                try:
                    st.table(json.loads(p["items"]))
                except:
                    st.text(p["items"])

                if p["estado"] == "confirmado":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"❌ Cancelar evento {p['id_pedido']}", key=f"cancel_pasado_{p['id_pedido']}"):
                            p["estado"] = "cotizacion"
                            guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                                "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                            ])
                            st.warning(f"El pedido {p['id_pedido']} ha sido regresado a cotización ⚠️")
                            st.rerun()
                    with col2:
                        if st.button(f"📦 Marcar como recogido {p['id_pedido']}", key=f"recoger_{p['id_pedido']}"):
                            p["estado"] = "recogido"
                            guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                                "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                            ])
                            st.success(f"El pedido {p['id_pedido']} ha sido marcado como recogido 📦✅")
                            st.rerun()

                elif p["estado"] == "recogido":
                    st.success("📦 Este pedido ya fue recogido. No se puede cancelar ni modificar.")
else:
    st.info("Aún no hay eventos pasados registrados.")


# =======================
# Sección 3: Eventos futuros (después de esta semana)
# =======================
st.header("🚀 Eventos futuros")
futuros = [p for p in pedidos if p["estado"] == "confirmado" and p["fecha_evento_dt"] and p["fecha_evento_dt"].date() > fin_semana]

if futuros:
    for p in futuros:
        with st.expander(f"📝 {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
            st.write(f"📅 Creado: {p['fecha_creacion']}")
            st.write(f"💰 Total: **${p['total']}**")
            st.write(f"📌 Estado: **{p['estado']}**")
            try:
                st.table(json.loads(p["items"]))
            except:
                st.text(p["items"])

            if p["estado"] == "confirmado":
                if st.button(f"❌ Cancelar evento {p['id_pedido']}", key=f"cancel_futuro_{p['id_pedido']}"):
                    p["estado"] = "cotizacion"
                    guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                        "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                    ])
                    st.warning(f"El pedido {p['id_pedido']} ha sido regresado a cotización ⚠️")
                    st.rerun()
else:
    st.info("⚠️ No hay eventos futuros programados más allá de esta semana.")

# =======================
# Sección 4: Buscar cliente (con autocompletado)
# =======================
st.header("🔍 Buscar cliente")

# Lista de todos los nombres de cliente
nombres_clientes = [p["nombre_cliente"] for p in pedidos]
nombres_clientes_unicos = list(set(nombres_clientes))

# Autocompletado para búsqueda de cliente
nombre_busqueda = st.selectbox(
    "Escribe o selecciona el nombre del cliente:",
    nombres_clientes_unicos,
    key="cliente_autocomplete",
)

if nombre_busqueda:
    resultados = [p for p in pedidos if nombre_busqueda.lower() in p["nombre_cliente"].lower()]

    if resultados:
        st.success(f"✅ Se encontraron {len(resultados)} pedidos para '{nombre_busqueda}'")

        for p in resultados:
            tipo = "📅 Futuro" if p["fecha_evento_dt"] and p["fecha_evento_dt"].date() >= hoy else "⏳ Pasado"
            with st.expander(f"{tipo} - {p['nombre_cliente']} - {p['fecha_evento']} (Pedido {p['id_pedido']})"):
                st.write(f"📅 Creado: {p['fecha_creacion']}")
                st.write(f"💰 Total: **${p['total']}**")
                st.write(f"📌 Estado: **{p['estado']}**")
                try:
                    st.table(json.loads(p["items"]))
                except:
                    st.text(p["items"])

                if p["estado"] == "cotizacion":
                    if st.button(f"✅ Confirmar pedido {p['id_pedido']}", key=f"conf_nombre_{p['id_pedido']}"):
                        p["estado"] = "confirmado"
                        guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                            "id_pedido", "fecha_creacion", "id_cliente", "nombre_cliente", "fecha_evento", "items", "total", "estado"
                        ])
                        st.success(f"El pedido {p['id_pedido']} ha sido confirmado como evento 🎉")
                        st.rerun()

                elif p["estado"] == "confirmado":
                    if st.button(f"❌ Cancelar evento {p['id_pedido']}", key=f"cancel_nombre_{p['id_pedido']}"):
                        p["estado"] = "cotizacion"
                        guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                            "id_pedido", "fecha_creacion", "id_cliente", "nombre_cliente", "fecha_evento", "items", "total", "estado"
                        ])
                        st.warning(f"El pedido {p['id_pedido']} ha sido regresado a cotización ⚠️")
                        st.rerun()

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
                st.write(f"📌 Estado: **{p['estado']}**")
                try:
                    st.table(json.loads(p["items"]))
                except:
                    st.text(p["items"])

                if p["estado"] == "cotizacion":
                    if st.button(f"✅ Confirmar pedido {p['id_pedido']}", key=f"conf_id_{p['id_pedido']}"):
                        p["estado"] = "confirmado"
                        guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                            "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                        ])
                        st.success(f"El pedido {p['id_pedido']} ha sido confirmado como evento 🎉")
                        st.rerun()

                elif p["estado"] == "confirmado":
                    if st.button(f"❌ Cancelar evento {p['id_pedido']}", key=f"cancel_id_{p['id_pedido']}"):
                        p["estado"] = "cotizacion"
                        guardar_csv(PEDIDOS_FILE, pedidos, fieldnames=[
                            "id_pedido","fecha_creacion","id_cliente","nombre_cliente","fecha_evento","items","total","estado"
                        ])
                        st.warning(f"El pedido {p['id_pedido']} ha sido regresado a cotización ⚠️")
                        st.rerun()
    else:
        st.warning(f"⚠️ No se encontró ningún pedido con el ID '{id_busqueda}'")
