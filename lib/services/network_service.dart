/*
Servicio de Red - Network Service
Responsable de escanear la red local para encontrar Smart TVs
*/

import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../core/constants.dart';
import '../models/barril_models.dart';

class NetworkScanToken {
  bool _isCancelled = false;
  bool get isCancelled => _isCancelled;

  void cancel() {
    _isCancelled = true;
  }
}

class NetworkScanProgress {
  const NetworkScanProgress({
    required this.current,
    required this.total,
    required this.currentIp,
    required this.foundCount,
  });

  final int current;
  final int total;
  final String currentIp;
  final int foundCount;

  double get ratio => total == 0 ? 0 : current / total;
}

class NetworkScanEvent {
  const NetworkScanEvent({
    required this.progress,
    this.tv,
  });

  final NetworkScanProgress progress;
  final SmartTV? tv;
}

class NetworkScanSummary {
  const NetworkScanSummary({
    required this.totalCandidates,
    required this.scanned,
    required this.found,
    required this.cancelled,
    this.errorMessage,
  });

  final int totalCandidates;
  final int scanned;
  final int found;
  final bool cancelled;
  final String? errorMessage;

  bool get hasError => errorMessage != null;
}

class NetworkService {
  final Dio _dio;
  final _logger = Logger();

  NetworkService()
      : _dio = Dio(
          BaseOptions(
            connectTimeout: const Duration(
              milliseconds: AppConstants.defaultScanTimeout,
            ),
            receiveTimeout: const Duration(
              milliseconds: AppConstants.defaultScanTimeout,
            ),
          ),
        );

  /// Escanea la red local en busca de Smart TVs y emite eventos de progreso.
  Stream<NetworkScanEvent> scanNetworkStream({
    String subnet = AppConstants.defaultSubnet,
    int startIp = AppConstants.scanRangeStart,
    int endIp = AppConstants.scanRangeEnd,
    NetworkScanToken? token,
    Duration perIpDelay = const Duration(milliseconds: 5),
  }) async* {
    final scanToken = token ?? NetworkScanToken();
    final totalIps = (endIp - startIp) + 1;
    int current = 0;
    int found = 0;

    for (int i = startIp; i <= endIp; i++) {
      if (scanToken.isCancelled) break;

      final ip = '$subnet.$i';
      final tv = await _scanSingleIP(ip);

      if (scanToken.isCancelled) break;

      current++;
      if (tv != null) {
        found++;
      }

      yield NetworkScanEvent(
        progress: NetworkScanProgress(
          current: current,
          total: totalIps,
          currentIp: ip,
          foundCount: found,
        ),
        tv: tv,
      );

      if (perIpDelay > Duration.zero) {
        await Future.delayed(perIpDelay);
      }
    }
  }

  /// Mantiene compatibilidad con la firma anterior acumulando el stream.
  Future<List<SmartTV>> scanNetworkForTVs({
    String subnet = AppConstants.defaultSubnet,
    int startIp = AppConstants.scanRangeStart,
    int endIp = AppConstants.scanRangeEnd,
    Function(int current, int total)? onProgress,
    NetworkScanToken? token,
  }) async {
    final results = <SmartTV>[];
    final stream = scanNetworkStream(
      subnet: subnet,
      startIp: startIp,
      endIp: endIp,
      token: token,
      perIpDelay: Duration.zero,
    );

    await for (final event in stream) {
      onProgress?.call(event.progress.current, event.progress.total);
      if (event.tv != null) {
        results.add(event.tv!);
      }
    }

    return results;
  }

  Future<SmartTV?> _scanSingleIP(String ip) async {
    const ports = [
      8080, // Samsung / HTTP genérico
      8001, // Samsung WebSocket
      3000, // LG WebOS
      1925, // Philips
      8060, // Roku
      55000, // Sony
      7345, // TCL
      36669, // Xiaomi
    ];

    for (final port in ports) {
      try {
        final socket = await Socket.connect(
          ip,
          port,
          timeout: const Duration(milliseconds: 500),
        );
        await socket.close();

        final brand = await _detectTVBrand(ip, port);
        if (brand != null) {
          return SmartTV(
            name: 'TV ${brand.name.toUpperCase()}',
            brand: brand,
            ip: ip,
            port: port,
            protocol: _getProtocolForBrand(brand),
            isOnline: true,
          );
        }
      } catch (_) {
        // Ignorar errores por IP/puerto
      }
    }

    return null;
  }

  Future<TVBrand?> _detectTVBrand(String ip, int port) async {
    final endpoints = {
      TVBrand.samsung: 'http://$ip:$port/api/v2/',
      TVBrand.lg: 'http://$ip:$port/',
      TVBrand.sony: 'http://$ip:$port/sony/',
      TVBrand.philips: 'http://$ip:$port/6/system',
      TVBrand.roku: 'http://$ip:$port/query/device-info',
    };

    for (final entry in endpoints.entries) {
      try {
        final response = await _dio.get(entry.value);
        if (response.statusCode == 200) {
          return entry.key;
        }
      } catch (_) {
        // probar siguiente endpoint
      }
    }

    return TVBrand.unknown;
  }

  TVProtocol _getProtocolForBrand(TVBrand brand) {
    switch (brand) {
      case TVBrand.samsung:
      case TVBrand.lg:
        return TVProtocol.websocket;
      case TVBrand.roku:
        return TVProtocol.roku;
      default:
        return TVProtocol.http;
    }
  }

  /// Valida que una TV responda según su protocolo/marca.
  Future<bool> validateTVConnection(
    String ip,
    int port, {
    TVBrand? brand,
  }) async {
    try {
      if (brand != null) {
        switch (brand) {
          case TVBrand.samsung:
            return await _validateSamsungConnection(ip, port);
          case TVBrand.lg:
            return await _validateLGConnection(ip, port);
          case TVBrand.sony:
            return await _validateSonyConnection(ip, port);
          case TVBrand.roku:
            return await _validateRokuConnection(ip, port);
          default:
            break;
        }
      }

      final socket = await Socket.connect(
        ip,
        port,
        timeout: const Duration(seconds: 3),
      );
      await socket.close();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> validateSmartTVConnection(SmartTV tv) {
    return validateTVConnection(tv.ip, tv.port, brand: tv.brand);
  }

  Future<bool> pairWithTV(SmartTV tv) async {
    switch (tv.brand) {
      case TVBrand.samsung:
        return _pairSamsungTV(tv);
      case TVBrand.lg:
        return _pairLGTV(tv);
      default:
        return true;
    }
  }

  Future<Map<String, dynamic>?> getTVInfo(SmartTV tv) async {
    try {
      String endpoint;
      switch (tv.brand) {
        case TVBrand.samsung:
          endpoint = 'http://${tv.ip}:${tv.port}/api/v2/';
          break;
        case TVBrand.lg:
          endpoint = 'http://${tv.ip}:${tv.port}/';
          break;
        case TVBrand.sony:
          endpoint = 'http://${tv.ip}:${tv.port}/sony/system';
          break;
        case TVBrand.philips:
          endpoint = 'http://${tv.ip}:${tv.port}/6/system';
          break;
        case TVBrand.roku:
          endpoint = 'http://${tv.ip}:${tv.port}/query/device-info';
          break;
        default:
          return null;
      }

      final response = await _dio.get(endpoint);
      if (response.statusCode == 200) {
        return Map<String, dynamic>.from(response.data);
      }
    } catch (e, s) {
      _logger.e('Error obteniendo info de TV', error: e, stackTrace: s);
    }
    return null;
  }

  Future<String> getCurrentSubnet() async {
    try {
      final interfaces = await NetworkInterface.list();
      for (final interface in interfaces) {
        for (final address in interface.addresses) {
          if (address.type == InternetAddressType.IPv4 && !address.isLoopback) {
            final parts = address.address.split('.');
            if (parts.length == 4) {
              return '${parts[0]}.${parts[1]}.${parts[2]}';
            }
          }
        }
      }
    } catch (e, s) {
      _logger.e('Error obteniendo subred', error: e, stackTrace: s);
    }
    return AppConstants.defaultSubnet;
  }

  void dispose() {
    _dio.close();
  }

  Future<bool> _validateSamsungConnection(String ip, int port) async {
    try {
      final response = await _dio.get(
        'http://$ip:$port/api/v2/',
        options: Options(
          receiveTimeout: const Duration(seconds: 3),
          sendTimeout: const Duration(seconds: 3),
        ),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> _validateLGConnection(String ip, int port) async {
    try {
      final response = await _dio.get(
        'http://$ip:$port/api/system/info',
        options: Options(
          receiveTimeout: const Duration(seconds: 3),
          sendTimeout: const Duration(seconds: 3),
        ),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> _validateSonyConnection(String ip, int port) async {
    try {
      final response = await _dio.post(
        'http://$ip:$port/sony/system',
        data: {
          'method': 'getSystemInformation',
          'params': [],
          'id': 1,
          'version': '1.0',
        },
        options: Options(
          receiveTimeout: const Duration(seconds: 3),
          sendTimeout: const Duration(seconds: 3),
        ),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> _validateRokuConnection(String ip, int port) async {
    try {
      final response = await _dio.get(
        'http://$ip:$port/query/device-info',
        options: Options(
          receiveTimeout: const Duration(seconds: 3),
          sendTimeout: const Duration(seconds: 3),
        ),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> _pairSamsungTV(SmartTV tv) async {
    await Future.delayed(const Duration(seconds: 2));
    return true;
  }

  Future<bool> _pairLGTV(SmartTV tv) async {
    await Future.delayed(const Duration(seconds: 2));
    return true;
  }
}
