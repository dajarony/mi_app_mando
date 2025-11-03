import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/smart_tv.dart';

class TVCard extends StatelessWidget {
  final SmartTV tv;
  final bool isSelected;
  final VoidCallback onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final VoidCallback? onToggleFavorite;
  final VoidCallback? onLongPress;
  final VoidCallback? onFavoriteToggle;

  const TVCard({
    super.key,
    required this.tv,
    required this.isSelected,
    required this.onTap,
    this.onEdit,
    this.onDelete,
    this.onToggleFavorite,
    this.onLongPress,
    this.onFavoriteToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(
        horizontal: AppConstants.defaultPadding,
        vertical: AppConstants.smallPadding,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
          child: Container(
            padding: const EdgeInsets.all(AppConstants.defaultPadding),
            decoration: BoxDecoration(
              color: const Color(AppColors.lightSurface),
              borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
              border: isSelected
                  ? Border.all(
                      color: const Color(AppColors.lightPrimary),
                      width: 2,
                    )
                  : null,
              boxShadow: const [
                // Sombra oscura (inferior derecha)
                BoxShadow(
                  color: Color(AppColors.lightShadowDark),
                  offset: Offset(6, 6),
                  blurRadius: 12,
                  spreadRadius: 0,
                ),
                // Sombra clara (superior izquierda) 
                BoxShadow(
                  color: Color(AppColors.lightShadowLight),
                  offset: Offset(-6, -6),
                  blurRadius: 12,
                  spreadRadius: 0,
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header con nombre y acciones
                Row(
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          // Icono de marca
                          _buildBrandIcon(),
                          const SizedBox(width: AppConstants.smallPadding),
                          // Información principal
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  tv.name,
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: Color(AppColors.lightText),
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                Text(
                                  tv.room,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Color(AppColors.lightTextSecondary),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Botón favorito
                    if (onToggleFavorite != null)
                      _buildActionButton(
                        icon: tv.isFavorite ? Icons.favorite : Icons.favorite_border,
                        color: tv.isFavorite ? Colors.red : null,
                        onPressed: onToggleFavorite!,
                      ),
                    // Botón de opciones
                    _buildActionButton(
                      icon: Icons.more_vert,
                      onPressed: () => _showOptionsMenu(context),
                    ),
                  ],
                ),
                
                const SizedBox(height: AppConstants.defaultPadding),
                
                // Información técnica
                Row(
                  children: [
                    _buildInfoChip(
                      icon: Icons.wifi,
                      label: tv.ip,
                      color: tv.isOnline ? Colors.green : Colors.grey,
                    ),
                    const SizedBox(width: AppConstants.smallPadding),
                    _buildInfoChip(
                      icon: _getProtocolIcon(),
                      label: tv.brand.toString().split('.').last.toUpperCase(),
                      color: _getBrandColor(),
                    ),
                  ],
                ),
                
                const SizedBox(height: AppConstants.defaultPadding),
                
                // Estado de conexión
                Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: _getStatusColor(),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: AppConstants.smallPadding),
                    Text(
                      _getStatusText(),
                      style: TextStyle(
                        fontSize: 12,
                        color: _getStatusColor(),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const Spacer(),
                    if (isSelected)
                      const Icon(
                        Icons.check_circle,
                        color: Color(AppColors.lightPrimary),
                        size: 20,
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

  Widget _buildBrandIcon() {
    IconData icon;
    Color color;

    switch (tv.brand.toString().split('.').last) {
      case 'samsung':
        icon = Icons.tv;
        color = const Color(AppColors.samsung);
        break;
      case 'lg':
        icon = Icons.smart_display;
        color = const Color(AppColors.lg);
        break;
      case 'sony':
        icon = Icons.live_tv;
        color = const Color(AppColors.sony);
        break;
      case 'philips':
        icon = Icons.display_settings;
        color = const Color(AppColors.philips);
        break;
      case 'roku':
        icon = Icons.cast;
        color = const Color(AppColors.roku);
        break;
      default:
        icon = Icons.tv;
        color = const Color(AppColors.lightTextSecondary);
    }

    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color.withAlpha((0.1 * 255).round()),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(
        icon,
        color: color,
        size: 20,
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required VoidCallback onPressed,
    Color? color,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
          ),
          child: Icon(
            icon,
            color: color ?? const Color(AppColors.lightTextSecondary),
            size: 20,
          ),
        ),
      ),
    );
  }

  Widget _buildInfoChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppConstants.smallPadding,
        vertical: 4,
      ),
      decoration: BoxDecoration(
        color: color.withAlpha((0.1 * 255).round()),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha((0.3 * 255).round())),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 12),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  IconData _getProtocolIcon() {
    switch (tv.protocol.toString().split('.').last) {
      case 'websocket':
        return Icons.sync_alt;
      case 'http':
        return Icons.http;
      case 'upnp':
        return Icons.network_cell;
      default:
        return Icons.device_unknown;
    }
  }

  Color _getBrandColor() {
    switch (tv.brand.toString().split('.').last) {
      case 'samsung':
        return const Color(AppColors.samsung);
      case 'lg':
        return const Color(AppColors.lg);
      case 'sony':
        return const Color(AppColors.sony);
      case 'philips':
        return const Color(AppColors.philips);
      case 'roku':
        return const Color(AppColors.roku);
      default:
        return const Color(AppColors.lightTextSecondary);
    }
  }

  Color _getStatusColor() {
    if (tv.isConnecting) {
      return const Color(AppColors.warning);
    } else if (tv.isOnline) {
      return const Color(AppColors.success);
    } else {
      return const Color(AppColors.error);
    }
  }

  String _getStatusText() {
    if (tv.isConnecting) {
      return 'Conectando...';
    } else if (tv.isOnline) {
      return 'En línea';
    } else {
      return 'Sin conexión';
    }
  }

  void _showOptionsMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Color(AppColors.lightSurface),
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(AppConstants.cardBorderRadius),
            topRight: Radius.circular(AppConstants.cardBorderRadius),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle bar
            Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.symmetric(vertical: 12),
              decoration: BoxDecoration(
                color: const Color(AppColors.lightTextSecondary).withAlpha((0.3 * 255).round()),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            
            // Opciones
            if (onEdit != null)
              ListTile(
                leading: const Icon(Icons.edit, color: Color(AppColors.lightPrimary)),
                title: const Text('Editar'),
                onTap: () {
                  Navigator.pop(context);
                  onEdit!();
                },
              ),
            
            ListTile(
              leading: const Icon(Icons.info, color: Color(AppColors.info)),
              title: const Text('Información'),
              onTap: () {
                Navigator.pop(context);
                _showInfoDialog(context);
              },
            ),
            
            if (onDelete != null)
              ListTile(
                leading: const Icon(Icons.delete, color: Color(AppColors.error)),
                title: const Text('Eliminar'),
                onTap: () {
                  Navigator.pop(context);
                  _showDeleteConfirmation(context);
                },
              ),
            
            const SizedBox(height: AppConstants.defaultPadding),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(tv.name),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildInfoRow('Marca', tv.brand.toString().split('.').last.toUpperCase()),
            _buildInfoRow('IP', tv.ip),
            _buildInfoRow('Puerto', tv.port.toString()),
            _buildInfoRow('Protocolo', tv.protocol.toString().split('.').last),
            _buildInfoRow('Habitación', tv.room),
            if (tv.model.isNotEmpty) _buildInfoRow('Modelo', tv.model),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  void _showDeleteConfirmation(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminar TV'),
        content: Text('¿Estás seguro de que quieres eliminar "${tv.name}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              onDelete?.call();
            },
            style: TextButton.styleFrom(
              foregroundColor: const Color(AppColors.error),
            ),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }
}