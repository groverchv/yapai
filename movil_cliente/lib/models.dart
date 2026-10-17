class Cliente {
  final int id;
  final String nombre;
  final String ci;
  final String telefono;
  final int saldoPuntos;
  final int puntosCongelados;

  Cliente({
    required this.id, required this.nombre, required this.ci,
    required this.telefono, required this.saldoPuntos, required this.puntosCongelados,
  });

  factory Cliente.fromJson(Map<String, dynamic> j) => Cliente(
        id: j['id'], nombre: j['nombre'], ci: j['ci'], telefono: j['telefono'],
        saldoPuntos: j['saldo_puntos'], puntosCongelados: j['puntos_congelados'],
      );
}

class Wallet {
  final int saldo, congelado, disponible;
  Wallet({required this.saldo, required this.congelado, required this.disponible});
  factory Wallet.fromJson(Map<String, dynamic> j) =>
      Wallet(saldo: j['saldo'], congelado: j['congelado'], disponible: j['disponible']);
}

class Movimiento {
  final int id, puntos;
  final String tipo, createdAt;
  final String? comercio, sucursal, premio;
  Movimiento({required this.id, required this.puntos, required this.tipo,
      required this.createdAt, this.comercio, this.sucursal, this.premio});
  factory Movimiento.fromJson(Map<String, dynamic> j) => Movimiento(
        id: j['id'], puntos: j['puntos'], tipo: j['tipo'], createdAt: j['created_at'],
        comercio: j['comercio'], sucursal: j['sucursal'], premio: j['premio']);
}

class Comercio {
  final int id, totalPremios;
  final String nombre;
  final String? logoUrl, categoria;
  Comercio({required this.id, required this.nombre, this.logoUrl,
      this.categoria, required this.totalPremios});
  factory Comercio.fromJson(Map<String, dynamic> j) => Comercio(
        id: j['id'], nombre: j['nombre_comercial'], logoUrl: j['logo_url'],
        categoria: j['categoria'], totalPremios: j['total_premios']);
}

class SucursalInfo {
  final int id;
  final String nombre;
  final String? direccion;
  SucursalInfo({required this.id, required this.nombre, this.direccion});
  factory SucursalInfo.fromJson(Map<String, dynamic> j) =>
      SucursalInfo(id: j['id'], nombre: j['nombre'], direccion: j['direccion']);
}

class Premio {
  final int id, costoPuntos;
  final String nombre;
  final String? descripcion, imagenUrl;
  final bool alcanzable;
  Premio({required this.id, required this.nombre, this.descripcion,
      this.imagenUrl, required this.costoPuntos, required this.alcanzable});
  factory Premio.fromJson(Map<String, dynamic> j) => Premio(
        id: j['id'], nombre: j['nombre'], descripcion: j['descripcion'],
        imagenUrl: j['imagen_url'], costoPuntos: j['costo_puntos'],
        alcanzable: j['alcanzable']);
}

class Pase {
  final int id, puntos;
  final String codigoQr, pinCorto, estado, premioNombre, comercio, createdAt;
  final String? expiraEn;
  Pase({required this.id, required this.codigoQr, required this.pinCorto,
      required this.puntos, required this.estado, required this.premioNombre,
      required this.comercio, required this.createdAt, this.expiraEn});
  factory Pase.fromJson(Map<String, dynamic> j) => Pase(
        id: j['id'], codigoQr: j['codigo_qr'], pinCorto: j['pin_corto'],
        puntos: j['puntos'], estado: j['estado'], premioNombre: j['premio_nombre'],
        comercio: j['comercio'], createdAt: j['created_at'], expiraEn: j['expira_en']);
}
