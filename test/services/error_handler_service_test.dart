import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/services/error_handler_service.dart';

void main() {
  group('ErrorHandlerService', () {
    test('should identify recoverable connection timeout error', () {
      final dioError = DioException(
        type: DioExceptionType.connectionTimeout,
        requestOptions: RequestOptions(path: '/test'),
      );
      
      expect(ErrorHandlerService.isRecoverableError(dioError), isTrue);
    });
    
    test('should identify recoverable server error (500)', () {
      final dioError = DioException(
        type: DioExceptionType.badResponse,
        response: Response(
          statusCode: 500,
          requestOptions: RequestOptions(path: '/test'),
        ),
        requestOptions: RequestOptions(path: '/test'),
      );
      
      expect(ErrorHandlerService.isRecoverableError(dioError), isTrue);
    });
    
    test('should identify non-recoverable client error (404)', () {
      final dioError = DioException(
        type: DioExceptionType.badResponse,
        response: Response(
          statusCode: 404,
          requestOptions: RequestOptions(path: '/test'),
        ),
        requestOptions: RequestOptions(path: '/test'),
      );
      
      expect(ErrorHandlerService.isRecoverableError(dioError), isFalse);
    });
    
    test('should identify non-recoverable bad certificate error', () {
      final dioError = DioException(
        type: DioExceptionType.badCertificate,
        requestOptions: RequestOptions(path: '/test'),
      );
      
      expect(ErrorHandlerService.isRecoverableError(dioError), isFalse);
    });
    
    test('should return correct error details for DioException', () {
      final dioError = DioException(
        type: DioExceptionType.connectionTimeout,
        message: 'Connection timeout',
        requestOptions: RequestOptions(
          path: '/api/test',
          method: 'GET',
        ),
      );
      
      final details = ErrorHandlerService.getErrorDetails(dioError);
      
      expect(details['error_type'], contains('DioException'));
      expect(details['dio_type'], contains('connectionTimeout'));
      expect(details['request_path'], equals('/api/test'));
      expect(details['request_method'], equals('GET'));
      expect(details['timestamp'], isNotNull);
    });
    
    test('should return basic error details for non-Dio errors', () {
      const error = FormatException('Invalid format');
      
      final details = ErrorHandlerService.getErrorDetails(error);
      
      expect(details['error_type'], contains('FormatException'));
      expect(details['error_message'], contains('Invalid format'));
      expect(details['timestamp'], isNotNull);
      expect(details.containsKey('dio_type'), isFalse);
    });
  });
}