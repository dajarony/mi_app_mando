/*
SUME DOCBLOCK

Nombre: Smart TV Manager - Versión Corregida y Completamente Funcional
Tipo: Entrada + Lógica + Salida

Entradas:
- Escaneo de red HTTP real
- APIs específicas por marca (Samsung, LG, Sony)
- Comandos de control remoto reales
- Formulario de registro manual

Acciones:
- Descubrimiento real de Smart TVs en la red
- Conexión HTTP/WebSocket real con dispositivos
- Control remoto funcional
- Persistencia de datos local

Salidas:
- Interfaz neumórfica moderna
- Comunicación real con Smart TVs
- Feedback en tiempo real
- Control remoto completo

DEPENDENCIAS MÍNIMAS REQUERIDAS:
dio: ^5.3.2
shared_preferences: ^2.2.2
uuid: ^4.0.0
http: ^1.1.0
web_socket_channel: ^2.4.0
*/

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:mi_app_expriment2/providers/tv_provider.dart';
import 'package:provider/provider.dart';
import 'package:mi_app_expriment2/models/smart_tv.dart';
import 'package:mi_app_expriment2/services/network_service.dart';
import 'package:mi_app_expriment2/services/storage_service.dart';
import 'package:mi_app_expriment2/services/tv_remote_service.dart';
import 'package:mi_app_expriment2/theme/app_theme.dart';
import 'package:mi_app_expriment2/widgets/remote_control_card.dart';
import 'package:mi_app_expriment2/widgets/selected_tv_card.dart';
import 'package:mi_app_expriment2/widgets/tv_list_card.dart';
import 'package:mi_app_expriment2/widgets/tv_registration_card.dart';

import 'remote_control_screen.dart';

// ==========================================
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final NetworkService _networkService = NetworkService();
  final TVRemoteService _remoteService = TVRemoteService();
  final StorageService _storageService = StorageService();

  List<SmartTV> _registeredTVs = [];
  SmartTV? _selectedTV;
  bool _isLoading = false;
  bool _isRegistering = false;
  
  // Animación para el botón de escaneo
  late AnimationController _scanAnimationController;

  @override
  void dispose() {
    _scanAnimationController.dispose();
    _remoteService.closeAllConnections();
    _networkService.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    
    // Inicializar animación de escaneo (rotación infinita)
    _scanAnimationController = AnimationController(
      duration: const Duration(seconds: 1),
      vsync: this,
    );
    
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    setState(() => _isLoading = true);

    try {
      await _storageService.initialize();

      // Inicializar TVProvider (esto añade la TV demo si no hay TVs)
      final tvProvider = context.read<TVProvider>();
      await tvProvider.initialize();
      
      // Sincronizar desde TVProvider para obtener todas las TVs (incluyendo la demo)
      _syncFromProvider(tvProvider);

      // Verificar estado de TVs si hay alguna registrada
      if (_registeredTVs.isNotEmpty) {
        _verifyTVsStatus();
      }
    } catch (e) {
      _showErrorMessage('Error inicializando app: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _verifyTVsStatus() async {
    final tvProvider = context.read<TVProvider>();
    for (int i = 0; i < _registeredTVs.length; i++) {
      final tv = _registeredTVs[i];
      final isOnline = await _networkService.validateSmartTVConnection(tv);

      final updatedTv = tv.copyWith(
        isOnline: isOnline,
        lastPing: DateTime.now(),
      );

      if (mounted) {
        setState(() {
          _registeredTVs[i] = updatedTv;
          if (_selectedTV?.id == updatedTv.id) {
            _selectedTV = updatedTv;
          }
        });
      }

      await tvProvider.updateTVStatus(
        tv.id,
        isOnline: isOnline,
      );
    }

    await _storageService.saveTVs(_registeredTVs);
  }

  void _syncFromProvider([TVProvider? provider]) {
    if (!mounted) return;
    final tvProvider = provider ?? context.read<TVProvider>();
    setState(() {
      _registeredTVs = List<SmartTV>.from(tvProvider.tvs);
      _selectedTV = tvProvider.selectedTV ?? _selectedTV;
    });
  }

  Future<void> _scanForTVs() async {
    final tvProvider = context.read<TVProvider>();

    if (tvProvider.isScanning) {
      tvProvider.cancelScan();
      _scanAnimationController.stop();
      _showInfoMessage('Escaneo cancelado');
      return;
    }

    // Iniciar animación de rotación
    _scanAnimationController.repeat();

    final summary = await tvProvider.scanNetwork(context);
    
    // Detener animación
    _scanAnimationController.stop();
    _scanAnimationController.reset();
    
    _syncFromProvider(tvProvider);

    if (summary.hasError) {
      _showErrorMessage(summary.errorMessage ?? 'Error al escanear la red');
    } else if (summary.cancelled) {
      _showInfoMessage('Escaneo cancelado');
    } else if (summary.found == 0) {
      _showInfoMessage('No se encontraron TVs nuevas en la red');
    } else {
      _showSuccessMessage('Se registraron ${summary.found} TV(s) nuevas');
    }
  }

  Future<void> _registerTVManually(SmartTV newTV) async {
    setState(() => _isRegistering = true);
    final scaffoldMessenger = ScaffoldMessenger.of(context);

    try {
      // Verificar que la IP no esté duplicada
      if (_registeredTVs.any((tv) => tv.ip == newTV.ip)) {
        _showErrorMessage('Ya existe una TV con esta IP');
        return;
      }

      final tvProvider = context.read<TVProvider>();
      final isOnline = await _networkService.validateSmartTVConnection(newTV);

      if (!mounted) return;

      if (isOnline) {
        final isPaired = await _networkService.pairWithTV(newTV);
        if (!mounted) return;

        final tvWithStatus = newTV.copyWith(
          isOnline: true,
          isPaired: isPaired,
          isRegistered: true,
          lastPing: DateTime.now(),
        );

        await tvProvider.addTV(tvWithStatus);
        await tvProvider.selectTV(tvWithStatus.id);
        _syncFromProvider(tvProvider);

        scaffoldMessenger.showSnackBar(
          SnackBar(
            content: Text('TV ${newTV.name} registrada exitosamente'),
            backgroundColor: AppTheme.accentGreen,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      } else {
        scaffoldMessenger.showSnackBar(
          SnackBar(
            content: Text(
                'No se pudo conectar con la TV en ${newTV.ip}:${newTV.port}'),
            backgroundColor: Theme.of(context).colorScheme.error,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } catch (e) {
      _showErrorMessage('❌ Error registrando TV: $e');
    } finally {
      if (mounted) {
        setState(() => _isRegistering = false);
      }
    }
  }

  Future<void> _selectTV(SmartTV tv) async {
    final tvProvider = context.read<TVProvider>();
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final theme = Theme.of(context);

    await tvProvider.selectTV(tv.id);
    _syncFromProvider(tvProvider);

    final isOnline = await _networkService.validateSmartTVConnection(tv);
    if (!mounted) return;

    setState(() {
      final index = _registeredTVs.indexWhere((t) => t.id == tv.id);
      if (index >= 0) {
        final updatedTv = _registeredTVs[index].copyWith(
          isOnline: isOnline,
          lastPing: DateTime.now(),
        );
        _registeredTVs[index] = updatedTv;
        if (_selectedTV?.id == updatedTv.id) {
          _selectedTV = updatedTv;
        }
      }
    });

    await tvProvider.updateTVStatus(
      tv.id,
      isOnline: isOnline,
    );

    if (isOnline) {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('TV ${tv.name} seleccionada y conectada'),
          backgroundColor: AppTheme.accentGreen,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    } else {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('TV ${tv.name} seleccionada pero no responde'),
          backgroundColor: theme.colorScheme.error,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    }
  }

  Future<void> _sendRemoteCommand(String command) async {
    if (_selectedTV == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona una TV primero')),
      );
      return;
    }

    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final success = await _remoteService.sendCommand(_selectedTV!, command);
    if (!mounted) return;

    if (success) {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('${command.toUpperCase()} enviado'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
      final index = _registeredTVs.indexWhere((t) => t.id == _selectedTV!.id);
      if (index >= 0) {
        setState(() {
          _registeredTVs[index] = _selectedTV!.copyWith(
            lastControlled: DateTime.now(),
          );
        });
      }
    } else {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('Error enviando comando ${command.toUpperCase()}'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }

  Future<void> _removeTV(SmartTV tv) async {
    // ignore: use_build_context_synchronously
    // ignore: use_build_context_synchronously
    final confirmed = await _showConfirmDialog(
      '¿Eliminar ${tv.name}?',
      'Esta acción no se puede deshacer',
    );

    if (confirmed) {
      if (!mounted) return;
      setState(() {
        _registeredTVs.removeWhere((t) => t.id == tv.id);
        if (_selectedTV?.id == tv.id) {
          _selectedTV = _registeredTVs.isNotEmpty ? _registeredTVs.first : null;
        }
      });

      await _storageService.saveTVs(_registeredTVs);
      if (_selectedTV != null) {
        await _storageService.setSelectedTVId(_selectedTV!.id);
      }

      if (!mounted) return;
      // ignore: use_build_context_synchronously
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('TV ${tv.name} eliminada'),
          backgroundColor: AppTheme.accentGreen,
        ),
      );
    }
  }

  Future<bool> _showConfirmDialog(String title, String content) async {
    if (!mounted) return false;
    final errorColor = Theme.of(context).colorScheme.error;
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text(title),
            content: Text(content),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancelar'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.pop(context, true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: errorColor,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Confirmar'),
              ),
            ],
          ),
        ) ??
        false;
  }

  void _showSuccessMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.accentGreen,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  void _showErrorMessage(String message) {
    if (!mounted) return;
    final errorColor = Theme.of(context).colorScheme.error;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: errorColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  void _showInfoMessage(String message) {
    if (!mounted) return;
    final primaryColor = Theme.of(context).colorScheme.primary;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: primaryColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tvProvider = context.watch<TVProvider>();
    final isScanning = tvProvider.isScanning;
    final backgroundColor = Theme.of(context).colorScheme.surface;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart TV Manager'),
        backgroundColor: backgroundColor,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.tv_outlined),
            onPressed: () {
              // Siempre navegar al control remoto
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => RemoteControlScreen(
                    tvIpAddress: _selectedTV?.ip,
                    tvName: _selectedTV?.name,
                  ),
                ),
              );
            },
            tooltip: 'Control Remoto',
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
            tooltip: 'Configuraciones',
          ),
          // Botón de escaneo con animación
          RotationTransition(
            turns: _scanAnimationController,
            child: IconButton(
              icon: Icon(
                isScanning ? Icons.stop_circle_outlined : Icons.radar,
                color: isScanning ? Theme.of(context).colorScheme.primary : null,
              ),
              onPressed: _scanForTVs,
              tooltip: isScanning ? 'Cancelar escaneo' : 'Escanear TVs',
            ),
          ),
        ],
      ),
      backgroundColor: backgroundColor,
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Cargando...'),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSelectedTVCard(),
                  const SizedBox(height: 20),
                  if (_selectedTV != null && _selectedTV!.isOnline)
                    _buildRemoteControlSection(),
                  if (_selectedTV != null && _selectedTV!.isOnline)
                    const SizedBox(height: 20),
                  _buildTVsList(),
                  const SizedBox(height: 20),
                  _buildManualRegistrationForm(),
                  const SizedBox(height: 100),
                ],
              ),
            ),
    );
  }

  Widget _buildSelectedTVCard() {
    return SelectedTVCard(
      selectedTV: _selectedTV,
      onScanPressed: _scanForTVs,
    );
  }

  Widget _buildRemoteControlSection() {
    return RemoteControlCard(onCommand: _sendRemoteCommand);
  }

  Widget _buildTVsList() {
    return TVListCard(
      tvs: _registeredTVs,
      selectedTV: _selectedTV,
      onSelectTV: _selectTV,
      onRemoveTV: _removeTV,
    );
  }

  Widget _buildManualRegistrationForm() {
    return TVRegistrationCard(
      isRegistering: _isRegistering,
      onRegister: _registerTVManually,
    );
  }
}
