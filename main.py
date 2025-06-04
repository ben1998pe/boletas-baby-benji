
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos
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

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == 'admin' and request.form['clave'] == '1234':
            session['usuario'] = 'admin'
            return redirect(url_for('panel'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect("boletas.db") as conn:
        boletas = conn.execute("SELECT * FROM boletas ORDER BY id DESC").fetchall()
    return render_template('panel.html', boletas=boletas)

@app.route('/registrar', methods=['POST'])
def registrar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    data = request.form
    archivo = request.files['imagen']
    filename = ""
    if archivo and archivo.filename != "":
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo.filename}")
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with sqlite3.connect("boletas.db") as conn:
        conn.execute("INSERT INTO boletas (cliente, fecha, estado, modelo, cantidad, total, notas, imagen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            data['cliente'], data['fecha'], data['estado'], data['modelo'], data['cantidad'], data['total'], data['notas'], filename
        ))
    return redirect(url_for('panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)
