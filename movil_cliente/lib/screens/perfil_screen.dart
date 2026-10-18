import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import '../api.dart';
import '../auth_state.dart';
import '../models.dart';

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
                  _AvatarPerfil(cliente: cliente),
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
          if (cliente?.codigoReferido != null) ...[
            const SizedBox(height: 16),
            Card(
              color: const Color(0xFF14213D),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Text('Tu código de referido',
                        style: TextStyle(color: Colors.white70, fontSize: 13)),
                    const SizedBox(height: 6),
                    Text(cliente!.codigoReferido!,
                        style: const TextStyle(color: Colors.white,
                            fontSize: 26, fontWeight: FontWeight.bold,
                            letterSpacing: 3)),
                    const SizedBox(height: 6),
                    const Text(
                      'Gana puntos por cada amigo que se registre con tu código',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: const BorderSide(color: Colors.white54),
                            ),
                            onPressed: () {
                              Clipboard.setData(ClipboardData(
                                  text: cliente.codigoReferido!));
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text('Código copiado')),
                              );
                            },
                            icon: const Icon(Icons.copy, size: 18),
                            label: const Text('Copiar'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: FilledButton.icon(
                            style: FilledButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: const Color(0xFF14213D),
                            ),
                            onPressed: () => SharePlus.instance.share(
                              ShareParams(
                                text: '¡Únete a YAPAI con mi código '
                                    '${cliente.codigoReferido} y gana puntos!',
                              ),
                            ),
                            icon: const Icon(Icons.share, size: 18),
                            label: const Text('Compartir'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
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

/// Avatar del perfil: muestra la foto Cloudinary o la inicial; tap para subir.
class _AvatarPerfil extends StatefulWidget {
  final Cliente? cliente;
  const _AvatarPerfil({this.cliente});

  @override
  State<_AvatarPerfil> createState() => _AvatarPerfilState();
}

class _AvatarPerfilState extends State<_AvatarPerfil> {
  bool _subiendo = false;

  Future<void> _subir() async {
    final auth = context.read<AuthState>();
    final picked = await ImagePicker()
        .pickImage(source: ImageSource.gallery, maxWidth: 800);
    if (picked == null || !mounted) return;
    setState(() => _subiendo = true);
    try {
      final bytes = await picked.readAsBytes();
      await auth.subirFoto(bytes, picked.name);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content:
                Text(e is ApiException ? e.detail : 'Error al subir la foto'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _subiendo = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final foto = widget.cliente?.fotoUrl;
    return GestureDetector(
      onTap: _subiendo ? null : _subir,
      child: Stack(
        children: [
          CircleAvatar(
            radius: 36,
            backgroundColor: Colors.green[50],
            child: ClipOval(
              child: _subiendo
                  ? const SizedBox(width: 24, height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : foto != null
                      ? Image.network(cloudinaryThumb(foto, w: 160),
                          width: 72, height: 72, fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => _inicial())
                      : _inicial(),
            ),
          ),
          Positioned(
            right: 0, bottom: 0,
            child: Container(
              padding: const EdgeInsets.all(5),
              decoration: BoxDecoration(
                color: Colors.green[700], shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
              ),
              child: const Icon(Icons.photo_camera,
                  size: 14, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  Widget _inicial() => Center(
        child: Text(
          widget.cliente?.nombre.substring(0, 1).toUpperCase() ?? '?',
          style: TextStyle(fontSize: 32, color: Colors.green[700]),
        ),
      );
}
