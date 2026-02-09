import 'package:flutter/foundation.dart';

/// Mode du canvas (sélection, création entité, association, lien).
enum CanvasMode {
  select,
  addEntity,
  addAssociation,
  createLink,
}

/// Activer les logs de changement de mode (aligné avec mcd_canvas.dart).
const bool _kCanvasModeDebug = false;

class CanvasModeState extends ChangeNotifier {
  CanvasModeState() : _mode = CanvasMode.select;

  CanvasMode _mode;
  CanvasMode get mode => _mode;

  void setMode(CanvasMode m) {
    if (_mode == m) {
      if (_kCanvasModeDebug) debugPrint('[CanvasMode] setMode($m) ignoré (déjà actif)');
      return;
    }
    if (_kCanvasModeDebug) debugPrint('[CanvasMode] setMode $_mode -> $m');
    _mode = m;
    _linkFirstTarget = null;
    notifyListeners();
  }

  /// Pour le mode Lien: première cible (entité ou association) cliquée.
  String? _linkFirstTarget;
  bool get isLinkFirstSelected => _linkFirstTarget != null;
  String? get linkFirstTarget => _linkFirstTarget;

  void setLinkFirstTarget(String? name) {
    _linkFirstTarget = name;
    notifyListeners();
  }

  void clearLinkFirstTarget() {
    _linkFirstTarget = null;
    notifyListeners();
  }

  bool _showGrid = true;
  bool get showGrid => _showGrid;
  void toggleGrid() {
    _showGrid = !_showGrid;
    notifyListeners();
  }
}
