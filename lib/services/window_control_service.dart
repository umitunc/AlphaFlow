import 'dart:ffi' as ffi;
import 'dart:io';
import 'package:flutter/services.dart';

/// 8 yönlü çerçevesiz pencere boyutlandırma kenar ve köşeleri.
enum ResizeEdge {
  topLeft,
  top,
  topRight,
  right,
  bottomRight,
  bottom,
  bottomLeft,
  left,
}

// --- Kernel32 FFI Signatures ---
typedef _GetCurrentProcessIdNative = ffi.Uint32 Function();
typedef _GetCurrentProcessIdDart = int Function();

typedef _LocalAllocNative = ffi.Pointer<ffi.Void> Function(
    ffi.Uint32 uFlags, ffi.IntPtr uBytes);
typedef _LocalAllocDart = ffi.Pointer<ffi.Void> Function(int uFlags, int uBytes);

typedef _LocalFreeNative = ffi.IntPtr Function(ffi.Pointer<ffi.Void> hMem);
typedef _LocalFreeDart = int Function(ffi.Pointer<ffi.Void> hMem);

// --- User32 FFI Signatures ---
typedef _FindWindowExWNative = ffi.IntPtr Function(
  ffi.IntPtr hWndParent,
  ffi.IntPtr hWndChildAfter,
  ffi.Pointer<ffi.Uint16> lpszClass,
  ffi.Pointer<ffi.Uint16> lpszWindow,
);
typedef _FindWindowExWDart = int Function(
  int hWndParent,
  int hWndChildAfter,
  ffi.Pointer<ffi.Uint16> lpszClass,
  ffi.Pointer<ffi.Uint16> lpszWindow,
);

typedef _GetWindowThreadProcessIdNative = ffi.Uint32 Function(
    ffi.IntPtr hWnd, ffi.Pointer<ffi.Uint32> lpdwProcessId);
typedef _GetWindowThreadProcessIdDart = int Function(
    int hWnd, ffi.Pointer<ffi.Uint32> lpdwProcessId);

typedef _IsWindowNative = ffi.Int32 Function(ffi.IntPtr hWnd);
typedef _IsWindowDart = int Function(int hWnd);

typedef _IsWindowVisibleNative = ffi.Int32 Function(ffi.IntPtr hWnd);
typedef _IsWindowVisibleDart = int Function(int hWnd);

typedef _GetWindowLongPtrWNative = ffi.IntPtr Function(
    ffi.IntPtr hWnd, ffi.Int32 nIndex);
typedef _GetWindowLongPtrWDart = int Function(int hWnd, int nIndex);

typedef _SetWindowLongPtrWNative = ffi.IntPtr Function(
    ffi.IntPtr hWnd, ffi.Int32 nIndex, ffi.IntPtr dwNewLong);
typedef _SetWindowLongPtrWDart = int Function(
    int hWnd, int nIndex, int dwNewLong);

typedef _SetWindowPosNative = ffi.Int32 Function(
  ffi.IntPtr hWnd,
  ffi.IntPtr hWndInsertAfter,
  ffi.Int32 x,
  ffi.Int32 y,
  ffi.Int32 cx,
  ffi.Int32 cy,
  ffi.Uint32 uFlags,
);
typedef _SetWindowPosDart = int Function(
  int hWnd,
  int hWndInsertAfter,
  int x,
  int y,
  int cx,
  int cy,
  int uFlags,
);

typedef _ShowWindowAsyncNative = ffi.Int32 Function(
    ffi.IntPtr hWnd, ffi.Int32 nCmdShow);
typedef _ShowWindowAsyncDart = int Function(int hWnd, int nCmdShow);

typedef _PostMessageWNative = ffi.Int32 Function(
  ffi.IntPtr hWnd,
  ffi.Uint32 msg,
  ffi.IntPtr wParam,
  ffi.IntPtr lParam,
);
typedef _PostMessageWDart = int Function(
    int hWnd, int msg, int wParam, int lParam);

typedef _IsZoomedNative = ffi.Int32 Function(ffi.IntPtr hWnd);
typedef _IsZoomedDart = int Function(int hWnd);

typedef _GetWindowRectNative = ffi.Int32 Function(
    ffi.IntPtr hWnd, ffi.Pointer<ffi.Int32> lpRect);
typedef _GetWindowRectDart = int Function(
    int hWnd, ffi.Pointer<ffi.Int32> lpRect);

typedef _GetCursorPosNative = ffi.Int32 Function(
    ffi.Pointer<ffi.Int32> lpPoint);
typedef _GetCursorPosDart = int Function(ffi.Pointer<ffi.Int32> lpPoint);

typedef _MonitorFromWindowNative = ffi.IntPtr Function(
    ffi.IntPtr hWnd, ffi.Uint32 dwFlags);
typedef _MonitorFromWindowDart = int Function(int hWnd, int dwFlags);

typedef _GetMonitorInfoWNative = ffi.Int32 Function(
    ffi.IntPtr hMonitor, ffi.Pointer<ffi.Int32> lpmi);
typedef _GetMonitorInfoWDart = int Function(
    int hMonitor, ffi.Pointer<ffi.Int32> lpmi);

class WindowControlService {
  static const MethodChannel _channel = MethodChannel('alphaflow/window');
  static int _cachedHwnd = 0;

  // Custom Maximize/Restore durumu ve pencere koordinat yedekleri
  static bool _isCustomMaximized = false;
  static int _restoreLeft = 100;
  static int _restoreTop = 80;
  static int _restoreWidth = 1280;
  static int _restoreHeight = 820;

  // Sürükleme (Drag) başlangıç koordinatları
  static int _dragStartCursorX = 0;
  static int _dragStartCursorY = 0;
  static int _dragStartWinX = 0;
  static int _dragStartWinY = 0;
  static bool _draggingActive = false;

  // Boyutlandırma (Resize) başlangıç koordinatları
  static ResizeEdge? _activeResizeEdge;
  static int _resizeStartCursorX = 0;
  static int _resizeStartCursorY = 0;
  static int _resizeStartLeft = 0;
  static int _resizeStartTop = 0;
  static int _resizeStartRight = 0;
  static int _resizeStartBottom = 0;

  static const int minWindowWidth = 920;
  static const int minWindowHeight = 620;

  static bool get isMaximized => _isCustomMaximized;

  static ffi.DynamicLibrary? _user32;
  static ffi.DynamicLibrary? _kernel32;

  static ffi.DynamicLibrary get _u32 =>
      _user32 ??= ffi.DynamicLibrary.open('user32.dll');
  static ffi.DynamicLibrary get _k32 =>
      _kernel32 ??= ffi.DynamicLibrary.open('kernel32.dll');

  static ffi.Pointer<ffi.Void> _allocZeroed(int bytes) {
    final alloc =
        _k32.lookupFunction<_LocalAllocNative, _LocalAllocDart>('LocalAlloc');
    // LPTR = 0x0040 (LMEM_FIXED | LMEM_ZEROINIT)
    return alloc(0x0040, bytes);
  }

  static void _free(ffi.Pointer<ffi.NativeType> ptr) {
    if (ptr.address == 0) return;
    final freeFn =
        _k32.lookupFunction<_LocalFreeNative, _LocalFreeDart>('LocalFree');
    freeFn(ptr.cast());
  }

  /// Dart UI izole thread'inden bağımsız olarak mevcut prosesin (PID) ana
  /// FLUTTER_RUNNER_WIN32_WINDOW pencere tanıtıcısını (HWND) %100 kesinlikle bulur.
  static int getWindowHandle() {
    if (!Platform.isWindows) return 0;
    try {
      final isWin =
          _u32.lookupFunction<_IsWindowNative, _IsWindowDart>('IsWindow');
      if (_cachedHwnd != 0 && isWin(_cachedHwnd) != 0) {
        return _cachedHwnd;
      }

      final getPid = _k32.lookupFunction<_GetCurrentProcessIdNative,
          _GetCurrentProcessIdDart>('GetCurrentProcessId');
      final findWin =
          _u32.lookupFunction<_FindWindowExWNative, _FindWindowExWDart>(
              'FindWindowExW');
      final getWinPid = _u32.lookupFunction<_GetWindowThreadProcessIdNative,
          _GetWindowThreadProcessIdDart>('GetWindowThreadProcessId');
      final isVisible = _u32.lookupFunction<_IsWindowVisibleNative,
          _IsWindowVisibleDart>('IsWindowVisible');

      final int myPid = getPid();
      final pidPtr = _allocZeroed(8).cast<ffi.Uint32>();

      // 1. Önce doğrudan FLUTTER_RUNNER_WIN32_WINDOW sınıfını ara
      const className = 'FLUTTER_RUNNER_WIN32_WINDOW';
      final classPtr =
          _allocZeroed((className.length + 1) * 2).cast<ffi.Uint16>();
      for (int i = 0; i < className.length; i++) {
        (classPtr + i).value = className.codeUnitAt(i);
      }

      int found = 0;
      int curr = 0;
      while (true) {
        curr = findWin(0, curr, classPtr, ffi.nullptr);
        if (curr == 0) break;
        pidPtr.value = 0;
        getWinPid(curr, pidPtr);
        if (pidPtr.value == myPid) {
          found = curr;
          break;
        }
      }

      // 2. Bulunamazsa mevcut prosese ait görünür üst-seviye pencereyi ara
      if (found == 0) {
        curr = 0;
        while (true) {
          curr = findWin(0, curr, ffi.nullptr, ffi.nullptr);
          if (curr == 0) break;
          pidPtr.value = 0;
          getWinPid(curr, pidPtr);
          if (pidPtr.value == myPid && isVisible(curr) != 0) {
            found = curr;
            break;
          }
        }
      }

      _free(classPtr);
      _free(pidPtr);

      if (found != 0) {
        _cachedHwnd = found;
      }
      return found;
    } catch (_) {
      return 0;
    }
  }

  /// Windows işletim sisteminin standart başlık çubuğunu ve sağ üstteki (— □ ✕)
  /// sistem butonlarını anında kaldırarak tam çerçevesiz (frameless) mod uygular.
  static void ensureFrameless() {
    if (!Platform.isWindows) return;
    try {
      final hwnd = getWindowHandle();
      if (hwnd == 0) return;

      const int gwlStyle = -16;
      const int gwlExStyle = -20;

      const int wsCaption = 0x00C00000;
      const int wsThickFrame = 0x00040000;
      const int wsSysMenu = 0x00080000;
      const int wsPopup = 0x80000000;
      const int wsVisible = 0x10000000;
      const int wsClipChildren = 0x02000000;
      const int wsMinimizeBox = 0x00020000;
      const int wsMaximizeBox = 0x00010000;

      const int wsExDlgModalFrame = 0x00000001;
      const int wsExWindowEdge = 0x00000100;
      const int wsExClientEdge = 0x00000200;
      const int wsExStaticEdge = 0x00020000;

      final getStyle = _u32
          .lookupFunction<_GetWindowLongPtrWNative, _GetWindowLongPtrWDart>(
              'GetWindowLongPtrW');
      final setStyle = _u32
          .lookupFunction<_SetWindowLongPtrWNative, _SetWindowLongPtrWDart>(
              'SetWindowLongPtrW');
      final setPos =
          _u32.lookupFunction<_SetWindowPosNative, _SetWindowPosDart>(
              'SetWindowPos');

      final currentStyle = getStyle(hwnd, gwlStyle);
      final strippedStyle =
          (currentStyle & ~wsCaption & ~wsThickFrame & ~wsSysMenu) |
              wsPopup |
              wsVisible |
              wsClipChildren |
              wsMinimizeBox |
              wsMaximizeBox;
      setStyle(hwnd, gwlStyle, strippedStyle);

      final currentExStyle = getStyle(hwnd, gwlExStyle);
      final strippedExStyle = currentExStyle &
          ~wsExDlgModalFrame &
          ~wsExWindowEdge &
          ~wsExClientEdge &
          ~wsExStaticEdge;
      setStyle(hwnd, gwlExStyle, strippedExStyle);

      // SWP_NOSIZE (0x0001) | SWP_NOMOVE (0x0002) | SWP_NOZORDER (0x0004) |
      // SWP_NOACTIVATE (0x0010) | SWP_FRAMECHANGED (0x0020) = 0x0037
      setPos(hwnd, 0, 0, 0, 0, 0, 0x0037);
    } catch (_) {}
  }

  /// Pencere sürüklemeyi başlatır (onPanStart).
  static void beginDrag() {
    if (!Platform.isWindows) {
      startDrag();
      return;
    }
    try {
      final hwnd = getWindowHandle();
      if (hwnd == 0 || _isCustomMaximized) {
        _draggingActive = false;
        return;
      }
      final getCursor =
          _u32.lookupFunction<_GetCursorPosNative, _GetCursorPosDart>(
              'GetCursorPos');
      final getRect =
          _u32.lookupFunction<_GetWindowRectNative, _GetWindowRectDart>(
              'GetWindowRect');

      final ptPtr = _allocZeroed(8).cast<ffi.Int32>();
      final rcPtr = _allocZeroed(16).cast<ffi.Int32>();

      if (getCursor(ptPtr) != 0 && getRect(hwnd, rcPtr) != 0) {
        _dragStartCursorX = ptPtr[0];
        _dragStartCursorY = ptPtr[1];
        _dragStartWinX = rcPtr[0];
        _dragStartWinY = rcPtr[1];
        _draggingActive = true;
      }

      _free(ptPtr);
      _free(rcPtr);
    } catch (_) {
      _draggingActive = false;
    }
  }

  /// Pencereyi fare hareketine göre taşır (onPanUpdate).
  static void updateDrag() {
    if (!Platform.isWindows || !_draggingActive) return;
    try {
      final hwnd = getWindowHandle();
      if (hwnd == 0) return;

      final getCursor =
          _u32.lookupFunction<_GetCursorPosNative, _GetCursorPosDart>(
              'GetCursorPos');
      final setPos =
          _u32.lookupFunction<_SetWindowPosNative, _SetWindowPosDart>(
              'SetWindowPos');

      final ptPtr = _allocZeroed(8).cast<ffi.Int32>();
      if (getCursor(ptPtr) != 0) {
        final dx = ptPtr[0] - _dragStartCursorX;
        final dy = ptPtr[1] - _dragStartCursorY;
        // SWP_NOSIZE (0x0001) | SWP_NOZORDER (0x0004) | SWP_NOACTIVATE (0x0010) = 0x0015
        setPos(
          hwnd,
          0,
          _dragStartWinX + dx,
          _dragStartWinY + dy,
          0,
          0,
          0x0015,
        );
      }
      _free(ptPtr);
    } catch (_) {}
  }

  /// Pencere sürüklemeyi sonlandırır (onPanEnd / onPanCancel).
  static void endDrag() {
    _draggingActive = false;
  }

  /// 8 yönlü kenar/köşe boyutlandırmayı başlatır.
  static void beginResize(ResizeEdge edge) {
    if (!Platform.isWindows || _isCustomMaximized) {
      _activeResizeEdge = null;
      return;
    }
    try {
      final hwnd = getWindowHandle();
      if (hwnd == 0) {
        _activeResizeEdge = null;
        return;
      }
      final getCursor =
          _u32.lookupFunction<_GetCursorPosNative, _GetCursorPosDart>(
              'GetCursorPos');
      final getRect =
          _u32.lookupFunction<_GetWindowRectNative, _GetWindowRectDart>(
              'GetWindowRect');

      final ptPtr = _allocZeroed(8).cast<ffi.Int32>();
      final rcPtr = _allocZeroed(16).cast<ffi.Int32>();

      if (getCursor(ptPtr) != 0 && getRect(hwnd, rcPtr) != 0) {
        _resizeStartCursorX = ptPtr[0];
        _resizeStartCursorY = ptPtr[1];
        _resizeStartLeft = rcPtr[0];
        _resizeStartTop = rcPtr[1];
        _resizeStartRight = rcPtr[2];
        _resizeStartBottom = rcPtr[3];
        _activeResizeEdge = edge;
      }

      _free(ptPtr);
      _free(rcPtr);
    } catch (_) {
      _activeResizeEdge = null;
    }
  }

  /// Aktif kenar/köşe sürüklemesine göre pencereyi yeniden boyutlandırır.
  static void updateResize() {
    final edge = _activeResizeEdge;
    if (!Platform.isWindows || edge == null || _isCustomMaximized) return;
    try {
      final hwnd = getWindowHandle();
      if (hwnd == 0) return;

      final getCursor =
          _u32.lookupFunction<_GetCursorPosNative, _GetCursorPosDart>(
              'GetCursorPos');
      final setPos =
          _u32.lookupFunction<_SetWindowPosNative, _SetWindowPosDart>(
              'SetWindowPos');

      final ptPtr = _allocZeroed(8).cast<ffi.Int32>();
      if (getCursor(ptPtr) != 0) {
        final dx = ptPtr[0] - _resizeStartCursorX;
        final dy = ptPtr[1] - _resizeStartCursorY;

        int newLeft = _resizeStartLeft;
        int newTop = _resizeStartTop;
        int newRight = _resizeStartRight;
        int newBottom = _resizeStartBottom;

        if (edge == ResizeEdge.left ||
            edge == ResizeEdge.topLeft ||
            edge == ResizeEdge.bottomLeft) {
          newLeft = (_resizeStartLeft + dx)
              .clamp(-10000, _resizeStartRight - minWindowWidth);
        }
        if (edge == ResizeEdge.right ||
            edge == ResizeEdge.topRight ||
            edge == ResizeEdge.bottomRight) {
          newRight = (_resizeStartRight + dx)
              .clamp(_resizeStartLeft + minWindowWidth, 20000);
        }
        if (edge == ResizeEdge.top ||
            edge == ResizeEdge.topLeft ||
            edge == ResizeEdge.topRight) {
          newTop = (_resizeStartTop + dy)
              .clamp(-10000, _resizeStartBottom - minWindowHeight);
        }
        if (edge == ResizeEdge.bottom ||
            edge == ResizeEdge.bottomLeft ||
            edge == ResizeEdge.bottomRight) {
          newBottom = (_resizeStartBottom + dy)
              .clamp(_resizeStartTop + minWindowHeight, 20000);
        }

        final newWidth = newRight - newLeft;
        final newHeight = newBottom - newTop;

        // SWP_NOZORDER (0x0004) | SWP_NOACTIVATE (0x0010) = 0x0014
        setPos(hwnd, 0, newLeft, newTop, newWidth, newHeight, 0x0014);
      }
      _free(ptPtr);
    } catch (_) {}
  }

  /// Kenar/köşe boyutlandırmayı sonlandırır.
  static void endResize() {
    _activeResizeEdge = null;
  }

  static Future<void> startDrag() async {
    if (Platform.isWindows) {
      beginDrag();
      return;
    }
    try {
      await _channel.invokeMethod<void>('startDrag');
    } catch (_) {}
  }

  /// Pencereyi görev çubuğuna küçültür (—).
  static Future<void> minimize() async {
    if (Platform.isWindows) {
      final hwnd = getWindowHandle();
      if (hwnd != 0) {
        try {
          final showAsync = _u32
              .lookupFunction<_ShowWindowAsyncNative, _ShowWindowAsyncDart>(
                  'ShowWindowAsync');
          // SW_MINIMIZE = 6
          showAsync(hwnd, 6);
          return;
        } catch (_) {}
      }
    }
    try {
      await _channel.invokeMethod<void>('minimize');
    } catch (_) {}
  }

  /// Pencereyi görev çubuğunu kapatmadan çalışma alanına (WorkArea) tam ekran yapar veya eski boyutuna döndürür (□).
  static Future<bool> toggleMaximize() async {
    if (Platform.isWindows) {
      final hwnd = getWindowHandle();
      if (hwnd != 0) {
        try {
          ensureFrameless();
          final isZoomed =
              _u32.lookupFunction<_IsZoomedNative, _IsZoomedDart>('IsZoomed');
          final showAsync = _u32
              .lookupFunction<_ShowWindowAsyncNative, _ShowWindowAsyncDart>(
                  'ShowWindowAsync');
          final getRect =
              _u32.lookupFunction<_GetWindowRectNative, _GetWindowRectDart>(
                  'GetWindowRect');
          final setPos =
              _u32.lookupFunction<_SetWindowPosNative, _SetWindowPosDart>(
              'SetWindowPos');
          final monFromWin = _u32.lookupFunction<_MonitorFromWindowNative,
              _MonitorFromWindowDart>('MonitorFromWindow');
          final getMonInfo =
              _u32.lookupFunction<_GetMonitorInfoWNative, _GetMonitorInfoWDart>(
                  'GetMonitorInfoW');

          if (_isCustomMaximized || isZoomed(hwnd) != 0) {
            if (isZoomed(hwnd) != 0) {
              // SW_RESTORE = 9
              showAsync(hwnd, 9);
            }
            // SWP_NOZORDER (0x0004) | SWP_FRAMECHANGED (0x0020) = 0x0024
            setPos(
              hwnd,
              0,
              _restoreLeft,
              _restoreTop,
              _restoreWidth,
              _restoreHeight,
              0x0024,
            );
            _isCustomMaximized = false;
            return false;
          } else {
            // Mevcut pencere koordinatlarını kaydet
            final rcPtr = _allocZeroed(16).cast<ffi.Int32>();
            if (getRect(hwnd, rcPtr) != 0) {
              _restoreLeft = rcPtr[0];
              _restoreTop = rcPtr[1];
              _restoreWidth = (rcPtr[2] - rcPtr[0]).clamp(640, 10000);
              _restoreHeight = (rcPtr[3] - rcPtr[1]).clamp(480, 10000);
            }
            _free(rcPtr);

            // Bulunduğu monitörün görev çubuğu hariç çalışma alanını (rcWork) al
            // MONITOR_DEFAULTTONEAREST = 2
            final hMon = monFromWin(hwnd, 2);
            final miPtr = _allocZeroed(40).cast<ffi.Int32>();
            miPtr[0] = 40; // sizeof(MONITORINFO)
            if (hMon != 0 && getMonInfo(hMon, miPtr) != 0) {
              final workLeft = miPtr[5];
              final workTop = miPtr[6];
              final workWidth = miPtr[7] - miPtr[5];
              final workHeight = miPtr[8] - miPtr[6];
              setPos(
                hwnd,
                0,
                workLeft,
                workTop,
                workWidth,
                workHeight,
                0x0024,
              );
              _isCustomMaximized = true;
            }
            _free(miPtr);
            return _isCustomMaximized;
          }
        } catch (_) {}
      }
    }
    try {
      final res = await _channel.invokeMethod<bool>('toggleMaximize');
      return res ?? false;
    } catch (_) {
      return false;
    }
  }

  /// Uygulamayı güvenli şekilde kapatır (✕).
  static Future<void> close() async {
    if (Platform.isWindows) {
      final hwnd = getWindowHandle();
      if (hwnd != 0) {
        try {
          final postMsg =
              _u32.lookupFunction<_PostMessageWNative, _PostMessageWDart>(
                  'PostMessageW');
          // WM_CLOSE = 0x0010
          postMsg(hwnd, 0x0010, 0, 0);
        } catch (_) {}
      }
      Future<void>.delayed(const Duration(milliseconds: 180), () {
        exit(0);
      });
      return;
    }
    try {
      await _channel.invokeMethod<void>('close');
    } catch (_) {
      exit(0);
    }
  }
}
