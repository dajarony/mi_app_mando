import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../screens/home_screen.dart';
import '../screens/remote_control_screen.dart';
import '../screens/theme/theme_selector_screen.dart';
import '../providers/settings_provider.dart';

class AppRoutes {
  static const String home = '/';
  static const String remoteControl = '/remote_control';
  static const String settings = '/settings';
  static const String themeSelector = '/theme_selector';

  static Map<String, WidgetBuilder> getRoutes() {
    return {
      home: (context) => const HomeScreen(),
      remoteControl: (context) => const RemoteControlScreen(),
      settings: (context) => const SettingsScreen(),
      themeSelector: (context) => const ThemeSelectorScreen(),
    };
  }

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case home:
        return MaterialPageRoute(
          builder: (context) => const HomeScreen(),
        );
      case remoteControl:
        return MaterialPageRoute(
          builder: (context) => const RemoteControlScreen(),
        );
      case '/settings':
        return MaterialPageRoute(
          builder: (context) => const SettingsScreen(),
        );
      case themeSelector:
        return MaterialPageRoute(
          builder: (context) => const ThemeSelectorScreen(),
        );
      default:
        return MaterialPageRoute(
          builder: (context) => const HomeScreen(),
        );
    }
  }
}

// La pantalla funcional está importada desde ../screens/remote_control_screen.dart

// Pantalla de configuraciones funcional
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _philipsIpController = TextEditingController();
  final _subnetController = TextEditingController();
  final _startIpController = TextEditingController();
  final _endIpController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final settingsProvider = context.read<SettingsProvider>();
      _philipsIpController.text = settingsProvider.philipsTvIp;
      _subnetController.text = settingsProvider.subnet;
      _startIpController.text = settingsProvider.scanIpStart.toString();
      _endIpController.text = settingsProvider.scanIpEnd.toString();
    });
  }

  Future<void> _saveSettings() async {
    final settingsProvider = context.read<SettingsProvider>();
    bool success = true;

    // Guardar IP de Philips
    final newPhilipsIp = _philipsIpController.text.trim();
    if (newPhilipsIp.isNotEmpty) {
      success &= await settingsProvider.savePhilipsTvIp(newPhilipsIp);
    }

    // Guardar configuración de escaneo
    final newSubnet = _subnetController.text.trim();
    final newStartIp = int.tryParse(_startIpController.text);
    final newEndIp = int.tryParse(_endIpController.text);

    if (newSubnet.isNotEmpty && newStartIp != null && newEndIp != null) {
      success &= await settingsProvider.saveNetworkScanSettings(
        subnet: newSubnet,
        startIp: newStartIp,
        endIp: newEndIp,
      );
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success
              ? 'Configuración guardada exitosamente'
              : 'Error al guardar la configuración'),
          backgroundColor: success ? Colors.green : Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    context.watch<SettingsProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuraciones'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Theme Selector Card
          Card(
            elevation: 2,
            color: Theme.of(context).colorScheme.surface,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: const Icon(Icons.palette_outlined, size: 32),
              title: const Text(
                'Tema de la Aplicación',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Personaliza los colores de la app'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                Navigator.pushNamed(context, AppRoutes.themeSelector);
              },
            ),
          ),
          const SizedBox(height: 24),

          // Network Scan Configuration Section
          const Text(
            'Escaneo de Red',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _subnetController,
            decoration: const InputDecoration(
              labelText: 'Subred a escanear',
              hintText: '192.168.1',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _startIpController,
                  decoration: const InputDecoration(
                    labelText: 'IP Inicial',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextField(
                  controller: _endIpController,
                  decoration: const InputDecoration(
                    labelText: 'IP Final',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                ),
              ),
            ],
          ),

          const SizedBox(height: 32),

          // TV Configuration Section
          const Text(
            'Configuración de TV Philips',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _philipsIpController,
            decoration: const InputDecoration(
              labelText: 'IP de la TV Philips',
              hintText: '192.168.1.100',
              border: OutlineInputBorder(),
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _saveSettings,
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: const Text('Guardar Toda la Configuración'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _philipsIpController.dispose();
    _subnetController.dispose();
    _startIpController.dispose();
    _endIpController.dispose();
    super.dispose();
  }
}
