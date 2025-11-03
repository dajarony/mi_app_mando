import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';

class PhilipsTvDirectService {
  late final Dio _dio;
  final String _tvIpAddress;
  final _logger = Logger();

  PhilipsTvDirectService({required String tvIpAddress})
      : _tvIpAddress = tvIpAddress {
    final options = BaseOptions(
      baseUrl: 'http://$_tvIpAddress:1925', // Usando HTTP y puerto 1925
      connectTimeout: const Duration(seconds: 3),
      receiveTimeout: const Duration(seconds: 3),
      sendTimeout: const Duration(seconds: 3),
      validateStatus: (status) => status! < 500,
    );
    _dio = Dio(options);

    // No se necesita configuración de certificado para HTTP.
  }

  /// Crea una instancia con la IP guardada en configuraciones
  static Future<PhilipsTvDirectService> createWithSavedIp() async {
    final prefs = await SharedPreferences.getInstance();
    final savedIp = prefs.getString('philips_tv_ip');
    if (savedIp == null) {
      throw Exception('Philips TV IP address not found in SharedPreferences.');
    }
    return PhilipsTvDirectService(tvIpAddress: savedIp);
  }

  /// Envía una tecla de control remoto a la TV.
  Future<void> sendKey(String key) async {
    try {
      await _dio.post(
        '/6/input/key', // Endpoint de la API v6 para teclas
        data: {'key': key},
      );
      _logger.d('Sent key: $key directly to TV');
    } catch (e, s) {
      _logger.e('Error sending key directly to TV', error: e, stackTrace: s);
    }
  }

  /// Ajusta el volumen de la TV.
  Future<void> setVolume(double volume) async {
    try {
      await _dio.post(
        '/6/audio/volume', // Endpoint de la API v6 para volumen
        data: {'muted': false, 'current': volume.round()},
      );
      _logger.d('Set volume to: $volume directly to TV');
    } catch (e, s) {
      _logger.e('Error setting volume directly to TV', error: e, stackTrace: s);
    }
  }

  /// Lanza una aplicación específica en la TV.
  Future<void> openApp(String appName) async {
    Map<String, dynamic>? payload;

    switch (appName) {
      case 'Netflix':
        payload = {
          'intent': {
            'action': 'android.intent.action.VIEW',
            'component': {
              'packageName': 'com.netflix.ninja',
              'className': 'com.netflix.ninja.MainActivity',
            },
          },
        };
        break;
      case 'YouTube':
        payload = {
          'intent': {
            'action': 'android.intent.action.VIEW',
            'component': {
              'packageName': 'com.google.android.youtube.tv',
              'className':
                  'com.google.android.apps.youtube.tv.activity.ShellActivity',
            },
          },
        };
        break;
      case 'Disney+':
        payload = {
          'intent': {
            'action': 'android.intent.action.VIEW',
            'component': {
              'packageName': 'com.disney.disneyplus',
              'className': 'com.bamtechmedia.dominguez.main.MainActivity',
            },
          },
        };
        break;
    }

    if (payload != null) {
      try {
        await _dio.post('/6/activities/launch', data: payload);
        _logger.d('Request sent to launch app: $appName');
      } catch (e, s) {
        _logger.e('Error launching app', error: e, stackTrace: s);
      }
    }
  }
}
