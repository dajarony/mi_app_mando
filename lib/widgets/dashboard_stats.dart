/*
Dashboard de Estadísticas - Dashboard Stats
Muestra estadísticas y métricas del sistema
*/

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/tv_provider.dart';
import '../services/command_history_service.dart';
import '../core/constants.dart';

class DashboardStats extends StatelessWidget {
  final CommandHistoryService? historyService;

  const DashboardStats({
    Key? key,
    this.historyService,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<TVProvider>(
      builder: (context, tvProvider, child) {
        final stats = historyService?.getStatistics();

        return SingleChildScrollView(
          padding: const EdgeInsets.all(AppConstants.defaultPadding),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Título
              const Text(
                'Resumen',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              // Estadísticas de TVs
              _buildStatsGrid([
                _StatItem(
                  icon: Icons.tv,
                  label: 'Total TVs',
                  value: tvProvider.tvCount.toString(),
                  color: const Color(AppColors.lightPrimary),
                ),
                _StatItem(
                  icon: Icons.wifi,
                  label: 'En línea',
                  value: tvProvider.onlineTVs.length.toString(),
                  color: const Color(AppColors.lightSuccess),
                ),
                _StatItem(
                  icon: Icons.star,
                  label: 'Favoritas',
                  value: tvProvider.favoriteTVs.length.toString(),
                  color: const Color(AppColors.lightWarning),
                ),
                if (stats != null)
                  _StatItem(
                    icon: Icons.history,
                    label: 'Comandos hoy',
                    value: stats['todayCommands'].toString(),
                    color: const Color(AppColors.lightInfo),
                  ),
              ]),

              const SizedBox(height: 24),

              // Historial de comandos (si está disponible)
              if (stats != null) ...[
                const Text(
                  'Historial de Comandos',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                _buildCommandStats(stats),
                const SizedBox(height: 24),
              ],

              // Marcas de TVs
              _buildBrandDistribution(tvProvider),

              const SizedBox(height: 24),

              // TVs favoritas
              if (tvProvider.favoriteTVs.isNotEmpty) ...[
                const Text(
                  'TVs Favoritas',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                ...tvProvider.favoriteTVs.map((tv) => _buildTVItem(tv)),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatsGrid(List<_StatItem> items) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
        childAspectRatio: 1.5,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return _buildStatCard(item);
      },
    );
  }

  Widget _buildStatCard(_StatItem item) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.2 * 255).round()),
            offset: const Offset(4, 4),
            blurRadius: 8,
          ),
          const BoxShadow(
            color: Color(AppColors.lightShadow),
            offset: Offset(-4, -4),
            blurRadius: 8,
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            item.icon,
            size: 32,
            color: item.color,
          ),
          const SizedBox(height: 8),
          Text(
            item.value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: item.color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            item.label,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCommandStats(Map<String, dynamic> stats) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.2 * 255).round()),
            offset: const Offset(4, 4),
            blurRadius: 8,
          ),
          const BoxShadow(
            color: Color(AppColors.lightShadow),
            offset: Offset(-4, -4),
            blurRadius: 8,
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStatRow(
            'Total de comandos',
            stats['totalCommands'].toString(),
          ),
          _buildStatRow(
            'Comandos exitosos',
            stats['successfulCommands'].toString(),
            const Color(AppColors.lightSuccess),
          ),
          _buildStatRow(
            'Comandos fallidos',
            stats['failedCommands'].toString(),
            const Color(AppColors.lightError),
          ),
          _buildStatRow(
            'Tasa de éxito',
            '${stats['successRate']}%',
            const Color(AppColors.lightInfo),
          ),
          const Divider(height: 24),
          const Text(
            'Comandos más usados:',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          ...((stats['mostUsedCommands'] as List).take(3).map((cmd) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    cmd['command'],
                    style: TextStyle(color: Colors.grey[700]),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(AppColors.lightPrimary).withAlpha((0.2 * 255).round()),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${cmd['count']}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Color(AppColors.lightPrimary),
                      ),
                    ),
                  ),
                ],
              ),
            );
          })),
        ],
      ),
    );
  }

  Widget _buildStatRow(String label, String value, [Color? valueColor]) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[700]),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBrandDistribution(TVProvider tvProvider) {
    // Agrupar por marca
    final brandCounts = <String, int>{};
    for (final tv in tvProvider.tvs) {
      final brandName = tv.brandDisplayName;
      brandCounts[brandName] = (brandCounts[brandName] ?? 0) + 1;
    }

    if (brandCounts.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Distribución por Marca',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Container(
          decoration: BoxDecoration(
            color: const Color(AppColors.lightSurface),
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            boxShadow: [
              BoxShadow(
                color: const Color(AppColors.darkShadow).withAlpha((0.2 * 255).round()),
                offset: const Offset(4, 4),
                blurRadius: 8,
              ),
              const BoxShadow(
                color: Color(AppColors.lightShadow),
                offset: Offset(-4, -4),
                blurRadius: 8,
              ),
            ],
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            children: brandCounts.entries.map((entry) {
              final percentage =
                  (entry.value / tvProvider.tvCount * 100).toStringAsFixed(0);
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          entry.key,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        Text(
                          '${entry.value} ($percentage%)',
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    LinearProgressIndicator(
                      value: entry.value / tvProvider.tvCount,
                      backgroundColor: Colors.grey[200],
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        Color(AppColors.lightPrimary),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildTVItem(tv) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius / 2),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.1 * 255).round()),
            offset: const Offset(2, 2),
            blurRadius: 4,
          ),
        ],
      ),
      child: Row(
        children: [
          const Icon(
            Icons.tv,
            color: Color(AppColors.lightPrimary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tv.name,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  '${tv.brandDisplayName} - ${tv.ip}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: tv.isOnline
                  ? const Color(AppColors.lightSuccess)
                  : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatItem {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  _StatItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });
}
