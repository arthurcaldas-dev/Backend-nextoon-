
import os
import mercadopago

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuração do CORS
CORS(app)

# Credenciais do Mercado Pago
ACCESS_TOKEN = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

# URLs do site
SITE_URL = os.getenv(
    "SITE_URL",
    "https://seu-site.com"
).rstrip("/")


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "Backend da Apoie a Nextoon funcionando!"
    }), 200


@app.route("/criar-pagamento", methods=["POST"])
def criar_pagamento():

    # Verifica se o token está configurado
    if not ACCESS_TOKEN:
        return jsonify({
            "erro": "Token do Mercado Pago não configurado."
        }), 500

    # Recebe os dados enviados pelo site
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    # Valida o valor do apoio
    try:
        valor = float(dados.get("amount"))

        if not (1 <= valor <= 10000):
            raise ValueError

        if not round(valor, 2) == valor:
            raise ValueError

    except (TypeError, ValueError, OverflowError):
        return jsonify({
            "erro": "O valor deve estar entre R$ 1,00 e R$ 10.000,00, com até duas casas decimais."
        }), 400

    # Inicializa o Mercado Pago
    sdk = mercadopago.SDK(ACCESS_TOKEN)

    # Dados do checkout
    pagamento = {
        "items": [
            {
                "title": "Apoio à Nextoon",
                "quantity": 1,
                "unit_price": round(valor, 2),
                "currency_id": "BRL"
            }
        ],
        "back_urls": {
            "success": f"{SITE_URL}/sucesso",
            "failure": f"{SITE_URL}/erro",
            "pending": f"{SITE_URL}/pendente"
        },
        "auto_return": "approved"
    }

    # Cria a preferência de pagamento
    try:
        resultado = sdk.preference().create(pagamento)

        if resultado.get("status") not in (200, 201):
            app.logger.error(
                "Erro Mercado Pago: %s",
                resultado.get("response")
            )

            return jsonify({
                "erro": "Não foi possível criar o pagamento."
            }), 502

        resposta = resultado.get("response", {})
        link = resposta.get("init_point")

        if not link:
            return jsonify({
                "erro": "O Mercado Pago não retornou o link de pagamento."
            }), 502

        return jsonify({
            "status": "success",
            "init_point": link
        }), 200

    except Exception:
        app.logger.exception(
            "Falha ao comunicar com o Mercado Pago."
        )

        return jsonify({
            "erro": "Erro interno ao processar o pagamento."
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )
