/*
*******************************************************************************
* Copyright (c) 2021 by M5Stack
*                  Equipped with M5Core2 sample source code
* Visit for more information: https://docs.m5stack.com/en/core/core2
*
* Describe: MQTT.
* Date: 2021/11/5
*******************************************************************************
*/
#include "M5Core2.h"
#include "Ultrasonic.h"
#include <WiFi.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient client(espClient);

// Configure the name and password of the connected wifi and your MQTT Serve
// host.
const char* ssid        = "infrastructure";
const char* password    = "q-CLNqxPd3HB";
const char* mqtt_server = "csse4011-iot.zones.eait.uq.edu.au";

// Prac specific definitions
<<<<<<< HEAD
const char* Globaltopic = "tellus-teal";
=======
const char* Globaltopic = "tellusteal";
>>>>>>> 0d62fe99a6c8f80438a73536c8692f22e152f21c

#define TRIG_PIN 33
#define ECHO_PIN 32

#define SPEED_SOUND 0.0343

Ultrasonic ultrasonic(TRIG_PIN, ECHO_PIN);

unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (50)
char msg[MSG_BUFFER_SIZE];
int value = 0;

void setupWifi();
void callback(char* topic, byte* payload, unsigned int length);
void reConnect();

void setup() {
    M5.begin();
    ultrasonic.setTimeout(40000UL); // Set timeout length for sensor (40 ms)
    setupWifi();
    client.setServer(mqtt_server, 1883);  // Sets the server details.
    client.setCallback(callback);  // Sets the message callback function.
}

void loop() {
    if (!client.connected()) {
        reConnect();
    }
    client.loop();  // This function is called periodically to allow clients to
                    // process incoming messages and maintain connections to the
                    // server.

	  long RangeInCentimeters;
    long prevValidDistance;

	  RangeInCentimeters = ultrasonic.read();
    
    if (RangeInCentimeters == 714) {
      RangeInCentimeters = prevValidDistance;
    } else {
      prevValidDistance = RangeInCentimeters;
    }

    int yDirection = 0;

    if (RangeInCentimeters <= 40) {
      yDirection = 1;
    } else if (RangeInCentimeters >= 70 && RangeInCentimeters < 200) {
      yDirection = -1;
    } else {
      yDirection = 0;
    }

	  delay(1500);

    unsigned long now =
        millis();  // Obtain the host startup duration.

    if (now - lastMsg > 100) {
        lastMsg = now;
        ++value;
        snprintf(msg, MSG_BUFFER_SIZE, "y %ld %d",
                 RangeInCentimeters, yDirection);  // Format to the specified string and store it in MSG.
        M5.Lcd.print("Publish message: ");
        M5.Lcd.println(msg);

        client.publish(Globaltopic, msg);  // Publishes a message to the specified topic.
        if (value % 12 == 0) {
            M5.Lcd.clear();
            M5.Lcd.setCursor(0, 0);
        }
    }
    
}

void setupWifi() {
    delay(10);
    M5.Lcd.println(WiFi.macAddress());
    M5.Lcd.printf("Connecting to %s", ssid);
    WiFi.mode(WIFI_STA);  // Set the mode to WiFi station mode.
    WiFi.begin(ssid, password);  // Start Wifi connection. 

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        M5.Lcd.print(".");
    }
    M5.Lcd.printf("\nSuccess\n");
}

void callback(char* topic, byte* payload, unsigned int length) {
    M5.Lcd.print("Message arrived [");
    M5.Lcd.print(topic);
    M5.Lcd.print("] ");
    for (int i = 0; i < length; i++) {
        M5.Lcd.print((char)payload[i]);
    }
    M5.Lcd.println();
}

void reConnect() {
    while (!client.connected()) {
        M5.Lcd.print("Attempting MQTT connection...");
        // Create a random client ID.
        String clientId = "M5Stack-";
        clientId += String(random(0xffff), HEX);
        // Attempt to connect.
        if (client.connect(clientId.c_str())) {
            M5.Lcd.printf("\nSuccess\n");
            // Once connected, publish an announcement to the topic.
            // client.publish(Globaltopic, "hello world");
            // ... and resubscribe.
            // client.subscribe(Globaltopic);
        } else {
            M5.Lcd.print("failed, rc=");
            M5.Lcd.print(client.state());
            M5.Lcd.println("try again in 5 seconds");
            delay(5000);
        }
    }
}
