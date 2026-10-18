import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_state.dart';

/// Login simplificado: solo teléfono + CI (sin OTP ni contraseña).
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  static const _demo = bool.fromEnvironment('DEMO', defaultValue: false);

  bool _esRegistro = false;
  final _nombre = TextEditingController();
  final _telefono = TextEditingController();
  final _ci = TextEditingController();
  final _codigoReferido = TextEditingController();
  String? _error;
  bool _cargando = false;

  Future<void> _enviar() async {
    setState(() { _error = null; _cargando = true; });
    try {
      final tel = _telefono.text.trim().replaceAll(RegExp(r'[\s\-]'), '');
      final ci = _ci.text.trim().replaceAll(RegExp(r'[\s\-]'), '');

      if (_esRegistro) {
        final nom = _nombre.text.trim();
        if (nom.length < 2) throw Exception('Ingresa tu nombre completo');
        if (tel.length < 4) throw Exception('Ingresa un teléfono válido');
        if (ci.length < 3) throw Exception('Ingresa una cédula válida');

        await context.read<AuthState>().registro(
          nom,
          tel,
          ci,
          _codigoReferido.text.trim().isEmpty ? null : _codigoReferido.text.trim(),
        );
      } else {
        await context.read<AuthState>().login(tel, ci);
      }
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('ApiException: ', '').replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset('assets/logo.png', height: 68),
                const SizedBox(height: 4),
                Text('Tu billetera de puntos',
                    style: TextStyle(color: Colors.grey[600], fontSize: 16)),
                const SizedBox(height: 32),

                // Selector de modo: Ingresar / Registrarme
                SegmentedButton<bool>(
                  segments: const [
                    ButtonSegment<bool>(
                      value: false,
                      label: Text('Ingresar'),
                      icon: Icon(Icons.login),
                    ),
                    ButtonSegment<bool>(
                      value: true,
                      label: Text('Registrarme'),
                      icon: Icon(Icons.person_add),
                    ),
                  ],
                  selected: {_esRegistro},
                  onSelectionChanged: (Set<bool> sel) {
                    setState(() {
                      _esRegistro = sel.first;
                      _error = null;
                    });
                  },
                ),
                const SizedBox(height: 24),

                if (_esRegistro) ...[
                  TextField(
                    controller: _nombre,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                      labelText: 'Nombre completo',
                      hintText: 'Ej: Juan Pérez',
                      prefixIcon: Icon(Icons.person),
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],

                TextField(
                  controller: _telefono,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Teléfono celular',
                    hintText: 'Ej: 70000001',
                    prefixIcon: Icon(Icons.phone),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),

                TextField(
                  controller: _ci,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Cédula de identidad (CI)',
                    hintText: 'Ej: 12345678',
                    prefixIcon: Icon(Icons.badge),
                    border: OutlineInputBorder(),
                  ),
                ),

                if (_esRegistro) ...[
                  const SizedBox(height: 16),
                  TextField(
                    controller: _codigoReferido,
                    textCapitalization: TextCapitalization.characters,
                    decoration: const InputDecoration(
                      labelText: 'Código de referido (opcional)',
                      hintText: 'Ej: B5QQ5D5E',
                      prefixIcon: Icon(Icons.card_giftcard),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ],

                if (_error != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red[50], borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(_error!, style: const TextStyle(color: Colors.red)),
                  ),
                ],
                const SizedBox(height: 24),

                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: FilledButton(
                    onPressed: _cargando ? null : _enviar,
                    child: _cargando
                        ? const SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : Text(_esRegistro ? 'Crear cuenta' : 'Ingresar',
                            style: const TextStyle(fontSize: 16)),
                  ),
                ),

                if (!_esRegistro && _demo) ...[
                  const SizedBox(height: 16),
                  TextButton.icon(
                    onPressed: _cargando
                        ? null
                        : () {
                            _telefono.text = '70000001';
                            _ci.text = '12345678';
                          },
                    icon: const Icon(Icons.play_circle_outline, size: 18),
                    label: const Text('Cargar usuario demo (70000001 / 12345678)'),
                  ),
                ],

                const SizedBox(height: 12),
                Text(
                  _esRegistro
                      ? 'Tus datos se guardarán en la base de datos para acumular y canjear puntos.'
                      : 'Usa el teléfono y la CI con los que te registraste en el local o en la app.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey[500], fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
