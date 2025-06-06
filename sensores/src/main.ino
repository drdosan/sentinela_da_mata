#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT22
#define MQ2_PIN 34  // Pino analógico para MQ-2

const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* serverUrl = "http://192.168.3.6:5000/leituras";  // Altere para o IP da sua API

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(ssid, password);
  
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi conectado");
}

void loop() {
  float umidade = dht.readHumidity();
  float temperatura = dht.readTemperature();
  int valorFumaca = analogRead(MQ2_PIN);  // valor de 0 a 4095

  if (!isnan(umidade) && !isnan(temperatura)) {
    Serial.println("📡 Leitura dos sensores:");
    Serial.print("🌡️ Temperatura: ");
    Serial.print(temperatura);
    Serial.println(" °C");

    Serial.print("💧 Umidade: ");
    Serial.print(umidade);
    Serial.println(" %");

    Serial.print("🔥 Fumaça (MQ-2): ");
    Serial.println(valorFumaca);

    // Comentado temporariamente o envio para a API
    
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");

      StaticJsonDocument<256> json;
      json["temperatura"] = temperatura;
      json["umidade"] = umidade;
      json["fumaca"] = valorFumaca;

      String jsonString;
      serializeJson(json, jsonString);

      int httpResponseCode = http.POST(jsonString);
      Serial.print("POST enviado → Código: ");
      Serial.println(httpResponseCode);

      if (httpResponseCode > 0) {
        String resposta = http.getString();
        Serial.println("✔️ Resposta: " + resposta);
      } else {
        Serial.println("❌ Falha no envio");
      }

      http.end();
    } else {
      Serial.println("⚠️ Wi-Fi desconectado");
    }
    
  } else {
    Serial.println("⚠️ Leitura inválida do DHT22");
  }

  delay(5000);
}
