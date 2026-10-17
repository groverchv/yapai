import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../auth_state.dart';
import '../models.dart';

const _tipos = {
  'registro': 'Registro en local',
  'ruleta': 'Ruleta',
  'bonus_manual': 'Bono por compra',
  'canje': 'Canje de premio',
  'congelar': 'Puntos congelados',
  'liberar': 'Puntos liberados',
  'anulacion': 'Anulación',
};

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  Wallet? _wallet;
  List<Movimiento> _movimientos = [];
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
      final wallet = await api.get('/cliente/wallet');
      final movs = await api.get('/cliente/movimientos?size=50');
      setState(() {
        _wallet = Wallet.fromJson(wallet);
        _movimientos = (movs['items'] as List).map((m) => Movimiento.fromJson(m)).toList();
      });
    } catch (e) {
      setState(() => _error = e.toString());
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

  @override
  Widget build(BuildContext context) {
    final verde = Theme.of(context).colorScheme.primary;
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Billetera')),
      body: RefreshIndicator(
        onRefresh: _cargar,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              color: verde,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Text('Saldo disponible',
                        style: TextStyle(color: Colors.white70)),
                    const SizedBox(height: 8),
                    Text(
                      _wallet == null ? '—' : '${_wallet!.disponible}',
                      style: const TextStyle(color: Colors.white, fontSize: 48,
                          fontWeight: FontWeight.bold),
                    ),
                    const Text('puntos YAPAI', style: TextStyle(color: Colors.white70)),
                    if (_wallet != null && _wallet!.congelado > 0) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white24, borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '${_wallet!.congelado} pts congelados en pases',
                          style: const TextStyle(color: Colors.white, fontSize: 12),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text('Historial de movimientos',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_cargando)
              const Padding(padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()))
            else if (_error != null)
              Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
            else if (_movimientos.isEmpty)
              const Padding(padding: EdgeInsets.all(32),
                  child: Center(child: Text('Sin movimientos todavía')))
            else
              ..._movimientos.map((m) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: m.puntos >= 0
                            ? Colors.green[50] : Colors.red[50],
                        child: Icon(
                          m.puntos >= 0 ? Icons.add : Icons.remove,
                          color: m.puntos >= 0 ? Colors.green : Colors.red,
                        ),
                      ),
                      title: Text(_tipos[m.tipo] ?? m.tipo),
                      subtitle: Text([
                        if (m.comercio != null) m.comercio!,
                        if (m.sucursal != null) m.sucursal!,
                        _fecha(m.createdAt),
                      ].join(' · ')),
                      trailing: Text(
                        '${m.puntos >= 0 ? '+' : ''}${m.puntos}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold, fontSize: 16,
                          color: m.puntos >= 0 ? Colors.green[700] : Colors.red[700],
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
