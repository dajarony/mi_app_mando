import 'package:flutter/material.dart';

/// Modelo de datos para representar una Smart TV registrada en la app.
enum TVBrand {
  samsung,
  lg,
  sony,
  philips,
  tcl,
  hisense,
  xiaomi,
  roku,
  androidtv,
  unknown,
}

enum TVProtocol { http, websocket, upnp, roku, unknown }

class SmartTV {
  final String id;
  final String name;
  final TVBrand brand;
  final String ip;
  final int port;
  final String room;
  final TVProtocol protocol;
  final String macAddress;
  final String model;
  final Map<String, dynamic> capabilities;
  bool isOnline;
  bool isRegistered;
  bool isFavorite;
  bool isConnecting;
  bool isPaired;
  final DateTime lastPing;
  DateTime? lastControlled;
  String? authToken;

  SmartTV({
    String? id,
    required this.name,
    required this.brand,
    required this.ip,
    this.port = 8080,
    this.room = 'Sin asignar',
    this.protocol = TVProtocol.http,
    this.macAddress = '',
    this.model = '',
    this.capabilities = const {},
    this.isOnline = false,
    this.isRegistered = false,
    this.isFavorite = false,
    this.isConnecting = false,
    this.isPaired = false,
    DateTime? lastPing,
    this.lastControlled,
    this.authToken,
  })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        lastPing = lastPing ?? DateTime.now();

  factory SmartTV.fromJson(Map<String, dynamic> json) {
    return SmartTV(
      id: json['id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      brand: _parseBrand(json['brand']),
      ip: json['ip']?.toString() ?? '',
      port: _parsePort(json['port']),
      room: json['room']?.toString() ?? 'Sin asignar',
      protocol: _parseProtocol(json['protocol']),
      macAddress: json['macAddress']?.toString() ?? '',
      model: json['model']?.toString() ?? '',
      capabilities: Map<String, dynamic>.from(json['capabilities'] ?? {}),
      isOnline: json['isOnline'] == true,
      isRegistered: json['isRegistered'] == true,
      isFavorite: json['isFavorite'] == true,
      isConnecting: json['isConnecting'] == true,
      isPaired: json['isPaired'] == true,
      lastPing: DateTime.tryParse(json['lastPing']?.toString() ?? '') ??
          DateTime.now(),
      lastControlled: json['lastControlled'] != null
          ? DateTime.tryParse(json['lastControlled'].toString())
          : null,
      authToken: json['authToken']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'brand': brand.name,
      'ip': ip,
      'port': port,
      'room': room,
      'protocol': protocol.name,
      'macAddress': macAddress,
      'model': model,
      'capabilities': capabilities,
      'isOnline': isOnline,
      'isRegistered': isRegistered,
      'isFavorite': isFavorite,
      'isConnecting': isConnecting,
      'isPaired': isPaired,
      'lastPing': lastPing.toIso8601String(),
      'lastControlled': lastControlled?.toIso8601String(),
      'authToken': authToken,
    };
  }

  SmartTV copyWith({
    String? id,
    String? name,
    TVBrand? brand,
    String? ip,
    int? port,
    String? room,
    TVProtocol? protocol,
    String? macAddress,
    String? model,
    Map<String, dynamic>? capabilities,
    bool? isOnline,
    bool? isRegistered,
    bool? isFavorite,
    bool? isConnecting,
    bool? isPaired,
    DateTime? lastPing,
    DateTime? lastControlled,
    String? authToken,
  }) {
    return SmartTV(
      id: id ?? this.id,
      name: name ?? this.name,
      brand: brand ?? this.brand,
      ip: ip ?? this.ip,
      port: port ?? this.port,
      room: room ?? this.room,
      protocol: protocol ?? this.protocol,
      macAddress: macAddress ?? this.macAddress,
      model: model ?? this.model,
      capabilities: capabilities ?? this.capabilities,
      isOnline: isOnline ?? this.isOnline,
      isRegistered: isRegistered ?? this.isRegistered,
      isFavorite: isFavorite ?? this.isFavorite,
      isConnecting: isConnecting ?? this.isConnecting,
      isPaired: isPaired ?? this.isPaired,
      lastPing: lastPing ?? this.lastPing,
      lastControlled: lastControlled ?? this.lastControlled,
      authToken: authToken ?? this.authToken,
    );
  }

  @override
  String toString() {
    return 'SmartTV(id: $id, name: $name, brand: $brand, ip: $ip, port: $port)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is SmartTV && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  String get brandDisplayName {
    switch (brand) {
      case TVBrand.samsung:
        return 'Samsung';
      case TVBrand.lg:
        return 'LG';
      case TVBrand.sony:
        return 'Sony';
      case TVBrand.philips:
        return 'Philips';
      case TVBrand.tcl:
        return 'TCL';
      case TVBrand.hisense:
        return 'Hisense';
      case TVBrand.xiaomi:
        return 'Xiaomi';
      case TVBrand.roku:
        return 'Roku';
      case TVBrand.androidtv:
        return 'Android TV';
      default:
        return 'Desconocida';
    }
  }

  IconData get brandIcon {
    switch (brand) {
      case TVBrand.samsung:
      case TVBrand.lg:
        return Icons.tv;
      case TVBrand.sony:
        return Icons.monitor;
      case TVBrand.philips:
        return Icons.desktop_windows;
      case TVBrand.roku:
        return Icons.cast_connected;
      default:
        return Icons.device_unknown;
    }
  }

  Color get statusColor {
    if (isConnecting) return Colors.amber;
    if (isPaired && isOnline) return Colors.green;
    if (isOnline) return Colors.blue;
    return Colors.grey;
  }

  String get statusText {
    if (isConnecting) return 'Conectando...';
    if (isPaired && isOnline) return 'Conectado';
    if (isOnline) return 'Disponible';
    return 'Desconectado';
  }

  String get protocolDisplayName {
    switch (protocol) {
      case TVProtocol.http:
        return 'HTTP';
      case TVProtocol.websocket:
        return 'WebSocket';
      case TVProtocol.upnp:
        return 'UPnP';
      case TVProtocol.roku:
        return 'Roku Protocol';
      default:
        return 'Desconocido';
    }
  }

  bool get isAvailable => isOnline && isPaired;

  static TVBrand _parseBrand(dynamic raw) {
    if (raw == null) return TVBrand.unknown;
    final normalized = raw.toString().toLowerCase();
    return TVBrand.values.firstWhere(
      (value) {
        final plain = value.name.toLowerCase();
        final legacy = 'tvbrand.$plain';
        return normalized == plain || normalized == legacy;
      },
      orElse: () => TVBrand.unknown,
    );
  }

  static TVProtocol _parseProtocol(dynamic raw) {
    if (raw == null) return TVProtocol.http;
    final normalized = raw.toString().toLowerCase();
    return TVProtocol.values.firstWhere(
      (value) {
        final plain = value.name.toLowerCase();
        final legacy = 'tvprotocol.$plain';
        return normalized == plain || normalized == legacy;
      },
      orElse: () => TVProtocol.http,
    );
  }

  static int _parsePort(dynamic raw) {
    if (raw == null) return 8080;
    if (raw is int) return raw;
    return int.tryParse(raw.toString()) ?? 8080;
  }
}
