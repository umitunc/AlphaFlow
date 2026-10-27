import 'package:flutter/material.dart';
import 'core/localization.dart';
import 'core/theme.dart';
import 'ui/main_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final dictionaries = await AppI18n.loadAllDictionaries();
  final initialLang = AppI18n.detectSystemLangCode();
  runApp(
    AlphaFlowStudioApp(
      dictionaries: dictionaries,
      initialLangCode: initialLang,
    ),
  );
}

class AlphaFlowStudioApp extends StatefulWidget {
  final Map<String, Map<String, String>> dictionaries;
  final String initialLangCode;

  const AlphaFlowStudioApp({
    super.key,
    required this.dictionaries,
    required this.initialLangCode,
  });

  @override
  State<AlphaFlowStudioApp> createState() => _AlphaFlowStudioAppState();
}

class _AlphaFlowStudioAppState extends State<AlphaFlowStudioApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  late String _langCode;

  @override
  void initState() {
    super.initState();
    _langCode = widget.initialLangCode;
  }

  @override
  Widget build(BuildContext context) {
    final activeMap =
        widget.dictionaries[_langCode] ?? widget.dictionaries['en'] ?? const {};
    final i18n = AppI18n(langCode: _langCode, strings: activeMap);

    return AppI18nScope(
      i18n: i18n,
      child: MaterialApp(
        title: 'AlphaFlow Studio Pro',
        debugShowCheckedModeBanner: false,
        themeMode: _themeMode,
        theme: AlphaFlowTheme.buildTheme(Brightness.light),
        darkTheme: AlphaFlowTheme.buildTheme(Brightness.dark),
        home: AlphaFlowMainScreen(
          themeMode: _themeMode,
          onThemeModeChanged: (mode) => setState(() => _themeMode = mode),
          langCode: _langCode,
          onLangCodeChanged: (code) => setState(() => _langCode = code),
        ),
      ),
    );
  }
}
