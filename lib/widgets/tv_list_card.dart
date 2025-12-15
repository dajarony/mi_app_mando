import 'package:flutter/material.dart';

import '../models/barril_models.dart';
import '../theme/app_theme.dart';

class TVListCard extends StatelessWidget {
  final List<SmartTV> tvs;
  final SmartTV? selectedTV;
  final Function(SmartTV) onSelectTV;
  final Function(SmartTV) onRemoveTV;

  const TVListCard({
    super.key,
    required this.tvs,
    required this.selectedTV,
    required this.onSelectTV,
    required this.onRemoveTV,
  });

  @override
  Widget build(BuildContext context) {
    final backgroundColor = Theme.of(context).colorScheme.surface;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final textPrimary =
        Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;
    final textSecondary =
        Theme.of(context).textTheme.bodyMedium?.color ?? Colors.grey;

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
                padding: const EdgeInsets.all(8),
                decoration: AppTheme.concaveDecoration(
                  backgroundColor: backgroundColor,
                  borderRadius: 8,
                ),
                child: Icon(
                  Icons.list,
                  color: primaryColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                'TVs Registradas',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: textPrimary,
                ),
              ),
              const Spacer(),
              Text(
                '${tvs.length}',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (tvs.isEmpty)
            Container(
              padding: const EdgeInsets.all(24),
              decoration: AppTheme.concaveDecoration(
                backgroundColor: backgroundColor,
                borderRadius: 12,
              ),
              child: Center(
                child: Column(
                  children: [
                    const Icon(Icons.tv_off, size: 48, color: Colors.grey),
                    const SizedBox(height: 12),
                    Text(
                      'No hay TVs registradas',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: textSecondary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Usa el escaneo automático o registro manual',
                      style: TextStyle(
                        color: Colors.grey,
                        fontSize: 14,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            )
          else
            Column(
              children: tvs.map((tv) => _buildTVListItem(context, tv)).toList(),
            ),
        ],
      ),
    );
  }

  Widget _buildTVListItem(BuildContext context, SmartTV tv) {
    final isSelected = selectedTV?.id == tv.id;
    final backgroundColor = Theme.of(context).colorScheme.surface;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final errorColor = Theme.of(context).colorScheme.error;
    final textPrimary =
        Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;
    final textSecondary =
        Theme.of(context).textTheme.bodyMedium?.color ?? Colors.grey;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: isSelected
          ? AppTheme.convexDecoration(
              backgroundColor: backgroundColor,
              borderRadius: 16,
            )
          : AppTheme.concaveDecoration(
              backgroundColor: backgroundColor,
              borderRadius: 16,
            ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => onSelectTV(tv),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: AppTheme.concaveDecoration(
                    backgroundColor: backgroundColor,
                    borderRadius: 8,
                  ),
                  child: Icon(
                    tv.brandIcon,
                    color: tv.statusColor,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              tv.name,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: isSelected ? primaryColor : textPrimary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (tv.isFavorite) ...[
                            const SizedBox(width: 8),
                            Icon(
                              Icons.favorite,
                              color: errorColor,
                              size: 16,
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${tv.brand.name.toUpperCase()} • ${tv.ip}:${tv.port} • ${tv.room}',
                        style: TextStyle(
                          color: textSecondary,
                          fontSize: 12,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: AppTheme.concaveDecoration(
                          backgroundColor: backgroundColor,
                          borderRadius: 6,
                        ),
                        child: Text(
                          tv.statusText,
                          style: TextStyle(
                            color: tv.statusColor,
                            fontSize: 10,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  children: [
                    Container(
                      decoration: isSelected
                          ? AppTheme.convexDecoration(
                              backgroundColor: primaryColor,
                              borderRadius: 8,
                            )
                          : AppTheme.concaveDecoration(
                              backgroundColor: backgroundColor,
                              borderRadius: 8,
                            ),
                      child: IconButton(
                        icon: Icon(
                          isSelected
                              ? Icons.check_circle
                              : Icons.radio_button_unchecked,
                          color: isSelected ? Colors.white : textSecondary,
                          size: 20,
                        ),
                        onPressed: () => onSelectTV(tv),
                        tooltip: isSelected ? 'TV Activa' : 'Seleccionar',
                      ),
                    ),
                    Container(
                      decoration: AppTheme.concaveDecoration(
                        backgroundColor: backgroundColor,
                        borderRadius: 8,
                      ),
                      child: IconButton(
                        icon: Icon(
                          Icons.delete_outline,
                          color: errorColor,
                          size: 18,
                        ),
                        onPressed: () => onRemoveTV(tv),
                        tooltip: 'Eliminar',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
