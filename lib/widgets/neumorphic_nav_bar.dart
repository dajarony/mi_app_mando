import 'package:flutter/material.dart';
import 'package:mi_app_expriment2/theme/app_theme.dart';

class NeumorphicNavigationBar extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const NeumorphicNavigationBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final backgroundColor = Theme.of(context).scaffoldBackgroundColor;

    return Container(
      decoration: AppTheme.neumorphicDecoration(
        baseColor: backgroundColor,
        backgroundColor: backgroundColor,
        borderRadius: 0, // No border radius for the bar itself
        isConvex: true, // A slight convex effect for the bar
        depth: 8, // Increased depth for more visible shadows
      ),
      padding: const EdgeInsets.symmetric(vertical: 8.0), // Padding for the bar content
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _NeumorphicNavItem(
            icon: Icons.home,
            label: "Inicio",
            index: 0,
            currentIndex: currentIndex,
            onTap: onTap,
          ),
          _NeumorphicNavItem(
            icon: Icons.settings,
            label: "Ajustes",
            index: 1,
            currentIndex: currentIndex,
            onTap: onTap,
          ),
          _NeumorphicNavItem(
            icon: Icons.person,
            label: "Perfil",
            index: 2,
            currentIndex: currentIndex,
            onTap: onTap,
          ),
        ],
      ),
    );
  }
}

class _NeumorphicNavItem extends StatefulWidget {
  final IconData icon;
  final String label;
  final int index;
  final int currentIndex;
  final Function(int) onTap;

  const _NeumorphicNavItem({
    required this.icon,
    required this.label,
    required this.index,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  State<_NeumorphicNavItem> createState() => _NeumorphicNavItemState();
}

class _NeumorphicNavItemState extends State<_NeumorphicNavItem> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 150),
    );
    _animation = Tween<double>(begin: 1.0, end: 0.8).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isSelected = widget.index == widget.currentIndex;
    final TextTheme textTheme = Theme.of(context).textTheme;
    final backgroundColor = Theme.of(context).scaffoldBackgroundColor;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final textColor = Theme.of(context).textTheme.bodyMedium?.color ?? Colors.grey;

    return GestureDetector(
      onTap: () async {
        _controller.forward();
        await Future.delayed(const Duration(milliseconds: 150));
        _controller.reverse();
        widget.onTap(widget.index); // Propagate the tap event
      },
      child: ScaleTransition(
        scale: _animation,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
          decoration: AppTheme.neumorphicDecoration(
            baseColor: backgroundColor,
            backgroundColor: backgroundColor,
            borderRadius: 12, // Rounded corners for individual items
            isConcave: isSelected, // Concave when selected, flat when not
            depth: isSelected ? 5 : 0, // Depth changes on selection
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                widget.icon,
                color: isSelected ? primaryColor : textColor,
                size: 24,
              ),
              const SizedBox(height: 4),
              Text(
                widget.label,
                style: textTheme.bodySmall?.copyWith(
                  color: isSelected ? primaryColor : textColor,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}