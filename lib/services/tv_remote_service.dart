/*
Servicio de Control Remoto - TV Remote Service
Responsable de enviar comandos a diferentes marcas de TVs
*/

import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/barril_models.dart';

class TVRemoteService {
  final _logger = Logger();
  final Dio _dio = Dio(BaseOptions(
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ));

  final Map<String, WebSocketChannel> _activeConnections = {};

  /// Envía un comando a una TV
  Future<bool> sendCommand(SmartTV tv, String command) async {
    try {
      switch (tv.brand) {
        case TVBrand.samsung:
          return await _sendSamsungCommand(tv, command);
        case TVBrand.lg:
          return await _sendLGCommand(tv, command);
        case TVBrand.sony:
          return await _sendSonyCommand(tv, command);
        case TVBrand.philips:
          return await _sendPhilipsCommand(tv, command);
        case TVBrand.roku:
          return await _sendRokuCommand(tv, command);
        case TVBrand.tcl:
        case TVBrand.hisense:
        case TVBrand.xiaomi:
        case TVBrand.androidtv:
          return await _sendAndroidTVCommand(tv, command);
        default:
          return await _sendGenericHTTPCommand(tv, command);
      }
    } catch (e, s) {
      _logger.e('Error enviando comando a ${tv.brand.name}', error: e, stackTrace: s);
      return false;
    }
  }

  /// Samsung - WebSocket
  Future<bool> _sendSamsungCommand(SmartTV tv, String command) async {
    try {
      final wsUrl = 'ws://${tv.ip}:8001/api/v2/channels/samsung.remote.control';

      if (!_activeConnections.containsKey(tv.id)) {
        _activeConnections[tv.id] = WebSocketChannel.connect(Uri.parse(wsUrl));
      }

      final channel = _activeConnections[tv.id]!;
      final payload = jsonEncode({
        'method': 'ms.remote.control',
        'params': {
          'Cmd': 'Click',
          'DataOfCmd': command,
          'Option': 'false',
          'TypeOfRemote': 'SendRemoteKey'
        }
      });

      channel.sink.add(payload);
      await Future.delayed(const Duration(milliseconds: 100));
      return true;
    } catch (e, s) {
      _logger.e('Error Samsung', error: e, stackTrace: s);
      _activeConnections.remove(tv.id);
      return false;
    }
  }

  /// LG WebOS - WebSocket
  Future<bool> _sendLGCommand(SmartTV tv, String command) async {
    try {
      final wsUrl = 'ws://${tv.ip}:3000/';

      if (!_activeConnections.containsKey(tv.id)) {
        _activeConnections[tv.id] = WebSocketChannel.connect(Uri.parse(wsUrl));
      }

      final channel = _activeConnections[tv.id]!;
      final payload = jsonEncode({
        'type': 'request',
        'id': 'ssap_${DateTime.now().millisecondsSinceEpoch}',
        'uri': 'ssap://system.launcher/$command'
      });

      channel.sink.add(payload);
      await Future.delayed(const Duration(milliseconds: 100));
      return true;
    } catch (e, s) {
      _logger.e('Error LG', error: e, stackTrace: s);
      _activeConnections.remove(tv.id);
      return false;
    }
  }

  /// Sony Bravia - HTTP
  Future<bool> _sendSonyCommand(SmartTV tv, String command) async {
    try {
      final url = 'http://${tv.ip}:${tv.port}/sony/IRCC';
      final response = await _dio.post(
        url,
        data: {
          'method': 'actRegister',
          'params': [
            {
              'clientid': 'SmartTVManager',
              'nickname': 'Mobile App',
              'level': 'private'
            },
            [
              {'value': command, 'function': 'ircc'}
            ]
          ],
          'id': 1,
          'version': '1.0'
        },
        options: Options(
          headers: {
            'Content-Type': 'application/json',
          },
        ),
      );

      return response.statusCode == 200;
    } catch (e, s) {
      _logger.e('Error Sony', error: e, stackTrace: s);
      return false;
    }
  }

  /// Philips - HTTP
  Future<bool> _sendPhilipsCommand(SmartTV tv, String command) async {
    try {
      final url = 'http://${tv.ip}:1925/6/input/key';
      final response = await _dio.post(
        url,
        data: {'key': command},
        options: Options(
          headers: {'Content-Type': 'application/json'},
        ),
      );

      return response.statusCode == 200;
    } catch (e, s) {
      _logger.e('Error Philips', error: e, stackTrace: s);
      return false;
    }
  }

  /// Roku - HTTP
  Future<bool> _sendRokuCommand(SmartTV tv, String command) async {
    try {
      final url = 'http://${tv.ip}:8060/keypress/$command';
      final response = await _dio.post(url);
      return response.statusCode == 200;
    } catch (e, s) {
      _logger.e('Error Roku', error: e, stackTrace: s);
      return false;
    }
  }

  /// Android TV - ADB over network (requiere configuración previa)
  Future<bool> _sendAndroidTVCommand(SmartTV tv, String command) async {
    try {
      // Para Android TV, se requiere ADB habilitado
      // Este es un endpoint genérico, puede variar
      final url = 'http://${tv.ip}:${tv.port}/v1/projects/androidtv/key';
      final response = await _dio.post(
        url,
        data: {'key': command},
      );
      return response.statusCode == 200;
    } catch (e, s) {
      _logger.e('Error Android TV', error: e, stackTrace: s);
      return false;
    }
  }

  /// Comando HTTP genérico
  Future<bool> _sendGenericHTTPCommand(SmartTV tv, String command) async {
    try {
      final url = 'http://${tv.ip}:${tv.port}/api/command';
      final response = await _dio.post(
        url,
        data: {'command': command},
      );
      return response.statusCode == 200;
    } catch (e, s) {
      _logger.e('Error genérico', error: e, stackTrace: s);
      return false;
    }
  }

  /// Envía múltiples comandos en secuencia
  Future<bool> sendCommandSequence(
    SmartTV tv,
    List<String> commands, {
    Duration delay = const Duration(milliseconds: 300),
  }) async {
    for (final command in commands) {
      final success = await sendCommand(tv, command);
      if (!success) return false;
      await Future.delayed(delay);
    }
    return true;
  }

  /// Obtiene el estado de la TV
  Future<Map<String, dynamic>?> getTVStatus(SmartTV tv) async {
    try {
      String endpoint;
      switch (tv.brand) {
        case TVBrand.samsung:
          endpoint = 'http://${tv.ip}:8001/api/v2/';
          break;
        case TVBrand.lg:
          endpoint = 'http://${tv.ip}:3000/';
          break;
        case TVBrand.sony:
          endpoint = 'http://${tv.ip}:${tv.port}/sony/system';
          break;
        case TVBrand.philips:
          endpoint = 'http://${tv.ip}:1925/6/system';
          break;
        case TVBrand.roku:
          endpoint = 'http://${tv.ip}:8060/query/device-info';
          break;
        default:
          return null;
      }

      final response = await _dio.get(endpoint);
      if (response.statusCode == 200) {
        return response.data as Map<String, dynamic>;
      }
    } catch (e, s) {
      _logger.e('Error obteniendo estado', error: e, stackTrace: s);
    }
    return null;
  }

  /// Cierra todas las conexiones WebSocket
  void closeAllConnections() {
    for (var connection in _activeConnections.values) {
      connection.sink.close();
    }
    _activeConnections.clear();
  }

  /// Cierra una conexión específica
  void closeConnection(String tvId) {
    if (_activeConnections.containsKey(tvId)) {
      _activeConnections[tvId]!.sink.close();
      _activeConnections.remove(tvId);
    }
  }

  void dispose() {
    closeAllConnections();
    _dio.close();
  }
}
