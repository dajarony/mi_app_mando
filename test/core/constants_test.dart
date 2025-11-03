import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/core/constants.dart';

void main() {
  group('AppConstants', () {
    test('should have correct default values', () {
      expect(AppConstants.appName, equals('Smart TV Manager'));
      expect(AppConstants.version, equals('1.0.0'));
      expect(AppConstants.defaultScanTimeout, equals(3000));
      expect(AppConstants.maxScanRetries, equals(2));
      expect(AppConstants.defaultSubnet, equals('192.168.1'));
    });

    test('should have scan range values', () {
      expect(AppConstants.scanRangeStart, equals(1));
      expect(AppConstants.scanRangeEnd, equals(50));
      expect(AppConstants.scanRangeStart, lessThan(AppConstants.scanRangeEnd));
    });

    test('should have UI constants', () {
      expect(AppConstants.cardBorderRadius, equals(12.0));
      expect(AppConstants.buttonBorderRadius, equals(8.0));
      expect(AppConstants.defaultPadding, equals(16.0));
      expect(AppConstants.smallPadding, equals(8.0));
      expect(AppConstants.largePadding, equals(24.0));
    });

    test('should have animation durations', () {
      expect(AppConstants.animationDurationMs, equals(300));
      expect(AppConstants.longAnimationDurationMs, equals(600));
      expect(AppConstants.quickAnimationDurationMs, equals(150));
      expect(AppConstants.quickAnimationDurationMs, lessThan(AppConstants.animationDurationMs));
      expect(AppConstants.animationDurationMs, lessThan(AppConstants.longAnimationDurationMs));
    });

    test('should have storage keys', () {
      expect(AppConstants.keyTvList, equals('saved_tvs'));
      expect(AppConstants.keySelectedTv, equals('selected_tv_id'));
      expect(AppConstants.keyPhilipsTvIp, equals('philips_tv_ip'));
      expect(AppConstants.keyUserPreferences, equals('user_preferences'));
    });
  });

  group('TVCommands', () {
    test('should have universal commands', () {
      expect(TVCommands.power, equals('power'));
      expect(TVCommands.volumeUp, equals('volume_up'));
      expect(TVCommands.volumeDown, equals('volume_down'));
      expect(TVCommands.mute, equals('mute'));
      expect(TVCommands.home, equals('home'));
      expect(TVCommands.back, equals('back'));
      expect(TVCommands.enter, equals('enter'));
      expect(TVCommands.menu, equals('menu'));
    });

    test('should have navigation commands', () {
      expect(TVCommands.up, equals('up'));
      expect(TVCommands.down, equals('down'));
      expect(TVCommands.left, equals('left'));
      expect(TVCommands.right, equals('right'));
    });

    test('should have channel commands', () {
      expect(TVCommands.channelUp, equals('channel_up'));
      expect(TVCommands.channelDown, equals('channel_down'));
    });

    test('should have streaming app commands', () {
      expect(TVCommands.netflix, equals('netflix'));
      expect(TVCommands.youtube, equals('youtube'));
      expect(TVCommands.amazon, equals('amazon'));
    });

    test('should have Philips specific commands mapping', () {
      expect(TVCommands.philipsCommands[TVCommands.power], equals('Standby'));
      expect(TVCommands.philipsCommands[TVCommands.volumeUp], equals('VolumeUp'));
      expect(TVCommands.philipsCommands[TVCommands.volumeDown], equals('VolumeDown'));
      expect(TVCommands.philipsCommands[TVCommands.up], equals('CursorUp'));
      expect(TVCommands.philipsCommands[TVCommands.down], equals('CursorDown'));
      expect(TVCommands.philipsCommands[TVCommands.left], equals('CursorLeft'));
      expect(TVCommands.philipsCommands[TVCommands.right], equals('CursorRight'));
      expect(TVCommands.philipsCommands[TVCommands.enter], equals('Confirm'));
      expect(TVCommands.philipsCommands[TVCommands.menu], equals('Options'));
    });

    test('should have number commands', () {
      expect(TVCommands.numbers, hasLength(10));
      expect(TVCommands.numbers, contains('0'));
      expect(TVCommands.numbers, contains('9'));
      expect(TVCommands.numbers.first, equals('0'));
      expect(TVCommands.numbers.last, equals('9'));
    });
  });

  group('AppColors', () {
    test('should have light theme colors', () {
      expect(AppColors.lightBackground, equals(0xFFE8E8E8));
      expect(AppColors.lightSurface, equals(0xFFF5F5F5));
      expect(AppColors.lightPrimary, equals(0xFF4299E1));
      expect(AppColors.lightText, equals(0xFF2D3748));
      expect(AppColors.lightTextSecondary, equals(0xFF4A5568));
    });

    test('should have neumorphic shadow colors', () {
      expect(AppColors.lightShadowDark, equals(0xFFBEBEBE));
      expect(AppColors.lightShadowLight, equals(0xFFFFFFFF));
    });

    test('should have status colors', () {
      expect(AppColors.success, equals(0xFF48BB78));
      expect(AppColors.error, equals(0xFFE53E3E));
      expect(AppColors.warning, equals(0xFFED8936));
      expect(AppColors.info, equals(0xFF3182CE));
    });

    test('should have brand colors', () {
      expect(AppColors.samsung, equals(0xFF1F4788));
      expect(AppColors.lg, equals(0xFFA50034));
      expect(AppColors.sony, equals(0xFF000000));
      expect(AppColors.philips, equals(0xFF0077BE));
      expect(AppColors.roku, equals(0xFF662D91));
    });
  });

  group('AppStrings', () {
    test('should have scanning related strings', () {
      expect(AppStrings.scanningNetworkTitle, equals('Escaneando Red'));
      expect(AppStrings.scanningNetworkSubtitle, equals('Buscando Smart TVs...'));
      expect(AppStrings.noTvsFoundTitle, equals('No se encontraron TVs'));
      expect(AppStrings.noTvsFoundSubtitle, equals('Verifica tu conexión WiFi'));
    });

    test('should have error related strings', () {
      expect(AppStrings.connectionErrorTitle, equals('Error de Conexión'));
      expect(AppStrings.connectionErrorSubtitle, equals('No se pudo conectar con la TV'));
    });

    test('should have success related strings', () {
      expect(AppStrings.tvRegisteredTitle, equals('TV Registrada'));
      expect(AppStrings.tvRegisteredSubtitle, equals('TV añadida exitosamente'));
    });

    test('should have form related strings', () {
      expect(AppStrings.tvNameLabel, equals('Nombre de la TV'));
      expect(AppStrings.tvNameHint, equals('Ej: TV Sala'));
      expect(AppStrings.tvIpLabel, equals('Dirección IP'));
      expect(AppStrings.tvIpHint, equals('192.168.1.100'));
      expect(AppStrings.tvRoomLabel, equals('Habitación'));
      expect(AppStrings.tvRoomHint, equals('Ej: Sala'));
    });

    test('should have button related strings', () {
      expect(AppStrings.registerButton, equals('Registrar TV'));
      expect(AppStrings.scanButton, equals('Escanear Red'));
      expect(AppStrings.saveButton, equals('Guardar'));
      expect(AppStrings.cancelButton, equals('Cancelar'));
    });

    test('should have navigation related strings', () {
      expect(AppStrings.homeTab, equals('Inicio'));
      expect(AppStrings.remoteTab, equals('Control'));
      expect(AppStrings.settingsTab, equals('Configuración'));
    });
  });

  group('TV Ports Configuration', () {
    test('should have correct ports for each brand', () {
      expect(AppConstants.tvPorts['samsung'], contains(8001));
      expect(AppConstants.tvPorts['samsung'], contains(8080));
      expect(AppConstants.tvPorts['lg'], contains(3000));
      expect(AppConstants.tvPorts['lg'], contains(3001));
      expect(AppConstants.tvPorts['sony'], contains(80));
      expect(AppConstants.tvPorts['sony'], contains(8080));
      expect(AppConstants.tvPorts['philips'], contains(1925));
      expect(AppConstants.tvPorts['roku'], contains(8060));
    });

    test('should have endpoints for each brand', () {
      expect(AppConstants.tvEndpoints['samsung'], 
          equals('/api/v2/channels/samsung.remote.control'));
      expect(AppConstants.tvEndpoints['lg'], 
          equals('/api/v2/channels/lg.remote.control'));
      expect(AppConstants.tvEndpoints['sony'], equals('/sony/IRCC'));
      expect(AppConstants.tvEndpoints['philips'], equals('/6/input/key'));
      expect(AppConstants.tvEndpoints['roku'], equals('/keypress'));
      expect(AppConstants.tvEndpoints['androidtv'], equals('/remote/input'));
    });
  });
}