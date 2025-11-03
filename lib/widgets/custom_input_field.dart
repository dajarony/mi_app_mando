import 'package:flutter/material.dart';

class CustomInputField extends StatelessWidget {
  final String? hintText;
  final String? labelText;
  final String? helperText;
  final IconData? icon;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final TextInputType? keyboardType;
  final bool obscureText;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final void Function(String)? onChanged;

  // Campos opcionales para compatibilidad con la API anterior
  final String? formProperty;
  final Map<String, String>? formValues;

  const CustomInputField({
    super.key,
    this.hintText,
    this.labelText,
    this.helperText,
    this.icon,
    this.prefixIcon,
    this.suffixIcon,
    this.keyboardType,
    this.obscureText = false,
    this.controller,
    this.validator,
    this.onChanged,
    this.formProperty,
    this.formValues,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      autofocus: false,
      initialValue: controller == null ? '' : null,
      textCapitalization: TextCapitalization.words,
      keyboardType: keyboardType,
      obscureText: obscureText,
      onChanged: onChanged ?? (formProperty != null && formValues != null
          ? (value) => formValues![formProperty!] = value
          : null),
      validator: validator ?? (value) {
        if (value == null || value.isEmpty) return 'Este campo es requerido';
        return value.length < 3 ? 'Mínimo de 3 letras' : null;
      },
      autovalidateMode: AutovalidateMode.onUserInteraction,
      decoration: InputDecoration(
        hintText: hintText,
        labelText: labelText,
        helperText: helperText,
        prefixIcon: prefixIcon != null ? Icon(prefixIcon) : null,
        suffixIcon: suffixIcon != null ? Icon(suffixIcon) : null,
        icon: icon != null ? Icon(icon) : null,
      ),
    );
  }
}
