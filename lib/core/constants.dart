// ==========================================
// CONSTANTES DE LA APLICACIÓN
// ==========================================

class AppConstants {
  // Información de la aplicación
  static const String appName = 'Smart TV Manager';
  static const String version = '1.0.0';
  
  // Configuración de red
  static const int defaultScanTimeout = 3000; // milisegundos
  static const int maxScanRetries = 2;
  static const String defaultSubnet = '192.168.1';
  static const int scanRangeStart = 1;
  static const int scanRangeEnd = 50;
  
  // Puertos por marca de TV
  static const Map<String, List<int>> tvPorts = {
    'samsung': [8001, 8080],
    'lg': [3000, 3001],
    'sony': [80, 8080],
    'philips': [1925],
    'roku': [8060],
    'androidtv': [8080, 9080],
    'tcl': [7345],
    'hisense': [36895],
    'xiaomi': [6095],
  };
  
  // Endpoints por marca
  static const Map<String, String> tvEndpoints = {
    'samsung': '/api/v2/channels/samsung.remote.control',
    'lg': '/api/v2/channels/lg.remote.control', 
    'sony': '/sony/IRCC',
    'philips': '/6/input/key',
    'roku': '/keypress',
    'androidtv': '/remote/input',
  };
  
  // Configuración de almacenamiento local
  static const String keyTvList = 'saved_tvs';
  static const String keySelectedTv = 'selected_tv_id';
  static const String keyPhilipsTvIp = 'philips_tv_ip';
  static const String keyUserPreferences = 'user_preferences';
  
  // Configuración de UI
  static const double cardBorderRadius = 12.0;
  static const double buttonBorderRadius = 8.0;
  static const double inputBorderRadius = 8.0;
  static const double defaultPadding = 16.0;
  static const double smallPadding = 8.0;
  static const double largePadding = 24.0;
  
  // Animaciones
  static const int animationDurationMs = 300;
  static const int longAnimationDurationMs = 600;
  static const int quickAnimationDurationMs = 150;
}

class TVCommands {
  // Comandos universales
  static const String power = 'power';
  static const String volumeUp = 'volume_up';
  static const String volumeDown = 'volume_down';
  static const String mute = 'mute';
  static const String channelUp = 'channel_up';
  static const String channelDown = 'channel_down';
  static const String home = 'home';
  static const String back = 'back';
  static const String up = 'up';
  static const String down = 'down';
  static const String left = 'left';
  static const String right = 'right';
  static const String enter = 'enter';
  static const String menu = 'menu';
  static const String netflix = 'netflix';
  static const String youtube = 'youtube';
  static const String amazon = 'amazon';
  
  // Comandos específicos de Philips
  static const Map<String, String> philipsCommands = {
    power: 'Standby',
    volumeUp: 'VolumeUp',
    volumeDown: 'VolumeDown',
    mute: 'Mute',
    channelUp: 'ChannelStepUp',
    channelDown: 'ChannelStepDown',
    home: 'Home',
    back: 'Back',
    up: 'CursorUp',
    down: 'CursorDown',
    left: 'CursorLeft',
    right: 'CursorRight',
    enter: 'Confirm',
    menu: 'Options',
  };
  
  // Números para control remoto
  static const List<String> numbers = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
  ];
}

class AppColors {
  // Tema neumórfico claro
  static const lightBackground = 0xFFE8E8E8;
  static const lightSurface = 0xFFF5F5F5;
  static const lightPrimary = 0xFF4299E1;
  static const lightText = 0xFF2D3748;
  static const lightTextSecondary = 0xFF4A5568;
  
  // Sombras neumórficas
  static const lightShadowDark = 0xFFBEBEBE;
  static const lightShadowLight = 0xFFFFFFFF;
  static const darkShadow = 0xFFBEBEBE;
  static const lightShadow = 0xFFFFFFFF;

  // Colores de estado
  static const success = 0xFF48BB78;
  static const error = 0xFFE53E3E;
  static const warning = 0xFFED8936;
  static const info = 0xFF3182CE;

  // Alias para widgets
  static const lightSuccess = success;
  static const lightError = error;
  static const lightWarning = warning;
  static const lightInfo = info;
  
  // Colores de marca de TV
  static const samsung = 0xFF1F4788;
  static const lg = 0xFFA50034;
  static const sony = 0xFF000000;
  static const philips = 0xFF0077BE;
  static const roku = 0xFF662D91;
}

class AppStrings {
  // Textos de la aplicación
  static const String scanningNetworkTitle = 'Escaneando Red';
  static const String scanningNetworkSubtitle = 'Buscando Smart TVs...';
  static const String noTvsFoundTitle = 'No se encontraron TVs';
  static const String noTvsFoundSubtitle = 'Verifica tu conexión WiFi';
  static const String connectionErrorTitle = 'Error de Conexión';
  static const String connectionErrorSubtitle = 'No se pudo conectar con la TV';
  static const String tvRegisteredTitle = 'TV Registrada';
  static const String tvRegisteredSubtitle = 'TV añadida exitosamente';
  
  // Formularios
  static const String tvNameLabel = 'Nombre de la TV';
  static const String tvNameHint = 'Ej: TV Sala';
  static const String tvIpLabel = 'Dirección IP';
  static const String tvIpHint = '192.168.1.100';
  static const String tvRoomLabel = 'Habitación';
  static const String tvRoomHint = 'Ej: Sala';
  static const String registerButton = 'Registrar TV';
  static const String scanButton = 'Escanear Red';
  static const String saveButton = 'Guardar';
  static const String cancelButton = 'Cancelar';
  
  // Navegación
  static const String homeTab = 'Inicio';
  static const String remoteTab = 'Control';
  static const String settingsTab = 'Configuración';
}