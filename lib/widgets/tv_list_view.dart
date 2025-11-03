/*
Widget de Lista de TVs - TV List View
Componente reutilizable para mostrar listas de Smart TVs
*/

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/barril_models.dart';
import '../providers/tv_provider.dart';
import '../core/constants.dart';
import 'tv_card.dart';
import 'app_notification.dart';

class TVListView extends StatefulWidget {
  final List<SmartTV>? customTVs;
  final bool showFavoritesOnly;
  final bool showOnlineOnly;
  final String? filterByRoom;
  final Function(SmartTV)? onTVTap;
  final Function(SmartTV)? onTVLongPress;
  final bool shrinkWrap;
  final ScrollPhysics? physics;

  const TVListView({
    Key? key,
    this.customTVs,
    this.showFavoritesOnly = false,
    this.showOnlineOnly = false,
    this.filterByRoom,
    this.onTVTap,
    this.onTVLongPress,
    this.shrinkWrap = false,
    this.physics,
  }) : super(key: key);

  @override
  State<TVListView> createState() => _TVListViewState();
}

class _TVListViewState extends State<TVListView> {
  @override
  Widget build(BuildContext context) {
    return Consumer<TVProvider>(
      builder: (context, tvProvider, child) {
        // Obtener lista de TVs
        List<SmartTV> tvs = widget.customTVs ?? tvProvider.tvs;

        // Aplicar filtros
        if (widget.showFavoritesOnly) {
          tvs = tvs.where((tv) => tv.isFavorite).toList();
        }

        if (widget.showOnlineOnly) {
          tvs = tvs.where((tv) => tv.isOnline).toList();
        }

        if (widget.filterByRoom != null && widget.filterByRoom!.isNotEmpty) {
          tvs = tvs
              .where((tv) => tv.room
                  .toLowerCase()
                  .contains(widget.filterByRoom!.toLowerCase()))
              .toList();
        }

        // Mostrar estado vacío si no hay TVs
        if (tvs.isEmpty) {
          return _buildEmptyState();
        }

        // Construir lista
        return ListView.builder(
          shrinkWrap: widget.shrinkWrap,
          physics: widget.physics,
          padding: const EdgeInsets.symmetric(
            horizontal: AppConstants.defaultPadding,
            vertical: AppConstants.defaultPadding / 2,
          ),
          itemCount: tvs.length,
          itemBuilder: (context, index) {
            final tv = tvs[index];
            final isSelected = tvProvider.selectedTVId == tv.id;

            return Padding(
              padding: const EdgeInsets.only(
                bottom: AppConstants.defaultPadding,
              ),
              child: TVCard(
                tv: tv,
                isSelected: isSelected,
                onTap: () {
                  if (widget.onTVTap != null) {
                    widget.onTVTap!(tv);
                  } else {
                    _handleTVTap(context, tv, tvProvider);
                  }
                },
                onLongPress: () {
                  if (widget.onTVLongPress != null) {
                    widget.onTVLongPress!(tv);
                  } else {
                    _handleTVLongPress(context, tv, tvProvider);
                  }
                },
                onFavoriteToggle: () => _handleFavoriteToggle(tv, tvProvider),
                onDelete: () => _handleDelete(context, tv, tvProvider),
                onEdit: () => _handleEdit(context, tv, tvProvider),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildEmptyState() {
    String title = 'No hay TVs';
    String subtitle = 'Escanea la red o añade una TV manualmente';

    if (widget.showFavoritesOnly) {
      title = 'Sin favoritos';
      subtitle = 'Marca tus TVs favoritas para verlas aquí';
    } else if (widget.showOnlineOnly) {
      title = 'Sin TVs en línea';
      subtitle = 'Ninguna TV está conectada actualmente';
    } else if (widget.filterByRoom != null) {
      title = 'Sin TVs en esta habitación';
      subtitle = 'No se encontraron TVs en "${widget.filterByRoom}"';
    }

    return EmptyStateWidget(
      icon: Icons.tv_off,
      title: title,
      subtitle: subtitle,
    );
  }

  void _handleTVTap(BuildContext context, SmartTV tv, TVProvider provider) {
    provider.selectTV(tv.id);
    AppNotification.showSuccess(
      context,
      'TV seleccionada: ${tv.name}',
    );
  }

  void _handleTVLongPress(
      BuildContext context, SmartTV tv, TVProvider provider) {
    _showTVOptions(context, tv, provider);
  }

  void _handleFavoriteToggle(SmartTV tv, TVProvider provider) {
    provider.toggleFavorite(tv.id);
  }

  Future<void> _handleDelete(
      BuildContext context, SmartTV tv, TVProvider provider) async {
    final confirmed = await _showDeleteConfirmation(context, tv);
    if (confirmed == true) {
      await provider.removeTV(tv.id);
      if (context.mounted) {
        AppNotification.showSuccess(
          context,
          'TV eliminada: ${tv.name}',
        );
      }
    }
  }

  void _handleEdit(BuildContext context, SmartTV tv, TVProvider provider) {
    // TODO: Implementar diálogo de edición
    AppNotification.showInfo(
      context,
      'Edición de TV próximamente',
    );
  }

  void _showTVOptions(BuildContext context, SmartTV tv, TVProvider provider) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: const BoxDecoration(
          color: Color(AppColors.lightSurface),
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(AppConstants.cardBorderRadius),
          ),
        ),
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Título
            Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Text(
              tv.name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),

            // Opciones
            _buildOption(
              icon: tv.isFavorite ? Icons.star : Icons.star_border,
              title: tv.isFavorite
                  ? 'Quitar de favoritos'
                  : 'Añadir a favoritos',
              onTap: () {
                Navigator.pop(context);
                _handleFavoriteToggle(tv, provider);
              },
            ),
            _buildOption(
              icon: Icons.edit,
              title: 'Editar',
              onTap: () {
                Navigator.pop(context);
                _handleEdit(context, tv, provider);
              },
            ),
            _buildOption(
              icon: Icons.info_outline,
              title: 'Ver detalles',
              onTap: () {
                Navigator.pop(context);
                _showTVDetails(context, tv);
              },
            ),
            _buildOption(
              icon: Icons.delete_outline,
              title: 'Eliminar',
              color: Colors.red,
              onTap: () {
                Navigator.pop(context);
                _handleDelete(context, tv, provider);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOption({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    Color? color,
  }) {
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(
        title,
        style: TextStyle(color: color),
      ),
      onTap: onTap,
    );
  }

  void _showTVDetails(BuildContext context, SmartTV tv) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(tv.name),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildDetailRow('Marca', tv.brandDisplayName),
              _buildDetailRow('IP', tv.ip),
              _buildDetailRow('Puerto', tv.port.toString()),
              _buildDetailRow('Habitación', tv.room),
              _buildDetailRow('Protocolo', tv.protocolDisplayName),
              _buildDetailRow('Estado', tv.statusText),
              if (tv.model.isNotEmpty) _buildDetailRow('Modelo', tv.model),
              if (tv.macAddress.isNotEmpty)
                _buildDetailRow('MAC', tv.macAddress),
            ],
          ),
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

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  Future<bool?> _showDeleteConfirmation(BuildContext context, SmartTV tv) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminar TV'),
        content: Text('¿Estás seguro de que quieres eliminar "${tv.name}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }
}
