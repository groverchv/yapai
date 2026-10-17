import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_state.dart';

class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});

  Future<void> _confirmarEliminar(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Eliminar cuenta'),
        content: const Text(
          'Se eliminará tu cuenta de forma permanente y perderás todos tus puntos '
          'acumulados y pases activos. Esta acción no se puede deshacer.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Volver')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Eliminar definitivamente'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    try {
      await context.read<AuthState>().eliminarCuenta();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cliente = context.watch<AuthState>().cliente;
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Perfil')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: Colors.green[50],
                    child: Text(
                      cliente?.nombre.substring(0, 1).toUpperCase() ?? '?',
                      style: TextStyle(fontSize: 32, color: Colors.green[700]),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(cliente?.nombre ?? '—',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  _fila(Icons.badge, 'Cédula', cliente?.ci ?? '—'),
                  _fila(Icons.phone, 'Teléfono', cliente?.telefono ?? '—'),
                  _fila(Icons.stars, 'Puntos acumulados',
                      '${cliente?.saldoPuntos ?? 0} pts'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => context.read<AuthState>().cerrarSesion(),
              icon: const Icon(Icons.logout),
              label: const Text('Cerrar sesión'),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: TextButton.icon(
              onPressed: () => _confirmarEliminar(context),
              icon: const Icon(Icons.delete_forever, color: Colors.red),
              label: const Text('Eliminar mi cuenta',
                  style: TextStyle(color: Colors.red)),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Al eliminar la cuenta pierdes tus puntos acumulados.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[500], fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _fila(IconData icono, String label, String valor) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: [
            Icon(icono, size: 20, color: Colors.grey),
            const SizedBox(width: 12),
            Text('$label: ', style: const TextStyle(color: Colors.grey)),
            Expanded(
              child: Text(valor,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                  textAlign: TextAlign.right),
            ),
          ],
        ),
      );
}
