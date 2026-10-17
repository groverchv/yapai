import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../auth_state.dart';
import '../models.dart';
import 'pases_screen.dart' show formatFechaCorta;

/// Detalle del pase digital: QR grande + PIN corto de respaldo + cancelar.
class PaseDetalleScreen extends StatefulWidget {
  final Pase pase;
  const PaseDetalleScreen({super.key, required this.pase});

  @override
  State<PaseDetalleScreen> createState() => _PaseDetalleScreenState();
}

class _PaseDetalleScreenState extends State<PaseDetalleScreen> {
  bool _cancelando = false;

  Future<void> _cancelar() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancelar pase'),
        content: const Text(
            'Se liberarán los puntos congelados y volverán a tu billetera de inmediato.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Volver')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Cancelar pase')),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _cancelando = true);
    try {
      await context.read<AuthState>().api
          .post('/cliente/pases/${widget.pase.id}/cancelar');
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Pase cancelado; puntos liberados')),
      );
    } catch (e) {
      setState(() => _cancelando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.pase;
    final activo = p.estado == 'activo';
    return Scaffold(
      appBar: AppBar(title: const Text('Pase digital')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Text(p.premioNombre,
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center),
              Text('${p.comercio} · ${p.puntos} pts',
                  style: TextStyle(color: Colors.grey[600])),
              const SizedBox(height: 8),
              Chip(
                label: Text(p.estado.toUpperCase()),
                backgroundColor: activo ? Colors.green[50] : Colors.grey[200],
              ),
              const SizedBox(height: 24),
              if (activo) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: QrImageView(
                    data: p.codigoQr,
                    size: 240,
                    eyeStyle: const QrEyeStyle(
                        eyeShape: QrEyeShape.square, color: Colors.black),
                  ),
                ),
                const SizedBox(height: 20),
                const Text('Si la cámara falla, dicta este PIN al cajero:'),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    p.pinCorto,
                    style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold,
                        letterSpacing: 6, fontFamily: 'monospace'),
                  ),
                ),
                const SizedBox(height: 16),
                Text('Válido hasta ${formatFechaCorta(p.expiraEn)}',
                    style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                const SizedBox(height: 24),
                OutlinedButton.icon(
                  onPressed: _cancelando ? null : _cancelar,
                  icon: const Icon(Icons.cancel_outlined),
                  label: Text(_cancelando ? 'Cancelando…' : 'Cancelar pase y liberar puntos'),
                  style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                ),
              ] else
                Padding(
                  padding: const EdgeInsets.all(32),
                  child: Icon(
                    p.estado == 'canjeado' ? Icons.check_circle : Icons.cancel,
                    size: 80,
                    color: p.estado == 'canjeado' ? Colors.green : Colors.grey,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
