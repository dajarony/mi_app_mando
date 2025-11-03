import 'package:flutter/material.dart';

import '../models/barril_models.dart';
import '../theme/app_theme.dart';

class TVRegistrationCard extends StatefulWidget {
  final bool isRegistering;
  final Future<void> Function(SmartTV) onRegister;

  const TVRegistrationCard({
    super.key,
    required this.isRegistering,
    required this.onRegister,
  });

  @override
  State<TVRegistrationCard> createState() => _TVRegistrationCardState();
}

class _TVRegistrationCardState extends State<TVRegistrationCard> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _ipController = TextEditingController();
  final _portController = TextEditingController(text: '1925');

  TVBrand _selectedBrand = TVBrand.philips;
  String _selectedRoom = 'Sala de Estar';

  @override
  void dispose() {
    _nameController.dispose();
    _ipController.dispose();
    _portController.dispose();
    super.dispose();
  }

  void _clearForm() {
    _nameController.clear();
    _ipController.clear();
    _portController.text = '1925';
    setState(() {
      _selectedBrand = TVBrand.philips;
      _selectedRoom = 'Sala de Estar';
    });
  }

  void _updatePortForBrand(TVBrand brand) {
    switch (brand) {
      case TVBrand.samsung:
        _portController.text = '8001';
        break;
      case TVBrand.lg:
        _portController.text = '3000';
        break;
      case TVBrand.sony:
        _portController.text = '80';
        break;
      case TVBrand.philips:
        _portController.text = '1925';
        break;
      case TVBrand.roku:
        _portController.text = '8060';
        break;
      default:
        _portController.text = '8080';
    }
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    final newTV = SmartTV(
      name: _nameController.text.trim(),
      brand: _selectedBrand,
      ip: _ipController.text.trim(),
      port: int.tryParse(_portController.text) ?? 8080,
      room: _selectedRoom,
      protocol: _getProtocolForBrand(_selectedBrand),
    );

    await widget.onRegister(newTV);

    if (mounted) {
      _clearForm();
    }
  }

  TVProtocol _getProtocolForBrand(TVBrand brand) {
    switch (brand) {
      case TVBrand.samsung:
      case TVBrand.lg:
        return TVProtocol.websocket;
      case TVBrand.sony:
        return TVProtocol.http;
      case TVBrand.roku:
        return TVProtocol.roku;
      default:
        return TVProtocol.http;
    }
  }

  String? _validateIP(String? value) {
    if (value == null || value.isEmpty) {
      return 'La IP es requerida';
    }
    final ipRegex = RegExp(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$');
    if (!ipRegex.hasMatch(value)) {
      return 'Formato de IP inválido';
    }
    return null;
  }

  String? _validatePort(String? value) {
    if (value == null || value.isEmpty) {
      return 'El puerto es requerido';
    }
    final port = int.tryParse(value);
    if (port == null || port < 1 || port > 65535) {
      return 'Puerto inválido (1-65535)';
    }
    return null;
  }

  String? _validateName(String? value) {
    if (value == null || value.isEmpty) {
      return 'El nombre es requerido';
    }
    if (value.length < 3) {
      return 'Mínimo 3 caracteres';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final backgroundColor = Theme.of(context).scaffoldBackgroundColor;
    final textPrimary =
        Theme.of(context).textTheme.bodyLarge?.color ?? Colors.black;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.concaveDecoration(
        backgroundColor: backgroundColor,
        borderRadius: 20,
      ),
      child: Form(
        key: _formKey,
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
                  child: const Icon(
                    Icons.add_circle_outline,
                    color: AppTheme.accentGreen,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  'Registrar TV Manualmente',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Container(
              decoration: AppTheme.concaveDecoration(
                backgroundColor: backgroundColor,
                borderRadius: 12,
              ),
              child: TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Nombre de la TV',
                  hintText: 'Mi TV Philips',
                  helperText: 'Dale un nombre fácil de recordar',
                  prefixIcon: Icon(Icons.tv),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
                validator: _validateName,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Container(
                    decoration: AppTheme.concaveDecoration(
                      backgroundColor: backgroundColor,
                      borderRadius: 12,
                    ),
                    child: TextFormField(
                      controller: _ipController,
                      decoration: const InputDecoration(
                        labelText: 'Dirección IP',
                        hintText: '192.168.1.100',
                        helperText: 'Busca la IP en configuración de red de tu TV',
                        prefixIcon: Icon(Icons.router),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.all(16),
                      ),
                      keyboardType: TextInputType.number,
                      validator: _validateIP,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Container(
                    decoration: AppTheme.concaveDecoration(
                      backgroundColor: backgroundColor,
                      borderRadius: 12,
                    ),
                    child: TextFormField(
                      controller: _portController,
                      decoration: const InputDecoration(
                        labelText: 'Puerto',
                        hintText: '8080',
                        prefixIcon: Icon(Icons.settings_ethernet),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.all(16),
                      ),
                      keyboardType: TextInputType.number,
                      validator: _validatePort,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: AppTheme.concaveDecoration(
                      backgroundColor: backgroundColor,
                      borderRadius: 12,
                    ),
                    child: DropdownButtonFormField<TVBrand>(
                      value: _selectedBrand,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Marca',
                        prefixIcon: Icon(Icons.tv),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(
                            horizontal: 12, vertical: 16),
                      ),
                      items: TVBrand.values
                          .where((brand) => brand != TVBrand.unknown)
                          .map((brand) {
                        return DropdownMenuItem(
                          value: brand,
                          child: Text(brand.name.toUpperCase()),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() {
                          _selectedBrand = value!;
                          _updatePortForBrand(value);
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Container(
                    decoration: AppTheme.concaveDecoration(
                      backgroundColor: backgroundColor,
                      borderRadius: 12,
                    ),
                    child: DropdownButtonFormField<String>(
                      value: _selectedRoom,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Habitación',
                        prefixIcon: Icon(Icons.location_on),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(
                            horizontal: 12, vertical: 16),
                      ),
                      items: const [
                        'Sala de Estar',
                        'Dormitorio Principal',
                        'Dormitorio Secundario',
                        'Cocina',
                        'Comedor',
                        'Estudio',
                      ].map((room) {
                        return DropdownMenuItem(
                          value: room,
                          child: Text(room),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() => _selectedRoom = value!);
                      },
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: Container(
                decoration: AppTheme.convexDecoration(
                  backgroundColor: AppTheme.accentGreen,
                  borderRadius: 12,
                ),
                child: ElevatedButton.icon(
                  onPressed: widget.isRegistering ? null : _handleRegister,
                  icon: widget.isRegistering
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.add, color: Colors.white),
                  label: Text(
                    widget.isRegistering ? 'Registrando...' : 'Registrar TV',
                    style: const TextStyle(color: Colors.white),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentGreen,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
