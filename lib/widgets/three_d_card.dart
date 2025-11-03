import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';

class ThreeDCard extends StatefulWidget {
  final Widget child;
  final double rotationFactor;

  const ThreeDCard({
    super.key,
    required this.child,
    this.rotationFactor = 0.02, // Adjust this for more/less rotation
  });

  @override
  State<ThreeDCard> createState() => _ThreeDCardState();
}

class _ThreeDCardState extends State<ThreeDCard> {
  Offset _mousePosition = Offset.zero;
  double _rotationX = 0;
  double _rotationY = 0;

  void _onPointerHover(PointerHoverEvent event) {
    setState(() {
      _mousePosition = event.localPosition;
      _updateRotation();
    });
  }

  void _onPointerExit(PointerExitEvent event) {
    setState(() {
      _rotationX = 0;
      _rotationY = 0;
    });
  }

  void _updateRotation() {
    final RenderBox box = context.findRenderObject() as RenderBox;
    final Size size = box.size;

    // Calculate rotation based on mouse position relative to the center of the card
    final double centerX = size.width / 2;
    final double centerY = size.height / 2;

    final double normalizedX = (_mousePosition.dx - centerX) / centerX;
    final double normalizedY = (_mousePosition.dy - centerY) / centerY;

    _rotationY = normalizedX * widget.rotationFactor; // Rotate around Y-axis based on X position
    _rotationX = -normalizedY * widget.rotationFactor; // Rotate around X-axis based on Y position
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onHover: _onPointerHover,
      onExit: _onPointerExit,
      child: Transform(
        alignment: FractionalOffset.center,
        transform: Matrix4.identity()
          ..setEntry(3, 2, 0.001) // Perspective
          ..rotateX(_rotationX)
          ..rotateY(_rotationY),
        child: widget.child,
      ),
    );
  }
}
