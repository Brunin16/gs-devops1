# 🛰️🔥 OrbitalFire — Aplicação Cloud (SDTCC / DevOps)

**Disciplina:** Secure DevOps Tools & Cloud Computing (SDTCC)
**Global Solution 2026 · 1º Semestre · Indústria Espacial**
**FIAP · Engenharia de Software · 4º Ano · ODS 13 (Ação Climática)**

> Integrantes:
> - Bruno Eduardo Caputo Paulino — RM 558303

Aplicação web (landing page) do produto **OrbitalFire**, publicada no **Azure App
Service** com **CI/CD via GitHub Actions**, segurança com **Key Vault + GitHub Secrets**
e monitoramento com **Application Insights**. A página apresenta a identidade do
produto, o problema espacial e o ODS, e representa o funcionamento da solução.

---

## Stack

- **App:** Python 3.11 + Flask (landing page) + Gunicorn
- **Cloud:** Azure App Service (Linux)
- **CI/CD:** GitHub Actions (`.github/workflows/deploy.yml`)
- **Segurança:** Service Principal + GitHub Secrets + Azure Key Vault
- **Monitoramento:** Application Insights + Alert Rule
- **Rotas:** `/` (landing) e `/health` (saúde, usada no alerta)

## Rodar localmente
```bash
pip install -r requirements.txt
python app.py        # http://localhost:8000
```

---

# 🚀 Runbook — Azure CLI

> Defina as variáveis uma vez. O **nome do Web App é global**, então use um sufixo único.

```bash
# Variáveis
RG="rg-orbitalfire"
LOC="brazilsouth"
PLAN="plan-orbitalfire"
APP="orbitalfire-devops-rm558303"     # precisa ser único no mundo
KV="kv-orbitalfire-558303"            # 3-24 chars, único
AI="ai-orbitalfire"

# Login
az login
az account set --subscription "<ID_DA_SUA_SUBSCRIPTION>"
SUB=$(az account show --query id -o tsv)
```

## 1. Infraestrutura (Resource Group + Plan + Web App)
```bash
az group create -n $RG -l $LOC

az appservice plan create -g $RG -n $PLAN --is-linux --sku B1

az webapp create -g $RG -p $PLAN -n $APP --runtime "PYTHON:3.11"

# Comando de inicialização (Gunicorn apontando para o objeto Flask 'app')
az webapp config set -g $RG -n $APP \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"
```

## 2. CI/CD — credenciais para o GitHub Actions (Service Principal + role assignment)
```bash
# Cria o Service Principal com papel Contributor NO ESCOPO do resource group
# (isto JÁ é o role assignment documentado exigido na rubrica)
az ad sp create-for-rbac \
  --name "gh-orbitalfire" \
  --role contributor \
  --scopes /subscriptions/$SUB/resourceGroups/$RG \
  --sdk-auth
```
- Copie **todo o JSON** de saída e crie o GitHub Secret **`AZURE_CREDENTIALS`**
  (repositório → Settings → Secrets and variables → Actions → New secret).
- Edite `env.AZURE_WEBAPP_NAME` no `deploy.yml` com o valor de `$APP`.
- Confirme o role assignment para o relatório:
```bash
az role assignment list -g $RG -o table
```

> **Subscription educacional bloqueou o SP?** Use o publish profile:
> ```bash
> az webapp deployment list-publishing-profiles -g $RG -n $APP --xml
> ```
> Cole o XML no Secret `AZURE_WEBAPP_PUBLISH_PROFILE` e siga o bloco "ALTERNATIVA"
> comentado no `deploy.yml`.

## 3. Segurança — Azure Key Vault (1 secret + acesso via Managed Identity)
```bash
# Cria o cofre e um segredo relacionado à solução
az keyvault create -g $RG -n $KV -l $LOC
az keyvault secret set --vault-name $KV --name "mission-note" \
  --value "OrbitalFire · ambiente seguro · segredo gerido pelo Key Vault"

# Liga a Managed Identity do App Service e dá acesso de leitura ao cofre
az webapp identity assign -g $RG -n $APP
PRINCIPAL_ID=$(az webapp identity show -g $RG -n $APP --query principalId -o tsv)
az keyvault set-policy -n $KV --object-id $PRINCIPAL_ID --secret-permissions get list

# Injeta o segredo como App Setting via REFERÊNCIA do Key Vault (não expõe o valor)
SECRET_URI=$(az keyvault secret show --vault-name $KV --name "mission-note" --query id -o tsv)
az webapp config appsettings set -g $RG -n $APP --settings \
  "MISSION_NOTE=@Microsoft.KeyVault(SecretUri=$SECRET_URI)"
```
A app lê `MISSION_NOTE` e o exibe no rodapé — provando que a referência ao Key Vault
funciona. **Nenhuma senha aparece no código ou no histórico do repositório.**

## 4. Monitoramento — Application Insights + Alert Rule
```bash
# Cria o recurso e conecta ao Web App
az monitor app-insights component create -g $RG -a $AI -l $LOC
AI_CONN=$(az monitor app-insights component show -g $RG -a $AI --query connectionString -o tsv)
az webapp config appsettings set -g $RG -n $APP --settings \
  "APPLICATIONINSIGHTS_CONNECTION_STRING=$AI_CONN"

# Alert Rule: dispara se houver falhas de requisição (5xx) na aplicação
APP_ID=$(az webapp show -g $RG -n $APP --query id -o tsv)
az monitor metrics alert create -g $RG -n "alerta-falhas-orbitalfire" \
  --scopes $APP_ID \
  --condition "total Http5xx > 5" \
  --window-size 5m --evaluation-frequency 1m --severity 2 \
  --description "Mais de 5 erros 5xx em 5 minutos no OrbitalFire"
```
Acompanhe em **Application Insights → Live Metrics / Logs** e tire prints durante os testes.

## 5. Pipeline rodando (2 deploys)
```bash
git add . && git commit -m "feat: deploy inicial OrbitalFire" && git push origin main
# faça um segundo commit (ex.: ajuste de texto na landing) para gerar o 2º deploy:
git commit -am "chore: ajuste de copy na landing" && git push origin main
```
Veja as duas execuções em **GitHub → Actions** e em **App Service → Deployment Center**.

URL pública: `https://<APP>.azurewebsites.net`

---

## Checklist da entrega (critérios SDTCC)

| Critério | Status | Onde |
|---|---|---|
| Aplicação no App Service (identidade, problema/ODS, funcionamento) | ✅ código | `app.py` + `templates/index.html` |
| Pipeline CI/CD (login seguro, 2 deploys) | ✅ código | `.github/workflows/deploy.yml` + passo 5 |
| Segurança (Key Vault + GitHub Secrets + IAM role) | ✅ runbook | passos 2 e 3 |
| Monitoramento (App Insights + Alert Rule) | ✅ runbook | passo 4 |
| Documentação (arquitetura, prints, link) | ⬜ você | relatório PDF com os prints |

**Pendências suas:** rodar o runbook na sua subscription, tirar os prints (Actions verde,
Deployment Center com 2 deploys, Key Vault, App Insights/Alert, app no ar) e montar o
relatório PDF. Me mande os prints que eu monto o relatório.
