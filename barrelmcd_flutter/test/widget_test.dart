// Test minimal pour BarrelMCD Flutter.
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:barrelmcd_flutter/app.dart';
import 'package:barrelmcd_flutter/core/api_client.dart';
import 'package:barrelmcd_flutter/core/canvas_mode.dart';
import 'package:barrelmcd_flutter/core/mcd_state.dart';

void main() {
  testWidgets('App démarre et affiche l\'interface', (WidgetTester tester) async {
    await tester.pumpWidget(
      Provider<ApiClient>(
        create: (_) => ApiClient(baseUrl: 'http://127.0.0.1:8000'),
        child: ChangeNotifierProvider<CanvasModeState>(
          create: (_) => CanvasModeState(),
          child: ChangeNotifierProvider<McdState>(
            create: (ctx) => McdState(api: ctx.read<ApiClient>()),
            child: const BarrelMcdApp(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('BarrelMCD'), findsWidgets);
  });
}
