import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../auth_state.dart';
import '../models.dart';
import 'pase_detalle.dart';

/// Buzón de pases digitales generados.
class PasesScreen extends StatefulWidget {
  const PasesScreen({super.key});

  @override
  State<PasesScreen> createState() => _PasesScreenState();
}

class _PasesScreenState extends State<PasesScreen> {
  List<Pase> _pases = [];
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
      final data = await api.get('/cliente/pases');
      setState(() {
        _pases = (data as List).map((p) => Pase.fromJson(p)).toList()
          ..sort((a, b) {
            const orden = {'activo': 0, 'canjeado': 1, 'cancelado': 2, 'expirado': 3};
            return (orden[a.estado] ?? 9).compareTo(orden[b.estado] ?? 9);
          });
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _cargando = false);
    }
  }

  Color _colorEstado(String estado) => switch (estado) {
        'activo' => Colors.green,
        'canjeado' => Colors.blue,
        'cancelado' => Colors.grey,
        _ => Colors.orange,
      };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mis Pases')),
      body: RefreshIndicator(
        onRefresh: _cargar,
        child: _cargando
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : _pases.isEmpty
                    ? ListView(children: const [
                        SizedBox(height: 120),
                        Center(child: Icon(Icons.qr_code_2, size: 64, color: Colors.grey)),
                        SizedBox(height: 16),
                        Center(child: Text('No tienes pases generados')),
                        Center(child: Text('Canjea un premio desde Explorar',
                            style: TextStyle(color: Colors.grey))),
                      ])
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _pases.length,
                        itemBuilder: (_, i) {
                          final p = _pases[i];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            child: ListTile(
                              leading: Icon(Icons.qr_code_2,
                                  color: _colorEstado(p.estado), size: 36),
                              title: Text(p.premioNombre,
                                  style: const TextStyle(fontWeight: FontWeight.bold)),
                              subtitle: Text([
                                '${p.comercio} · ${p.puntos} pts · PIN ${p.pinCorto}',
                                if (p.estado == 'activo' && p.expiraEn != null)
                                  'Vence ${formatFechaCorta(p.expiraEn)}',
                              ].join('\n')),
                              trailing: Chip(
                                label: Text(p.estado,
                                    style: const TextStyle(fontSize: 11)),
                                backgroundColor: _colorEstado(p.estado).withAlpha(30),
                              ),
                              onTap: () => Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => PaseDetalleScreen(pase: p),
                                ),
                              ).then((_) => _cargar()),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}

String formatFechaCorta(String? iso) {
  if (iso == null) return '—';
  try {
    return DateFormat('dd/MM/yy HH:mm').format(DateTime.parse(iso).toLocal());
  } catch (_) {
    return iso;
  }
}
