import 'package:flutter/material.dart';
import '../core/constants.dart';

enum NotificationType {
  success,
  error, 
  warning,
  info,
  loading
}

class AppNotification {
  static void show(
    BuildContext context, {
    required String message,
    NotificationType type = NotificationType.info,
    Duration duration = const Duration(seconds: 3),
    String? actionLabel,
    VoidCallback? onActionPressed,
  }) {
    Color backgroundColor;
    Color textColor = Colors.white;
    IconData icon;

    switch (type) {
      case NotificationType.success:
        backgroundColor = const Color(AppColors.success);
        icon = Icons.check_circle_outline;
        break;
      case NotificationType.error:
        backgroundColor = const Color(AppColors.error);
        icon = Icons.error_outline;
        break;
      case NotificationType.warning:
        backgroundColor = const Color(AppColors.warning);
        icon = Icons.warning_outlined;
        textColor = Colors.black87;
        break;
      case NotificationType.info:
        backgroundColor = const Color(AppColors.info);
        icon = Icons.info_outline;
        break;
      case NotificationType.loading:
        backgroundColor = Colors.grey.shade700;
        icon = Icons.hourglass_empty;
        break;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(icon, color: textColor, size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                  color: textColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        backgroundColor: backgroundColor,
        duration: duration,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppConstants.buttonBorderRadius),
        ),
        action: actionLabel != null
            ? SnackBarAction(
                label: actionLabel,
                textColor: textColor,
                onPressed: onActionPressed ?? () {},
              )
            : null,
      ),
    );
  }

  // Métodos de conveniencia
  static void showSuccess(BuildContext context, String message) {
    show(context, message: message, type: NotificationType.success);
  }

  static void showError(BuildContext context, String message) {
    show(context, message: message, type: NotificationType.error);
  }

  static void showWarning(BuildContext context, String message) {
    show(context, message: message, type: NotificationType.warning);
  }

  static void showInfo(BuildContext context, String message) {
    show(context, message: message, type: NotificationType.info);
  }

  static void showLoading(BuildContext context, String message) {
    show(
      context, 
      message: message, 
      type: NotificationType.loading,
      duration: const Duration(seconds: 10),
    );
  }
}

// Widget para mostrar estado de carga con indicador
class LoadingOverlay extends StatelessWidget {
  final String message;
  final bool isVisible;

  const LoadingOverlay({
    super.key,
    required this.message,
    required this.isVisible,
  });

  @override
  Widget build(BuildContext context) {
    if (!isVisible) return const SizedBox.shrink();

    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(AppConstants.defaultPadding),
          padding: const EdgeInsets.all(AppConstants.largePadding),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            boxShadow: const [
              BoxShadow(
                color: Colors.black26,
                blurRadius: 10,
                offset: Offset(0, 5),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(
                  Color(AppColors.lightPrimary),
                ),
              ),
              const SizedBox(height: AppConstants.defaultPadding),
              Text(
                message,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Color(AppColors.lightText),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Widget para mostrar estado vacío
class EmptyStateWidget extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String? buttonText;
  final VoidCallback? onButtonPressed;

  const EmptyStateWidget({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.buttonText,
    this.onButtonPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.defaultPadding),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: const Color(AppColors.lightTextSecondary),
            ),
            const SizedBox(height: AppConstants.defaultPadding),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Color(AppColors.lightText),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppConstants.smallPadding),
            Text(
              subtitle,
              style: const TextStyle(
                fontSize: 16,
                color: Color(AppColors.lightTextSecondary),
              ),
              textAlign: TextAlign.center,
            ),
            if (buttonText != null) ...[
              const SizedBox(height: AppConstants.largePadding),
              ElevatedButton.icon(
                onPressed: onButtonPressed,
                icon: const Icon(Icons.refresh),
                label: Text(buttonText!),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(AppColors.lightPrimary),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(
                      AppConstants.buttonBorderRadius,
                    ),
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppConstants.largePadding,
                    vertical: AppConstants.defaultPadding,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}