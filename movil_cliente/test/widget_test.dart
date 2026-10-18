import 'package:flutter_test/flutter_test.dart';
import 'package:movil_cliente/models.dart';

void main() {
  test('Cliente.fromJson parsea los campos del API', () {
    final c = Cliente.fromJson({
      'id': 1, 'nombre': 'Demo', 'ci': '123', 'telefono': '700',
      'saldo_puntos': 350, 'puntos_congelados': 50,
      'codigo_referido': 'B5QQ5D5E',
    });
    expect(c.saldoPuntos, 350);
    expect(c.puntosCongelados, 50);
    expect(c.codigoReferido, 'B5QQ5D5E');
  });

  test('Comunicado.fromJson parsea el feed de ofertas', () {
    final c = Comunicado.fromJson({
      'id': 7, 'titulo': '2x1 pizzas', 'descripcion': 'Solo martes',
      'imagen_url': 'https://res.cloudinary.com/x/image/upload/v1/a.png',
      'premio_id': 3, 'publicado_en': '2026-10-17T00:00:00',
      'vigencia_hasta': '2026-11-01T00:00:00', 'tenant_id': 1,
      'comercio': 'Pizzería', 'logo_url': null,
    });
    expect(c.comercio, 'Pizzería');
    expect(c.premioId, 3);
    expect(c.logoUrl, isNull);
  });

  test('cloudinaryThumb inserta la transformación solo en URLs Cloudinary', () {
    const url = 'https://res.cloudinary.com/x/image/upload/v1/a.png';
    expect(cloudinaryThumb(url, w: 400),
        'https://res.cloudinary.com/x/image/upload/w_400,c_fill,q_auto,f_auto/v1/a.png');
    const otra = 'https://otro.com/a.png';
    expect(cloudinaryThumb(otra), otra);
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
