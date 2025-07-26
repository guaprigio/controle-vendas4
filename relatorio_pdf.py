from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime
import sqlite3
from app import app

@app.route('/relatorio_pdf/<int:cliente_id>')
def relatorio_pdf(cliente_id):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    cursor.execute(
        "SELECT p.nome, v.quantidade, v.data_venda "
        "FROM vendas v "
        "JOIN produtos p ON v.produto_id = p.id "
        "WHERE v.cliente_id = ? AND strftime('%m', v.data_venda) = ? AND strftime('%Y', v.data_venda) = ?",
        (cliente_id, f"{mes_atual:02d}", str(ano_atual))
    )

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
    for produto, quantidade, data_venda in vendas:
        c.drawString(50, y, produto)
        c.drawString(250, y, str(quantidade))
        c.drawString(400, y, data_venda)
        y -= 20

    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='relatorio.pdf', mimetype='application/pdf')
