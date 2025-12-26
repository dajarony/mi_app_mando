import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../screens/home_screen.dart';
import '../screens/remote_control_screen.dart';
import '../screens/theme/theme_selector_screen.dart';
import '../providers/settings_provider.dart';
import '../theme/app_theme.dart';

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
    final backgroundColor = Theme.of(context).colorScheme.surface;
    final textColor = Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;

    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        title: const Text('Configuraciones'),
        backgroundColor: backgroundColor,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Theme Selector Card - Neumorphic
          Container(
            decoration: AppTheme.convexDecoration(
              backgroundColor: backgroundColor,
              borderRadius: 16,
            ),
            child: ListTile(
              contentPadding: const EdgeInsets.all(16),
              leading: Container(
                padding: const EdgeInsets.all(10),
                decoration: AppTheme.concaveDecoration(
                  backgroundColor: backgroundColor,
                  borderRadius: 12,
                ),
                child: Icon(Icons.palette_outlined, size: 28, color: Theme.of(context).colorScheme.primary),
              ),
              title: Text(
                'Tema de la Aplicación',
                style: TextStyle(fontWeight: FontWeight.w600, color: textColor),
              ),
              subtitle: Text(
                'Personaliza los colores de la app',
                style: TextStyle(color: textColor.withValues(alpha: 0.7)),
              ),
              trailing: Icon(Icons.chevron_right, color: textColor),
              onTap: () {
                Navigator.pushNamed(context, AppRoutes.themeSelector);
              },
            ),
          ),
          const SizedBox(height: 24),

          // Network Scan Configuration Section
          Container(
            padding: const EdgeInsets.all(20),
            decoration: AppTheme.concaveDecoration(
              backgroundColor: backgroundColor,
              borderRadius: 16,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: AppTheme.concaveDecoration(
                        backgroundColor: backgroundColor,
                        borderRadius: 8,
                      ),
                      child: Icon(Icons.radar, color: Theme.of(context).colorScheme.primary),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Escaneo de Red',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Container(
                  decoration: AppTheme.concaveDecoration(
                    backgroundColor: backgroundColor,
                    borderRadius: 12,
                  ),
                  child: TextField(
                    controller: _subnetController,
                    style: TextStyle(color: textColor),
                    decoration: const InputDecoration(
                      labelText: 'Subred a escanear',
                      hintText: '192.168.1',
                      prefixIcon: Icon(Icons.router),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.all(16),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        decoration: AppTheme.concaveDecoration(
                          backgroundColor: backgroundColor,
                          borderRadius: 12,
                        ),
                        child: TextField(
                          controller: _startIpController,
                          style: TextStyle(color: textColor),
                          decoration: const InputDecoration(
                            labelText: 'IP Inicial',
                            prefixIcon: Icon(Icons.first_page),
                            border: InputBorder.none,
                            contentPadding: EdgeInsets.all(16),
                          ),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Container(
                        decoration: AppTheme.concaveDecoration(
                          backgroundColor: backgroundColor,
                          borderRadius: 12,
                        ),
                        child: TextField(
                          controller: _endIpController,
                          style: TextStyle(color: textColor),
                          decoration: const InputDecoration(
                            labelText: 'IP Final',
                            prefixIcon: Icon(Icons.last_page),
                            border: InputBorder.none,
                            contentPadding: EdgeInsets.all(16),
                          ),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          // TV Configuration Section
          Container(
            padding: const EdgeInsets.all(20),
            decoration: AppTheme.concaveDecoration(
              backgroundColor: backgroundColor,
              borderRadius: 16,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: AppTheme.concaveDecoration(
                        backgroundColor: backgroundColor,
                        borderRadius: 8,
                      ),
                      child: Icon(Icons.tv, color: Theme.of(context).colorScheme.primary),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Configuración de TV',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: textColor),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Container(
                  decoration: AppTheme.concaveDecoration(
                    backgroundColor: backgroundColor,
                    borderRadius: 12,
                  ),
                  child: TextField(
                    controller: _philipsIpController,
                    style: TextStyle(color: textColor),
                    decoration: const InputDecoration(
                      labelText: 'IP de la TV',
                      hintText: '192.168.1.100',
                      prefixIcon: Icon(Icons.settings_ethernet),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.all(16),
                    ),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 24),
          
          // Save Button - Neumorphic
          Container(
            decoration: AppTheme.convexDecoration(
              backgroundColor: Theme.of(context).colorScheme.primary,
              borderRadius: 12,
            ),
            child: ElevatedButton(
              onPressed: _saveSettings,
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Guardar Toda la Configuración',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ),
          const SizedBox(height: 32),
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
