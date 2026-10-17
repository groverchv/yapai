import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';

class ApiException implements Exception {
  final int status;
  final String detail;
  ApiException(this.status, this.detail);
  @override
  String toString() => detail;
}

/// Cliente HTTP con JWT + refresh automático.
/// El estado de sesión lo inyecta AuthState (sin dependencia circular).
class ApiClient {
  String? accessToken;
  String? refreshToken;
  Future<bool> Function()? onRefreshNeeded;
  void Function()? onSessionExpired;

  Future<http.Response> _send(String method, String path,
      {Object? body, bool retry = true}) async {
    final uri = Uri.parse('$apiBase$path');
    final headers = <String, String>{
      if (body != null) 'Content-Type': 'application/json',
      if (accessToken != null) 'Authorization': 'Bearer $accessToken',
    };
    final res = await switch (method) {
      'GET' => http.get(uri, headers: headers),
      'POST' => http.post(uri, headers: headers,
          body: body != null ? jsonEncode(body) : null),
      'PATCH' => http.patch(uri, headers: headers, body: jsonEncode(body)),
      'DELETE' => http.delete(uri, headers: headers),
      _ => throw ArgumentError(method),
    };

    if (res.statusCode == 401 && retry && onRefreshNeeded != null) {
      if (await onRefreshNeeded!()) return _send(method, path, body: body, retry: false);
      onSessionExpired?.call();
    }
    return res;
  }

  dynamic _decodificar(http.Response res) {
    if (res.statusCode >= 400) {
      String detalle = 'Error ${res.statusCode}';
      try {
        detalle = jsonDecode(utf8.decode(res.bodyBytes))['detail'] ?? detalle;
      } catch (_) {}
      throw ApiException(res.statusCode, detalle);
    }
    if (res.bodyBytes.isEmpty) return null;
    return jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<dynamic> get(String path) async => _decodificar(await _send('GET', path));
  Future<dynamic> post(String path, [Object? body]) async =>
      _decodificar(await _send('POST', path, body: body));
  Future<dynamic> patch(String path, Object body) async =>
      _decodificar(await _send('PATCH', path, body: body));
  Future<dynamic> delete(String path) async => _decodificar(await _send('DELETE', path));
}
