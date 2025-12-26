import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:logger/logger.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/constants.dart';
import '../services/error_handler_service.dart';
import '../services/network_service.dart';
import '../models/smart_tv.dart';
import 'settings_provider.dart';

class TVProvider extends ChangeNotifier {
  final _logger = Logger();
  final List<SmartTV> _tvs = [];
  String? _selectedTVId;
  bool _isScanning = false;
  bool _isLoading = false;
  String? _errorMessage;
  final NetworkService _networkService = NetworkService();
  NetworkScanToken? _scanToken;
  double _scanProgress = 0;
  int _scanTotalIps = 0;
  int _scanCompletedIps = 0;
  int _scanFoundCount = 0;
  String? _scanCurrentIp;
  bool _scanCancelled = false;

  // Getters
  List<SmartTV> get tvs => List.unmodifiable(_tvs);
  List<SmartTV> get favoriteTVs => _tvs.where((tv) => tv.isFavorite).toList();
  List<SmartTV> get onlineTVs => _tvs.where((tv) => tv.isOnline).toList();
  SmartTV? get selectedTV {
    if (_selectedTVId != null) {
      try {
        return _tvs.firstWhere((tv) => tv.id == _selectedTVId);
      } catch (e) {
        // Si la TV seleccionada ya no existe, seleccionar la primera disponible
        _selectedTVId = _tvs.isNotEmpty ? _tvs.first.id : null;
        return _tvs.isNotEmpty ? _tvs.first : null;
      }
    }
    return _tvs.isNotEmpty ? _tvs.first : null;
  }

  String? get selectedTVId => _selectedTVId;
  bool get isScanning => _isScanning;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get hasTVs => _tvs.isNotEmpty;
  int get tvCount => _tvs.length;
  double get scanProgress => _scanProgress;
  int get scanTotalIps => _scanTotalIps;
  int get scanCompletedIps => _scanCompletedIps;
  int get scanFoundCount => _scanFoundCount;
  String? get scanCurrentIp => _scanCurrentIp;
  bool get isScanCancelled => _scanCancelled;

  // Inicialización
  Future<void> initialize() async {
    _setLoading(true);
    try {
      await _loadTVsFromStorage();
      await _loadSelectedTVFromStorage();
      
      // Si no hay TVs registradas, añadir una TV de demo para mostrar cómo se ve
      if (_tvs.isEmpty) {
        await _addDemoTV();
      }
    } catch (error, stackTrace) {
      _setError('Error al inicializar las TVs: $error');
      _logger.e('Error al inicializar las TVs', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    } finally {
      _setLoading(false);
    }
  }

  /// Añade una TV de demostración para que el usuario vea cómo se ve
  Future<void> _addDemoTV() async {
    final demoTV = SmartTV(
      id: 'demo_tv_001',
      name: 'TV Sala (Demo)',
      brand: TVBrand.philips,
      ip: '192.168.1.100',
      port: 1925,
      room: 'Sala de estar',
      macAddress: 'AA:BB:CC:DD:EE:FF',
      model: 'Android TV Demo',
      isOnline: false,
      isRegistered: true,
      isPaired: false,
    );
    
    _tvs.add(demoTV);
    await _saveTVsToStorage();
    await selectTV(demoTV.id);
    _logger.i('Demo TV added for first-time users');
  }

  // Gestión de TVs
  Future<void> addTV(SmartTV tv) async {
    try {
      // Verificar si ya existe una TV con la misma IP
      if (_tvs.any((existingTV) => existingTV.ip == tv.ip)) {
        _setError('Ya existe una TV con esta dirección IP');
        return;
      }

      _tvs.add(tv);
      await _saveTVsToStorage();

      // Seleccionar automáticamente si es la primera TV
      if (_selectedTVId == null) {
        await selectTV(tv.id);
      }

      _clearError();
      notifyListeners();
    } catch (error, stackTrace) {
      _setError('Error al añadir la TV: $error');
      _logger.e('Error al añadir la TV', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    }
  }

  Future<void> removeTV(String tvId) async {
    try {
      _tvs.removeWhere((tv) => tv.id == tvId);

      // Si la TV eliminada era la seleccionada, seleccionar otra
      if (_selectedTVId == tvId) {
        _selectedTVId = _tvs.isNotEmpty ? _tvs.first.id : null;
        await _saveSelectedTVToStorage();
      }

      await _saveTVsToStorage();
      _clearError();
      notifyListeners();
    } catch (error, stackTrace) {
      _setError('Error al eliminar la TV: $error');
      _logger.e('Error al eliminar la TV', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    }
  }

  Future<void> updateTV(SmartTV updatedTV) async {
    try {
      final index = _tvs.indexWhere((tv) => tv.id == updatedTV.id);
      if (index != -1) {
        _tvs[index] = updatedTV;
        await _saveTVsToStorage();
        _clearError();
        notifyListeners();
      }
    } catch (error, stackTrace) {
      _setError('Error al actualizar la TV: $error');
      _logger.e('Error al actualizar la TV', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    }
  }

  Future<void> toggleFavorite(String tvId) async {
    try {
      final index = _tvs.indexWhere((tv) => tv.id == tvId);
      if (index != -1) {
        _tvs[index] = _tvs[index].copyWith(isFavorite: !_tvs[index].isFavorite);
        await _saveTVsToStorage();
        notifyListeners();
      }
    } catch (error, stackTrace) {
      _setError('Error al cambiar favorito: $error');
      _logger.e('Error al cambiar favorito', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    }
  }

  Future<NetworkScanSummary> scanNetwork(BuildContext context) async {
    if (_isScanning) {
      return NetworkScanSummary(
        totalCandidates: _scanTotalIps,
        scanned: _scanCompletedIps,
        found: _scanFoundCount,
        cancelled: true,
        errorMessage: 'Ya hay un escaneo en progreso.',
      );
    }

    _errorMessage = null;

    final settings = context.read<SettingsProvider>();

    final token = NetworkScanToken();
    _scanToken = token;
    _isScanning = true;
    _scanCancelled = false;
    _scanProgress = 0;
    _scanTotalIps = settings.scanIpEnd - settings.scanIpStart + 1;
    _scanCompletedIps = 0;
    _scanFoundCount = 0;
    _scanCurrentIp = null;
    notifyListeners();

    int newlyAdded = 0;

    try {
      final stream = _networkService.scanNetworkStream(
        subnet: settings.subnet,
        startIp: settings.scanIpStart,
        endIp: settings.scanIpEnd,
        token: token,
      );

      await for (final event in stream) {
        if (token.isCancelled) {
          _scanCancelled = true;
          break;
        }

        final progress = event.progress;
        _scanCompletedIps = progress.current;
        _scanTotalIps = progress.total;
        _scanFoundCount = progress.foundCount;
        _scanCurrentIp = progress.currentIp;
        _scanProgress = progress.ratio;

        final tv = event.tv;
        if (tv != null && !_tvs.any((existing) => existing.ip == tv.ip)) {
          _tvs.add(tv);
          newlyAdded++;
        }
        notifyListeners();
      }

      await _saveTVsToStorage();

      return NetworkScanSummary(
        totalCandidates: _scanTotalIps,
        scanned: _scanCompletedIps,
        found: newlyAdded,
        cancelled: _scanCancelled || token.isCancelled,
      );
    } catch (error, stackTrace) {
      final message = 'Error al escanear la red: $error';
      _logger.e(message, error: error, stackTrace: stackTrace);
      _errorMessage = message;
      notifyListeners();

      return NetworkScanSummary(
        totalCandidates: _scanTotalIps,
        scanned: _scanCompletedIps,
        found: newlyAdded,
        cancelled: true,
        errorMessage: message,
      );
    } finally {
      _isScanning = false;
      _scanToken = null;
      _scanProgress = 0;
      _scanCompletedIps = 0;
      _scanTotalIps = 0;
      _scanFoundCount = 0;
      _scanCurrentIp = null;
      _scanCancelled = false;
      notifyListeners();
    }
  }

  void cancelScan() {
    if (_scanToken == null) return;
    _scanCancelled = true;
    _scanToken!.cancel();
    notifyListeners();
  }

  Future<void> selectTV(String tvId) async {
    try {
      if (_tvs.any((tv) => tv.id == tvId)) {
        _selectedTVId = tvId;
        await _saveSelectedTVToStorage();
        _clearError();
        notifyListeners();
      }
    } catch (error, stackTrace) {
      _setError('Error al seleccionar la TV: $error');
      _logger.e('Error al seleccionar la TV', error: error, stackTrace: stackTrace);
      ErrorHandlerService.handleStorageError(null, error,
          showNotification: false);
    }
  }

  Future<void> updateTVStatus(
    String tvId, {
    bool? isOnline,
    bool? isConnecting,
    bool? isPaired,
    DateTime? lastControlled,
  }) async {
    try {
      final index = _tvs.indexWhere((tv) => tv.id == tvId);
      if (index != -1) {
        _tvs[index] = _tvs[index].copyWith(
          isOnline: isOnline,
          isConnecting: isConnecting,
          isPaired: isPaired,
          lastControlled: lastControlled,
        );

        // Solo guardar si hay cambios importantes
        if (isOnline != null || isPaired != null) {
          await _saveTVsToStorage();
        }

        notifyListeners();
      }
    } catch (error, stackTrace) {
      _logger.e('Error updating TV status', error: error, stackTrace: stackTrace);
    }
  }

  // Filtros y búsqueda
  List<SmartTV> filterTVsByBrand(TVBrand brand) {
    return _tvs.where((tv) => tv.brand == brand).toList();
  }

  List<SmartTV> filterTVsByRoom(String room) {
    return _tvs
        .where((tv) => tv.room.toLowerCase().contains(room.toLowerCase()))
        .toList();
  }

  List<SmartTV> searchTVs(String query) {
    final lowercaseQuery = query.toLowerCase();
    return _tvs
        .where((tv) =>
            tv.name.toLowerCase().contains(lowercaseQuery) ||
            tv.room.toLowerCase().contains(lowercaseQuery) ||
            tv.ip.contains(query) ||
            tv.brand.toString().toLowerCase().contains(lowercaseQuery))
        .toList();
  }

  // Almacenamiento
  Future<void> _loadTVsFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final tvsJson = prefs.getString(AppConstants.keyTvList);

      if (tvsJson != null) {
        final List<dynamic> tvsList = jsonDecode(tvsJson);
        _tvs.clear();
        _tvs.addAll(tvsList.map((tvJson) => SmartTV.fromJson(tvJson)));
      }
    } catch (error, stackTrace) {
      _logger.e('Error loading TVs from storage', error: error, stackTrace: stackTrace);
      rethrow;
    }
  }

  Future<void> _saveTVsToStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final tvsJson = jsonEncode(_tvs.map((tv) => tv.toJson()).toList());
      await prefs.setString(AppConstants.keyTvList, tvsJson);
    } catch (error, stackTrace) {
      _logger.e('Error saving TVs to storage', error: error, stackTrace: stackTrace);
      rethrow;
    }
  }

  Future<void> _loadSelectedTVFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _selectedTVId = prefs.getString(AppConstants.keySelectedTv);

      // Verificar que la TV seleccionada aún existe
      if (_selectedTVId != null && !_tvs.any((tv) => tv.id == _selectedTVId)) {
        _selectedTVId = _tvs.isNotEmpty ? _tvs.first.id : null;
        await _saveSelectedTVToStorage();
      }
    } catch (error, stackTrace) {
      _logger.e('Error loading selected TV from storage', error: error, stackTrace: stackTrace);
    }
  }

  Future<void> _saveSelectedTVToStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (_selectedTVId != null) {
        await prefs.setString(AppConstants.keySelectedTv, _selectedTVId!);
      } else {
        await prefs.remove(AppConstants.keySelectedTv);
      }
    } catch (error, stackTrace) {
      _logger.e('Error saving selected TV to storage', error: error, stackTrace: stackTrace);
      rethrow;
    }
  }

  // Gestión de estado interno
  void _setLoading(bool loading) {
    _isLoading = loading;
    if (loading) _clearError();
    notifyListeners();
  }

  void _setError(String error) {
    _errorMessage = error;
    _isLoading = false;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _networkService.dispose();
    super.dispose();
  }

  // Limpieza se maneja automáticamente por ChangeNotifier
}
