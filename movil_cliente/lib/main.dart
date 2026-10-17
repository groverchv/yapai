import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'auth_state.dart';
import 'screens/home_shell.dart';
import 'screens/login_screen.dart';

// Sentry se activa solo si se compila con --dart-define SENTRY_DSN=...
const _sentryDsn = String.fromEnvironment('SENTRY_DSN', defaultValue: '');

Future<void> main() async {
  final app = ChangeNotifierProvider(
    create: (_) => AuthState(),
    child: const YapaiApp(),
  );
  if (_sentryDsn.isEmpty) {
    runApp(app);
    return;
  }
  await SentryFlutter.init(
    (o) {
      o.dsn = _sentryDsn;
      o.tracesSampleRate = 0.1;
      o.environment = const String.fromEnvironment('APP_ENV', defaultValue: 'production');
    },
    appRunner: () => runApp(app),
  );
}

class YapaiApp extends StatelessWidget {
  const YapaiApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Marca YAPAI: azul marino primario + verde esmeralda de acento
    const navy = Color(0xFF1B2A63);
    const verde = Color(0xFF1ABC9C);
    return MaterialApp(
      title: 'YAPAI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: navy,
          primary: navy,
          secondary: verde,
        ),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(centerTitle: true),
      ),
      home: const _AuthGate(),
    );
  }
}

class _AuthGate extends StatelessWidget {
  const _AuthGate();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    if (auth.cargando) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return auth.autenticado ? const HomeShell() : const LoginScreen();
  }
}
