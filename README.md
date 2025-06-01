# 🔥 Sentinela da Mata - Sistema de Prevenção a Queimadas 🌿

Projeto acadêmico desenvolvido na FIAP com foco em prevenção a incêndios florestais utilizando IoT, Machine Learning e alertas automatizados via e-mail.

---

## 📦 Estrutura do Projeto

```
sentinela_da_mata/
├── sensores/
│   └── main.ino
│
├── api/
│   ├── app.py # API Flask principal
│   ├── treinar_modelo.py # Treinamento do modelo de risco
│   ├── modelo_risco_queimada.pkl # Modelo Treinado
│   └── requirements.txt # Dependências do projeto
│
├── .gitignore
└── README.md
```

## 🌡️ Fase 1 - ESP32 com Sensores Ambientais

O circuito foi simulado na plataforma [Wokwi](https://wokwi.com/) com os seguintes componentes:

- ✅ **ESP32 DevKit v1**
- 🌡️ **Sensor DHT22** (temperatura e umidade)
- 💨 **Sensor MQ-2** (simulando nível de fumaça)

### 🔄 Comportamento:

- A cada 5 segundos, o ESP32 lê os valores dos sensores e envia via `HTTP POST` para a API.
- Os dados só são enviados se o endpoint `/status-irrigacao` retornar que é permitido (baseado na previsão do tempo).

---

## 🧠 Fase 2 - API Flask com MySQL e Alertas

A API realiza:

- 🔎 Recebimento de leituras do ESP32 (`/leituras`)
- 📊 Classificação de risco (`baixo`, `moderado`, `alto`)
- 📤 Envio de alertas por e-mail para destinatários cadastrados
- 📁 Armazenamento de todas as leituras e alertas no banco de dados

### ▶️ Como Executar

```bash
cd api
pip install -r requirements.txt
python app.py
```

### 🌐 Swagger

Acesse a documentação da API:

👉 **http://{base_url_api}:5000/apidocs**

---

## 🧠 Fase 3 - Machine Learning com Scikit-Learn

O script `treinar_modelo.py` treina um modelo de classificação de risco com base em dados históricos, usando:

- `temperatura`, `umidade`, `fumaca` → `risco`

O modelo `modelo_risco_queimada.pkl` é carregado pela API, mas **pode ser desativado** se preferir lógica por regras fixas.

### ▶️ Como Executar

```bash
cd api
pip install -r requirements.txt
python treinar_modelo.py
```

---

## 📬 Envio de Alertas por E-mail

A cada leitura com risco `moderado` ou `alto`:

- A API verifica se **já existe alerta similar nos últimos 15 minutos**
- Se não houver, grava o alerta e dispara e-mails para os destinatários com `send_email = TRUE`

### 📥 Cadastro de destinatários

Via endpoint:

```http
POST /destinatarios
{
  "nome": "Fulano",
  "email": "fulano@dominio.com",
  "telefone": "11999999999",
  "send_email": true,
  "send_sms": false
}
```
---


## 🧑‍🤝‍🧑 Membros do Grupo

| Matrícula                 | Aluno               											  |
|---------------------------|---------------------------------------------|
|        RM 565150          | Andre de Oliveira Santos Burger							|
|        RM 565497          | Vera Maria Chaves de Souza									| 
|        RM 565286          | Diogo Rebello dos Santos										|
|        RM 565555          | Marcos Vinícius dos Santos Fernandes				|
