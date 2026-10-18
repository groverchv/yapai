import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';

import '../api.dart';
import '../auth_state.dart';
import '../models.dart';
import 'explorar_screen.dart';

const _tipos = {
  'registro': 'Registro en local',
  'ruleta': 'Ruleta',
  'bonus_manual': 'Bono por compra',
  'referido': 'Bono por referido',
  'canje': 'Canje de premio',
  'congelar': 'Puntos congelados',
  'liberar': 'Puntos liberados',
  'anulacion': 'Anulación',
};

const _navy = Color(0xFF14213D);
const _navyClaro = Color(0xFF1F3460);

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  Wallet? _wallet;
  List<Movimiento> _movimientos = [];
  List<Comunicado> _comunicados = [];
  String? _error;
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      final api = context.read<AuthState>().api;
      final resultados = await Future.wait([
        api.get('/cliente/wallet'),
        api.get('/cliente/movimientos?size=50'),
        api.get('/cliente/comunicados?size=30'),
      ]);
      setState(() {
        _wallet = Wallet.fromJson(resultados[0]);
        _movimientos = (resultados[1]['items'] as List)
            .map((m) => Movimiento.fromJson(m)).toList();
        _comunicados = (resultados[2]['items'] as List)
            .map((c) => Comunicado.fromJson(c)).toList();
      });
    } catch (e) {
      setState(() => _error = e is ApiException ? e.detail : 'Sin conexión');
    } finally {
      setState(() => _cargando = false);
    }
  }

  String _fecha(String iso) {
    try {
      return DateFormat('dd/MM/yy HH:mm').format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return iso;
    }
  }

  bool _subiendoFoto = false;

  Future<void> _cambiarFoto() async {
    final auth = context.read<AuthState>();
    final picked = await ImagePicker()
        .pickImage(source: ImageSource.gallery, maxWidth: 800);
    if (picked == null || !mounted) return;
    setState(() => _subiendoFoto = true);
    try {
      final bytes = await picked.readAsBytes();
      await auth.subirFoto(bytes, picked.name);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e is ApiException ? e.detail : 'Error al subir'),
              backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _subiendoFoto = false);
    }
  }

  void _mostrarHistorial() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.4,
        maxChildSize: 0.92,
        expand: false,
        builder: (_, scroll) => ListView(
          controller: scroll,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          children: [
            Text('Historial de movimientos',
                style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 12),
            if (_movimientos.isEmpty)
              const Padding(padding: EdgeInsets.all(32),
                  child: Center(child: Text('Sin movimientos todavía')))
            else
              ..._movimientos.map((m) => _MovimientoTile(
                  movimiento: m, fecha: _fecha(m.createdAt))),
          ],
        ),
      ),
    );
  }

  void _mostrarQr(Cliente cliente) {
    final codigo = cliente.codigoReferido ?? 'YAPAI-${cliente.id}';
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Mi código YAPAI',
                style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text('Compártelo y gana puntos por cada amigo que se registre',
                style: TextStyle(color: Colors.grey[600], fontSize: 13),
                textAlign: TextAlign.center),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: QrImageView(
                data: 'yapai:ref:$codigo',
                size: 200,
                eyeStyle: const QrEyeStyle(
                    eyeShape: QrEyeShape.square, color: _navy),
              ),
            ),
            const SizedBox(height: 12),
            Text(codigo,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold,
                    letterSpacing: 2)),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () => SharePlus.instance.share(ShareParams(
                  text: '¡Únete a YAPAI con mi código $codigo y gana puntos '
                      'en tus comercios favoritos!',
                )),
                icon: const Icon(Icons.share),
                label: const Text('Compartir mi código'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _mostrarComunicado(Comunicado c) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.75,
        minChildSize: 0.5,
        maxChildSize: 0.92,
        expand: false,
        builder: (_, scroll) => ListView(
          controller: scroll,
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.network(
                cloudinaryThumb(c.imagenUrl, w: 800),
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => Container(
                  height: 160, color: Colors.grey[200],
                  child: const Icon(Icons.image_not_supported,
                      size: 48, color: Colors.grey),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                if (c.logoUrl != null)
                  ClipOval(
                    child: Image.network(
                      cloudinaryThumb(c.logoUrl!, w: 64),
                      width: 32, height: 32, fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => CircleAvatar(
                        radius: 16, backgroundColor: Colors.grey[100],
                        child: const Icon(Icons.storefront, size: 16),
                      ),
                    ),
                  )
                else
                  CircleAvatar(
                    radius: 16, backgroundColor: Colors.grey[100],
                    child: const Icon(Icons.storefront, size: 16),
                  ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(c.comercio,
                      style: TextStyle(color: Colors.grey[700], fontSize: 13)),
                ),
                if (c.vigenciaHasta != null)
                  Chip(
                    label: Text('Vence ${_vence(c.vigenciaHasta!)}',
                        style: const TextStyle(fontSize: 11)),
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Text(c.titulo, style: Theme.of(ctx).textTheme.headlineSmall),
            if (c.descripcion != null) ...[
              const SizedBox(height: 8),
              Text(c.descripcion!,
                  style: TextStyle(color: Colors.grey[800], height: 1.4)),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ComercioScreen(
                        comercio: Comercio(
                            id: c.tenantId, nombre: c.comercio,
                            logoUrl: c.logoUrl, totalPremios: 0),
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.card_giftcard),
                label: Text(c.premioId != null
                    ? 'Ver premio en ${c.comercio}'
                    : 'Ver ${c.comercio}'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _vence(String iso) {
    try {
      return DateFormat('dd/MM').format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    final cliente = context.watch<AuthState>().cliente;
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(title: const Text('Mi Billetera')),
      body: RefreshIndicator(
        onRefresh: _cargar,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _TarjetaId(
              cliente: cliente,
              wallet: _wallet,
              subiendoFoto: _subiendoFoto,
              onQr: cliente == null ? null : () => _mostrarQr(cliente),
              onAvatar: _cambiarFoto,
              onHistorial: _mostrarHistorial,
            ),
            const SizedBox(height: 20),
            Text('Ofertas', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_cargando)
              const Padding(padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()))
            else if (_comunicados.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Icon(Icons.local_offer_outlined,
                          size: 40, color: Colors.grey[400]),
                      const SizedBox(height: 8),
                      Text('Aún no hay ofertas publicadas',
                          style: TextStyle(color: Colors.grey[600])),
                    ],
                  ),
                ),
              )
            else
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  mainAxisSpacing: 8,
                  crossAxisSpacing: 8,
                ),
                itemCount: _comunicados.length,
                itemBuilder: (_, i) => _OfertaTile(
                  comunicado: _comunicados[i],
                  onTap: () => _mostrarComunicado(_comunicados[i]),
                ),
              ),
            if (_error != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      Text(_error!, style: const TextStyle(color: Colors.red)),
                      TextButton(onPressed: _cargar,
                          child: const Text('Reintentar')),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Tarjeta de identidad estilo credencial: foto, nombre, CI, saldo,
/// acceso al QR de referido y al historial de movimientos.
class _TarjetaId extends StatelessWidget {
  final Cliente? cliente;
  final Wallet? wallet;
  final bool subiendoFoto;
  final VoidCallback? onQr;
  final VoidCallback? onAvatar;
  final VoidCallback? onHistorial;
  const _TarjetaId({this.cliente, this.wallet, this.subiendoFoto = false,
      this.onQr, this.onAvatar, this.onHistorial});

  String get _iniciales {
    final n = (cliente?.nombre ?? '?').trim();
    final partes = n.split(RegExp(r'\s+'));
    return partes.take(2).map((p) => p[0].toUpperCase()).join();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [_navy, _navyClaro],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: _navy.withValues(alpha: 0.4),
              blurRadius: 12, offset: const Offset(0, 6)),
        ],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              GestureDetector(
                onTap: onAvatar,
                child: Stack(
                  children: [
                    CircleAvatar(
                      radius: 26,
                      backgroundColor: Colors.white24,
                      child: ClipOval(
                        child: subiendoFoto
                            ? const SizedBox(width: 24, height: 24,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : cliente?.fotoUrl != null
                                ? Image.network(
                                    cloudinaryThumb(cliente!.fotoUrl!, w: 120),
                                    width: 52, height: 52, fit: BoxFit.cover,
                                    errorBuilder: (_, _, _) => Text(
                                        _iniciales,
                                        style: const TextStyle(
                                            color: Colors.white, fontSize: 20,
                                            fontWeight: FontWeight.bold)),
                                  )
                                : Center(
                                    child: Text(_iniciales,
                                        style: const TextStyle(
                                            color: Colors.white, fontSize: 20,
                                            fontWeight: FontWeight.bold)),
                                  ),
                      ),
                    ),
                    Positioned(
                      right: 0, bottom: 0,
                      child: Container(
                        padding: const EdgeInsets.all(3),
                        decoration: const BoxDecoration(
                          color: Colors.white, shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.photo_camera,
                            size: 12, color: _navy),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(cliente?.nombre ?? '—',
                        style: const TextStyle(color: Colors.white,
                            fontSize: 17, fontWeight: FontWeight.bold),
                        maxLines: 1, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 2),
                    Text('CI ${cliente?.ci ?? '—'}',
                        style: const TextStyle(color: Colors.white70,
                            fontSize: 13)),
                  ],
                ),
              ),
              const Icon(Icons.verified_user_outlined,
                  color: Colors.white38, size: 28),
            ],
          ),
          const SizedBox(height: 18),
          const Divider(color: Colors.white24, height: 1),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('PUNTOS DISPONIBLES',
                        style: TextStyle(color: Colors.white60, fontSize: 11,
                            letterSpacing: 1.2)),
                    const SizedBox(height: 4),
                    Text('${wallet?.disponible ?? '—'}',
                        style: const TextStyle(color: Colors.white,
                            fontSize: 36, fontWeight: FontWeight.bold,
                            height: 1)),
                    if (wallet != null && wallet!.congelado > 0)
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          '${wallet!.congelado} pts congelados en pases',
                          style: const TextStyle(color: Colors.white70,
                              fontSize: 11),
                        ),
                      ),
                  ],
                ),
              ),
              Column(
                children: [
                  _BotonTarjeta(
                    icono: Icons.qr_code_2,
                    tooltip: 'Mi código',
                    onTap: onQr,
                  ),
                  const SizedBox(height: 8),
                  _BotonTarjeta(
                    icono: Icons.receipt_long,
                    tooltip: 'Historial',
                    onTap: onHistorial,
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Botón blanco cuadrado embebido en la tarjeta (QR, historial).
class _BotonTarjeta extends StatelessWidget {
  final IconData icono;
  final String tooltip;
  final VoidCallback? onTap;
  const _BotonTarjeta({required this.icono, required this.tooltip, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: Icon(icono, color: _navy, size: 26),
          ),
        ),
      ),
    );
  }
}

/// Fila de un movimiento de puntos (historial en bottom sheet).
class _MovimientoTile extends StatelessWidget {
  final Movimiento movimiento;
  final String fecha;
  const _MovimientoTile({required this.movimiento, required this.fecha});

  @override
  Widget build(BuildContext context) {
    final m = movimiento;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: m.puntos >= 0 ? Colors.green[50] : Colors.red[50],
          child: Icon(
            m.puntos >= 0 ? Icons.add : Icons.remove,
            color: m.puntos >= 0 ? Colors.green : Colors.red,
          ),
        ),
        title: Text(_tipos[m.tipo] ?? m.tipo),
        subtitle: Text([
          if (m.comercio != null) m.comercio!,
          if (m.sucursal != null) m.sucursal!,
          fecha,
        ].join(' · ')),
        trailing: Text(
          '${m.puntos >= 0 ? '+' : ''}${m.puntos}',
          style: TextStyle(
            fontWeight: FontWeight.bold, fontSize: 16,
            color: m.puntos >= 0 ? Colors.green[700] : Colors.red[700],
          ),
        ),
      ),
    );
  }
}

/// Celda del grid de ofertas: imagen + título superpuesto.
class _OfertaTile extends StatelessWidget {
  final Comunicado comunicado;
  final VoidCallback onTap;
  const _OfertaTile({required this.comunicado, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap: onTap,
        child: Stack(
          fit: StackFit.expand,
          children: [
            Image.network(
              cloudinaryThumb(comunicado.imagenUrl),
              fit: BoxFit.cover,
              errorBuilder: (_, _, _) => Container(
                color: Colors.grey[200],
                child: const Icon(Icons.image_not_supported,
                    color: Colors.grey),
              ),
              loadingBuilder: (_, child, progress) => progress == null
                  ? child
                  : Container(
                      color: Colors.grey[200],
                      child: const Center(
                        child: SizedBox(width: 20, height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2)),
                      ),
                    ),
            ),
            Positioned(
              left: 0, right: 0, bottom: 0,
              child: Container(
                padding: const EdgeInsets.fromLTRB(8, 18, 8, 6),
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.transparent, Colors.black87],
                  ),
                ),
                child: Text(
                  comunicado.titulo,
                  style: const TextStyle(color: Colors.white, fontSize: 11,
                      fontWeight: FontWeight.w600),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
