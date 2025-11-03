import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:mi_app_expriment2/services/philips_tv_direct_service.dart';
import 'package:mi_app_expriment2/providers/tv_provider.dart';

class RemoteControlScreen extends StatefulWidget {
  final String? tvIpAddress;
  final String? tvName;

  const RemoteControlScreen({
    super.key,
    this.tvIpAddress,
    this.tvName,
  });

  @override
  State<RemoteControlScreen> createState() => _RemoteControlScreenState();
}

class _RemoteControlScreenState extends State<RemoteControlScreen> {
  PhilipsTvDirectService? _apiService;
  bool _isInitializing = true;
  String? _initializationError;

  // Color base para el diseño neuromórfico
  final Color _baseColor = const Color(0xFFF8FAFC); // bg-[#f8fafc]

  // Estado para controlar la visibilidad del teclado numérico
  bool _showNumberPad = false;

  @override
  void initState() {
    super.initState();
    _initializeService();
  }

  Future<void> _initializeService() async {
    setState(() {
      _isInitializing = true;
      _initializationError = null;
    });

    try {
      String? ip = widget.tvIpAddress;

      // Si no se proporcionó IP, intentar obtenerla del TVProvider
      if (ip == null || ip.isEmpty) {
        if (!mounted) return;
        final tvProvider = context.read<TVProvider>();
        final selectedTV = tvProvider.selectedTV;

        if (selectedTV != null) {
          ip = selectedTV.ip;
        } else {
          // Como último recurso, intentar cargar desde SharedPreferences
          final service = await PhilipsTvDirectService.createWithSavedIp();
          if (!mounted) return;
          setState(() {
            _apiService = service;
            _isInitializing = false;
          });
          return;
        }
      }

      final service = PhilipsTvDirectService(tvIpAddress: ip);

      if (!mounted) return;
      setState(() {
        _apiService = service;
        _isInitializing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _apiService = null;
        _isInitializing = false;
        _initializationError =
            'No se pudo inicializar el control remoto. Por favor, selecciona una TV desde la pantalla principal.';
      });
    }
  }

  Future<void> _retryInitialization() async {
    if (_isInitializing) return;
    await _initializeService();
  }

  void _sendKey(String key) {
    _apiService?.sendKey(key);
  }

  // Estilos neuromórficos para los botones
  BoxDecoration _neuromorphicDecoration({
    bool isPressed = false,
    double borderRadius = 36.0, // Para botones circulares
    Color? pressedColor, // Color al presionar
  }) {
    return BoxDecoration(
      color: isPressed
          ? (pressedColor ?? Colors.green.shade100)
          : _baseColor, // Tono verde al presionar
      borderRadius: BorderRadius.circular(borderRadius),
      boxShadow: isPressed
          ? [
              // Sombra interior para efecto presionado
              BoxShadow(
                color: Colors.grey.shade400,
                offset: const Offset(2, 2),
                blurRadius: 5,
                spreadRadius: 1,
              ),
              const BoxShadow(
                color: Colors.white,
                offset: Offset(-2, -2),
                blurRadius: 5,
                spreadRadius: 1,
              ),
            ]
          : [
              // Sombra exterior para efecto cóncavo (más pronunciado)
              BoxShadow(
                color: Colors.grey.shade400, // Sombra oscura
                offset: const Offset(6, 6),
                blurRadius: 12,
                spreadRadius: 2,
              ),
              const BoxShadow(
                color: Colors.white, // Sombra clara
                offset: Offset(-6, -6),
                blurRadius: 12,
                spreadRadius: 2,
              ),
            ],
    );
  }

  Widget _buildNeuromorphicButton({
    required Widget child,
    required VoidCallback onPressed,
    double size = 72.0,
    Color? textColor,
    double borderRadius = 36.0,
    Color? pressedColor,
  }) {
    bool isPressed = false;
    return StatefulBuilder(
      builder: (context, setState) {
        return GestureDetector(
          onTapDown: (_) {
            setState(() {
              isPressed = true;
            });
          },
          onTapUp: (_) {
            setState(() {
              isPressed = false;
            });
            onPressed();
          },
          onTapCancel: () {
            setState(() {
              isPressed = false;
            });
          },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 100),
            width: size,
            height: size,
            decoration: _neuromorphicDecoration(
              isPressed: isPressed,
              borderRadius: borderRadius,
              pressedColor: pressedColor,
            ),
            alignment: Alignment.center,
            child: DefaultTextStyle(
              style: TextStyle(
                color: textColor ?? const Color(0xFF64748B), // #64748b
                fontSize: size == 72.0
                    ? 32.0
                    : (size == 44.8 ? 20.0 : 16.0), // wire-btn-lg, md, sm
                fontWeight: FontWeight.normal,
              ),
              child: child,
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final Widget bodyContent;
    if (_isInitializing) {
      bodyContent = _buildLoadingState();
    } else if (_apiService == null) {
      bodyContent = _buildErrorState();
    } else {
      bodyContent = _buildRemoteContent();
    }

    return Scaffold(
      backgroundColor: _baseColor, // bg-[#f8fafc]
      appBar: AppBar(
        backgroundColor: _baseColor, // Color de fondo del AppBar
        elevation: 0, // Sin sombra
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back,
            color: Color(0xFF64748B),
          ), // Color del icono
          onPressed: () {
            Navigator.pop(context); // Vuelve a la pantalla anterior
          },
        ),
        title: Text(
          widget.tvName != null
              ? 'Control: ${widget.tvName}'
              : 'Control Remoto',
          style: const TextStyle(
            color: Color(0xFF64748B), // Color del título
          ),
        ),
        centerTitle: true,
      ),
      body: bodyContent,
    );
  }

  Widget _buildRemoteContent() {
    return SafeArea(
      child: Center(
        child: Container(
          width: 370,
          constraints: const BoxConstraints(minHeight: 670),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24.0), // rounded-3xl
            boxShadow: [
              BoxShadow(
                color: Colors.black.withAlpha(
                  (255 * 0.1).round(),
                ), // shadow-2xl
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          padding: const EdgeInsets.all(32.0), // p-8
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize
                  .min, // Para que el Column no ocupe todo el alto disponible
              children: [
                // Power principal
                Column(
                  children: [
                    _buildNeuromorphicButton(
                      size: 72.0,
                      textColor: const Color(0xFFEF4444),
                      onPressed: () => _sendKey('Standby'),
                      child: const Icon(
                        Icons.power_settings_new,
                        size: 32.0,
                      ), // Icono de power
                      pressedColor:
                          Colors.red.shade100, // Tono rojo al presionar
                    ),
                    const SizedBox(height: 4.0),
                    const Text(
                      'Power',
                      style: TextStyle(
                        fontSize: 16.8,
                        color: Color(0xFF64748B),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24.0),

                // Botón para alternar entre D-pad y teclado numérico
                _buildNeuromorphicButton(
                  size: 44.8,
                  onPressed: () {
                    setState(() {
                      _showNumberPad = !_showNumberPad;
                    });
                  },
                  child: Icon(
                    _showNumberPad ? Icons.gamepad : Icons.dialpad,
                    size: 24,
                  ),
                ),
                const SizedBox(height: 24.0),

                // Mostrar D-pad o teclado numérico según el estado
                _showNumberPad ? _buildNumberPad() : _buildDpad(),

                const SizedBox(height: 24.0),

                // Botones de volumen
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('VolumeDown'),
                          child: const Icon(Icons.volume_down, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Vol-',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('Mute'),
                          child: const Icon(Icons.volume_off, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Mute',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('VolumeUp'),
                          child: const Icon(Icons.volume_up, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Vol+',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),

                const SizedBox(height: 24.0),

                // Botones adicionales
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('Back'),
                          child: const Icon(Icons.arrow_back, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Back',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('Home'),
                          child: const Icon(Icons.home, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Home',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                    Column(
                      children: [
                        _buildNeuromorphicButton(
                          size: 44.8,
                          onPressed: () => _sendKey('Options'),
                          child: const Icon(Icons.menu, size: 24),
                        ),
                        const SizedBox(height: 4.0),
                        const Text(
                          'Menu',
                          style: TextStyle(
                            fontSize: 12.0,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Widget para el D-pad (sin el botón de alternancia)
  Widget _buildLoadingState() {
    return const SafeArea(
      child: Center(
        child: CircularProgressIndicator(),
      ),
    );
  }

  Widget _buildErrorState() {
    final message = _initializationError ??
        'No se pudo cargar la configuración del control remoto.';
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.tv_off,
                size: 48,
                color: Color(0xFFEF4444),
              ),
              const SizedBox(height: 16),
              Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: _retryInitialization,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reintentar'),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.arrow_back),
                    label: const Text('Volver'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Widget para el D-pad (sin el botón central)
  Widget _buildDpad() {
    return Column(
      children: [
        // D-pad
        Column(
          children: [
            _buildNeuromorphicButton(
              size: 44.8,
              onPressed: () => _sendKey('CursorUp'),
              child: const Icon(Icons.keyboard_arrow_up, size: 24),
            ),
            const SizedBox(height: 8.0),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildNeuromorphicButton(
                  size: 44.8,
                  onPressed: () => _sendKey('CursorLeft'),
                  child: const Icon(Icons.keyboard_arrow_left, size: 24),
                ),
                const SizedBox(width: 12), // Espacio entre botones
                _buildNeuromorphicButton(
                  size: 44.8,
                  onPressed: () => _sendKey('Confirm'),
                  child: const Text('OK', style: TextStyle(fontSize: 20)),
                ),
                const SizedBox(width: 12), // Espacio entre botones
                _buildNeuromorphicButton(
                  size: 44.8,
                  onPressed: () => _sendKey('CursorRight'),
                  child: const Icon(Icons.keyboard_arrow_right, size: 24),
                ),
              ],
            ),
            const SizedBox(height: 8.0),
            _buildNeuromorphicButton(
              size: 44.8,
              onPressed: () => _sendKey('CursorDown'),
              child: const Icon(Icons.keyboard_arrow_down, size: 24),
            ),
          ],
        ),
      ],
    );
  }

  // Widget para el teclado numérico (sin el botón de alternancia)
  Widget _buildNumberPad() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0), // px-5
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 12.0, // gap-3
              mainAxisSpacing: 12.0, // gap-3
              childAspectRatio: 1.0, // Para que los botones sean cuadrados
            ),
            itemCount: 12,
            itemBuilder: (context, index) {
              final String buttonText;
              if (index == 9) {
                buttonText = ''; // Espacio vacío
              } else if (index == 10) {
                buttonText = '0';
              } else if (index == 11) {
                buttonText = ''; // Espacio vacío
              } else {
                buttonText = (index + 1).toString();
              }

              if (buttonText.isEmpty) {
                return Container(); // Contenedor vacío para los espacios
              }

              return _buildNeuromorphicButton(
                size: 44.8,
                onPressed: () => _sendKey('Digit$buttonText'),
                child: Text(buttonText),
              );
            },
          ),
        ),
        const SizedBox(height: 24.0),
      ],
    );
  }
}
