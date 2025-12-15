
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/barril_models.dart';
import '../providers/tv_provider.dart';
import '../theme/app_theme.dart';

class SelectedTVCard extends StatelessWidget {
  const SelectedTVCard({
    super.key,
    required this.selectedTV,
    required this.onScanPressed,
  });

  final SmartTV? selectedTV;
  final VoidCallback onScanPressed;

  @override
  Widget build(BuildContext context) {
    final isScanning = context.watch<TVProvider>().isScanning;
    final backgroundColor = Theme.of(context).colorScheme.surface;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final errorColor = Theme.of(context).colorScheme.error;
    final textPrimary =
        Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;
    final textSecondary =
        Theme.of(context).textTheme.bodyMedium?.color ?? Colors.grey;

    if (selectedTV == null) {
      return _buildNoTVSelectedCard(
        backgroundColor: backgroundColor,
        isScanning: isScanning,
        errorColor: errorColor,
        primaryColor: primaryColor,
        onScanPressed: onScanPressed,
      );
    }

    return _buildSelectedTVInfoCard(
      backgroundColor: backgroundColor,
      textSecondary: textSecondary,
      textPrimary: textPrimary,
      selectedTV: selectedTV!,
    );
  }

  Widget _buildNoTVSelectedCard({
    required Color backgroundColor,
    required bool isScanning,
    required Color errorColor,
    required Color primaryColor,
    required VoidCallback onScanPressed,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.concaveDecoration(
        backgroundColor: backgroundColor,
        borderRadius: 20,
      ),
      child: Column(
        children: [
          const Icon(Icons.tv_off, size: 48, color: Colors.grey),
          const SizedBox(height: 16),
          const Text(
            'No hay TV seleccionada',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Escanea la red o registra una TV manualmente',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          Container(
            decoration: AppTheme.convexDecoration(
              backgroundColor: isScanning ? errorColor : primaryColor,
              borderRadius: 12,
            ),
            child: ElevatedButton.icon(
              onPressed: onScanPressed,
              icon: Icon(
                isScanning ? Icons.stop : Icons.radar,
                color: Colors.white,
              ),
              label: Text(
                isScanning ? 'Cancelar escaneo' : 'Buscar TVs',
                style: const TextStyle(color: Colors.white),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: isScanning ? errorColor : primaryColor,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSelectedTVInfoCard({
    required Color backgroundColor,
    required Color textSecondary,
    required Color textPrimary,
    required SmartTV selectedTV,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.concaveDecoration(
        backgroundColor: backgroundColor,
        borderRadius: 20,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: AppTheme.concaveDecoration(
                  backgroundColor: backgroundColor,
                  borderRadius: 12,
                ),
                child: Icon(
                  selectedTV.brandIcon,
                  size: 32,
                  color: selectedTV.statusColor,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'TV Seleccionada',
                      style: TextStyle(
                        fontSize: 14,
                        color: textSecondary,
                      ),
                    ),
                    Text(
                      selectedTV.name,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: textPrimary,
                      ),
                    ),
                    Text(
                      '${selectedTV.brand.name.toUpperCase()} • ${selectedTV.ip}:${selectedTV.port}',
                      style: TextStyle(
                        color: textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: AppTheme.concaveDecoration(
                  backgroundColor: backgroundColor,
                  borderRadius: 12,
                ),
                child: Text(
                  selectedTV.statusText,
                  style: TextStyle(
                    color: selectedTV.statusColor,
                    fontWeight: FontWeight.w600,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          if (selectedTV.lastControlled != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: AppTheme.concaveDecoration(
                backgroundColor: backgroundColor,
                borderRadius: 8,
              ),
              child: Text(
                'Último control: ${_formatDateTime(selectedTV.lastControlled!)}',
                style: TextStyle(fontSize: 12, color: textSecondary),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }
}
