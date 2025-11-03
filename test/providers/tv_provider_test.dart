import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/models/smart_tv.dart';
import 'package:mi_app_expriment2/providers/settings_provider.dart';
import 'package:mi_app_expriment2/providers/tv_provider.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'tv_provider_test.mocks.dart';

@GenerateMocks([SettingsProvider, BuildContext])
void main() {
  group('TVProvider', () {
    late TVProvider tvProvider;

    setUp(() {
      // Mock SharedPreferences
      SharedPreferences.setMockInitialValues({});
      tvProvider = TVProvider();
    });

    test('should initialize with empty TV list', () {
      expect(tvProvider.tvs, isEmpty);
      expect(tvProvider.selectedTV, isNull);
      expect(tvProvider.hasTVs, isFalse);
      expect(tvProvider.tvCount, equals(0));
    });

    test('should add TV successfully', () async {
      final tv = SmartTV(
        id: 'test-tv-1',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await tvProvider.addTV(tv);

      expect(tvProvider.tvs, hasLength(1));
      expect(tvProvider.tvs.first.name, equals('Test TV'));
      expect(tvProvider.hasTVs, isTrue);
      expect(tvProvider.tvCount, equals(1));
    });

    test('should not add TV with duplicate IP', () async {
      final tv1 = SmartTV(
        id: 'test-tv-1',
        name: 'Test TV 1',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final tv2 = SmartTV(
        id: 'test-tv-2',
        name: 'Test TV 2',
        brand: TVBrand.lg,
        ip: '192.168.1.100', // Same IP
      );

      await tvProvider.addTV(tv1);
      await tvProvider.addTV(tv2);

      expect(tvProvider.tvs, hasLength(1));
      expect(tvProvider.errorMessage, isNotNull);
      expect(tvProvider.errorMessage, contains('Ya existe una TV'));
    });

    test('should select first TV automatically when adding first TV', () async {
      final tv = SmartTV(
        id: 'test-tv-1',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await tvProvider.addTV(tv);

      expect(tvProvider.selectedTVId, equals('test-tv-1'));
      expect(tvProvider.selectedTV, isNotNull);
      expect(tvProvider.selectedTV!.name, equals('Test TV'));
    });

    test('should remove TV successfully', () async {
      final tv = SmartTV(
        id: 'test-tv-1',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await tvProvider.addTV(tv);
      expect(tvProvider.tvs, hasLength(1));

      await tvProvider.removeTV('test-tv-1');
      expect(tvProvider.tvs, isEmpty);
      expect(tvProvider.selectedTV, isNull);
    });

    test('should toggle favorite status', () async {
      final tv = SmartTV(
        id: 'test-tv-1',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        isFavorite: false,
      );

      await tvProvider.addTV(tv);
      expect(tvProvider.tvs.first.isFavorite, isFalse);

      await tvProvider.toggleFavorite('test-tv-1');
      expect(tvProvider.tvs.first.isFavorite, isTrue);

      await tvProvider.toggleFavorite('test-tv-1');
      expect(tvProvider.tvs.first.isFavorite, isFalse);
    });

    test('should filter TVs by brand', () async {
      final samsungTV = SmartTV(
        id: 'samsung-tv',
        name: 'Samsung TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final lgTV = SmartTV(
        id: 'lg-tv',
        name: 'LG TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await tvProvider.addTV(samsungTV);
      await tvProvider.addTV(lgTV);

      final samsungTVs = tvProvider.filterTVsByBrand(TVBrand.samsung);
      expect(samsungTVs, hasLength(1));
      expect(samsungTVs.first.brand, equals(TVBrand.samsung));
    });

    test('should search TVs by name', () async {
      final tv1 = SmartTV(
        id: 'tv-1',
        name: 'Living Room TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      final tv2 = SmartTV(
        id: 'tv-2',
        name: 'Bedroom TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
      );

      await tvProvider.addTV(tv1);
      await tvProvider.addTV(tv2);

      final searchResults = tvProvider.searchTVs('living');
      expect(searchResults, hasLength(1));
      expect(searchResults.first.name, contains('Living Room'));
    });

    test('should search TVs by IP', () async {
      final tv = SmartTV(
        id: 'tv-1',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
      );

      await tvProvider.addTV(tv);

      final searchResults = tvProvider.searchTVs('192.168.1.100');
      expect(searchResults, hasLength(1));
      expect(searchResults.first.ip, equals('192.168.1.100'));
    });

    test('should return favorite TVs only', () async {
      final favoriteTV = SmartTV(
        id: 'fav-tv',
        name: 'Favorite TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        isFavorite: true,
      );

      final regularTV = SmartTV(
        id: 'regular-tv',
        name: 'Regular TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
        isFavorite: false,
      );

      await tvProvider.addTV(favoriteTV);
      await tvProvider.addTV(regularTV);

      final favorites = tvProvider.favoriteTVs;
      expect(favorites, hasLength(1));
      expect(favorites.first.isFavorite, isTrue);
      expect(favorites.first.name, equals('Favorite TV'));
    });

    test('should return online TVs only', () async {
      final onlineTV = SmartTV(
        id: 'online-tv',
        name: 'Online TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        isOnline: true,
      );

      final offlineTV = SmartTV(
        id: 'offline-tv',
        name: 'Offline TV',
        brand: TVBrand.lg,
        ip: '192.168.1.101',
        isOnline: false,
      );

      await tvProvider.addTV(onlineTV);
      await tvProvider.addTV(offlineTV);

      final onlineTVs = tvProvider.onlineTVs;
      expect(onlineTVs, hasLength(1));
      expect(onlineTVs.first.isOnline, isTrue);
      expect(onlineTVs.first.name, equals('Online TV'));
    });

    test('should update TV status', () async {
      final tv = SmartTV(
        id: 'test-tv',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        isOnline: false,
        isConnecting: false,
      );

      await tvProvider.addTV(tv);

      await tvProvider.updateTVStatus(
        'test-tv',
        isOnline: true,
        isConnecting: false,
      );

      expect(tvProvider.tvs.first.isOnline, isTrue);
      expect(tvProvider.tvs.first.isConnecting, isFalse);
    });

    test('should handle scanning state', () async {
      final mockContext = MockBuildContext();
      final mockSettingsProvider = MockSettingsProvider();

      when(mockContext.read<SettingsProvider>()).thenReturn(mockSettingsProvider);
      when(mockSettingsProvider.subnet).thenReturn('192.168.1');
      when(mockSettingsProvider.scanIpStart).thenReturn(1);
      when(mockSettingsProvider.scanIpEnd).thenReturn(10);

      expect(tvProvider.isScanning, isFalse);

      final summary = tvProvider.scanNetwork(mockContext);

      expect(tvProvider.isScanning, isTrue);

      await summary;

      expect(tvProvider.isScanning, isFalse);
    });
  });

  group('SmartTV Model', () {
    test('should serialize to JSON correctly', () {
      final tv = SmartTV(
        id: 'test-tv',
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        port: 8080,
        room: 'Living Room',
        isFavorite: true,
      );

      final json = tv.toJson();

      expect(json['id'], equals('test-tv'));
      expect(json['name'], equals('Test TV'));
      expect(json['brand'], contains('samsung'));
      expect(json['ip'], equals('192.168.1.100'));
      expect(json['port'], equals(8080));
      expect(json['room'], equals('Living Room'));
      expect(json['isFavorite'], isTrue);
    });

    test('should deserialize from JSON correctly', () {
      final json = {
        'id': 'test-tv',
        'name': 'Test TV',
        'brand': 'TVBrand.samsung',
        'ip': '192.168.1.100',
        'port': 8080,
        'room': 'Living Room',
        'isFavorite': true,
        'isOnline': false,
        'lastPing': DateTime.now().toIso8601String(),
      };

      final tv = SmartTV.fromJson(json);

      expect(tv.id, equals('test-tv'));
      expect(tv.name, equals('Test TV'));
      expect(tv.brand, equals(TVBrand.samsung));
      expect(tv.ip, equals('192.168.1.100'));
      expect(tv.port, equals(8080));
      expect(tv.room, equals('Living Room'));
      expect(tv.isFavorite, isTrue);
      expect(tv.isOnline, isFalse);
    });

    test('should create copy with modified values', () {
      final originalTV = SmartTV(
        id: 'test-tv',
        name: 'Original Name',
        brand: TVBrand.samsung,
        ip: '192.168.1.100',
        isFavorite: false,
      );

      final modifiedTV = originalTV.copyWith(
        name: 'Modified Name',
        isFavorite: true,
      );

      expect(modifiedTV.id, equals(originalTV.id)); // Unchanged
      expect(modifiedTV.brand, equals(originalTV.brand)); // Unchanged
      expect(modifiedTV.ip, equals(originalTV.ip)); // Unchanged
      expect(modifiedTV.name, equals('Modified Name')); // Changed
      expect(modifiedTV.isFavorite, isTrue); // Changed
    });
  });
}
