import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mi_app_expriment2/screens/remote_control_screen.dart';
import 'package:mi_app_expriment2/providers/tv_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('RemoteControlScreen', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    testWidgets('muestra el contenido tras inicializar sin IP proporcionada',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        ChangeNotifierProvider<TVProvider>(
          create: (_) => TVProvider(),
          child: const MaterialApp(
            home: RemoteControlScreen(),
          ),
        ),
      );

      // Estado de carga inicial
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Al completarse la inicialización debe mostrarse el layout principal
      // o un estado de error si no hay TV seleccionada.
      expect(
        find.byWidgetPredicate(
          (widget) =>
              widget is Text && widget.data?.contains('Control') == true ||
              widget is Text && widget.data?.contains('Reintentar') == true,
        ),
        findsWidgets,
      );
    });
  });
}
