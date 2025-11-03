/*
Servicio de Historial de Comandos - Command History Service
Rastrea y almacena el historial de comandos enviados a las TVs
*/

import 'dart:convert';
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/barril_models.dart';

class CommandHistoryEntry {
  final String id;
  final String tvId;
  final String tvName;
  final String command;
  final DateTime timestamp;
  final bool wasSuccessful;
  final String? errorMessage;

  CommandHistoryEntry({
    String? id,
    required this.tvId,
    required this.tvName,
    required this.command,
    DateTime? timestamp,
    this.wasSuccessful = true,
    this.errorMessage,
  })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tvId': tvId,
      'tvName': tvName,
      'command': command,
      'timestamp': timestamp.toIso8601String(),
      'wasSuccessful': wasSuccessful,
      'errorMessage': errorMessage,
    };
  }

  factory CommandHistoryEntry.fromJson(Map<String, dynamic> json) {
    return CommandHistoryEntry(
      id: json['id'],
      tvId: json['tvId'],
      tvName: json['tvName'],
      command: json['command'],
      timestamp: DateTime.parse(json['timestamp']),
      wasSuccessful: json['wasSuccessful'] ?? true,
      errorMessage: json['errorMessage'],
    );
  }
}

class CommandHistoryService {
  static const String _kHistoryKey = 'command_history';
  static const int _maxHistorySize = 100;

  SharedPreferences? _prefs;
  final List<CommandHistoryEntry> _history = [];
  final _logger = Logger();

  /// Inicializa el servicio
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    await _loadHistory();
  }

  /// Registra un comando en el historial
  Future<void> logCommand({
    required SmartTV tv,
    required String command,
    bool wasSuccessful = true,
    String? errorMessage,
  }) async {
    final entry = CommandHistoryEntry(
      tvId: tv.id,
      tvName: tv.name,
      command: command,
      wasSuccessful: wasSuccessful,
      errorMessage: errorMessage,
    );

    _history.insert(0, entry);

    // Limitar tamaño del historial
    if (_history.length > _maxHistorySize) {
      _history.removeRange(_maxHistorySize, _history.length);
    }

    await _saveHistory();
  }

  /// Obtiene todo el historial
  List<CommandHistoryEntry> getHistory() {
    return List.unmodifiable(_history);
  }

  /// Obtiene el historial de una TV específica
  List<CommandHistoryEntry> getHistoryForTV(String tvId) {
    return _history.where((entry) => entry.tvId == tvId).toList();
  }

  /// Obtiene el historial de comandos exitosos
  List<CommandHistoryEntry> getSuccessfulCommands() {
    return _history.where((entry) => entry.wasSuccessful).toList();
  }

  /// Obtiene el historial de comandos fallidos
  List<CommandHistoryEntry> getFailedCommands() {
    return _history.where((entry) => !entry.wasSuccessful).toList();
  }

  /// Obtiene el historial del día actual
  List<CommandHistoryEntry> getTodayHistory() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);

    return _history.where((entry) {
      final entryDate = DateTime(
        entry.timestamp.year,
        entry.timestamp.month,
        entry.timestamp.day,
      );
      return entryDate.isAtSameMomentAs(today);
    }).toList();
  }

  /// Obtiene estadísticas del historial
  Map<String, dynamic> getStatistics() {
    final totalCommands = _history.length;
    final successfulCommands =
        _history.where((e) => e.wasSuccessful).length;
    final failedCommands = totalCommands - successfulCommands;

    // Comandos más usados
    final commandCounts = <String, int>{};
    for (final entry in _history) {
      commandCounts[entry.command] = (commandCounts[entry.command] ?? 0) + 1;
    }

    final sortedCommands = commandCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final mostUsedCommands = sortedCommands.take(5).map((e) => {
          'command': e.key,
          'count': e.value,
        }).toList();

    // TVs más controladas
    final tvCounts = <String, Map<String, dynamic>>{};
    for (final entry in _history) {
      if (!tvCounts.containsKey(entry.tvId)) {
        tvCounts[entry.tvId] = {
          'tvId': entry.tvId,
          'tvName': entry.tvName,
          'count': 0,
        };
      }
      tvCounts[entry.tvId]!['count'] =
          (tvCounts[entry.tvId]!['count'] as int) + 1;
    }

    final sortedTVs = tvCounts.values.toList()
      ..sort((a, b) => (b['count'] as int).compareTo(a['count'] as int));

    final mostControlledTVs = sortedTVs.take(5).toList();

    return {
      'totalCommands': totalCommands,
      'successfulCommands': successfulCommands,
      'failedCommands': failedCommands,
      'successRate': totalCommands > 0
          ? (successfulCommands / totalCommands * 100).toStringAsFixed(1)
          : '0',
      'mostUsedCommands': mostUsedCommands,
      'mostControlledTVs': mostControlledTVs,
      'todayCommands': getTodayHistory().length,
    };
  }

  /// Busca en el historial
  List<CommandHistoryEntry> searchHistory(String query) {
    final lowercaseQuery = query.toLowerCase();
    return _history.where((entry) {
      return entry.tvName.toLowerCase().contains(lowercaseQuery) ||
          entry.command.toLowerCase().contains(lowercaseQuery);
    }).toList();
  }

  /// Limpia el historial completo
  Future<void> clearHistory() async {
    _history.clear();
    await _saveHistory();
  }

  /// Limpia el historial de una TV específica
  Future<void> clearHistoryForTV(String tvId) async {
    _history.removeWhere((entry) => entry.tvId == tvId);
    await _saveHistory();
  }

  /// Limpia el historial anterior a una fecha
  Future<void> clearHistoryBefore(DateTime date) async {
    _history.removeWhere((entry) => entry.timestamp.isBefore(date));
    await _saveHistory();
  }

  /// Elimina una entrada específica del historial
  Future<void> removeEntry(String entryId) async {
    _history.removeWhere((entry) => entry.id == entryId);
    await _saveHistory();
  }

  /// Carga el historial desde el almacenamiento
  Future<void> _loadHistory() async {
    try {
      final jsonString = _prefs!.getString(_kHistoryKey);
      if (jsonString != null && jsonString.isNotEmpty) {
        final List<dynamic> jsonList = jsonDecode(jsonString);
        _history.clear();
        _history.addAll(
          jsonList.map((json) => CommandHistoryEntry.fromJson(json)),
        );
      }
    } catch (e, s) {
      _logger.e('Error loading command history', error: e, stackTrace: s);
    }
  }

  /// Guarda el historial en el almacenamiento
  Future<void> _saveHistory() async {
    try {
      final jsonString = jsonEncode(
        _history.map((entry) => entry.toJson()).toList(),
      );
      await _prefs!.setString(_kHistoryKey, jsonString);
    } catch (e, s) {
      _logger.e('Error saving command history', error: e, stackTrace: s);
    }
  }
}
