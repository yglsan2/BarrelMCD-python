import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'theme/app_theme.dart';

class BarrelMcdApp extends StatelessWidget {
  const BarrelMcdApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BarrelMCD',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const HomeScreen(),
    );
  }
}
