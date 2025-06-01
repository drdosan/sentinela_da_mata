import pandas as pd
import pymysql
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Conexão com o banco MySQL
conn = pymysql.connect(
    host='192.185.217.47',
    user='bsconsul_global_solution',
    password='Padr@ao321',
    database='bsconsul_global_solution',
    cursorclass=pymysql.cursors.DictCursor
)

# Carrega os dados de leitura
query = """
    SELECT umidade AS valor_umidade,
           fumaca AS valor_fumaca,
           temperatura AS valor_temperatura
    FROM leituras
    WHERE umidade IS NOT NULL AND fumaca IS NOT NULL AND temperatura IS NOT NULL
"""

df = pd.read_sql(query, conn)

# ✅ Converte para tipos numéricos
df['valor_umidade'] = pd.to_numeric(df['valor_umidade'], errors='coerce')
df['valor_fumaca'] = pd.to_numeric(df['valor_fumaca'], errors='coerce')
df['valor_temperatura'] = pd.to_numeric(df['valor_temperatura'], errors='coerce')

conn.close()

# Geração de rótulo com base nas regras
def classificar_risco(row):
    if row['valor_temperatura'] > 40 and row['valor_umidade'] < 30 and row['valor_fumaca'] > 2000:
        return 'alto'
    elif row['valor_temperatura'] > 35 and row['valor_umidade'] < 40 and row['valor_fumaca'] > 1500:
        return 'medio'
    else:
        return 'baixo'

df['risco'] = df.apply(classificar_risco, axis=1)

# Separar X (entradas) e y (saída/risco)
X = df[['valor_temperatura', 'valor_umidade', 'valor_fumaca']]
y = df['risco']

# Dividir em treino/teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Treinar o modelo
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

# Avaliação do modelo
y_pred = modelo.predict(X_test)
print("Relatório de Classificação:")
print(classification_report(y_test, y_pred))

# Salvar o modelo em arquivo
joblib.dump(modelo, 'modelo_risco_queimada.pkl')
