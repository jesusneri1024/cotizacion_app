from jinja2 import Environment, FileSystemLoader
import subprocess
import csv
import os
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
cliente_data = {}
with open("cliente.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    cliente_data = next(reader)  # Tomamos la primera fila del archivo

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
    "telefono_cliente": cliente_data.get("telefono_cliente", "")
}

# ---------------------------
# Renderizar LaTeX
# ---------------------------
rendered_tex = template.render(datos)

tex_file = "cotizacion.tex"
with open(tex_file, "w") as f:
    f.write(rendered_tex)

# ---------------------------
# Compilar con tectonic
# ---------------------------
try:
    subprocess.run(["tectonic", tex_file], check=True)

    # Renombrar el PDF final con el folio
    if os.path.exists("cotizacion.pdf"):
        pdf_name = f"{folio_str}.pdf"
        os.rename("cotizacion.pdf", pdf_name)
        print(f"✅ PDF generado: {pdf_name}")
    else:
        print("❌ No se generó el PDF esperado")

except subprocess.CalledProcessError as e:
    print("❌ Error al compilar LaTeX:", e)
