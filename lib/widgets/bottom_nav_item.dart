import 'package:flutter/material.dart';

class BottomNavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final String routeName;

  const BottomNavItem({
    super.key,
    required this.icon,
    required this.label,
    this.isSelected = false,
    required this.routeName,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: () {
          if (!isSelected) {
            Navigator.pushReplacementNamed(context, routeName);
          }
        },
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? const Color(0xFF101518) : const Color(0xFF5C778A), // text-[#101518] o text-[#5c778a]
              size: 24,
            ),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? const Color(0xFF101518) : const Color(0xFF5C778A), // text-[#101518] o text-[#5c778a]
                fontSize: 12, // Ajuste para que quepa bien
              ),
            ),
          ],
        ),
      ),
    );
  }
}
