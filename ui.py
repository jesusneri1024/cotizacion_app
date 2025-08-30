import streamlit as st
import csv
import subprocess
import os
import datetime
import uuid
import historial 


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

# Cargar clientes (con ID incluido)
clientes = leer_csv(
    CLIENTE_FILE,
    fieldnames=["id", "cliente", "direccion", "direccion_entrega", "fecha_evento", "telefono_cliente"]
)

# 🔧 Normalizar: asegurar que todos los clientes tengan un ID
for c in clientes:
    if not c.get("id"):  
        c["id"] = str(uuid.uuid4())

# Reescribir archivo para que quede limpio y consistente
if clientes:
    escribir_csv(CLIENTE_FILE, clientes, fieldnames=["id", "cliente", "direccion", "direccion_entrega", "fecha_evento", "telefono_cliente"])

nombres_clientes = [c["cliente"] for c in clientes] if clientes else []

# Cliente vacío por defecto
cliente = {
    "id": "",
    "cliente": "",
    "direccion": "",
    "direccion_entrega": "",
    "fecha_evento": "",
    "telefono_cliente": ""
}

# Selección de modo
modo = st.radio("¿Qué quieres hacer?", ["➕ Nuevo cliente", "✏️ Editar cliente existente"])

if modo == "✏️ Editar cliente existente" and nombres_clientes:
    # Campo de búsqueda
    busqueda = st.text_input("🔍 Buscar cliente (nombre, teléfono o dirección)")

    if busqueda:
        resultados = [
            c for c in clientes
            if busqueda.lower() in c["cliente"].lower()
            or busqueda.lower() in c["telefono_cliente"].lower()
            or busqueda.lower() in c["direccion"].lower()
        ]
    else:
        resultados = clientes

    if resultados:
        # Crear etiquetas descriptivas seguras con .get()
        opciones = {
            f'{c.get("cliente","")} - {c.get("telefono_cliente","")} - {c.get("direccion","")} (ID: {c.get("id","N/A")})': c
            for c in resultados
        }
        seleccionado = st.selectbox("Selecciona cliente", list(opciones.keys()))
        cliente = opciones[seleccionado]
    else:
        st.warning("⚠️ No se encontraron clientes con ese criterio")

# Campos de entrada
cliente["cliente"] = st.text_input("Nombre del cliente", cliente.get("cliente", ""))
cliente["direccion"] = st.text_input("Dirección", cliente.get("direccion", ""))

# Fecha del evento
if cliente.get("fecha_evento"):
    try:
        fecha_guardada = datetime.datetime.strptime(cliente["fecha_evento"], "%d-%m-%Y").date()
    except:
        fecha_guardada = datetime.date.today()
else:
    fecha_guardada = datetime.date.today()

fecha_evento = st.date_input("📅 Fecha del evento", value=fecha_guardada)
cliente["fecha_evento"] = fecha_evento.strftime("%d-%m-%Y")

# Mostrar también en formato largo (ejemplo: viernes 29 agosto 2025)
fecha_larga = fecha_evento.strftime("%A %d %B %Y").capitalize()
st.caption(f"📌 Fecha seleccionada: {fecha_larga}")

cliente["telefono_cliente"] = st.text_input("Teléfono", cliente.get("telefono_cliente", ""))

# Guardar cliente
if st.button("💾 Guardar cliente"):
    # Validar duplicados (nombre + teléfono)
    duplicado = next(
        (c for c in clientes if c["cliente"].strip().lower() == cliente["cliente"].strip().lower()
         and c["telefono_cliente"].strip() == cliente["telefono_cliente"].strip()
         and c["id"] != cliente.get("id", "")),  # Ignora si es el mismo cliente que estamos editando
        None
    )

    if duplicado:
        st.error("⚠️ Ya existe un cliente con el mismo nombre y teléfono. No se puede duplicar.")
    else:
        if not cliente.get("id"):  
            # Asignar UUID en lugar de secuencial (más robusto)
            import uuid
            cliente["id"] = str(uuid.uuid4())

        existe = False
        for i, c in enumerate(clientes):
            if c["id"] == cliente["id"]:
                clientes[i] = cliente
                existe = True
                break
        if not existe:
            clientes.append(cliente)

        escribir_csv(
            CLIENTE_FILE,
            clientes,
            fieldnames=["id", "cliente", "direccion", "direccion_entrega", "fecha_evento", "telefono_cliente"]
        )
        st.success("✅ Cliente guardado/actualizado")


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
    # 1. Guardar pedido y obtener el ID
    pedido = historial.guardar_pedido(cliente, new_items)

    # 2. Llamar al script de generación de PDF pasando cliente + id_pedido
    result = subprocess.run(
        ["python", "cotizacion.py", cliente["cliente"], pedido["id_pedido"]],
        capture_output=True, text=True
    )
    
    # 3. Validar resultado
    if result.returncode == 0:
        st.success("✅ Cotización generada")
        st.success(f"📌 Pedido guardado (ID: {pedido['id_pedido']})")
    else:
        st.error(f"❌ Error: {result.stderr}")
