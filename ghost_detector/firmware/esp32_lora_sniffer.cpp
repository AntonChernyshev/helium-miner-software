/*
 * Helium LoRa Sniffer for ESP32
 *
 * This firmware turns an ESP32 with a LoRa module into a packet sniffer.
 * It listens for LoRa packets on a specified frequency and, upon reception,
 * sends the packet's metadata (RSSI, SNR) to a central server via HTTP POST.
 *
 * Dependencies (PlatformIO):
 * - RadioLib by JGWorks
 * - ArduinoJson by Benoit Blanchon
 *
 * Hardware assumptions:
 * - ESP32 development board.
 * - SX127x-based LoRa module (e.g., SX1276, SX1278).
 *
 * Pinout (standard SPI for ESP32):
 * - NSS:  5
 * - MOSI: 23
 * - MISO: 19
 * - SCK:  18
 * - RST:  14
 * - DIO0: 2
 */

#include <Arduino.h>
#include <RadioLib.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- Configuration ---
// WiFi credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Server endpoint
const char* SERVER_URL = "http://YOUR_SERVER_IP:PORT/data"; // e.g., http://192.168.1.100:8080/data

// LoRa module configuration
// Heltec LoRa 32 pinout
SX1276 radio = new Module(5, 2, 14, RADIOLIB_NC);
// For a generic module, use:
// SX1276 radio = new Module(PIN_NSS, PIN_DIO0, PIN_RST, PIN_DIO1);

// Frequency to listen on (in MHz). Change this to your region's frequency.
// US915, EU868, etc.
float frequency = 915.0;

// --- Function Prototypes ---
void connectWiFi();
void sendDataToServer(float rssi, float snr, int size);

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Serial.println("Starting ESP32 LoRa Sniffer...");

  // Initialize WiFi
  connectWiFi();

  // Initialize LoRa module
  Serial.print(F("[LoRa] Initializing ... "));
  int state = radio.begin(frequency);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print(F("failed, code "));
    Serial.println(state);
    while (true);
  }
  Serial.println(F("success!"));

  // Start listening for LoRa packets
  Serial.print(F("[LoRa] Starting to listen ... "));
  state = radio.startReceive();
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print(F("failed, code "));
    Serial.println(state);
    while (true);
  }
  Serial.println(F("success!"));
}

void loop() {
  // Check if a packet has been received
  int state = radio.receive(NULL, 0);

  if (state == RADIOLIB_ERR_NONE) {
    // Packet received!
    Serial.println(F("[LoRa] Packet received!"));

    // Get packet metadata
    float rssi = radio.getRSSI();
    float snr = radio.getSNR();
    int packetSize = radio.getPacketLength();

    Serial.print(F("[LoRa] RSSI: "));
    Serial.print(rssi);
    Serial.println(F(" dBm"));

    Serial.print(F("[LoRa] SNR: "));
    Serial.print(snr);
    Serial.println(F(" dB"));

    Serial.print(F("[LoRa] Size: "));
    Serial.print(packetSize);
    Serial.println(F(" bytes"));

    // Send the data to the server
    sendDataToServer(rssi, snr, packetSize);

    // Go back to listening mode
    radio.startReceive();

  } else if (state == RADIOLIB_ERR_RX_TIMEOUT) {
    // Timeout occurred, this is normal, just continue listening
  } else if (state == RADIOLIB_ERR_CRC_MISMATCH) {
    Serial.println(F("[LoRa] CRC error!"));
  } else {
    // Some other error occurred
    Serial.print(F("[LoRa] Failed, code "));
    Serial.println(state);
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void sendDataToServer(float rssi, float snr, int size) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload
    StaticJsonDocument<200> jsonDoc;
    jsonDoc["rssi"] = rssi;
    jsonDoc["snr"] = snr;
    jsonDoc["size"] = size;
    // You could add more data here, like ESP32's own ID or location
    // jsonDoc["sensor_id"] = "ESP32_A";

    String requestBody;
    serializeJson(jsonDoc, requestBody);

    Serial.print("Sending data to server: ");
    Serial.println(requestBody);

    int httpResponseCode = http.POST(requestBody);

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      String response = http.getString();
      Serial.println(response);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected. Cannot send data.");
  }
}
