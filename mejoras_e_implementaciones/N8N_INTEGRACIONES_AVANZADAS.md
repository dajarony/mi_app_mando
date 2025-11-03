# 🤖 N8N - INTEGRACIONES AVANZADAS
## Smart TV Manager - Automatizaciones Sin Límites

---

## 📋 ÍNDICE

1. [Introducción a n8n](#introducción-a-n8n)
2. [Arquitectura de Integración](#arquitectura-de-integración)
3. [Configuración Inicial](#configuración-inicial)
4. [Workflows Básicos](#workflows-básicos)
5. [Workflows Avanzados](#workflows-avanzados)
6. [Integraciones por Categoría](#integraciones-por-categoría)
7. [Casos de Uso Reales](#casos-de-uso-reales)
8. [APIs y Webhooks](#apis-y-webhooks)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 INTRODUCCIÓN A N8N

### **¿Qué es n8n?**
n8n es una plataforma de automatización de workflows **open-source** que permite conectar apps y servicios mediante una interfaz visual sin necesidad de programar (low-code).

### **¿Por qué n8n para Smart TV Manager?**

✅ **Ventajas:**
- **Sin programación compleja** - Visual workflow builder
- **400+ integraciones nativas** - Google, Telegram, Notion, etc.
- **Self-hosted o cloud** - Tú decides dónde corre
- **Webhooks ilimitados** - Comunicación bidireccional
- **Gratis y open-source** - Sin costos de licencia
- **Escalable** - De hobby a producción

❌ **Sin n8n tendrías que:**
- Programar cada integración manualmente
- Mantener múltiples APIs
- Lidiar con autenticación compleja
- Hosting de servicios adicionales

---

## 🏗️ ARQUITECTURA DE INTEGRACIÓN

### **Diagrama Completo:**

```
┌─────────────────────────────────────────────────────────┐
│                    FLUTTER APP                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         WebhookService (Puerto 8080)             │    │
│  │                                                  │    │
│  │  📥 RECIBE:                                      │    │
│  │  • POST /api/command  - Ejecutar comando        │    │
│  │  • POST /api/macro    - Ejecutar macro          │    │
│  │  • GET  /api/status   - Estado de TVs           │    │
│  │  • POST /api/schedule - Programar acción        │    │
│  │                                                  │    │
│  │  📤 ENVÍA:                                       │    │
│  │  • POST /n8n/webhook/event - Eventos de app     │    │
│  │  • POST /n8n/webhook/alert - Alertas críticas   │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ HTTP/WebSocket (Túnel seguro)
                 │
┌────────────────▼────────────────────────────────────────┐
│                      N8N SERVER                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              WORKFLOWS ENGINE                    │    │
│  │                                                  │    │
│  │  🔄 PROCESA:                                     │    │
│  │  • Triggers externos → Comandos a app           │    │
│  │  • Eventos de app → Notificaciones              │    │
│  │  • Schedules → Automatizaciones                 │    │
│  │  • Condiciones → Lógica compleja                │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────┬────────────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Telegram│ │ Google  │ │  Otros   │
│ WhatsApp│ │ Calendar│ │ Servicios│
│ Discord │ │ Sheets  │ │ (400+)   │
└─────────┘ └─────────┘ └──────────┘
```

---

## 🔧 CONFIGURACIÓN INICIAL

### **PASO 1: Instalar n8n**

#### **Opción A: Cloud (Recomendado para empezar)**
```
1. Ir a https://n8n.cloud
2. Crear cuenta gratis
3. Acceder al editor visual
4. ✅ Listo en 2 minutos
```

#### **Opción B: Self-Hosted con Docker (Más control)**
```bash
# Crear carpeta de datos
mkdir ~/.n8n

# Ejecutar n8n
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Acceder a http://localhost:5678
```

#### **Opción C: NPM (Desarrollo)**
```bash
npm install -g n8n
n8n start
```

---

### **PASO 2: Configurar Flutter App**

#### **Crear WebhookService en Flutter:**

```dart
// lib/services/webhook_service.dart

import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';

class WebhookService {
  HttpServer? _server;
  final int port = 8080;
  final String n8nWebhookUrl = 'https://tu-n8n.app/webhook/flutter-events';

  // Servicios necesarios
  final TVRemoteService _tvRemoteService;
  final MacroService _macroService;
  final StorageService _storageService;

  WebhookService({
    required TVRemoteService tvRemoteService,
    required MacroService macroService,
    required StorageService storageService,
  })  : _tvRemoteService = tvRemoteService,
        _macroService = macroService,
        _storageService = storageService;

  /// Iniciar servidor HTTP para recibir comandos de n8n
  Future<void> startServer() async {
    try {
      _server = await HttpServer.bind(InternetAddress.anyIPv4, port);
      debugPrint('✅ Webhook server running on port $port');

      _server!.listen((HttpRequest request) async {
        await _handleRequest(request);
      });
    } catch (e) {
      debugPrint('❌ Error starting webhook server: $e');
    }
  }

  /// Manejar requests entrantes
  Future<void> _handleRequest(HttpRequest request) async {
    final response = request.response;

    // CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*');
    response.headers.add('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
    response.headers.add('Content-Type', 'application/json');

    if (request.method == 'OPTIONS') {
      response.statusCode = 200;
      await response.close();
      return;
    }

    try {
      final body = await utf8.decoder.bind(request).join();
      final data = jsonDecode(body) as Map<String, dynamic>;

      dynamic result;

      // Rutas
      switch (request.uri.path) {
        case '/api/command':
          result = await _handleCommand(data);
          break;

        case '/api/macro':
          result = await _handleMacro(data);
          break;

        case '/api/status':
          result = await _handleStatus(data);
          break;

        case '/api/schedule':
          result = await _handleSchedule(data);
          break;

        default:
          result = {'error': 'Unknown endpoint'};
          response.statusCode = 404;
      }

      response.write(jsonEncode(result));
    } catch (e) {
      response.statusCode = 500;
      response.write(jsonEncode({'error': e.toString()}));
    }

    await response.close();
  }

  /// Ejecutar comando de TV
  Future<Map<String, dynamic>> _handleCommand(Map<String, dynamic> data) async {
    final tvId = data['tvId'] as String;
    final command = data['command'] as String;
    final action = data['action'] as String?;

    await _tvRemoteService.sendCommand(tvId, command, action);

    // Enviar evento a n8n
    await _sendEventToN8n({
      'type': 'command_executed',
      'tvId': tvId,
      'command': command,
      'action': action,
      'timestamp': DateTime.now().toIso8601String(),
    });

    return {
      'success': true,
      'message': 'Command sent to TV',
      'tvId': tvId,
      'command': command,
    };
  }

  /// Ejecutar macro
  Future<Map<String, dynamic>> _handleMacro(Map<String, dynamic> data) async {
    final macroId = data['macroId'] as String;

    await _macroService.executeMacro(macroId);

    return {
      'success': true,
      'message': 'Macro executed',
      'macroId': macroId,
    };
  }

  /// Obtener estado de TVs
  Future<Map<String, dynamic>> _handleStatus(Map<String, dynamic> data) async {
    final tvs = await _storageService.loadTVs();

    return {
      'success': true,
      'tvs': tvs.map((tv) => {
        'id': tv.id,
        'name': tv.name,
        'isOnline': tv.isOnline,
        'brand': tv.brand.name,
      }).toList(),
    };
  }

  /// Programar acción
  Future<Map<String, dynamic>> _handleSchedule(Map<String, dynamic> data) async {
    // Guardar schedule y programar ejecución
    final schedule = data['schedule'];

    return {
      'success': true,
      'message': 'Schedule created',
      'schedule': schedule,
    };
  }

  /// Enviar evento a n8n
  Future<void> _sendEventToN8n(Map<String, dynamic> event) async {
    try {
      final dio = Dio();
      await dio.post(
        n8nWebhookUrl,
        data: event,
      );
    } catch (e) {
      debugPrint('Error sending event to n8n: $e');
    }
  }

  /// Detener servidor
  Future<void> stopServer() async {
    await _server?.close();
    debugPrint('🛑 Webhook server stopped');
  }
}
```

---

### **PASO 3: Inicializar en Main.dart**

```dart
// lib/main.dart

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar servicios
  final webhookService = WebhookService(
    tvRemoteService: TVRemoteService(),
    macroService: MacroService(),
    storageService: StorageService(),
  );

  // Iniciar servidor webhook
  await webhookService.startServer();

  runApp(MyApp());
}
```

---

## 🔄 WORKFLOWS BÁSICOS

### **1. Control por Voz via Telegram**

#### **Descripción:**
Enviar comandos de voz por Telegram y que se ejecuten en la TV.

#### **Flujo:**
```
Usuario envía mensaje a Telegram Bot
  ↓
n8n recibe mensaje
  ↓
Extraer texto y mapear comando
  ↓
HTTP Request a Flutter App
  ↓
App ejecuta comando en TV
  ↓
Responder confirmación a Telegram
```

#### **Workflow n8n (JSON):**
```json
{
  "nodes": [
    {
      "name": "Telegram Trigger",
      "type": "n8n-nodes-base.telegramTrigger",
      "position": [250, 300],
      "webhookId": "telegram-bot-token"
    },
    {
      "name": "Extract Command",
      "type": "n8n-nodes-base.function",
      "position": [450, 300],
      "parameters": {
        "functionCode": "const text = items[0].json.message.text.toLowerCase();\n\nlet command = '';\nlet tvId = 'living-room-tv';\n\nif (text.includes('enciende')) command = 'power_on';\nelse if (text.includes('apaga')) command = 'power_off';\nelse if (text.includes('sube volumen')) command = 'volume_up';\nelse if (text.includes('baja volumen')) command = 'volume_down';\nelse if (text.includes('netflix')) command = 'open_netflix';\n\nreturn [{\n  json: {\n    tvId,\n    command,\n    originalText: text\n  }\n}];"
      }
    },
    {
      "name": "Send to Flutter App",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "http://TU_IP_LOCAL:8080/api/command",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={{ $json }}"
      }
    },
    {
      "name": "Send Confirmation",
      "type": "n8n-nodes-base.telegram",
      "position": [850, 300],
      "parameters": {
        "operation": "sendMessage",
        "chatId": "={{ $node['Telegram Trigger'].json.message.chat.id }}",
        "text": "✅ Comando ejecutado: {{ $node['Extract Command'].json.command }}"
      }
    }
  ],
  "connections": {
    "Telegram Trigger": {
      "main": [[{"node": "Extract Command"}]]
    },
    "Extract Command": {
      "main": [[{"node": "Send to Flutter App"}]]
    },
    "Send to Flutter App": {
      "main": [[{"node": "Send Confirmation"}]]
    }
  }
}
```

#### **Comandos Soportados:**
- "Enciende la TV" → `power_on`
- "Apaga la TV" → `power_off`
- "Sube el volumen" → `volume_up`
- "Baja el volumen" → `volume_down`
- "Pon Netflix" → `open_netflix`
- "Pausa" → `pause`
- "Play" → `play`
- "Canal 5" → `channel_5`

---

### **2. Automatización por Horario**

#### **Descripción:**
Ejecutar rutinas automáticas a horas específicas.

#### **Ejemplos:**
- **8:00 PM** → Encender TV + Poner Netflix + Volumen 30
- **11:00 PM** → Apagar TV automáticamente
- **7:00 AM** → Encender TV en canal de noticias

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 20 * * *"
            }
          ]
        }
      }
    },
    {
      "name": "Evening Routine",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "method": "POST",
        "url": "http://TU_IP_LOCAL:8080/api/macro",
        "jsonParameters": true,
        "bodyParametersJson": "{\n  \"macroId\": \"evening_routine\"\n}"
      }
    },
    {
      "name": "Notify Telegram",
      "type": "n8n-nodes-base.telegram",
      "position": [650, 300],
      "parameters": {
        "operation": "sendMessage",
        "chatId": "TU_CHAT_ID",
        "text": "🌙 Rutina nocturna activada"
      }
    }
  ]
}
```

---

### **3. Notificación cuando TV se Desconecta**

#### **Descripción:**
Recibir alerta cuando una TV pierde conexión.

#### **Flujo:**
```
Flutter App detecta TV offline
  ↓
Envía webhook a n8n
  ↓
n8n envía notificación a Telegram/Email
```

#### **Código Flutter:**
```dart
// En TVProvider cuando detectas desconexión
void _onTVDisconnected(SmartTV tv) async {
  // Enviar evento a n8n
  await _webhookService.sendEventToN8n({
    'type': 'tv_disconnected',
    'tvId': tv.id,
    'tvName': tv.name,
    'timestamp': DateTime.now().toIso8601String(),
  });
}
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "path": "flutter-events",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Check if Disconnected",
      "type": "n8n-nodes-base.if",
      "position": [450, 300],
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.type }}",
              "value2": "tv_disconnected"
            }
          ]
        }
      }
    },
    {
      "name": "Send Alert",
      "type": "n8n-nodes-base.telegram",
      "position": [650, 300],
      "parameters": {
        "operation": "sendMessage",
        "chatId": "TU_CHAT_ID",
        "text": "⚠️ {{ $json.tvName }} se ha desconectado a las {{ $json.timestamp }}"
      }
    }
  ]
}
```

---

## 🚀 WORKFLOWS AVANZADOS

### **4. Control Basado en Ubicación (GPS)**

#### **Descripción:**
Cuando llegas a casa, enciende la TV automáticamente.

#### **Servicios Necesarios:**
- Life360 / Google Location Sharing
- n8n
- Flutter App

#### **Flujo:**
```
Life360 detecta que llegaste a casa
  ↓
n8n recibe evento de ubicación
  ↓
Verifica que es tu ubicación de casa
  ↓
Envía comando "welcome_home" macro
  ↓
TV se enciende + Música de fondo
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Life360 Trigger",
      "type": "n8n-nodes-base.life360Trigger",
      "position": [250, 300],
      "parameters": {
        "event": "place_arrival"
      }
    },
    {
      "name": "Check if Home",
      "type": "n8n-nodes-base.if",
      "position": [450, 300],
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.place.name }}",
              "value2": "Home"
            }
          ]
        }
      }
    },
    {
      "name": "Welcome Home Routine",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "http://TU_IP_LOCAL:8080/api/macro",
        "bodyParametersJson": "{\n  \"macroId\": \"welcome_home\"\n}"
      }
    }
  ]
}
```

---

### **5. Control Basado en Clima**

#### **Descripción:**
Si llueve, sugerir películas. Si hace calor, ajustar configuración.

#### **Flujo:**
```
Weather API (OpenWeather)
  ↓
n8n verifica clima cada hora
  ↓
Si está lloviendo → Notificación con sugerencias
  ↓
Usuario responde "Sí" → Abre Netflix automáticamente
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Schedule Check Weather",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 1}]
        }
      }
    },
    {
      "name": "Get Weather",
      "type": "n8n-nodes-base.openWeatherMap",
      "parameters": {
        "operation": "currentWeather",
        "location": "Tu Ciudad"
      }
    },
    {
      "name": "Is Raining?",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.weather[0].main }}",
              "value2": "Rain"
            }
          ]
        }
      }
    },
    {
      "name": "Suggest Movies",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "🌧️ Está lloviendo! ¿Quieres ver una película?\n\nSugerencias:\n• Netflix\n• Prime Video\n• Disney+\n\nResponde 'Netflix' para abrir automáticamente"
      }
    }
  ]
}
```

---

### **6. Integración con Google Calendar**

#### **Descripción:**
Cuando hay evento deportivo en tu calendario, enciende TV en canal específico.

#### **Flujo:**
```
Google Calendar tiene evento "Partido de fútbol"
  ↓
n8n detecta evento próximo (15 min antes)
  ↓
Enciende TV + Cambia a canal deportivo
  ↓
Notifica al usuario
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Google Calendar Trigger",
      "type": "n8n-nodes-base.googleCalendarTrigger",
      "parameters": {
        "event": "eventStart",
        "minutesBefore": 15
      }
    },
    {
      "name": "Check if Sports Event",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.summary.toLowerCase() }}",
              "operation": "contains",
              "value2": "partido"
            }
          ]
        }
      }
    },
    {
      "name": "Turn ON TV Sports Channel",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://TU_IP_LOCAL:8080/api/command",
        "bodyParametersJson": "{\n  \"tvId\": \"living-room\",\n  \"command\": \"channel\",\n  \"action\": \"espn\"\n}"
      }
    },
    {
      "name": "Notify User",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "⚽ Tu partido comienza en 15 minutos!\nTV encendida en canal deportivo"
      }
    }
  ]
}
```

---

### **7. Backup Automático a Google Drive**

#### **Descripción:**
Cada noche a las 3 AM, hacer backup de configuraciones a Google Drive.

#### **Flujo:**
```
Cron 3 AM diario
  ↓
n8n solicita export de configuración a Flutter
  ↓
Flutter devuelve JSON
  ↓
n8n sube archivo a Google Drive
  ↓
Notificación de backup exitoso
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Daily Backup Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 3 * * *"
            }
          ]
        }
      }
    },
    {
      "name": "Get App Data",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://TU_IP_LOCAL:8080/api/export"
      }
    },
    {
      "name": "Upload to Drive",
      "type": "n8n-nodes-base.googleDrive",
      "parameters": {
        "operation": "upload",
        "name": "smart_tv_backup_{{ $now.format('YYYY-MM-DD') }}.json",
        "binaryData": false,
        "fileContent": "={{ JSON.stringify($json) }}"
      }
    },
    {
      "name": "Confirm Backup",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "✅ Backup completado: {{ $now.format('DD/MM/YYYY HH:mm') }}"
      }
    }
  ]
}
```

---

### **8. Log de Comandos en Google Sheets**

#### **Descripción:**
Registrar todos los comandos ejecutados en una hoja de cálculo.

#### **Flujo:**
```
Flutter ejecuta comando
  ↓
Envía evento a n8n webhook
  ↓
n8n añade fila a Google Sheets
```

#### **Workflow n8n:**
```json
{
  "nodes": [
    {
      "name": "Webhook Events",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "flutter-events"
      }
    },
    {
      "name": "Filter Command Events",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.type }}",
              "value2": "command_executed"
            }
          ]
        }
      }
    },
    {
      "name": "Log to Sheets",
      "type": "n8n-nodes-base.googleSheets",
      "parameters": {
        "operation": "append",
        "sheetId": "TU_SHEET_ID",
        "range": "A:E",
        "options": {},
        "dataMode": "autoMapInputData",
        "data": {
          "Timestamp": "={{ $json.timestamp }}",
          "TV ID": "={{ $json.tvId }}",
          "Command": "={{ $json.command }}",
          "Action": "={{ $json.action }}",
          "Status": "success"
        }
      }
    }
  ]
}
```

---

## 📁 INTEGRACIONES POR CATEGORÍA

### **🎤 Control por Voz**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Telegram Bot** | Comandos por texto/voz | ⭐ Fácil |
| **WhatsApp Business** | Vía WhatsApp oficial | ⭐⭐ Media |
| **Discord Bot** | Control desde Discord | ⭐ Fácil |
| **Slack Bot** | Para equipos/oficinas | ⭐ Fácil |
| **Google Assistant** | Via IFTTT/Webhooks | ⭐⭐⭐ Difícil |
| **Alexa** | Custom Skill + n8n | ⭐⭐⭐ Difícil |

---

### **📅 Automatizaciones Temporales**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Google Calendar** | Eventos → Acciones | ⭐⭐ Media |
| **Calendly** | Reuniones → Preparar TV | ⭐⭐ Media |
| **Sunrise/Sunset** | Basado en hora solar | ⭐ Fácil |
| **Timezone** | Ajustes por zona horaria | ⭐ Fácil |

---

### **🌐 Servicios Web**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **OpenWeather** | Clima → Sugerencias | ⭐ Fácil |
| **IFTTT** | Cualquier trigger → TV | ⭐⭐ Media |
| **Zapier** | Integraciones premium | ⭐⭐ Media |
| **RSS Feeds** | Noticias → Notificar | ⭐ Fácil |
| **TMDb API** | Info de películas | ⭐⭐ Media |

---

### **🏠 Smart Home**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Home Assistant** | Hub smart home | ⭐⭐⭐ Difícil |
| **Philips Hue** | Luces + TV sincronizado | ⭐⭐ Media |
| **Nest** | Termostato → Rutinas | ⭐⭐ Media |
| **Ring** | Timbre → Pausar TV | ⭐⭐ Media |
| **SmartThings** | Samsung ecosystem | ⭐⭐⭐ Difícil |

---

### **📊 Analytics & Storage**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Google Sheets** | Logs de comandos | ⭐ Fácil |
| **Airtable** | Base de datos visual | ⭐⭐ Media |
| **Notion** | Dashboard personalizado | ⭐⭐ Media |
| **Google Drive** | Backups automáticos | ⭐ Fácil |
| **Dropbox** | Almacenamiento cloud | ⭐ Fácil |
| **Firebase** | Database real-time | ⭐⭐⭐ Difícil |

---

### **🔔 Notificaciones**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Telegram** | Notificaciones rápidas | ⭐ Fácil |
| **Email (Gmail)** | Alertas por correo | ⭐ Fácil |
| **SMS (Twilio)** | Mensajes de texto | ⭐⭐ Media |
| **Push (OneSignal)** | Notificaciones push app | ⭐⭐ Media |
| **Slack** | Para equipos | ⭐ Fácil |

---

### **🤖 Inteligencia Artificial**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **ChatGPT API** | Asistente conversacional | ⭐⭐⭐ Difícil |
| **Google AI** | Procesamiento de lenguaje | ⭐⭐⭐ Difícil |
| **Wit.ai** | NLP para comandos | ⭐⭐⭐ Difícil |
| **Dialogflow** | Chatbot inteligente | ⭐⭐⭐ Difícil |

---

### **📍 Ubicación**

| Servicio | Descripción | Complejidad |
|----------|-------------|-------------|
| **Life360** | Ubicación familiar | ⭐⭐ Media |
| **Google Location** | Historial ubicación | ⭐⭐⭐ Difícil |
| **Geofencing** | Zonas geográficas | ⭐⭐⭐ Difícil |

---

## 💡 CASOS DE USO REALES

### **Caso 1: Rutina de Mañana**
```
6:30 AM - Alarma suena (IFTTT)
  ↓
n8n detecta alarma
  ↓
Enciende TV en canal de noticias
  ↓
Volumen bajo (20%)
  ↓
Muestra clima del día
```

### **Caso 2: Control Parental Inteligente**
```
Detecta que es hora de dormir (9 PM)
  ↓
n8n verifica si TV está encendida
  ↓
Envía notificación: "Es hora de dormir"
  ↓
Si no se responde en 10 min → Apaga TV
  ↓
Log en Google Sheets para padres
```

### **Caso 3: Modo Cine Automático**
```
Usuario dice "Modo cine" en Telegram
  ↓
n8n ejecuta secuencia:
  • Apaga luces Philips Hue
  • Enciende TV
  • Abre Netflix
  • Ajusta volumen a 40%
  • Activa modo Game/Cinema en TV
```

### **Caso 4: Gaming Session**
```
Consola PS5 se enciende (detectado por SmartThings)
  ↓
n8n recibe evento
  ↓
Cambia TV a HDMI 2
  ↓
Activa modo Game
  ↓
Ajusta latencia baja
  ↓
Notifica a Discord "En partida"
```

### **Caso 5: Watch Party Remoto**
```
Amigo envía mensaje "Vemos la serie?"
  ↓
n8n coordina:
  • Enciende ambas TVs (tu casa + su casa)
  • Abre Netflix
  • Reproduce mismo episodio
  • Inicia videollamada Discord
```

---

## 🔌 APIS Y WEBHOOKS

### **Endpoints Flutter App:**

#### **POST /api/command**
Ejecutar comando en TV.

```json
// Request
{
  "tvId": "living-room-tv",
  "command": "power",
  "action": "on"
}

// Response
{
  "success": true,
  "message": "Command sent to TV",
  "tvId": "living-room-tv",
  "command": "power"
}
```

#### **POST /api/macro**
Ejecutar macro predefinido.

```json
// Request
{
  "macroId": "evening_routine"
}

// Response
{
  "success": true,
  "message": "Macro executed",
  "macroId": "evening_routine",
  "steps": [
    {"command": "power_on", "status": "completed"},
    {"command": "open_netflix", "status": "completed"},
    {"command": "volume_30", "status": "completed"}
  ]
}
```

#### **GET /api/status**
Obtener estado de todas las TVs.

```json
// Response
{
  "success": true,
  "tvs": [
    {
      "id": "living-room-tv",
      "name": "TV Sala",
      "isOnline": true,
      "brand": "samsung",
      "lastCommand": "volume_up",
      "lastCommandTime": "2025-10-05T14:30:00Z"
    }
  ]
}
```

#### **GET /api/export**
Exportar configuración completa.

```json
// Response
{
  "version": "1.0.0",
  "timestamp": "2025-10-05T15:00:00Z",
  "tvs": [...],
  "favorites": [...],
  "macros": [...],
  "settings": {...}
}
```

---

### **Webhooks hacia n8n:**

#### **POST https://n8n.app/webhook/flutter-events**
Enviar eventos desde Flutter.

```json
// Evento: Comando ejecutado
{
  "type": "command_executed",
  "tvId": "living-room-tv",
  "command": "power_on",
  "timestamp": "2025-10-05T14:30:00Z",
  "success": true
}

// Evento: TV desconectada
{
  "type": "tv_disconnected",
  "tvId": "living-room-tv",
  "tvName": "TV Sala",
  "timestamp": "2025-10-05T14:35:00Z"
}

// Evento: Error crítico
{
  "type": "error",
  "tvId": "living-room-tv",
  "error": "Connection timeout",
  "timestamp": "2025-10-05T14:40:00Z"
}
```

---

## 🛠️ TROUBLESHOOTING

### **Problema 1: n8n no puede acceder a Flutter App**

**Causa:** Flutter está en red local, n8n en cloud.

**Solución:**
```bash
# Opción A: Usar ngrok para túnel
ngrok http 8080

# Copiar URL pública
# https://abc123.ngrok.io → Usar en workflows n8n

# Opción B: Self-host n8n en misma red
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

---

### **Problema 2: Webhooks no se reciben**

**Checklist:**
- [ ] Servidor Flutter corriendo en puerto 8080
- [ ] Firewall permite conexiones
- [ ] IP correcta en workflows n8n
- [ ] CORS configurado correctamente

---

### **Problema 3: Comandos lentos**

**Optimizaciones:**
- Usar WebSocket en lugar de HTTP
- Caché de conexiones a TVs
- Queue de comandos
- Reducir timeouts

---

## 🚀 PRÓXIMOS PASOS

### **Implementación Paso a Paso:**

1. **Día 1: Setup Básico**
   - Instalar n8n (cloud o local)
   - Crear WebhookService en Flutter
   - Probar conexión

2. **Día 2: Primer Workflow**
   - Crear bot de Telegram
   - Workflow control por voz
   - Testear comandos

3. **Día 3: Automatizaciones**
   - Schedule triggers
   - Rutinas por horario
   - Notificaciones

4. **Día 4-5: Integraciones Avanzadas**
   - Google Calendar
   - Weather API
   - Backup automático

5. **Día 6-7: Refinamiento**
   - Error handling
   - Logging completo
   - Documentación

---

**¿Listo para empezar con n8n? 🤖**

*Documento creado: 2025-10-05*
*Versión: 1.0*
*Smart TV Manager - n8n Integration Guide*
