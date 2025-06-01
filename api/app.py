from flask import Flask, request, jsonify
import pymysql
from datetime import datetime
from flasgger import Swagger, swag_from
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
import joblib
import numpy as np

modelo_risco = joblib.load("modelo_risco_queimada.pkl")
rotulos = {
    0: 'baixo',
    1: 'moderado',
    2: 'alto'
}

app = Flask(__name__)
template = {
    "swagger": "2.0",
    "info": {
        "title": "API Sentinela da Mata",
        "description": "API para registro de leituras ambientais e alertas de risco de queimada.",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"]
}
swagger = Swagger(app, template=template)

# CONFIGURAÇÕES DO MYSQL
def get_connection():
    return pymysql.connect(
        host='192.185.217.47',
        user='bsconsul_global_solution',
        password='Padr@ao321',
        database='bsconsul_global_solution',
        cursorclass=pymysql.cursors.DictCursor
    )

# FUNÇÃO DE ENVIO DE EMAIL
def enviar_emails_alerta(destinatarios, risco, dados):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "drdosan@gmail.com"
    smtp_pass = "Padr@ao321"

    assunto = f"[ALERTA] Risco de Queimada: {risco.upper()}"
    corpo_html = f"""
        <html>
        <body>
            <h2>⚠️ Alerta de Queimada ({risco.upper()})</h2>
            <p><strong>Temperatura:</strong> {dados['temperatura']}°C</p>
            <p><strong>Umidade:</strong> {dados['umidade']}%</p>
            <p><strong>Fumaça:</strong> {dados['fumaca']}</p>
            <p><strong>Data:</strong> {dados['data_hora']}</p>
        </body>
        </html>
    """

    for dest in destinatarios:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = smtp_user
        msg["To"] = dest['email']
        msg.attach(MIMEText(corpo_html, "html"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, dest['email'], msg.as_string())
            print(f"✅ E-mail enviado para {dest['email']}")
        except Exception as e:
            print(f"❌ Erro ao enviar para {dest['email']}: {e}")

# ================== LEITURAS E ALERTAS ==================

@app.route('/leituras', methods=['POST'])
@swag_from({
    'tags': ['Leitura Sensor'],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'schema': {
            'properties': {
                'temperatura': {'type': 'number'},
                'umidade': {'type': 'number'},
                'fumaca': {'type': 'integer'}
            },
            'required': ['temperatura', 'umidade', 'fumaca']
        }
    }],
    'responses': {201: {'description': 'Leitura registrada com sucesso'}}
})
def create_leitura():
    data = request.json
    temperatura = data['temperatura']
    umidade = data['umidade']
    fumaca = data['fumaca']

    # Classificação de risco baseada em regras manuais
    if temperatura > 45 and umidade < 30 and fumaca > 2000:
        risco = 'alto'
    elif temperatura > 40 and umidade < 40 and fumaca > 1500:
        risco = 'moderado'
    else:
        risco = 'baixo'

    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            # Verifica se já há um alerta do mesmo tipo nos últimos 15 minutos
            cur.execute("""
                SELECT COUNT(*) AS total FROM alertas
                WHERE tipo = %s AND data_alerta >= NOW() - INTERVAL 15 MINUTE
            """, (risco,))
            resultado = cur.fetchone()
            alerta_recente = resultado['total'] > 0

            # Registra leitura
            cur.execute("""
                INSERT INTO leituras (temperatura, umidade, fumaca, risco)
                VALUES (%s, %s, %s, %s)
            """, (temperatura, umidade, fumaca, risco))
            leitura_id = cur.lastrowid

            if risco in ('moderado', 'alto') and not alerta_recente:
                mensagem = f"Risco de queimada: {risco.upper()}"
                cur.execute("""
                    INSERT INTO alertas (leitura_id, tipo, mensagem)
                    VALUES (%s, %s, %s)
                """, (leitura_id, risco, mensagem))

                # Envio de e-mail aos destinatários
                cur.execute("SELECT nome, email FROM destinatarios_alerta WHERE send_email = TRUE")
                destinatarios = cur.fetchall()

                smtp_host = "smtp.zoho.com"
                smtp_port = 587
                smtp_user = "suporte@cuidamais.care"
                smtp_pass = "pbnfn9i8"

                for dest in destinatarios:
                    try:
                        msg = EmailMessage()
                        msg['Subject'] = f'Alerta de Risco - {risco.upper()}'
                        msg['From'] = smtp_user
                        msg['To'] = dest['email']
                        msg.set_content(f"Olá {dest['nome']},\n\n{mensagem}\n\nDados:\nTemperatura: {temperatura}°C\nUmidade: {umidade}%\nFumaça: {fumaca}\n\nSentinela da Mata")



                        with smtplib.SMTP(smtp_host, smtp_port) as server:
                            server.starttls()
                            server.login(smtp_user, smtp_pass)
                            server.send_message(msg)
                    except Exception as e:
                        print(f"Erro ao enviar e-mail para {dest['email']}: {e}")

        conn.commit()

    return jsonify({
        'message': 'Leitura registrada com sucesso',
        'risco': risco
    }), 201



@app.route('/destinatarios', methods=['POST'])
@swag_from({
    'tags': ['Destinatários'],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'properties': {
                'nome': {'type': 'string'},
                'email': {'type': 'string'},
                'telefone': {'type': 'string'},
                'send_email': {'type': 'boolean'},
                'send_sms': {'type': 'boolean'}
            },
            'required': ['nome', 'email']
        }
    }],
    'responses': {201: {'description': 'Destinatário cadastrado'}}
})
def add_destinatario():
    data = request.json
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO destinatarios_alerta (nome, email, telefone, send_email, send_sms)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['nome'],
                data['email'],
                data.get('telefone', ''),
                data.get('send_email', True),
                data.get('send_sms', False)
            ))
        conn.commit()
    return jsonify({'message': 'Destinatário cadastrado com sucesso'}), 201

@app.route('/leituras', methods=['GET'])
@swag_from({'tags': ['Leitura Sensor'], 'responses': {200: {'description': 'Lista de leituras registradas'}}})
def get_leituras():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM leituras ORDER BY data_hora DESC")
            rows = cur.fetchall()
    return jsonify(rows)

@app.route('/alertas', methods=['GET'])
@swag_from({'tags': ['Alertas'], 'responses': {200: {'description': 'Lista de alertas registrados'}}})
def get_alertas():
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM alertas ORDER BY data_alerta DESC")
            rows = cur.fetchall()
    return jsonify(rows)


@app.route('/classificacao_risco', methods=['POST'])
@swag_from({
    'tags': ['Classificação'],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'properties': {
                'temperatura': {'type': 'number'},
                'umidade': {'type': 'number'},
                'fumaca': {'type': 'integer'}
            },
            'required': ['temperatura', 'umidade', 'fumaca']
        }
    }],
    'responses': {200: {'description': 'Classificação de risco gerada com sucesso'}}
})
def classificar_risco_ml():
    data = request.json
    temperatura = data['temperatura']
    umidade = data['umidade']
    fumaca = data['fumaca']

    entrada = np.array([[temperatura, umidade, fumaca]])
    classe = modelo_risco.predict(entrada)[0]
    risco = rotulos.get(classe, 'baixo')

    return jsonify({
        'risco': risco,
        'entrada': {
            'temperatura': temperatura,
            'umidade': umidade,
            'fumaca': fumaca
        }
    })



# =============== RUN APP ===============
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
