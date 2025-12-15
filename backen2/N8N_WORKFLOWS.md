# 🔄 Workflows de n8n para SUMETV

Este documento describe los workflows automáticos que puedes crear en n8n para controlar tu Smart TV.

## 🚀 Acceso a n8n

Una vez que Docker esté corriendo:

- **URL**: http://localhost:5678
- **Usuario**: admin
- **Contraseña**: sumetv2024

---

## 📋 Workflows Disponibles

### 1. ⏰ Apagar TV por Horario

**Trigger**: Cron (Schedule)
**Acción**: Apagar TV automáticamente a las 11:00 PM

```json
{
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "triggerTimes": {
          "item": [{ "hour": 23, "minute": 0 }]
        }
      }
    },
    {
      "name": "Apagar TV",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://backend:8080/tv/power",
        "bodyParameters": {
          "parameters": [
            { "name": "tv_ip", "value": "192.168.0.41" }
          ]
        }
      }
    }
  ]
}
```

### 2. 📱 Control por Telegram Bot

**Trigger**: Telegram Trigger
**Acción**: Enviar comandos desde Telegram

Comandos disponibles:
- `/tv_on` - Encender TV
- `/tv_off` - Apagar TV
- `/volumen_up` - Subir volumen
- `/volumen_down` - Bajar volumen
- `/mute` - Silenciar

### 3. 🏠 Encender TV al Llegar a Casa (Geofencing)

**Trigger**: Webhook desde IFTTT/Shortcuts
**Acción**: Encender TV cuando llegas a casa

URL del webhook: `http://tu-ip:5678/webhook/llegue-a-casa`

### 4. 🌅 Encender TV al Atardecer

**Trigger**: Cron + API de clima
**Acción**: Encender TV cuando oscurece

### 5. 🗣️ Control por Voz (Google Assistant)

**Trigger**: Webhook desde Google Assistant (vía IFTTT)
**Acciones**:
- "Hey Google, enciende la tele"
- "Hey Google, pon Netflix"
- "Hey Google, sube el volumen"

---

## 🔧 Configuración del Backend

El backend está disponible dentro de Docker como:
- **Host interno**: `http://backend:8080`
- **Host externo**: `http://localhost:8080`

### Endpoints útiles para n8n:

| Endpoint | Método | Body | Descripción |
|----------|--------|------|-------------|
| `/tv/remote` | POST | `{"command": "Standby", "tv_ip": "192.168.0.41"}` | Comando de mando |
| `/tv/power` | POST | `{"tv_ip": "192.168.0.41"}` | Toggle encendido |
| `/tv/channels` | POST | `{"action": "up", "tv_ip": "192.168.0.41"}` | Cambiar canal |
| `/tv/cast-youtube` | POST | `{"url": "https://youtube.com/watch?v=xxx", "tv_ip": "192.168.0.41"}` | Enviar YouTube |

### Comandos de mando disponibles:
- `Standby` - Encender/Apagar
- `VolumeUp` / `VolumeDown` - Volumen
- `ChannelStepUp` / `ChannelStepDown` - Canales
- `Mute` - Silenciar
- `Home` - Menú principal
- `Back` - Volver
- `CursorUp/Down/Left/Right` - Navegación
- `Confirm` - OK/Seleccionar

---

## 📦 Iniciar los Servicios

```bash
cd backen2
docker-compose up -d
```

Esto iniciará:
1. **Backend** en puerto 8080
2. **n8n** en puerto 5678
3. **Redis** en puerto 6379

---

## 🔒 Seguridad para Producción

Antes de desplegar en producción, cambiar en `docker-compose.yml`:

1. `N8N_BASIC_AUTH_PASSWORD` - Usar contraseña fuerte
2. `WEBHOOK_URL` - Usar URL pública con HTTPS
3. Configurar Cloudflare Tunnel o similar para acceso externo seguro
