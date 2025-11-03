import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mi_app_expriment2/services/command_history_service.dart';
import 'package:mi_app_expriment2/models/barril_models.dart';

void main() {
  group('CommandHistoryService', () {
    late CommandHistoryService historyService;

    setUp(() async {
      SharedPreferences.setMockInitialValues({});
      historyService = CommandHistoryService();
      await historyService.initialize();
    });

    test('should initialize with empty history', () {
      final history = historyService.getHistory();
      expect(history, isEmpty);
    });

    test('should log command successfully', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(
        tv: tv,
        command: 'power',
        wasSuccessful: true,
      );

      final history = historyService.getHistory();
      expect(history.length, equals(1));
      expect(history.first.command, equals('power'));
      expect(history.first.wasSuccessful, isTrue);
    });

    test('should log failed command with error message', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await historyService.logCommand(
        tv: tv,
        command: 'volume_up',
        wasSuccessful: false,
        errorMessage: 'Connection timeout',
      );

      final history = historyService.getHistory();
      expect(history.length, equals(1));
      expect(history.first.wasSuccessful, isFalse);
      expect(history.first.errorMessage, equals('Connection timeout'));
    });

    test('should filter history by TV', () async {
      final tv1 = SmartTV(
        id: 'tv-filter-1',
        name: 'TV 1',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final tv2 = SmartTV(
        id: 'tv-filter-2',
        name: 'TV 2',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await historyService.logCommand(tv: tv1, command: 'power');
      await historyService.logCommand(tv: tv2, command: 'volume_up');
      await historyService.logCommand(tv: tv1, command: 'mute');

      final tv1History = historyService.getHistoryForTV(tv1.id);
      expect(tv1History.length, equals(2));
      expect(tv1History.every((e) => e.tvId == tv1.id), isTrue);
    });

    test('should get successful commands only', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(
        tv: tv,
        command: 'power',
        wasSuccessful: true,
      );
      await historyService.logCommand(
        tv: tv,
        command: 'volume_up',
        wasSuccessful: false,
      );
      await historyService.logCommand(
        tv: tv,
        command: 'mute',
        wasSuccessful: true,
      );

      final successfulCommands = historyService.getSuccessfulCommands();
      expect(successfulCommands.length, equals(2));
      expect(successfulCommands.every((e) => e.wasSuccessful), isTrue);
    });

    test('should get failed commands only', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(
        tv: tv,
        command: 'power',
        wasSuccessful: true,
      );
      await historyService.logCommand(
        tv: tv,
        command: 'volume_up',
        wasSuccessful: false,
      );

      final failedCommands = historyService.getFailedCommands();
      expect(failedCommands.length, equals(1));
      expect(failedCommands.every((e) => !e.wasSuccessful), isTrue);
    });

    test('should generate statistics correctly', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      // Añadir varios comandos
      await historyService.logCommand(tv: tv, command: 'power', wasSuccessful: true);
      await historyService.logCommand(tv: tv, command: 'power', wasSuccessful: true);
      await historyService.logCommand(tv: tv, command: 'volume_up', wasSuccessful: true);
      await historyService.logCommand(tv: tv, command: 'mute', wasSuccessful: false);

      final stats = historyService.getStatistics();

      expect(stats['totalCommands'], equals(4));
      expect(stats['successfulCommands'], equals(3));
      expect(stats['failedCommands'], equals(1));
      expect(stats['successRate'], equals('75.0'));
      expect(stats['mostUsedCommands'], isNotEmpty);
    });

    test('should search history', () async {
      final tv1 = SmartTV(
        name: 'Samsung TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final tv2 = SmartTV(
        name: 'LG TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await historyService.logCommand(tv: tv1, command: 'power');
      await historyService.logCommand(tv: tv2, command: 'volume_up');

      final results = historyService.searchHistory('samsung');
      expect(results.length, equals(1));
      expect(results.first.tvName, contains('Samsung'));
    });

    test('should limit history size', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      // Añadir más de 100 comandos
      for (int i = 0; i < 110; i++) {
        await historyService.logCommand(tv: tv, command: 'test_$i');
      }

      final history = historyService.getHistory();
      expect(history.length, equals(100));
    });

    test('should clear history', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(tv: tv, command: 'power');
      await historyService.logCommand(tv: tv, command: 'volume_up');

      await historyService.clearHistory();

      final history = historyService.getHistory();
      expect(history, isEmpty);
    });

    test('should clear history for specific TV', () async {
      final tv1 = SmartTV(
        id: 'tv-1',
        name: 'TV 1',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final tv2 = SmartTV(
        id: 'tv-2',
        name: 'TV 2',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await historyService.logCommand(tv: tv1, command: 'power');
      await historyService.logCommand(tv: tv2, command: 'volume_up');
      await historyService.logCommand(tv: tv1, command: 'mute');

      await historyService.clearHistoryForTV(tv1.id);

      final history = historyService.getHistory();
      expect(history.length, equals(1));
      expect(history.first.tvId, equals(tv2.id));
    });

    test('should remove specific entry', () async {
      final tv = SmartTV(
        id: 'tv-test',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(tv: tv, command: 'power');
      await Future.delayed(const Duration(milliseconds: 10)); // Asegurar IDs únicos
      await historyService.logCommand(tv: tv, command: 'volume_up');

      final history = historyService.getHistory();
      final entryToRemove = history.first;

      await historyService.removeEntry(entryToRemove.id);

      final updatedHistory = historyService.getHistory();
      expect(updatedHistory.length, equals(1));
      expect(updatedHistory.any((e) => e.id == entryToRemove.id), isFalse);
    });

    test('should get today history', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(tv: tv, command: 'power');

      final todayHistory = historyService.getTodayHistory();
      expect(todayHistory.length, greaterThanOrEqualTo(1));
    });

    test('should persist history between sessions', () async {
      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await historyService.logCommand(tv: tv, command: 'power');

      // Crear nueva instancia del servicio
      final newHistoryService = CommandHistoryService();
      await newHistoryService.initialize();

      final history = newHistoryService.getHistory();
      expect(history.length, equals(1));
      expect(history.first.command, equals('power'));
    });
  });
}
