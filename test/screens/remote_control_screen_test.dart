import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mi_app_expriment2/screens/remote_control_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('RemoteControlScreen', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    testWidgets('muestra el contenido tras inicializar sin IP proporcionada',
        (WidgetTester tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: RemoteControlScreen(),
      ));

      // Estado de carga inicial
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      await tester.pumpAndSettle();

      // Al completarse la inicialización debe mostrarse el layout principal.
      expect(find.textContaining('Control'), findsWidgets);
    });
  });
}
