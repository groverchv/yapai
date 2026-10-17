import 'package:flutter/material.dart';

import 'explorar_screen.dart';
import 'pases_screen.dart';
import 'perfil_screen.dart';
import 'wallet_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;

  final _pantallas = const [
    WalletScreen(),
    ExplorarScreen(),
    PasesScreen(),
    PerfilScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _tab, children: _pantallas),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.account_balance_wallet_outlined),
              selectedIcon: Icon(Icons.account_balance_wallet), label: 'Billetera'),
          NavigationDestination(icon: Icon(Icons.storefront_outlined),
              selectedIcon: Icon(Icons.storefront), label: 'Explorar'),
          NavigationDestination(icon: Icon(Icons.qr_code_2_outlined),
              selectedIcon: Icon(Icons.qr_code_2), label: 'Pases'),
          NavigationDestination(icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person), label: 'Perfil'),
        ],
      ),
    );
  }
}
