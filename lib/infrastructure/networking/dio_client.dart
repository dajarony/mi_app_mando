
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

const String _apiBaseUrl = 'http://192.168.0.162:8000';
const String _authToken = 'IR15K!UTHwlVKeWu&VtUx8K02S59A11m^AuI6fQGaOeFrF^2';

final logger = Logger();

Dio createDioClient() {
  final dio = Dio(
    BaseOptions(
      baseUrl: _apiBaseUrl,
      headers: {
        'Authorization': 'Bearer $_authToken',
        'Content-Type': 'application/json',
      },
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 3),
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        logger.i('REQUEST[${options.method}] => PATH: ${options.path}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        logger.d('RESPONSE[${response.statusCode}] => PATH: ${response.requestOptions.path}');
        return handler.next(response);
      },
      onError: (DioException e, handler) {
        logger.e(
          'ERROR[${e.response?.statusCode}] => PATH: ${e.requestOptions.path}',
          error: e.error,
          stackTrace: e.stackTrace,
        );
        return handler.next(e);
      },
    ),
  );

  return dio;
}
