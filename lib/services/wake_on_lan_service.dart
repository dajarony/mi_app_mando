import 'dart:io';
import 'dart:typed_data';
import 'package:logger/logger.dart';

/// Servicio para enviar paquetes Wake-on-LAN (Magic Packets)
/// Permite encender TVs que están en standby/apagadas
class WakeOnLanService {
  final _logger = Logger();
  
  /// Puerto estándar para Wake-on-LAN
  static const int wolPort = 9;
  
  /// Dirección de broadcast para la red local
  static const String broadcastAddress = '255.255.255.255';

  /// Valida el formato de una dirección MAC
  /// Acepta formatos: AA:BB:CC:DD:EE:FF o AA-BB-CC-DD-EE-FF
  bool isValidMacAddress(String mac) {
    if (mac.isEmpty) return false;
    
    // Normalizar: quitar separadores y convertir a mayúsculas
    final normalized = mac.replaceAll(RegExp(r'[:\-\.]'), '').toUpperCase();
    
    // Debe tener exactamente 12 caracteres hexadecimales
    if (normalized.length != 12) return false;
    
    // Verificar que todos sean caracteres hexadecimales
    return RegExp(r'^[0-9A-F]{12}$').hasMatch(normalized);
  }

  /// Convierte una dirección MAC en bytes
  List<int> _macToBytes(String mac) {
    final normalized = mac.replaceAll(RegExp(r'[:\-\.]'), '').toUpperCase();
    final bytes = <int>[];
    
    for (var i = 0; i < normalized.length; i += 2) {
      bytes.add(int.parse(normalized.substring(i, i + 2), radix: 16));
    }
    
    return bytes;
  }

  /// Construye el Magic Packet para Wake-on-LAN
  /// Estructura: 6 bytes de 0xFF + MAC address repetida 16 veces
  Uint8List _buildMagicPacket(String macAddress) {
    final macBytes = _macToBytes(macAddress);
    final packet = <int>[];
    
    // 6 bytes de 0xFF (sincronización)
    for (var i = 0; i < 6; i++) {
      packet.add(0xFF);
    }
    
    // MAC address repetida 16 veces
    for (var i = 0; i < 16; i++) {
      packet.addAll(macBytes);
    }
    
    return Uint8List.fromList(packet);
  }

  /// Envía un paquete Wake-on-LAN para encender la TV
  /// [macAddress] - Dirección MAC de la TV (ej: "AA:BB:CC:DD:EE:FF")
  /// Returns true si el paquete fue enviado exitosamente
  Future<bool> wakeUp(String macAddress) async {
    if (!isValidMacAddress(macAddress)) {
      _logger.e('Invalid MAC address format: $macAddress');
      return false;
    }

    try {
      // Construir el Magic Packet
      final magicPacket = _buildMagicPacket(macAddress);
      
      // Crear socket UDP
      final socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);
      
      // Habilitar broadcast
      socket.broadcastEnabled = true;
      
      // Enviar el paquete a la dirección de broadcast
      final bytesSent = socket.send(
        magicPacket,
        InternetAddress(broadcastAddress),
        wolPort,
      );
      
      // Cerrar el socket
      socket.close();
      
      if (bytesSent > 0) {
        _logger.i('Wake-on-LAN packet sent to $macAddress ($bytesSent bytes)');
        return true;
      } else {
        _logger.w('Wake-on-LAN packet may not have been sent');
        return false;
      }
    } catch (e, s) {
      _logger.e('Error sending Wake-on-LAN packet', error: e, stackTrace: s);
      return false;
    }
  }

  /// Envía múltiples paquetes WoL (algunas TVs necesitan varios intentos)
  Future<bool> wakeUpWithRetry(String macAddress, {int attempts = 3}) async {
    for (var i = 0; i < attempts; i++) {
      final success = await wakeUp(macAddress);
      if (success) {
        // Pequeña pausa entre intentos
        if (i < attempts - 1) {
          await Future.delayed(const Duration(milliseconds: 100));
        }
      }
    }
    _logger.i('Sent $attempts Wake-on-LAN packets to $macAddress');
    return true;
  }
}
