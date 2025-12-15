/*
Widget de Escaneo de Red - Network Scanner
Componente para escanear la red y mostrar progreso usando TVProvider
*/

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/tv_provider.dart';
import '../core/constants.dart';
import 'app_notification.dart';

class NetworkScanner extends StatefulWidget {
  final VoidCallback? onScanComplete;
  final String? customSubnet;

  const NetworkScanner({
    Key? key,
    this.onScanComplete,
    this.customSubnet,
  }) : super(key: key);

  @override
  State<NetworkScanner> createState() => _NetworkScannerState();
}

class _NetworkScannerState extends State<NetworkScanner>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _rotationAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _animationController,
        curve: Curves.linear,
      ),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final tvProvider = Provider.of<TVProvider>(context);
    if (tvProvider.isScanning) {
      if (!_animationController.isAnimating) {
        _animationController.repeat();
      }
    } else {
      if (_animationController.isAnimating) {
        _animationController.stop();
        _animationController.reset();
      }
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _handleAction() async {
    final tvProvider = context.read<TVProvider>();

    if (tvProvider.isScanning) {
      tvProvider.cancelScan();
      AppNotification.showInfo(context, 'Escaneo cancelado');
      return;
    }

    final summary = await tvProvider.scanNetwork(context);

    if (!mounted) return;

    if (summary.hasError) {
      AppNotification.showError(
        context,
        summary.errorMessage ?? 'Error al escanear la red',
      );
    } else if (summary.cancelled) {
      AppNotification.showWarning(context, 'Escaneo cancelado');
    } else if (summary.found == 0) {
      AppNotification.showWarning(
        context,
        'No se encontraron TVs en la red',
      );
    } else {
      AppNotification.showSuccess(
        context,
        'Encontradas ${summary.found} TV(s) nuevas',
      );
    }

    widget.onScanComplete?.call();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tvProvider = context.watch<TVProvider>();
    final isScanning = tvProvider.isScanning;
    final progress = tvProvider.scanProgress;
    final completed = tvProvider.scanCompletedIps;
    final total = tvProvider.scanTotalIps;
    final found = tvProvider.scanFoundCount;
    final currentIp = tvProvider.scanCurrentIp;
    final statusText = isScanning
        ? (tvProvider.isScanCancelled
            ? 'Cancelando...'
            : (currentIp != null
                ? 'Escaneando $currentIp...'
                : 'Escaneando...'))
        : 'Busca automáticamente Smart TVs en tu red local';

    return Container(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        boxShadow: [
          BoxShadow(
            color: theme.shadowColor.withAlpha((0.2 * 255).round()),
            offset: const Offset(4, 4),
            blurRadius: 10,
          ),
          BoxShadow(
            color: theme.brightness == Brightness.light
                ? Colors.white
                : theme.shadowColor.withAlpha((0.1 * 255).round()),
            offset: const Offset(-4, -4),
            blurRadius: 10,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              RotationTransition(
                turns: _rotationAnimation,
                child: Icon(
                  Icons.wifi_find,
                  color: isScanning
                      ? theme.primaryColor
                      : theme.disabledColor,
                  size: 32,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Escaneo de Red',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: theme.textTheme.titleLarge?.color,
                      ),
                    ),
                    Text(
                      statusText,
                      style: TextStyle(
                        fontSize: 12,
                        color: theme.textTheme.bodyMedium?.color?.withAlpha(153),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (isScanning) ...[
            LinearProgressIndicator(
              value: progress.clamp(0, 1),
              backgroundColor: theme.disabledColor.withAlpha(51),
              valueColor: AlwaysStoppedAnimation<Color>(
                theme.primaryColor,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '$completed / $total IPs escaneadas',
                  style: TextStyle(
                    fontSize: 12,
                    color: theme.textTheme.bodyMedium?.color?.withAlpha(153),
                  ),
                ),
                Text(
                  '$found encontradas',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.secondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
          ],
          ElevatedButton.icon(
            onPressed: _handleAction,
            icon: Icon(isScanning ? Icons.stop : Icons.search),
            label: Text(isScanning ? 'Cancelar escaneo' : 'Iniciar escaneo'),
            style: ElevatedButton.styleFrom(
              backgroundColor: isScanning
                  ? theme.colorScheme.error
                  : theme.primaryColor,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(AppConstants.buttonBorderRadius),
              ),
              elevation: isScanning ? 0 : 4,
            ),
          ),
          if (!isScanning) ...[
            const SizedBox(height: 12),
            Text(
              'Asegúrate de que tu dispositivo esté en la misma red que las TVs.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: theme.textTheme.bodyMedium?.color?.withAlpha(153),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
