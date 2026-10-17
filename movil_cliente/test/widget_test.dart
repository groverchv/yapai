import 'package:flutter_test/flutter_test.dart';
import 'package:movil_cliente/models.dart';

void main() {
  test('Cliente.fromJson parsea los campos del API', () {
    final c = Cliente.fromJson({
      'id': 1, 'nombre': 'Demo', 'ci': '123', 'telefono': '700',
      'saldo_puntos': 350, 'puntos_congelados': 50,
    });
    expect(c.saldoPuntos, 350);
    expect(c.puntosCongelados, 50);
  });

  test('Pase.fromJson parsea estado y pin', () {
    final p = Pase.fromJson({
      'id': 1, 'codigo_qr': 'abc', 'pin_corto': 'JK6G5Q', 'puntos': 160,
      'estado': 'activo', 'premio_nombre': 'Gaseosa', 'comercio': 'Pizza',
      'created_at': '2026-10-17T00:00:00', 'expira_en': null,
    });
    expect(p.pinCorto, 'JK6G5Q');
    expect(p.estado, 'activo');
  });
}
