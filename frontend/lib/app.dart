import 'package:flutter/material.dart';
import 'package:ciro_app/core/theme/app_theme.dart';
import 'package:ciro_app/core/router/app_router.dart';

class CiroApp extends StatelessWidget {
  const CiroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'CIRO — Crisis Dashboard',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      routerConfig: appRouter,
    );
  }
}
