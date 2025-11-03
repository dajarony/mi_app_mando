/*
Formulario de Registro de TV - TV Registration Form
Widget para registrar una TV manualmente
*/

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/barril_models.dart';
import '../providers/tv_provider.dart';
import '../services/network_service.dart';
import '../core/constants.dart';
import 'app_notification.dart';
import 'custom_input_field.dart';

class TVRegistrationForm extends StatefulWidget {
  final SmartTV? tvToEdit;
  final VoidCallback? onSuccess;

  const TVRegistrationForm({
    Key? key,
    this.tvToEdit,
    this.onSuccess,
  }) : super(key: key);

  @override
  State<TVRegistrationForm> createState() => _TVRegistrationFormState();
}

class _TVRegistrationFormState extends State<TVRegistrationForm> {
  final _formKey = GlobalKey<FormState>();
  final NetworkService _networkService = NetworkService();

  late TextEditingController _nameController;
  late TextEditingController _ipController;
  late TextEditingController _portController;
  late TextEditingController _roomController;

  TVBrand _selectedBrand = TVBrand.samsung;
  TVProtocol _selectedProtocol = TVProtocol.websocket;
  bool _isValidating = false;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.tvToEdit?.name ?? '');
    _ipController = TextEditingController(text: widget.tvToEdit?.ip ?? '');
    _portController = TextEditingController(
      text: widget.tvToEdit?.port.toString() ?? '8080',
    );
    _roomController = TextEditingController(
      text: widget.tvToEdit?.room ?? 'Sala',
    );

    if (widget.tvToEdit != null) {
      _selectedBrand = widget.tvToEdit!.brand;
      _selectedProtocol = widget.tvToEdit!.protocol;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _ipController.dispose();
    _portController.dispose();
    _roomController.dispose();
    _networkService.dispose();
    super.dispose();
  }

  Future<void> _validateAndSave() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isValidating = true);

    try {
      // Validar conexión
      final ip = _ipController.text.trim();
      final port = int.parse(_portController.text.trim());

      final isReachable = await _networkService.validateTVConnection(ip, port);

      if (!isReachable) {
        if (mounted) {
          final shouldContinue = await _showConnectionWarning();
          if (shouldContinue != true) {
            setState(() => _isValidating = false);
            return;
          }
        }
      }

      // Crear o actualizar TV
      final tv = SmartTV(
        id: widget.tvToEdit?.id,
        name: _nameController.text.trim(),
        brand: _selectedBrand,
        ip: ip,
        port: port,
        room: _roomController.text.trim(),
        protocol: _selectedProtocol,
        isOnline: isReachable,
        isRegistered: true,
      );

      if (!mounted) return;
      final tvProvider = Provider.of<TVProvider>(context, listen: false);

      if (widget.tvToEdit != null) {
        await tvProvider.updateTV(tv);
      } else {
        await tvProvider.addTV(tv);
      }

      if (mounted) {
        AppNotification.showSuccess(
          context,
          widget.tvToEdit != null
              ? 'TV actualizada correctamente'
              : 'TV añadida correctamente',
        );
        widget.onSuccess?.call();
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        AppNotification.showError(
          context,
          'Error al guardar: $e',
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isValidating = false);
      }
    }
  }

  Future<bool?> _showConnectionWarning() {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Advertencia'),
        content: const Text(
          'No se pudo conectar con la TV. '
          '¿Deseas guardarla de todos modos?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppConstants.defaultPadding),
      decoration: BoxDecoration(
        color: const Color(AppColors.lightSurface),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        boxShadow: [
          BoxShadow(
            color: const Color(AppColors.darkShadow).withAlpha((0.2 * 255).round()),
            offset: const Offset(4, 4),
            blurRadius: 10,
          ),
          const BoxShadow(
            color: Color(AppColors.lightShadow),
            offset: Offset(-4, -4),
            blurRadius: 10,
          ),
        ],
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Título
              Row(
                children: [
                  Icon(
                    widget.tvToEdit != null ? Icons.edit : Icons.add_box,
                    color: const Color(AppColors.lightPrimary),
                    size: 32,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    widget.tvToEdit != null
                        ? 'Editar TV'
                        : 'Registrar TV Manualmente',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // Nombre
              CustomInputField(
                controller: _nameController,
                labelText: 'Nombre de la TV',
                hintText: 'Ej: TV Sala',
                prefixIcon: Icons.tv,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor ingresa un nombre';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // Marca
              _buildBrandSelector(),

              const SizedBox(height: 16),

              // IP
              CustomInputField(
                controller: _ipController,
                labelText: 'Dirección IP',
                hintText: '192.168.1.100',
                prefixIcon: Icons.network_wifi,
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor ingresa una IP';
                  }
                  final parts = value.split('.');
                  if (parts.length != 4) {
                    return 'IP inválida';
                  }
                  for (final part in parts) {
                    final num = int.tryParse(part);
                    if (num == null || num < 0 || num > 255) {
                      return 'IP inválida';
                    }
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // Puerto
              CustomInputField(
                controller: _portController,
                labelText: 'Puerto',
                hintText: '8080',
                prefixIcon: Icons.settings_ethernet,
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Por favor ingresa un puerto';
                  }
                  final port = int.tryParse(value);
                  if (port == null || port < 1 || port > 65535) {
                    return 'Puerto inválido';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 16),

              // Habitación
              CustomInputField(
                controller: _roomController,
                labelText: 'Habitación',
                hintText: 'Sala',
                prefixIcon: Icons.room,
              ),

              const SizedBox(height: 16),

              // Protocolo
              _buildProtocolSelector(),

              const SizedBox(height: 24),

              // Botones
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _isValidating
                          ? null
                          : () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        side: const BorderSide(
                          color: Color(AppColors.lightPrimary),
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(
                            AppConstants.buttonBorderRadius,
                          ),
                        ),
                      ),
                      child: const Text('Cancelar'),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isValidating ? null : _validateAndSave,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(AppColors.lightPrimary),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(
                            AppConstants.buttonBorderRadius,
                          ),
                        ),
                      ),
                      child: _isValidating
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : Text(widget.tvToEdit != null
                              ? 'Actualizar'
                              : 'Guardar'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBrandSelector() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(AppColors.lightBackground),
        borderRadius: BorderRadius.circular(AppConstants.inputBorderRadius),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: DropdownButtonFormField<TVBrand>(
        value: _selectedBrand,
        decoration: const InputDecoration(
          labelText: 'Marca',
          border: InputBorder.none,
          prefixIcon: Icon(Icons.business),
        ),
        items: TVBrand.values.map((brand) {
          return DropdownMenuItem(
            value: brand,
            child: Text(_getBrandDisplayName(brand)),
          );
        }).toList(),
        onChanged: (value) {
          if (value != null) {
            setState(() {
              _selectedBrand = value;
              _selectedProtocol = _getDefaultProtocolForBrand(value);
            });
          }
        },
      ),
    );
  }

  Widget _buildProtocolSelector() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(AppColors.lightBackground),
        borderRadius: BorderRadius.circular(AppConstants.inputBorderRadius),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: DropdownButtonFormField<TVProtocol>(
        value: _selectedProtocol,
        decoration: const InputDecoration(
          labelText: 'Protocolo',
          border: InputBorder.none,
          prefixIcon: Icon(Icons.cable),
        ),
        items: TVProtocol.values.map((protocol) {
          return DropdownMenuItem(
            value: protocol,
            child: Text(_getProtocolDisplayName(protocol)),
          );
        }).toList(),
        onChanged: (value) {
          if (value != null) {
            setState(() => _selectedProtocol = value);
          }
        },
      ),
    );
  }

  String _getBrandDisplayName(TVBrand brand) {
    switch (brand) {
      case TVBrand.samsung:
        return 'Samsung';
      case TVBrand.lg:
        return 'LG';
      case TVBrand.sony:
        return 'Sony';
      case TVBrand.philips:
        return 'Philips';
      case TVBrand.tcl:
        return 'TCL';
      case TVBrand.hisense:
        return 'Hisense';
      case TVBrand.xiaomi:
        return 'Xiaomi';
      case TVBrand.roku:
        return 'Roku';
      case TVBrand.androidtv:
        return 'Android TV';
      default:
        return 'Desconocida';
    }
  }

  String _getProtocolDisplayName(TVProtocol protocol) {
    switch (protocol) {
      case TVProtocol.http:
        return 'HTTP';
      case TVProtocol.websocket:
        return 'WebSocket';
      case TVProtocol.upnp:
        return 'UPnP';
      case TVProtocol.roku:
        return 'Roku Protocol';
      default:
        return 'Desconocido';
    }
  }

  TVProtocol _getDefaultProtocolForBrand(TVBrand brand) {
    switch (brand) {
      case TVBrand.samsung:
      case TVBrand.lg:
        return TVProtocol.websocket;
      case TVBrand.roku:
        return TVProtocol.roku;
      default:
        return TVProtocol.http;
    }
  }
}
