// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:mi_app_expriment2/main.dart';
import 'package:mi_app_expriment2/providers/tv_provider.dart';

void main() {
  testWidgets('Smart TV Manager app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());
    await tester.pump(); // Solo un pump para evitar timeout
    
    // Verify that our app loads with basic structure
    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.byType(MultiProvider), findsOneWidget);
  });

  testWidgets('TVProvider integration test', (WidgetTester tester) async {
    // Create a test widget that uses TVProvider
    await tester.pumpWidget(
      MaterialApp(
        home: ChangeNotifierProvider(
          create: (context) => TVProvider(),
          child: Consumer<TVProvider>(
            builder: (context, tvProvider, child) {
              return Scaffold(
                body: Text('TV Count: ${tvProvider.tvCount}'),
              );
            },
          ),
        ),
      ),
    );

    // Verify TVProvider starts with 0 TVs
    expect(find.text('TV Count: 0'), findsOneWidget);
  });
}
