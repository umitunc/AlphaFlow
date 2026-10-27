import 'dart:convert';
import 'dart:io';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppI18n {
  final String langCode;
  final Map<String, String> strings;

  const AppI18n({
    required this.langCode,
    required this.strings,
  });

  /// İşletim sistemi dilini kontrol eder: Türkçe ise 'tr', değilse 'en' döner.
  static String detectSystemLangCode() {
    try {
      final dispatcherLang =
          PlatformDispatcher.instance.locale.languageCode.toLowerCase();
      if (dispatcherLang == 'tr') return 'tr';
      final osLocale = Platform.localeName.toLowerCase();
      if (osLocale.startsWith('tr')) return 'tr';
    } catch (_) {}
    return 'en';
  }

  static Future<Map<String, Map<String, String>>> loadAllDictionaries() async {
    final result = <String, Map<String, String>>{};
    for (final code in ['tr', 'en']) {
      try {
        final raw = await rootBundle.loadString('assets/i18n/$code.json');
        final decoded = jsonDecode(raw) as Map<String, dynamic>;
        result[code] = decoded.map((k, v) => MapEntry(k, v.toString()));
      } catch (_) {
        result[code] = {};
      }
    }
    return result;
  }

  String t(String key, [Map<String, String>? params]) {
    var val = strings[key] ?? key;
    if (params != null) {
      params.forEach((k, v) {
        val = val.replaceAll('{$k}', v);
      });
    }
    return val;
  }

  static AppI18n of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<AppI18nScope>();
    return scope?.i18n ?? const AppI18n(langCode: 'en', strings: {});
  }
}

class AppI18nScope extends InheritedWidget {
  final AppI18n i18n;

  const AppI18nScope({
    super.key,
    required this.i18n,
    required super.child,
  });

  @override
  bool updateShouldNotify(covariant AppI18nScope oldWidget) {
    return oldWidget.i18n.langCode != i18n.langCode ||
        oldWidget.i18n != i18n;
  }
}
