import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'api.dart';
import 'config.dart';
import 'models.dart';

/// Sesión persistente del cliente: tokens en flutter_secure_storage (regla: sesión persistente).
class AuthState extends ChangeNotifier {
  final ApiClient api = ApiClient();
  final _storage = const FlutterSecureStorage();

  Cliente? cliente;
  bool cargando = true;

  AuthState() {
    api.onRefreshNeeded = _refresh;
    api.onSessionExpired = cerrarSesion;
    _restaurar();
  }

  bool get autenticado => api.accessToken != null && cliente != null;

  Future<void> _restaurar() async {
    try {
      final access = await _storage.read(key: 'access');
      final refresh = await _storage.read(key: 'refresh');
      final clienteJson = await _storage.read(key: 'cliente');
      if (access != null && refresh != null && clienteJson != null) {
        api.accessToken = access;
        api.refreshToken = refresh;
        cliente = Cliente.fromJson(jsonDecode(clienteJson));
        // Refresca datos del cliente en segundo plano
        api.get('/cliente/me').then((data) {
          cliente = Cliente.fromJson(data);
          _guardarCliente();
          notifyListeners();
        }).catchError((_) {});
      }
    } catch (_) {} finally {
      cargando = false;
      notifyListeners();
    }
  }

  Future<bool> _refresh() async {
    if (api.refreshToken == null) return false;
    try {
      final res = await http.post(
        Uri.parse('$apiBase/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': api.refreshToken}),
      );
      if (res.statusCode != 200) return false;
      final tokens = jsonDecode(res.body);
      api.accessToken = tokens['access_token'];
      api.refreshToken = tokens['refresh_token'];
      await _guardarTokens();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> login(String telefono, String ci) async {
    final res = await http.post(
      Uri.parse('$apiBase/auth/cliente/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'telefono': telefono, 'ci': ci}),
    );
    final data = jsonDecode(utf8.decode(res.bodyBytes));
    if (res.statusCode != 200) {
      throw ApiException(res.statusCode, data['detail'] ?? 'Credenciales inválidas');
    }
    api.accessToken = data['tokens']['access_token'];
    api.refreshToken = data['tokens']['refresh_token'];
    cliente = Cliente.fromJson(data['cliente']);
    await _guardarTokens();
    await _guardarCliente();
    notifyListeners();
  }

  Future<void> registro(String nombre, String telefono, String ci, [String? codigoReferido]) async {
    final payload = <String, dynamic>{
      'nombre': nombre,
      'telefono': telefono,
      'ci': ci,
    };
    if (codigoReferido != null && codigoReferido.trim().isNotEmpty) {
      payload['codigo_referido'] = codigoReferido.trim().toUpperCase();
    }
    final res = await http.post(
      Uri.parse('$apiBase/auth/cliente/registro'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    final data = jsonDecode(utf8.decode(res.bodyBytes));
    if (res.statusCode != 201) {
      throw ApiException(res.statusCode, data['detail'] ?? 'Error al registrar cliente');
    }
    api.accessToken = data['tokens']['access_token'];
    api.refreshToken = data['tokens']['refresh_token'];
    cliente = Cliente.fromJson(data['cliente']);
    await _guardarTokens();
    await _guardarCliente();
    notifyListeners();
  }

  Future<void> cerrarSesion() async {
    final refresh = api.refreshToken;
    api.accessToken = null;
    api.refreshToken = null;
    cliente = null;
    await _storage.deleteAll();
    notifyListeners();
    if (refresh != null) {
      try {
        await http.post(
          Uri.parse('$apiBase/auth/logout'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': refresh}),
        );
      } catch (_) {}
    }
  }

  Future<void> eliminarCuenta() async {
    await api.delete('/cliente/me');
    await cerrarSesion();
  }

  void actualizarCliente(Cliente c) {
    cliente = c;
    _guardarCliente();
    notifyListeners();
  }

  Future<void> _guardarTokens() async {
    await _storage.write(key: 'access', value: api.accessToken);
    await _storage.write(key: 'refresh', value: api.refreshToken);
  }

  Future<void> _guardarCliente() async {
    if (cliente != null) {
      await _storage.write(key: 'cliente', value: jsonEncode({
        'id': cliente!.id, 'nombre': cliente!.nombre, 'ci': cliente!.ci,
        'telefono': cliente!.telefono, 'saldo_puntos': cliente!.saldoPuntos,
        'puntos_congelados': cliente!.puntosCongelados,
        'codigo_referido': cliente!.codigoReferido,
      }));
    }
  }
}
