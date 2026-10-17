import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// URL base del backend. En el emulador de Android, localhost del PC es 10.0.2.2.
/// Se puede sobreescribir con: flutter run --dart-define=API_BASE=http://IP:8000/api/v1
String get apiBase {
  const definida = String.fromEnvironment('API_BASE');
  if (definida.isNotEmpty) return definida;
  if (!kIsWeb && Platform.isAndroid) return 'http://10.0.2.2:8000/api/v1';
  return 'http://localhost:8000/api/v1';
}
