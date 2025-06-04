from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader

# Configuración de Cloudinary
cloudinary.config(
    cloud_name="djo3pubvc",  # ✅ El correcto
    api_key="111981522849654",
    api_secret="PRlmu3nNEFk59lotK6iUd8yZog0"
)

app = Flask(__name__)
app.secret_key = 'clave_secreta'


# Inicializa la base de datos si no existe
def init_db():
    with sqlite3.connect("boletas.db") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS boletas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            fecha TEXT,
            estado TEXT,
            modelo TEXT,
            cantidad INTEGER,
            total REAL,
            notas TEXT,
            imagen TEXT
        )""")


# ⚠️ Asegúrate de llamar init_db aquí para que se ejecute al arrancar el servidor
init_db()

# Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == 'admin' and request.form[
                'clave'] == '1234':
            session['usuario'] = 'admin'
            return redirect(url_for('registrar_boleta'))
        else:
            return render_template('login.html',
                                   error="Credenciales incorrectas")
    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Vista del formulario para registrar boleta
@app.route('/boletas/registrar')
def registrar_boleta():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('registrar.html')


# Guarda la boleta en la BD
@app.route('/registrar', methods=['POST'])
@app.route('/registrar', methods=['POST'])
def guardar_boleta():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    data = request.form
    archivo = request.files.get('imagen')
    imagen_url = ""

    print("📦 Formulario recibido:")
    print("Cliente:", data.get('cliente'))
    print("Archivo adjunto:",
          archivo.filename if archivo else "No se recibió archivo")

    if archivo and archivo.filename != "":
        # Validaciones
        mimetype_permitido = ["image/jpeg", "image/png", "image/webp"]
        if archivo.mimetype not in mimetype_permitido:
            return "❌ Formato no permitido. Usa JPEG, PNG o WEBP", 400

        archivo.seek(0, os.SEEK_END)
        file_size = archivo.tell()
        archivo.seek(0)

        if file_size > 2 * 1024 * 1024:  # 2MB
            return "❌ Imagen muy pesada. Máximo 2MB", 400

        try:
            print("⏫ Subiendo a Cloudinary...")
            resultado = cloudinary.uploader.upload(archivo)
            imagen_url = resultado['secure_url']
            print("✅ Imagen subida:", imagen_url)
        except Exception as e:
            print("❌ Error al subir imagen:", e)
            imagen_url = ""

    with sqlite3.connect("boletas.db") as conn:
        conn.execute(
            """
            INSERT INTO boletas (cliente, fecha, estado, modelo, cantidad, total, notas, imagen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['cliente'], data['fecha'], data['estado'], data['modelo'],
              data['cantidad'], data['total'], data['notas'], imagen_url))

    return redirect(url_for('consultar_boletas'))


# Consulta de boletas
@app.route('/boletas/consultar')
def consultar_boletas():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cliente = request.args.get('cliente', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    fecha_hasta = request.args.get('fecha_hasta', '').strip()
    estado = request.args.get('estado', '').strip()

    query = "SELECT * FROM boletas WHERE 1=1"
    params = []

    if cliente:
        query += " AND cliente LIKE ?"
        params.append(f"%{cliente}%")
    if fecha_desde:
        query += " AND fecha >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        query += " AND fecha <= ?"
        params.append(fecha_hasta)
    if estado:
        query += " AND LOWER(estado) = ?"
        params.append(estado.lower())

    query += " ORDER BY id DESC"

    with sqlite3.connect("boletas.db") as conn:
        boletas = conn.execute(query, params).fetchall()

    return render_template("consultar.html", boletas=boletas)


# Vista de detalle
@app.route('/boleta/<int:id>')
def detalle_boleta(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect("boletas.db") as conn:
        boleta = conn.execute("SELECT * FROM boletas WHERE id = ?",
                              (id, )).fetchone()

    if not boleta:
        return "Boleta no encontrada", 404

    return render_template("detalle.html", boleta=boleta)


# Cambiar estado desde el detalle
@app.route('/boleta/<int:id>/actualizar_estado', methods=['POST'])
def actualizar_estado(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    nuevo_estado = request.form.get('nuevo_estado')

    with sqlite3.connect("boletas.db") as conn:
        conn.execute("UPDATE boletas SET estado = ? WHERE id = ?",
                     (nuevo_estado, id))

    return redirect(url_for('detalle_boleta', id=id))


@app.route('/boleta/<int:id>/eliminar', methods=['POST'])
def eliminar_boleta(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect("boletas.db") as conn:
        conn.execute("DELETE FROM boletas WHERE id = ?", (id, ))

    return redirect(url_for('consultar_boletas'))


# Run
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)
