import streamlit as st
import csv
import subprocess
import os
import datetime


ITEMS_FILE = "items.csv"
CLIENTE_FILE = "cliente.csv"


# -------------------------
# Funciones utilitarias
# -------------------------
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


# -------------------------
# UI Streamlit
# -------------------------
st.title("🧾 Editor de Cotizaciones")


# =======================
# Sección Cliente
# =======================
st.header("📌 Datos del Cliente")
cliente_data = leer_csv(CLIENTE_FILE, fieldnames=["cliente", "direccion", "direccion_entrega", "fecha_evento", "telefono_cliente"])

if cliente_data:
    cliente = cliente_data[0]
else:
    cliente = {
        "cliente": "",
        "direccion": "",
        "direccion_entrega": "",
        "fecha_evento": "",
        "telefono_cliente": ""
    }

cliente["cliente"] = st.text_input("Nombre del cliente", cliente.get("cliente", ""))
cliente["direccion"] = st.text_input("Dirección", cliente.get("direccion", ""))
# cliente["direccion_entrega"] = st.text_input("Dirección de entrega", cliente.get("direccion_entrega", ""))


#cliente["fecha_evento"] = st.text_input("Fecha del evento", cliente.get("fecha_evento", ""))

# Fecha por defecto: si ya existe en el CSV, la usamos; si no, hoy
if cliente.get("fecha_evento"):
    try:
        fecha_guardada = datetime.datetime.strptime(cliente["fecha_evento"], "%d-%m-%Y").date()
    except:
        fecha_guardada = datetime.date.today()
else:
    fecha_guardada = datetime.date.today()

# Calendario interactivo
fecha_evento = st.date_input("📅 Fecha del evento", value=fecha_guardada)

# Guardamos en texto en formato dd-mm-aaaa
cliente["fecha_evento"] = fecha_evento.strftime("%d-%m-%Y")




cliente["telefono_cliente"] = st.text_input("Teléfono", cliente.get("telefono_cliente", ""))

if st.button("💾 Guardar cliente"):
    escribir_csv(CLIENTE_FILE, [cliente], fieldnames=cliente.keys())
    st.success("✅ Cliente actualizado")


# =======================
# Sección Ítems
# =======================
st.header("📋 Ítems de la cotización")

# Cargar ítems
items = leer_csv(ITEMS_FILE, fieldnames=["descripcion", "cantidad", "precio_unitario"])

if not items:  # aseguramos que haya al menos 1
    items = [{"descripcion": "", "cantidad": "1", "precio_unitario": "0"}]

# Guardamos número dinámico de ítems en sesión
if "num_items" not in st.session_state:
    st.session_state.num_items = len(items)

# Botones de control
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Agregar ítem"):
        st.session_state.num_items += 1
with col2:
    if st.button("➖ Quitar ítem") and st.session_state.num_items > 1:
        st.session_state.num_items -= 1

new_items = []
for i in range(st.session_state.num_items):
    st.subheader(f"Ítem {i+1}")
    if i < len(items):
        item = items[i]
    else:
        item = {"descripcion": "", "cantidad": "1", "precio_unitario": "0"}

    descripcion = st.text_input("Descripción", item["descripcion"], key=f"desc_{i}")
    cantidad = st.number_input("Cantidad", min_value=1, value=int(item["cantidad"]), key=f"cant_{i}")
    precio = st.number_input("Precio unitario", min_value=0.0, value=float(item["precio_unitario"]), key=f"precio_{i}")

    new_items.append({
        "descripcion": descripcion,
        "cantidad": str(cantidad),
        "precio_unitario": str(precio)
    })

if st.button("💾 Guardar ítems"):
    escribir_csv(ITEMS_FILE, new_items, fieldnames=["descripcion", "cantidad", "precio_unitario"])
    st.success("✅ Ítems actualizados")


# =======================
# Generar PDF
# =======================
st.header("⚙️ Exportar")
if st.button("📄 Generar PDF"):
    result = subprocess.run(["python", "cotizacion.py"], capture_output=True, text=True)
    if result.returncode == 0:
        st.success("✅ Cotización generada")
    else:
        st.error(f"❌ Error: {result.stderr}")
