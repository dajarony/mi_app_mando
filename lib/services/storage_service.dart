/*
Servicio de Almacenamiento - Storage Service
Responsable de persistir y recuperar datos localmente
*/

import 'dart:convert';
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/barril_models.dart';

class StorageService {
  static const String _kTVsKey = 'saved_tvs';
  static const String _kSelectedTVKey = 'selected_tv_id';
  static const String _kFavoritesKey = 'favorite_tv_ids';
  static const String _kSettingsKey = 'app_settings';

  SharedPreferences? _prefs;
  final _logger = Logger();

  /// Inicializa el servicio
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
  }

  /// Guarda la lista de TVs
  Future<bool> saveTVs(List<SmartTV> tvs) async {
    try {
      final tvsJson = tvs.map((tv) => tv.toJson()).toList();
      final jsonString = jsonEncode(tvsJson);
      return await _prefs!.setString(_kTVsKey, jsonString);
    } catch (e, s) {
      _logger.e('Error guardando TVs', error: e, stackTrace: s);
      return false;
    }
  }

  /// Carga la lista de TVs guardadas
  Future<List<SmartTV>> loadTVs() async {
    try {
      final jsonString = _prefs!.getString(_kTVsKey);
      if (jsonString == null || jsonString.isEmpty) {
        return [];
      }

      final List<dynamic> tvsJson = jsonDecode(jsonString);
      return tvsJson.map((json) => SmartTV.fromJson(json)).toList();
    } catch (e, s) {
      _logger.e('Error cargando TVs', error: e, stackTrace: s);
      return [];
    }
  }

  /// Guarda una TV individual
  Future<bool> saveTV(SmartTV tv, List<SmartTV> existingTVs) async {
    try {
      final index = existingTVs.indexWhere((t) => t.id == tv.id);
      if (index >= 0) {
        existingTVs[index] = tv;
      } else {
        existingTVs.add(tv);
      }
      return await saveTVs(existingTVs);
    } catch (e, s) {
      _logger.e('Error guardando TV', error: e, stackTrace: s);
      return false;
    }
  }

  /// Elimina una TV
  Future<bool> deleteTV(String tvId, List<SmartTV> existingTVs) async {
    try {
      existingTVs.removeWhere((tv) => tv.id == tvId);
      return await saveTVs(existingTVs);
    } catch (e, s) {
      _logger.e('Error eliminando TV', error: e, stackTrace: s);
      return false;
    }
  }

  /// Obtiene el ID de la TV seleccionada
  String? getSelectedTVId() {
    return _prefs!.getString(_kSelectedTVKey);
  }

  /// Establece la TV seleccionada
  Future<bool> setSelectedTVId(String? tvId) async {
    if (tvId == null) {
      return await _prefs!.remove(_kSelectedTVKey);
    }
    return await _prefs!.setString(_kSelectedTVKey, tvId);
  }

  /// Obtiene los IDs de TVs favoritas
  List<String> getFavoriteTVIds() {
    return _prefs!.getStringList(_kFavoritesKey) ?? [];
  }

  /// Añade una TV a favoritos
  Future<bool> addToFavorites(String tvId) async {
    final favorites = getFavoriteTVIds();
    if (!favorites.contains(tvId)) {
      favorites.add(tvId);
      return await _prefs!.setStringList(_kFavoritesKey, favorites);
    }
    return true;
  }

  /// Elimina una TV de favoritos
  Future<bool> removeFromFavorites(String tvId) async {
    final favorites = getFavoriteTVIds();
    favorites.remove(tvId);
    return await _prefs!.setStringList(_kFavoritesKey, favorites);
  }

  /// Alterna el estado de favorito de una TV
  Future<bool> toggleFavorite(String tvId) async {
    final favorites = getFavoriteTVIds();
    if (favorites.contains(tvId)) {
      return await removeFromFavorites(tvId);
    } else {
      return await addToFavorites(tvId);
    }
  }

  /// Verifica si una TV es favorita
  bool isFavorite(String tvId) {
    return getFavoriteTVIds().contains(tvId);
  }

  /// Guarda configuraciones de la app
  Future<bool> saveSettings(Map<String, dynamic> settings) async {
    try {
      final jsonString = jsonEncode(settings);
      return await _prefs!.setString(_kSettingsKey, jsonString);
    } catch (e, s) {
      _logger.e('Error guardando configuraciones', error: e, stackTrace: s);
      return false;
    }
  }

  /// Carga configuraciones de la app
  Map<String, dynamic> loadSettings() {
    try {
      final jsonString = _prefs!.getString(_kSettingsKey);
      if (jsonString == null || jsonString.isEmpty) {
        return {};
      }
      return jsonDecode(jsonString) as Map<String, dynamic>;
    } catch (e, s) {
      _logger.e('Error cargando configuraciones', error: e, stackTrace: s);
      return {};
    }
  }

  /// Limpia todos los datos
  Future<bool> clearAll() async {
    return await _prefs!.clear();
  }

  /// Limpia solo las TVs
  Future<bool> clearTVs() async {
    final success1 = await _prefs!.remove(_kTVsKey);
    final success2 = await _prefs!.remove(_kSelectedTVKey);
    final success3 = await _prefs!.remove(_kFavoritesKey);
    return success1 && success2 && success3;
  }
}
