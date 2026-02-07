import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'core/api_client.dart';
import 'core/canvas_mode.dart';
import 'core/mcd_state.dart';

void main() {
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
}
