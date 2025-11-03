import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../widgets/app_notification.dart';

class ErrorHandlerService {
  static final ErrorHandlerService _instance = ErrorHandlerService._internal();
  factory ErrorHandlerService() => _instance;
  ErrorHandlerService._internal();

  /// Maneja errores de red y muestra notificaciones apropiadas
  static void handleNetworkError(
    BuildContext? context,
    dynamic error, {
    String? customMessage,
    bool showNotification = true,
  }) {
    String message = customMessage ?? _getErrorMessage(error);
    
    if (kDebugMode) {
      print('Network Error: $error');
      print('Error Type: ${error.runtimeType}');
      if (error is DioException) {
        print('Dio Error Type: ${error.type}');
        print('Status Code: ${error.response?.statusCode}');
        print('Response Data: ${error.response?.data}');
      }
    }

    if (context != null && showNotification) {
      AppNotification.showError(context, message);
    }
  }

  /// Maneja errores de conexión con TVs
  static void handleTVConnectionError(
    BuildContext? context,
    dynamic error, {
    String? tvName,
    bool showNotification = true,
  }) {
    String message = tvName != null
        ? 'No se pudo conectar con $tvName'
        : 'Error de conexión con la TV';
    
    if (kDebugMode) {
      print('TV Connection Error: $error');
    }

    if (context != null && showNotification) {
      AppNotification.showError(context, message);
    }
  }

  /// Maneja errores de escaneo de red
  static void handleScanError(
    BuildContext? context,
    dynamic error, {
    bool showNotification = true,
  }) {
    String message = 'Error al escanear la red. Verifica tu conexión WiFi.';
    
    if (kDebugMode) {
      print('Network Scan Error: $error');
    }

    if (context != null && showNotification) {
      AppNotification.showWarning(context, message);
    }
  }

  /// Maneja errores de almacenamiento local
  static void handleStorageError(
    BuildContext? context,
    dynamic error, {
    bool showNotification = true,
  }) {
    String message = 'Error al guardar los datos localmente';
    
    if (kDebugMode) {
      print('Storage Error: $error');
    }

    if (context != null && showNotification) {
      AppNotification.showError(context, message);
    }
  }

  /// Maneja errores de comandos de TV
  static void handleTVCommandError(
    BuildContext? context,
    dynamic error, {
    String? command,
    String? tvName,
    bool showNotification = true,
  }) {
    String message = 'Error al enviar comando';
    if (tvName != null) {
      message += ' a $tvName';
    }
    if (command != null) {
      message += ' ($command)';
    }
    
    if (kDebugMode) {
      print('TV Command Error: $error');
      print('Command: $command, TV: $tvName');
    }

    if (context != null && showNotification) {
      AppNotification.showError(context, message);
    }
  }

  /// Convierte diferentes tipos de errores en mensajes legibles
  static String _getErrorMessage(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
          return 'Tiempo de conexión agotado. Verifica tu red.';
        case DioExceptionType.sendTimeout:
          return 'Error al enviar datos. Intenta nuevamente.';
        case DioExceptionType.receiveTimeout:
          return 'Tiempo de respuesta agotado.';
        case DioExceptionType.badResponse:
          return _getHttpErrorMessage(error.response?.statusCode);
        case DioExceptionType.cancel:
          return 'Operación cancelada.';
        case DioExceptionType.connectionError:
          return 'Error de conexión. Verifica tu red WiFi.';
        case DioExceptionType.badCertificate:
          return 'Error de certificado de seguridad.';
        case DioExceptionType.unknown:
          return 'Error de conexión desconocido.';
      }
    }

    if (error is FormatException) {
      return 'Formato de datos inválido.';
    }

    if (error is TypeError) {
      return 'Error de tipo de datos.';
    }

    // Error genérico
    return 'Ha ocurrido un error inesperado.';
  }

  /// Convierte códigos de estado HTTP en mensajes legibles
  static String _getHttpErrorMessage(int? statusCode) {
    if (statusCode == null) return 'Error de respuesta del servidor.';

    switch (statusCode) {
      case 400:
        return 'Solicitud inválida (Error 400).';
      case 401:
        return 'No autorizado. Verifica las credenciales (Error 401).';
      case 403:
        return 'Acceso prohibido (Error 403).';
      case 404:
        return 'Recurso no encontrado (Error 404).';
      case 408:
        return 'Tiempo de solicitud agotado (Error 408).';
      case 429:
        return 'Demasiadas solicitudes. Intenta más tarde (Error 429).';
      case 500:
        return 'Error interno del servidor (Error 500).';
      case 502:
        return 'Error de gateway (Error 502).';
      case 503:
        return 'Servicio no disponible (Error 503).';
      case 504:
        return 'Tiempo de gateway agotado (Error 504).';
      default:
        return 'Error del servidor (Error $statusCode).';
    }
  }

  /// Retorna información detallada de un error para debugging
  static Map<String, dynamic> getErrorDetails(dynamic error) {
    Map<String, dynamic> details = {
      'timestamp': DateTime.now().toIso8601String(),
      'error_type': error.runtimeType.toString(),
      'error_message': error.toString(),
    };

    if (error is DioException) {
      details.addAll({
        'dio_type': error.type.toString(),
        'status_code': error.response?.statusCode,
        'response_data': error.response?.data,
        'request_path': error.requestOptions.path,
        'request_method': error.requestOptions.method,
      });
    }

    return details;
  }

  /// Valida si un error es recuperable (puede reintentarse)
  static bool isRecoverableError(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
        case DioExceptionType.connectionError:
          return true;
        case DioExceptionType.badResponse:
          final statusCode = error.response?.statusCode;
          return statusCode != null && (
            statusCode == 408 || // Request Timeout
            statusCode == 429 || // Too Many Requests
            statusCode >= 500    // Server Errors
          );
        default:
          return false;
      }
    }
    return false;
  }

  /// Muestra un diálogo de error con opción de reintento
  static void showRetryDialog(
    BuildContext context, {
    required String title,
    required String message,
    required VoidCallback onRetry,
    VoidCallback? onCancel,
  }) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.red,
              size: 24,
            ),
            const SizedBox(width: 8),
            Text(title),
          ],
        ),
        content: Text(message),
        actions: [
          if (onCancel != null)
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                onCancel();
              },
              child: const Text('Cancelar'),
            ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context).pop();
              onRetry();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}