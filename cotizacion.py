from jinja2 import Environment, FileSystemLoader
import subprocess
import csv
import os
import sys
from datetime import datetime


# ---------------------------
# Configurar Jinja2
# ---------------------------
env = Environment(
    loader=FileSystemLoader("."),
    block_start_string="(%",
    block_end_string="%)",
    variable_start_string="((",
    variable_end_string="))",
    comment_start_string="(#",
    comment_end_string="#)"
)

template = env.get_template("plantilla.tex")

# ---------------------------
# Leer ítems desde items.csv
# ---------------------------
items = []
with open("items.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cantidad = int(row["cantidad"])
        precio_unitario = float(row["precio_unitario"])
        items.append({
            "descripcion": row["descripcion"],
            "cantidad": cantidad,
            "precio_unitario": precio_unitario
        })

# ---------------------------
# Calcular totales
# ---------------------------
subtotal = sum(item["cantidad"] * item["precio_unitario"] for item in items)
iva = subtotal * 0.16
total = subtotal + iva

# ---------------------------
# Generar fecha actual
# ---------------------------
fecha_hoy = datetime.today().strftime("%d/%m/%Y")

# ---------------------------
# Manejo de folio automático
# ---------------------------
folio_file = "folio.txt"

if not os.path.exists(folio_file):
    last_folio = 0
else:
    with open(folio_file, "r") as f:
        last_folio = int(f.read().strip())

new_folio = last_folio + 1

# Guardar nuevo folio
with open(folio_file, "w") as f:
    f.write(str(new_folio))

folio_str = f"COT-{new_folio:03d}"  # -> COT-001, COT-002, etc.


# ---------------------------
# Leer datos del cliente desde cliente.csv
# ---------------------------
cliente_nombre = sys.argv[1] if len(sys.argv) > 1 else None
cliente_data = None
id_pedido = sys.argv[2] if len(sys.argv) > 2 else None

with open("cliente.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if cliente_nombre and row["cliente"] == cliente_nombre:
            cliente_data = row
            break

if not cliente_data:
    print("[ERROR] Cliente no encontrado en cliente.csv")
    sys.exit(1)

# ---------------------------
# Datos de la cotización
# ---------------------------
datos = {
    "folio": folio_str,
    "fecha": fecha_hoy,
    "cliente": cliente_data.get("cliente", ""),
    "direccion": cliente_data.get("direccion", ""),
    "direccion_entrega": cliente_data.get("direccion_entrega", ""),
    "fecha_evento": cliente_data.get("fecha_evento", ""),
    "items": items,
    "subtotal": subtotal,
    "iva": iva,
    "total": total,
    "condiciones": "Cotización válida por 15 días. Se requiere anticipo del 50%.",
    "telefono_cliente": cliente_data.get("telefono_cliente", ""),
    "id_pedido": id_pedido
}

# ---------------------------
# Renderizar LaTeX
# ---------------------------
rendered_tex = template.render(datos)

tex_file = "cotizacion.tex"
with open(tex_file, "w", encoding="utf-8") as f:
    f.write(rendered_tex)


# ---------------------------
# Compilar con tectonic
# ---------------------------
try:
    result = subprocess.run(
        ["tectonic", tex_file],
        check=True,
        capture_output=True,
        text=True
    )
    print("[INFO] STDOUT:\n", result.stdout)
    print("[INFO] STDERR:\n", result.stderr)

    if os.path.exists("cotizacion.pdf"):
        os.makedirs("pdfs", exist_ok=True)  # 📂 Asegurar carpeta pdfs
        pdf_name = f"COT-{new_folio:03d}.pdf"
        pdf_path = os.path.join("pdfs", pdf_name)
        os.rename("cotizacion.pdf", pdf_path)
        print(f"[OK] PDF generado: {pdf_path}")
    else:
        print("[ERROR] No se generó el PDF esperado")

except subprocess.CalledProcessError as e:
    print("[ERROR] Error al compilar LaTeX")
    print("----- STDOUT -----")
    print(e.stdout)
    print("----- STDERR -----")
    print(e.stderr)
