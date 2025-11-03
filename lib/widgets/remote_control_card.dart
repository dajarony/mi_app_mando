import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class RemoteControlCard extends StatelessWidget {
  final Function(String) onCommand;

  const RemoteControlCard({super.key, required this.onCommand});

  @override
  Widget build(BuildContext context) {
    final backgroundColor = Theme.of(context).scaffoldBackgroundColor;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final errorColor = Theme.of(context).colorScheme.error;
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
                  Icons.control_camera,
                  color: primaryColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                'Control Remoto',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildRemoteButton(context, 'Encender', Icons.power_settings_new,
                  'power', errorColor),
              _buildRemoteButton(
                  context, 'Silenciar', Icons.volume_off, 'mute', primaryColor),
              _buildRemoteButton(context, 'Inicio', Icons.home, 'home',
                  AppTheme.accentGreen),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildRemoteButton(context, 'Vol -', Icons.volume_down,
                  'volume_down', textSecondary),
              _buildRemoteButton(
                  context, 'Vol +', Icons.volume_up, 'volume_up', textSecondary),
            ],
          ),
          const SizedBox(height: 16),
          Column(
            children: [
              _buildRemoteButton(
                  context, 'Arriba', Icons.keyboard_arrow_up, 'up', textSecondary),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildRemoteButton(context, '◄', Icons.keyboard_arrow_left,
                      'left', textSecondary),
                  _buildRemoteButton(
                      context, 'OK', Icons.radio_button_checked, 'enter', primaryColor),
                  _buildRemoteButton(context, '►', Icons.keyboard_arrow_right,
                      'right', textSecondary),
                ],
              ),
              const SizedBox(height: 8),
              _buildRemoteButton(context, 'Abajo', Icons.keyboard_arrow_down,
                  'down', textSecondary),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildRemoteButton(context, 'Canal -', Icons.remove,
                  'channel_down', textSecondary),
              _buildRemoteButton(
                  context, 'Canal +', Icons.add, 'channel_up', textSecondary),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildRemoteButton(
                  context, 'Atrás', Icons.arrow_back, 'back', textSecondary),
              _buildRemoteButton(
                  context, 'Menú', Icons.menu, 'menu', textSecondary),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRemoteButton(BuildContext context, String label, IconData icon,
      String command, Color color) {
    final backgroundColor = Theme.of(context).scaffoldBackgroundColor;

    return Expanded(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        decoration: AppTheme.convexDecoration(
          backgroundColor: backgroundColor,
          borderRadius: 12,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => onCommand(command),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 24, color: color),
                  const SizedBox(height: 4),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 10,
                      color: color,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
