"""
OrbitalFire - Aplicacao web (Azure App Service) | Disciplina SDTCC / DevOps.

Landing page que representa o produto OrbitalFire (monitoramento orbital de
queimadas). Expoe tambem /health para monitoramento e regras de alerta.

Integracoes opcionais (ativadas por variaveis de ambiente, nunca por codigo):
  - APPLICATIONINSIGHTS_CONNECTION_STRING -> telemetria no Application Insights
  - MISSION_NOTE -> texto exibido no rodape; em producao vem de uma
                    referencia do Azure Key Vault (ver README)
"""

import os
import logging
from datetime import datetime

from flask import Flask, render_template, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- Application Insights (opcional, so ativa se a connection string existir) ---
if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor()
        app.logger.info("Application Insights ativo.")
    except Exception as exc:  # nao derruba o app se o pacote/credencial faltar
        app.logger.warning("Application Insights nao configurado: %s", exc)

EQUIPE = [
    {"nome": "Bruno Eduardo Caputo Paulino", "rm": "558303"},
    {"nome": "Teste de pipeline", "rm": "xxxxxx"}

]

# Em producao este valor chega via Key Vault reference (App Setting). Localmente usa o default.
MISSION_NOTE = os.environ.get(
    "MISSION_NOTE", "Ambiente local — segredo de missao virá do Azure Key Vault em produção."
)


@app.route("/")
def home():
    return render_template(
        "index.html",
        equipe=EQUIPE,
        ano=datetime.now().year,
        mission_note=MISSION_NOTE,
    )


@app.route("/health")
def health():
    """Endpoint de saude para monitoramento / Alert Rule do Application Insights."""
    return jsonify(status="ok", service="orbitalfire-devops"), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
