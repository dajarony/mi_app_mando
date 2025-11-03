/*
Vista de Historial de Comandos - Command History View
Muestra el historial de comandos enviados a las TVs
*/

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/command_history_service.dart';
import '../core/constants.dart';

class CommandHistoryView extends StatefulWidget {
  final CommandHistoryService historyService;
  final String? filterByTVId;

  const CommandHistoryView({
    Key? key,
    required this.historyService,
    this.filterByTVId,
  }) : super(key: key);

  @override
  State<CommandHistoryView> createState() => _CommandHistoryViewState();
}

class _CommandHistoryViewState extends State<CommandHistoryView> {
  List<CommandHistoryEntry> _history = [];
  bool _showOnlyFailed = false;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  void _loadHistory() {
    setState(() {
      if (widget.filterByTVId != null) {
        _history = widget.historyService.getHistoryForTV(widget.filterByTVId!);
      } else {
        _history = widget.historyService.getHistory();
      }
      _applyFilters();
    });
  }

  void _applyFilters() {
    var filtered = widget.filterByTVId != null
        ? widget.historyService.getHistoryForTV(widget.filterByTVId!)
        : widget.historyService.getHistory();

    if (_showOnlyFailed) {
      filtered = filtered.where((e) => !e.wasSuccessful).toList();
    }

    if (_searchQuery.isNotEmpty) {
      final query = _searchQuery.toLowerCase();
      filtered = filtered.where((e) {
        return e.tvName.toLowerCase().contains(query) ||
            e.command.toLowerCase().contains(query);
      }).toList();
    }

    setState(() {
      _history = filtered;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Barra de búsqueda y filtros
        _buildSearchAndFilters(),

        const SizedBox(height: 16),

        // Lista de historial
        Expanded(
          child: _history.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  itemCount: _history.length,
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppConstants.defaultPadding,
                  ),
                  itemBuilder: (context, index) {
                    final entry = _history[index];
                    return _buildHistoryItem(entry);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildSearchAndFilters() {
    return Container(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.1 * 255).round()),
            offset: const Offset(0, 2),
            blurRadius: 4,
          ),
        ],
      ),
      child: Column(
        children: [
          // Buscador
          TextField(
            decoration: InputDecoration(
              hintText: 'Buscar en historial...',
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(
                  AppConstants.inputBorderRadius,
                ),
              ),
              filled: true,
              fillColor: const Color(AppColors.lightBackground),
            ),
            onChanged: (value) {
              setState(() {
                _searchQuery = value;
              });
              _applyFilters();
            },
          ),

          const SizedBox(height: 12),

          // Filtros
          Row(
            children: [
              Expanded(
                child: CheckboxListTile(
                  title: const Text(
                    'Solo errores',
                    style: TextStyle(fontSize: 14),
                  ),
                  value: _showOnlyFailed,
                  onChanged: (value) {
                    setState(() {
                      _showOnlyFailed = value ?? false;
                    });
                    _applyFilters();
                  },
                  controlAffinity: ListTileControlAffinity.leading,
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              TextButton.icon(
                onPressed: () => _showStatistics(),
                icon: const Icon(Icons.bar_chart),
                label: const Text('Estadísticas'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(CommandHistoryEntry entry) {
    final dateFormat = DateFormat('dd/MM/yyyy HH:mm:ss');

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.1 * 255).round()),
            offset: const Offset(2, 2),
            blurRadius: 4,
          ),
          const BoxShadow(
            color: Color(AppColors.lightShadow),
            offset: Offset(-2, -2),
            blurRadius: 4,
          ),
        ],
      ),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: entry.wasSuccessful
              ? const Color(AppColors.lightSuccess).withAlpha((0.2 * 255).round())
              : const Color(AppColors.lightError).withAlpha((0.2 * 255).round()),
          child: Icon(
            entry.wasSuccessful ? Icons.check : Icons.error_outline,
            color: entry.wasSuccessful
                ? const Color(AppColors.lightSuccess)
                : const Color(AppColors.lightError),
          ),
        ),
        title: Text(
          entry.command,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              entry.tvName,
              style: TextStyle(color: Colors.grey[600]),
            ),
            Text(
              dateFormat.format(entry.timestamp),
              style: TextStyle(fontSize: 12, color: Colors.grey[500]),
            ),
            if (!entry.wasSuccessful && entry.errorMessage != null)
              Text(
                'Error: ${entry.errorMessage}',
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(AppColors.lightError),
                ),
              ),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline),
          onPressed: () => _deleteEntry(entry),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.history,
            size: 64,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            _searchQuery.isNotEmpty
                ? 'No se encontraron resultados'
                : 'Sin historial de comandos',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _searchQuery.isNotEmpty
                ? 'Intenta con otros términos de búsqueda'
                : 'Los comandos enviados aparecerán aquí',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteEntry(CommandHistoryEntry entry) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Eliminar entrada'),
        content: const Text(
          '¿Estás seguro de que quieres eliminar esta entrada del historial?',
        ),
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

    if (confirmed == true) {
      await widget.historyService.removeEntry(entry.id);
      _loadHistory();
    }
  }

  void _showStatistics() {
    final stats = widget.historyService.getStatistics();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Estadísticas de Uso'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildStatRow('Total de comandos', stats['totalCommands']),
              _buildStatRow('Exitosos', stats['successfulCommands']),
              _buildStatRow('Fallidos', stats['failedCommands']),
              _buildStatRow('Tasa de éxito', '${stats['successRate']}%'),
              _buildStatRow('Comandos hoy', stats['todayCommands']),
              const SizedBox(height: 16),
              const Text(
                'Comandos más usados:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              ...((stats['mostUsedCommands'] as List).map((cmd) {
                return Padding(
                  padding: const EdgeInsets.only(left: 16, top: 4),
                  child: Text('${cmd['command']}: ${cmd['count']} veces'),
                );
              })),
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

  Widget _buildStatRow(String label, dynamic value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value.toString(),
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
