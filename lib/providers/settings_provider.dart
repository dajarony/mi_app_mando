import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/constants.dart';

class SettingsProvider extends ChangeNotifier {
  final _logger = Logger();
  bool _isLoading = false;
  String _philipsTvIp = AppConstants.defaultSubnet;
  String _subnet = AppConstants.defaultSubnet;
  int _scanIpStart = AppConstants.scanRangeStart;
  int _scanIpEnd = AppConstants.scanRangeEnd;

  bool get isLoading => _isLoading;
  String get philipsTvIp => _philipsTvIp;
  String get subnet => _subnet;
  int get scanIpStart => _scanIpStart;
  int get scanIpEnd => _scanIpEnd;

  static const String _keyPhilipsTvIp = 'philips_tv_ip';
  static const String _keySubnet = 'scan_subnet';
  static const String _keyScanIpStart = 'scan_ip_start';
  static const String _keyScanIpEnd = 'scan_ip_end';

  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      _philipsTvIp = prefs.getString(_keyPhilipsTvIp) ?? AppConstants.defaultSubnet;
      _subnet = prefs.getString(_keySubnet) ?? AppConstants.defaultSubnet;
      _scanIpStart =
          prefs.getInt(_keyScanIpStart) ?? AppConstants.scanRangeStart;
      _scanIpEnd = prefs.getInt(_keyScanIpEnd) ?? AppConstants.scanRangeEnd;
    } catch (e, s) {
      _logger.e('Error loading settings', error: e, stackTrace: s);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> savePhilipsTvIp(String ip) async {
    if (ip.trim().isEmpty) {
      return false;
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_keyPhilipsTvIp, ip.trim());
      _philipsTvIp = ip.trim();
      notifyListeners();
      return true;
    } catch (e, s) {
      _logger.e('Error saving Philips TV IP', error: e, stackTrace: s);
      return false;
    }
  }

  Future<bool> saveNetworkScanSettings({
    required String subnet,
    required int startIp,
    required int endIp,
  }) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_keySubnet, subnet);
      await prefs.setInt(_keyScanIpStart, startIp);
      await prefs.setInt(_keyScanIpEnd, endIp);

      _subnet = subnet;
      _scanIpStart = startIp;
      _scanIpEnd = endIp;

      notifyListeners();
      return true;
    } catch (e, s) {
      _logger.e('Error saving network scan settings', error: e, stackTrace: s);
      return false;
    }
  }
}
