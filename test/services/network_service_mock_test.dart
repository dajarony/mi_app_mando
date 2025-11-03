import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:mi_app_expriment2/services/network_service.dart';
import 'package:mi_app_expriment2/models/smart_tv.dart';



@GenerateMocks([Dio])
void main() {
  group('NetworkService con Mocks', () {


    test('getCurrentSubnet debe retornar subnet por defecto en caso de error', () async {
      final networkService = NetworkService();
      final subnet = await networkService.getCurrentSubnet();

      expect(subnet, isNotNull);
      expect(subnet.split('.').length, equals(3));

      networkService.dispose();
    });

    test('validateTVConnection debe retornar false para IP inválida', () async {
      final networkService = NetworkService();

      final isValid = await networkService.validateTVConnection(
        '192.168.1.999',
        8080,
      );

      expect(isValid, isFalse);

      networkService.dispose();
    });

    test('validateTVConnection debe retornar false para puerto inválido', () async {
      final networkService = NetworkService();

      final isValid = await networkService.validateTVConnection(
        '192.168.1.1',
        99999,
      );

      expect(isValid, isFalse);

      networkService.dispose();
    });

    test('getTVInfo debe retornar null para TV desconocida', () async {
      final networkService = NetworkService();

      final tvInfo = await networkService.getTVInfo(
        SmartTV(
          name: 'Test TV',
          brand: TVBrand.unknown,
          ip: '192.168.1.999',
          port: 8080,
        ),
      );

      expect(tvInfo, isNull);

      networkService.dispose();
    });

    test('scanNetworkStream debe emitir eventos de progreso', () async {
      final networkService = NetworkService();
      final events = <NetworkScanEvent>[];

      // Escanear solo 2 IPs para el test
      final stream = networkService.scanNetworkStream(
        subnet: '192.168.1',
        startIp: 1,
        endIp: 2,
        perIpDelay: Duration.zero,
      );

      await for (final event in stream) {
        events.add(event);
      }

      expect(events.length, equals(2));
      expect(events.first.progress.current, equals(1));
      expect(events.last.progress.current, equals(2));
      expect(events.last.progress.total, equals(2));

      networkService.dispose();
    });

    test('scanNetworkStream debe respetar cancelación', () async {
      final networkService = NetworkService();
      final token = NetworkScanToken();
      final events = <NetworkScanEvent>[];

      final stream = networkService.scanNetworkStream(
        subnet: '192.168.1',
        startIp: 1,
        endIp: 100,
        token: token,
        perIpDelay: Duration.zero,
      );

      int count = 0;
      await for (final event in stream) {
        events.add(event);
        count++;
        if (count >= 5) {
          token.cancel();
        }
      }

      // Debe detenerse después de la cancelación
      expect(events.length, lessThan(100));
      expect(events.length, greaterThanOrEqualTo(5));

      networkService.dispose();
    });

    test('validateSmartTVConnection debe validar TV correctamente', () async {
      final networkService = NetworkService();

      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.samsung,
        ip: '192.168.1.999',
        port: 8080,
      );

      final isValid = await networkService.validateSmartTVConnection(tv);

      expect(isValid, isFalse);

      networkService.dispose();
    });

    test('pairWithTV debe retornar true para marcas no soportadas', () async {
      final networkService = NetworkService();

      final tv = SmartTV(
        name: 'Test TV',
        brand: TVBrand.unknown,
        ip: '192.168.1.100',
        port: 8080,
      );

      final paired = await networkService.pairWithTV(tv);

      expect(paired, isTrue);

      networkService.dispose();
    });

    test('scanNetworkForTVs debe llamar onProgress callback', () async {
      final networkService = NetworkService();
      int progressCalls = 0;
      int lastCurrent = 0;
      int lastTotal = 0;

      final tvs = await networkService.scanNetworkForTVs(
        subnet: '192.168.1',
        startIp: 1,
        endIp: 3,
        onProgress: (current, total) {
          progressCalls++;
          lastCurrent = current;
          lastTotal = total;
        },
      );

      expect(tvs, isNotNull);
      expect(tvs, isA<List<SmartTV>>());
      expect(progressCalls, greaterThan(0));
      expect(lastTotal, equals(3));
      expect(lastCurrent, equals(3));

      networkService.dispose();
    });

    test('NetworkScanToken debe permitir cancelación', () {
      final token = NetworkScanToken();

      expect(token.isCancelled, isFalse);

      token.cancel();

      expect(token.isCancelled, isTrue);
    });

    test('NetworkScanProgress debe calcular ratio correctamente', () {
      const progress = NetworkScanProgress(
        current: 50,
        total: 100,
        currentIp: '192.168.1.50',
        foundCount: 5,
      );

      expect(progress.ratio, equals(0.5));
    });

    test('NetworkScanProgress debe retornar 0 cuando total es 0', () {
      const progress = NetworkScanProgress(
        current: 0,
        total: 0,
        currentIp: '192.168.1.0',
        foundCount: 0,
      );

      expect(progress.ratio, equals(0));
    });

    test('NetworkScanSummary debe detectar errores correctamente', () {
      const summaryWithError = NetworkScanSummary(
        totalCandidates: 100,
        scanned: 50,
        found: 2,
        cancelled: false,
        errorMessage: 'Error de prueba',
      );

      expect(summaryWithError.hasError, isTrue);

      const summaryWithoutError = NetworkScanSummary(
        totalCandidates: 100,
        scanned: 100,
        found: 5,
        cancelled: false,
      );

      expect(summaryWithoutError.hasError, isFalse);
    });
  });
}
