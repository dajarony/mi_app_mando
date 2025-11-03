

class PowerInfo {
  final bool success;
  final String powerstate;
  final String message;

  PowerInfo({
    required this.success,
    required this.powerstate,
    required this.message,
  });

  factory PowerInfo.fromJson(Map<String, dynamic> json) {
    return PowerInfo(
      success: json['success'] as bool,
      powerstate: json['powerstate'] as String,
      message: json['message'] as String,
    );
  }
}

class VolumeDetails {
  final int min;
  final int max;
  final int current;
  final bool muted;

  VolumeDetails({
    required this.min,
    required this.max,
    required this.current,
    required this.muted,
  });

  factory VolumeDetails.fromJson(Map<String, dynamic> json) {
    return VolumeDetails(
      min: json['min'] as int,
      max: json['max'] as int,
      current: json['current'] as int,
      muted: json['muted'] as bool,
    );
  }
}

class VolumeInfo {
  final bool success;
  final VolumeDetails volume;
  final String message;

  VolumeInfo({
    required this.success,
    required this.volume,
    required this.message,
  });

  factory VolumeInfo.fromJson(Map<String, dynamic> json) {
    return VolumeInfo(
      success: json['success'] as bool,
      volume: VolumeDetails.fromJson(json['volume'] as Map<String, dynamic>),
      message: json['message'] as String,
    );
  }
}

class TVStatusResponse {
  final String tvIp;
  final PowerInfo power;
  final VolumeInfo volume;
  final DateTime timestamp;

  TVStatusResponse({
    required this.tvIp,
    required this.power,
    required this.volume,
    required this.timestamp,
  });

  factory TVStatusResponse.fromJson(Map<String, dynamic> json) {
    return TVStatusResponse(
      tvIp: json['tv_ip'] as String,
      power: PowerInfo.fromJson(json['power'] as Map<String, dynamic>),
      volume: VolumeInfo.fromJson(json['volume'] as Map<String, dynamic>),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}