import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/api_client.dart';
import 'core/canvas_mode.dart';
import 'core/mcd_state.dart';

void main() {
  runZonedGuarded(() {
    runApp(
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
  }, (error, stack) {
    // Évite l'écran rouge pour les exceptions asynchrones non gérées (ex. API injoignable).
    assert(() {
      debugPrint('Exception asynchrone: $error\n$stack');
      return true;
    }());
  });
}
