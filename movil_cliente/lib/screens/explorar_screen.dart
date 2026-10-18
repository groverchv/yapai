import 'dart:async';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../auth_state.dart';
import '../models.dart';
import 'pase_detalle.dart';

class ExplorarScreen extends StatefulWidget {
  const ExplorarScreen({super.key});

  @override
  State<ExplorarScreen> createState() => _ExplorarScreenState();
}

class _ExplorarScreenState extends State<ExplorarScreen> {
  List<Comercio> _comercios = [];
  List<Map<String, dynamic>> _categorias = [];
  String _busqueda = '';
  int? _categoriaId;
  bool _cargando = true;
  String? _error;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  void _buscar(String v) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), () {
      _busqueda = v;
      _cargar();
    });
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      final api = context.read<AuthState>().api;
      final params = <String>[
        if (_busqueda.isNotEmpty) 'q=${Uri.encodeComponent(_busqueda)}',
        if (_categoriaId != null) 'categoria_id=$_categoriaId',
      ];
      final qs = params.isEmpty ? '' : '?${params.join('&')}';
      final comercios = await api.get('/cliente/comercios$qs');
      if (_categorias.isEmpty) {
        final cats = await api.get('/cliente/comercios/categorias');
        _categorias = List<Map<String, dynamic>>.from(cats);
      }
      setState(() {
        _comercios = (comercios as List).map((c) => Comercio.fromJson(c)).toList();
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Explorar')),
      body: RefreshIndicator(
        onRefresh: _cargar,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              decoration: InputDecoration(
                hintText: 'Buscar comercio…',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onChanged: _buscar,
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: const Text('Todas'),
                      selected: _categoriaId == null,
                      onSelected: (_) { setState(() => _categoriaId = null); _cargar(); },
                    ),
                  ),
                  ..._categorias.map((c) => Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: FilterChip(
                          label: Text(c['nombre']),
                          selected: _categoriaId == c['id'],
                          onSelected: (_) {
                            setState(() => _categoriaId = c['id']);
                            _cargar();
                          },
                        ),
                      )),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (_cargando)
              const Padding(padding: EdgeInsets.all(48),
                  child: Center(child: CircularProgressIndicator()))
            else if (_error != null)
              Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
            else if (_comercios.isEmpty)
              const Padding(padding: EdgeInsets.all(48),
                  child: Center(child: Text('No hay comercios disponibles')))
            else
              ..._comercios.map((c) => Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: _LogoComercio(url: c.logoUrl),
                      title: Text(c.nombre,
                          style: const TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text([
                        if (c.categoria != null) c.categoria!,
                        '${c.totalPremios} premios',
                      ].join(' · ')),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ComercioScreen(comercio: c),
                        ),
                      ),
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}

/// Logo circular del comercio con fallback al icono si falta o falla la carga.
class _LogoComercio extends StatelessWidget {
  final String? url;
  const _LogoComercio({this.url});

  @override
  Widget build(BuildContext context) {
    final fallback = CircleAvatar(
      backgroundColor: Colors.green[50],
      child: const Icon(Icons.storefront, color: Colors.green),
    );
    if (url == null) return fallback;
    return ClipOval(
      child: Image.network(
        cloudinaryThumb(url!, w: 100),
        width: 40,
        height: 40,
        fit: BoxFit.cover,
        loadingBuilder: (_, child, progress) =>
            progress == null ? child : fallback,
        errorBuilder: (_, _, _) => fallback,
      ),
    );
  }
}

/// Detalle del comercio: catálogo de premios + sucursales + canje.
class ComercioScreen extends StatefulWidget {
  final Comercio comercio;
  const ComercioScreen({super.key, required this.comercio});

  @override
  State<ComercioScreen> createState() => _ComercioScreenState();
}

class _ComercioScreenState extends State<ComercioScreen> {
  List<Premio> _premios = [];
  List<SucursalInfo> _sucursales = [];
  int _disponible = 0;
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      final api = context.read<AuthState>().api;
      final detalle = await api.get('/cliente/comercios/${widget.comercio.id}');
      final premios = await api.get('/cliente/comercios/${widget.comercio.id}/premios');
      final wallet = await api.get('/cliente/wallet');
      setState(() {
        _sucursales = (detalle['sucursales'] as List)
            .map((s) => SucursalInfo.fromJson(s)).toList();
        _premios = (premios as List).map((p) => Premio.fromJson(p)).toList();
        _disponible = wallet['disponible'];
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _cargando = false);
    }
  }

  Future<void> _confirmarCanje(Premio p) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmar canje'),
        content: Text(
          'Vas a generar un pase para "${p.nombre}" por ${p.costoPuntos} puntos.\n\n'
          'Los puntos quedarán congelados hasta que el cajero valide la entrega '
          'o canceles el pase.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Volver')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Generar pase')),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    try {
      final api = context.read<AuthState>().api;
      final data = await api.post('/cliente/pases', {'premio_id': p.id});
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => PaseDetalleScreen(pase: Pase.fromJson(data))),
      ).then((_) => _cargar());
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.comercio.nombre)),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (_sucursales.isNotEmpty) ...[
                        Text('Dónde reclamar',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        ..._sucursales.map((s) => ListTile(
                              dense: true,
                              leading: const Icon(Icons.location_on_outlined),
                              title: Text(s.nombre),
                              subtitle: s.direccion != null ? Text(s.direccion!) : null,
                            )),
                        const Divider(height: 32),
                      ],
                      Text('Premios',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 8),
                      Center(
                        child: Chip(
                          avatar: const Icon(Icons.stars, size: 16),
                          label: Text('Tu saldo: $_disponible pts'),
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (_premios.isEmpty)
                        const Padding(padding: EdgeInsets.all(24),
                            child: Center(child: Text('Sin premios disponibles')))
                      else
                        GridView.count(
                          crossAxisCount: 2,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          mainAxisSpacing: 10,
                          crossAxisSpacing: 10,
                          childAspectRatio: 0.78,
                          children: _premios.map((p) => _PremioCard(
                                premio: p,
                                onCanjear: p.alcanzable ? () => _confirmarCanje(p) : null,
                              )).toList(),
                        ),
                    ],
                  ),
                ),
    );
  }
}

class _PremioCard extends StatelessWidget {
  final Premio premio;
  final VoidCallback? onCanjear;
  const _PremioCard({required this.premio, this.onCanjear});

  @override
  Widget build(BuildContext context) {
    final bloqueado = !premio.alcanzable;
    return Opacity(
      opacity: bloqueado ? 0.55 : 1,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: premio.imagenUrl != null
                  ? Image.network(cloudinaryThumb(premio.imagenUrl!),
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) => _placeholder())
                  : _placeholder(),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(premio.nombre,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  Text('${premio.costoPuntos} pts',
                      style: TextStyle(color: Colors.green[700],
                          fontWeight: FontWeight.bold)),
                  if (premio.vigenciaHasta != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        'Vence ${_vence(premio.vigenciaHasta!)}',
                        style: TextStyle(color: Colors.orange[800],
                            fontSize: 11),
                      ),
                    ),
                  const SizedBox(height: 6),
                  SizedBox(
                    width: double.infinity,
                    child: bloqueado
                        ? const Chip(
                            label: Text('Puntos insuficientes',
                                style: TextStyle(fontSize: 11)),
                            visualDensity: VisualDensity.compact,
                          )
                        : FilledButton.tonal(
                            onPressed: onCanjear,
                            child: const Text('Canjear'),
                          ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _placeholder() => Container(
        color: Colors.grey[200],
        child: const Center(child: Icon(Icons.card_giftcard, size: 40, color: Colors.grey)),
      );

  String _vence(String iso) {
    try {
      return DateFormat('dd/MM').format(DateTime.parse(iso).toLocal());
    } catch (_) {
      return '';
    }
  }
}
