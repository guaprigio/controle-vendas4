from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)

# --- Banco de Dados ---
def criar_banco():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            data TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id),
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Rotas ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        cursor.execute("INSERT INTO clientes (nome) VALUES (?)", (nome,))
        conn.commit()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/produtos', methods=['GET', 'POST'])
def produtos():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
        conn.commit()
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()
    cursor.execute("SELECT id, nome FROM produtos")
    produtos = cursor.fetchall()

    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        data = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO vendas (cliente_id, produto_id, quantidade, data) VALUES (?, ?, ?, ?)",
                       (cliente_id, produto_id, quantidade, data))
        conn.commit()

    cursor.execute("""
        SELECT v.id, c.nome, p.nome, v.quantidade, v.data
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data DESC
    """)
    todas_vendas = cursor.fetchall()
    conn.close()
    return render_template('vendas.html', clientes=clientes, produtos=produtos, vendas=todas_vendas)

@app.route('/relatorios')
def relatorios():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.nome, p.nome, SUM(v.quantidade) AS total_vendido
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        GROUP BY c.id, p.nome
        ORDER BY total_vendido DESC
    """)
    relatorio = cursor.fetchall()
    conn.close()
    return render_template('relatorios.html', relatorio=relatorio)

@app.route('/relatorio_pdf/<int:cliente_id>')
def relatorio_pdf(cliente_id):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    cursor.execute('''
        SELECT p.nome, v.quantidade, v.data
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.cliente_id = ? AND strftime('%m', v.data) = ? AND strftime('%Y', v.data) = ?
    ''', (cliente_id, f'{mes_atual:02d}', str(ano_atual)))
    vendas = cursor.fetchall()
    conn.close()

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, f"Relatório de Vendas - Cliente ID {cliente_id}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, "Produto")
    c.drawString(250, height - 100, "Quantidade")
    c.drawString(400, height - 100, "Data")

    y = height - 120
    c.setFont("Helvetica", 12)
    for produto, quantidade, data in vendas:
        c.drawString(50, y, produto)
        c.drawString(250, y, str(quantidade))
        c.drawString(400, y, data)
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name='relatorio.pdf', mimetype='application/pdf')

# --- Início da aplicação ---
if __name__ == '__main__':
    criar_banco()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
