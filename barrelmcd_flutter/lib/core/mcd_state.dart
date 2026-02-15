import 'api_client.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart' show Offset;
import '../utils/link_geometry.dart';
import '../utils/auto_layout.dart';

/// État global du MCD (entités, associations, liens) pour l'UI Flutter.
class McdState extends ChangeNotifier {
  McdState({required ApiClient api}) : _api = api;

  final ApiClient _api;
  static const int _maxHistory = 50;

  List<Map<String, dynamic>> _entities = [];
  List<Map<String, dynamic>> _associations = [];
  List<Map<String, dynamic>> _inheritanceLinks = [];
  /// Liens association ↔ entité (un élément = un arc).
  /// Chaque lien : association, entity, card_entity, card_assoc, arm_index (optionnel).
  /// Cardinalités MCD : 0,1 | 1,1 | 0,n | 1,n
  List<Map<String, dynamic>> _associationLinks = [];
  List<String> _logMessages = [];
  String? _lastError;

  /// Sélection multiple : ensembles d'indices par type (séparément ou tout ensemble).
  final Set<int> _selectedEntityIndices = {};
  final Set<int> _selectedAssociationIndices = {};
  final Set<int> _selectedLinkIndices = {};
  final Set<int> _selectedInheritanceIndices = {};

  Set<int> get selectedEntityIndices => Set<int>.from(_selectedEntityIndices);
  Set<int> get selectedAssociationIndices => Set<int>.from(_selectedAssociationIndices);
  Set<int> get selectedLinkIndices => Set<int>.from(_selectedLinkIndices);
  Set<int> get selectedInheritanceIndices => Set<int>.from(_selectedInheritanceIndices);

  /// Sélection « primaire » (pour barre d'outils / dialogue) : premier de chaque type.
  String? get selectedType {
    if (_selectedEntityIndices.isNotEmpty) return 'entity';
    if (_selectedAssociationIndices.isNotEmpty) return 'association';
    if (_selectedLinkIndices.isNotEmpty) return 'link';
    if (_selectedInheritanceIndices.isNotEmpty) return 'inheritance';
    return null;
  }

  int get selectedIndex {
    if (_selectedEntityIndices.isNotEmpty) return _selectedEntityIndices.first;
    if (_selectedAssociationIndices.isNotEmpty) return _selectedAssociationIndices.first;
    if (_selectedLinkIndices.isNotEmpty) return _selectedLinkIndices.first;
    if (_selectedInheritanceIndices.isNotEmpty) return _selectedInheritanceIndices.first;
    return -1;
  }

  bool get hasSelection =>
      _selectedEntityIndices.isNotEmpty ||
      _selectedAssociationIndices.isNotEmpty ||
      _selectedLinkIndices.isNotEmpty ||
      _selectedInheritanceIndices.isNotEmpty;

  int get selectionCount =>
      _selectedEntityIndices.length +
      _selectedAssociationIndices.length +
      _selectedLinkIndices.length +
      _selectedInheritanceIndices.length;

  final List<Map<String, dynamic>> _undoStack = [];
  final List<Map<String, dynamic>> _redoStack = [];

  /// Si true, la transposition MLD/MPD utilise héritage et CIF/CIFF ; si false, uniquement entités et associations.
  bool _useInheritanceAndCifForTransposition = false;
  bool get useInheritanceAndCifForTransposition => _useInheritanceAndCifForTransposition;
  set useInheritanceAndCifForTransposition(bool value) {
    if (_useInheritanceAndCifForTransposition == value) return;
    _useInheritanceAndCifForTransposition = value;
    notifyListeners();
  }

  /// Si true, les cardinalités des liens sont affichées en notation UML (0..1, 1..*, etc.) au lieu du MCD (0,1, 1,n).
  bool _showUmlCardinalities = false;
  bool get showUmlCardinalities => _showUmlCardinalities;
  set showUmlCardinalities(bool value) {
    if (_showUmlCardinalities == value) return;
    _showUmlCardinalities = value;
    notifyListeners();
  }
  void toggleUmlCardinalities() {
    _showUmlCardinalities = !_showUmlCardinalities;
    notifyListeners();
  }

  /// Marge au début du trait de flèche (px). Utilisé par link_geometry et link_arrow.
  double _arrowStartMargin = 10.0;
  double get arrowStartMargin => _arrowStartMargin;
  set arrowStartMargin(double value) {
    final v = value.clamp(0.0, 50.0);
    if (_arrowStartMargin == v) return;
    _arrowStartMargin = v;
    notifyListeners();
  }

  /// Marge à la pointe de flèche (px). Utilisé par link_geometry.
  double _arrowTipMargin = 12.0;
  double get arrowTipMargin => _arrowTipMargin;
  set arrowTipMargin(double value) {
    final v = value.clamp(0.0, 50.0);
    if (_arrowTipMargin == v) return;
    _arrowTipMargin = v;
    notifyListeners();
  }

  /// Épaisseur par défaut du trait des liens (1–6). Utilisée quand un lien n'a pas de stroke_width personnalisé.
  double _defaultStrokeWidth = 2.5;
  double get defaultStrokeWidth => _defaultStrokeWidth;
  set defaultStrokeWidth(double value) {
    final v = value.clamp(1.0, 6.0);
    if (_defaultStrokeWidth == v) return;
    _defaultStrokeWidth = v;
    notifyListeners();
  }

  /// Convertit une cardinalité MCD (0,1 1,1 0,n 1,n) en notation UML (0..1 1..1 0..* 1..*).
  static String mcdToUmlCardinality(String mcd) {
    final s = mcd.trim().toLowerCase().replaceAll(' ', '');
    if (s.contains('..') || s.contains('*')) return mcd;
    switch (s) {
      case '0,1': return '0..1';
      case '1,1': return '1..1';
      case '0,n': return '0..*';
      case '1,n': return '1..*';
      default: return mcd;
    }
  }

  /// Cache MLD / MPD / SQL (par dbms) pour sauvegarde projet et export sans régénération.
  Map<String, dynamic>? _cachedMld;
  final Map<String, Map<String, dynamic>> _cachedMpd = {};
  final Map<String, String> _cachedSql = {};
  /// Version SQL avec types d'origine (non traduits pour le SGBD), gardée en stock local.
  final Map<String, String> _cachedSqlOriginal = {};
  /// Liste des traductions automatiques (table, column, original_type, translated_type) pour bulle d'info.
  final Map<String, List<Map<String, dynamic>>> _cachedSqlTranslations = {};

  static const List<String> supportedDbms = ['mysql', 'postgresql', 'sqlite', 'sqlserver'];

  Map<String, dynamic>? get cachedMld => _cachedMld != null ? Map<String, dynamic>.from(_cachedMld!) : null;
  Map<String, dynamic>? getCachedMpd(String dbms) => _cachedMpd[dbms] != null ? Map<String, dynamic>.from(_cachedMpd[dbms]!) : null;
  String? getCachedSql(String dbms) => _cachedSql[dbms];
  String? getCachedSqlOriginal(String dbms) => _cachedSqlOriginal[dbms];
  List<Map<String, dynamic>> getCachedSqlTranslations(String dbms) => List<Map<String, dynamic>>.from(_cachedSqlTranslations[dbms] ?? []);

  void setCachedMld(Map<String, dynamic>? mld) {
    _cachedMld = mld != null ? Map<String, dynamic>.from(mld) : null;
    notifyListeners();
  }

  void restoreMldMpdSqlCache(Map<String, dynamic> data) {
    final mld = data['mld'] as Map<String, dynamic>?;
    _cachedMld = mld != null ? Map<String, dynamic>.from(mld) : null;
    for (final dbms in supportedDbms) {
      final mpd = data['mpd_$dbms'] as Map<String, dynamic>?;
      if (mpd != null) _cachedMpd[dbms] = Map<String, dynamic>.from(mpd);
      final sql = data['sql_$dbms'] as String?;
      if (sql != null) _cachedSql[dbms] = sql;
      final sqlOrig = data['sql_original_$dbms'] as String?;
      if (sqlOrig != null) _cachedSqlOriginal[dbms] = sqlOrig;
      final tr = data['sql_translations_$dbms'] as List?;
      if (tr != null) _cachedSqlTranslations[dbms] = tr.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    notifyListeners();
  }

  void clearMldMpdSqlCache() {
    _cachedMld = null;
    _cachedMpd.clear();
    _cachedSql.clear();
    _cachedSqlOriginal.clear();
    _cachedSqlTranslations.clear();
    notifyListeners();
    _scheduleMldMpdSqlRefresh();
  }

  /// Rafraîchit MLD/MPD/SQL en arrière-plan après invalidation (transposition instantanée).
  /// Toutes les exceptions (ex. API indisponible) sont capturées pour éviter l'écran rouge.
  void _scheduleMldMpdSqlRefresh() {
    Future.microtask(() async {
      if (_entities.isEmpty) return;
      try {
        await generateMld();
        for (final dbms in supportedDbms) {
          await generateMpd(dbms: dbms);
          await generateSql(dbms: dbms);
        }
      } catch (e, st) {
        if (kDebugMode) debugPrint('[McdState._scheduleMldMpdSqlRefresh] API indisponible: $e\n$st');
      }
    });
  }

  List<Map<String, dynamic>> get entities => List.unmodifiable(_entities);
  List<Map<String, dynamic>> get associations => List.unmodifiable(_associations);
  List<Map<String, dynamic>> get inheritanceLinks => List.unmodifiable(_inheritanceLinks);
  List<Map<String, dynamic>> get associationLinks => List.unmodifiable(_associationLinks);

  /// Contraintes d'intégrité fonctionnelle (CIF/CIFF).
  List<Map<String, dynamic>> get cifConstraints => List.unmodifiable(_cifConstraints);
  List<Map<String, dynamic>> _cifConstraints = [];

  /// Position du symbole d'héritage par parent (clé = nom entité parente). Null = position auto.
  Map<String, Map<String, double>> get inheritanceSymbolPositions => Map.unmodifiable(_inheritanceSymbolPositions);
  final Map<String, Map<String, double>> _inheritanceSymbolPositions = {};
  List<String> get logMessages => List.unmodifiable(_logMessages);
  String? get lastError => _lastError;
  bool get canUndo => _undoStack.isNotEmpty;
  bool get canRedo => _redoStack.isNotEmpty;

  /// Format MCD pour l'API: associations avec entities + 4 cardinalités (côté entité et côté association par lien).
  Map<String, dynamic> get mcdData {
    final assocWithLinks = <Map<String, dynamic>>[];
    for (final a in _associations) {
      final name = a['name'] as String? ?? '';
      final linksToThis = _associationLinks.where((l) => l['association'] == name).toList();
      final entityNames = linksToThis.map((l) => l['entity'] as String).toSet().toList();
      final cardinalities = <String, String>{};
      final cardinalitiesAssoc = <String, String>{};
      for (final l in linksToThis) {
        final ent = l['entity'] as String;
        cardinalities[ent] = l['card_entity'] as String? ?? l['cardinality'] as String? ?? '1,n';
        cardinalitiesAssoc[ent] = l['card_assoc'] as String? ?? '1,n';
      }
      assocWithLinks.add({
        ...a,
        'entities': entityNames,
        'cardinalities': cardinalities,
        'cardinalities_assoc': cardinalitiesAssoc,
      });
    }
    return {
      'entities': _entities,
      'associations': assocWithLinks,
      'inheritance_links': _inheritanceLinks,
      'association_links': _associationLinks,
      'cif_constraints': _cifConstraints.map((c) => Map<String, dynamic>.from(c)).toList(),
      'inheritance_symbol_positions': _inheritanceSymbolPositions.map((k, v) => MapEntry(k, Map<String, double>.from(v))),
    };
  }

  /// Payload pour transposition MLD/MPD : pas d’héritage ni CIF/CIFF (symboles et liens restent visuels uniquement).
  Map<String, dynamic> get mcdDataForTransposition {
    final data = mcdData;
    return {
      ...data,
      'inheritance_links': <Map<String, dynamic>>[],
      'cif_constraints': <Map<String, dynamic>>[],
      'inheritance_symbol_positions': <String, Map<String, double>>{},
    };
  }

  void setInheritanceSymbolPosition(String parentName, double x, double y) {
    _inheritanceSymbolPositions[parentName] = {'x': x, 'y': y};
    notifyListeners();
  }

  /// Crée le symbole héritage « placable » sur le canvas s'il n'existe pas encore (quand on ouvre le panneau Héritage).
  void ensureStandaloneInheritanceSymbol(double defaultX, double defaultY) {
    if (_inheritanceSymbolPositions.containsKey('_standalone')) return;
    _inheritanceSymbolPositions['_standalone'] = {'x': defaultX, 'y': defaultY};
    notifyListeners();
  }

  void clearInheritanceSymbolPosition(String parentName) {
    if (!_inheritanceSymbolPositions.containsKey(parentName)) return;
    _pushUndo();
    _inheritanceSymbolPositions.remove(parentName);
    notifyListeners();
  }

  /// Supprime tous les liens d'héritage dont le parent est [parentName].
  void removeInheritanceLinksForParent(String parentName) {
    final linksToRemove = _inheritanceLinks.where((l) => (l['parent'] as String?) == parentName).toList();
    if (linksToRemove.isEmpty) return;
    _pushUndo();
    final children = linksToRemove.map((l) => l['child'] as String?).whereType<String>().toSet().toList();
    _inheritanceLinks.removeWhere((l) => (l['parent'] as String?) == parentName);
    _inheritanceSymbolPositions.remove(parentName);
    for (final child in children) {
      _entities = _entities.map((e) => (e['name'] as String?) == child ? {...e, 'parent_entity': null} : Map<String, dynamic>.from(e)).toList();
    }
    notifyListeners();
  }

  void setCifConstraintPosition(int index, double x, double y) {
    if (index < 0 || index >= _cifConstraints.length) return;
    _cifConstraints[index] = {..._cifConstraints[index], 'position': {'x': x, 'y': y}};
    notifyListeners();
  }

  /// À appeler une fois au début d’un déplacement de symbole héritage (pour undo).
  void beginMoveInheritanceSymbol() => _pushUndo();

  /// À appeler une fois au début d’un déplacement de forme CIF (pour undo).
  void beginMoveCifConstraint() => _pushUndo();

  void _pushUndo() {
    _undoStack.add(_snapshot());
    if (_undoStack.length > _maxHistory) _undoStack.removeAt(0);
    _redoStack.clear();
  }

  Map<String, dynamic> _snapshot() {
    return {
      'entities': _entities.map(_copyEntityForSnapshot).toList(),
      'associations': _associations.map(_copyAssociationForSnapshot).toList(),
      'inheritance_links': _inheritanceLinks.map((l) => Map<String, dynamic>.from(l)).toList(),
      'association_links': _associationLinks.map((l) => Map<String, dynamic>.from(l)).toList(),
      'cif_constraints': _cifConstraints.map((c) => Map<String, dynamic>.from(c)).toList(),
      'inheritance_symbol_positions': _inheritanceSymbolPositions.map((k, v) => MapEntry(k, Map<String, double>.from(v))),
    };
  }

  static Map<String, dynamic> _copyEntityForSnapshot(Map<String, dynamic> e) {
    final out = Map<String, dynamic>.from(e);
    final pos = e['position'] as Map<String, dynamic>?;
    out['position'] = {
      'x': (pos?['x'] as num?)?.toDouble() ?? 0.0,
      'y': (pos?['y'] as num?)?.toDouble() ?? 0.0,
    };
    return out;
  }

  static Map<String, dynamic> _copyAssociationForSnapshot(Map<String, dynamic> a) {
    final out = Map<String, dynamic>.from(a);
    final pos = a['position'] as Map<String, dynamic>?;
    out['position'] = {
      'x': (pos?['x'] as num?)?.toDouble() ?? 0.0,
      'y': (pos?['y'] as num?)?.toDouble() ?? 0.0,
    };
    return out;
  }

  void _restore(Map<String, dynamic> snap) {
    _entities = (snap['entities'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ?? [];
    _associations = (snap['associations'] as List?)?.map((a) => Map<String, dynamic>.from(a as Map)).toList() ?? [];
    _inheritanceLinks = (snap['inheritance_links'] as List?)?.map((l) => Map<String, dynamic>.from(l as Map)).toList() ?? [];
    final rawLinks = (snap['association_links'] as List?)?.map((l) => Map<String, dynamic>.from(l as Map)).toList() ?? [];
    _associationLinks = rawLinks.map(_normalizeLink).toList();
    _cifConstraints = (snap['cif_constraints'] as List?)?.map((c) => Map<String, dynamic>.from(c as Map)).toList() ?? [];
    _inheritanceSymbolPositions.clear();
    final isp = snap['inheritance_symbol_positions'] as Map<String, dynamic>?;
    if (isp != null) for (final e in isp.entries) _inheritanceSymbolPositions[e.key] = Map<String, double>.from((e.value as Map).map((k, v) => MapEntry(k as String, (v as num).toDouble())));
    _selectedEntityIndices.clear();
    _selectedAssociationIndices.clear();
    _selectedLinkIndices.clear();
    _selectedInheritanceIndices.clear();
    notifyListeners();
  }

  /// Garantit card_entity, card_assoc, arm_index, entity_side (left|right|top|bottom), arrow_tip, entity_ratio, locks.
  static Map<String, dynamic> _normalizeLink(Map<String, dynamic> l) {
    try {
    final out = Map<String, dynamic>.from(l);
    final legacy = l['cardinality'] as String?;
    out['card_entity'] = l['card_entity'] as String? ?? legacy ?? '1,n';
    out['card_assoc'] = l['card_assoc'] as String? ?? '1,n';
    out['arm_index'] = (l['arm_index'] as num?)?.toInt() ?? 0;
    out['entity_arm_index'] = (l['entity_arm_index'] as num?)?.toInt() ?? 0;
    if (!out.containsKey('arrow_at_association')) out['arrow_at_association'] = false;
    const sides = ['left', 'right', 'top', 'bottom'];
    if (sides.contains(out['entity_side'])) {} else out.remove('entity_side');
    final tipX = (out['arrow_tip_x'] as num?)?.toDouble();
    final tipY = (out['arrow_tip_y'] as num?)?.toDouble();
    if (tipX == null || tipY == null) { out.remove('arrow_tip_x'); out.remove('arrow_tip_y'); }
    final ratio = (out['entity_ratio'] as num?)?.toDouble();
    if (ratio == null || ratio < 0 || ratio > 1) out['entity_ratio'] = 0.5;
    if (out['entity_attachment_locked'] != true) out['entity_attachment_locked'] = false;
    if (out['arm_attachment_locked'] != true) out['arm_attachment_locked'] = false;
    const lineStyles = ['straight', 'elbow_h', 'elbow_v'];
    if (!lineStyles.contains(out['line_style'])) out['line_style'] = 'straight';
    if (out['arrow_reversed'] != true) out['arrow_reversed'] = false;
    final sw = (out['stroke_width'] as num?)?.toDouble();
    if (sw == null || sw < 1 || sw > 6) out['stroke_width'] = 2.5;
    const arrowHeads = ['arrow', 'diamond', 'block', 'none'];
    if (!arrowHeads.contains(out['arrow_head'])) out['arrow_head'] = 'arrow';
    const startCaps = ['dot', 'diamond', 'square', 'none'];
    if (!startCaps.contains(out['start_cap'])) out['start_cap'] = 'dot';
    // Point de cassure (style JMerise) : optionnel, pour polyligne from → break → to.
    final breakX = (out['break_x'] as num?)?.toDouble();
    final breakY = (out['break_y'] as num?)?.toDouble();
    if (breakX == null || breakY == null) {
      out.remove('break_x');
      out.remove('break_y');
    } else {
      out['break_x'] = breakX;
      out['break_y'] = breakY;
    }
    return out;
    } catch (e, st) {
      debugPrint('[McdState] _normalizeLink ERROR: $e');
      debugPrint(st.toString());
      return Map<String, dynamic>.from(l);
    }
  }

  /// Met à jour le style d'affichage d'un lien (coudé, courbe, sens flèche, épaisseur, formes d'extrémité).
  void updateLinkStyle(int index, {String? lineStyle, bool? arrowReversed, double? strokeWidth, String? arrowHead, String? startCap}) {
    if (index < 0 || index >= _associationLinks.length) return;
    final link = Map<String, dynamic>.from(_associationLinks[index]);
    const lineStyles = ['straight', 'elbow_h', 'elbow_v'];
    if (lineStyle != null && lineStyles.contains(lineStyle)) link['line_style'] = lineStyle;
    if (arrowReversed != null) link['arrow_reversed'] = arrowReversed;
    if (strokeWidth != null && strokeWidth >= 1 && strokeWidth <= 6) link['stroke_width'] = strokeWidth;
    const arrowHeads = ['arrow', 'diamond', 'block', 'none'];
    if (arrowHead != null && arrowHeads.contains(arrowHead)) link['arrow_head'] = arrowHead;
    const startCaps = ['dot', 'diamond', 'square', 'none'];
    if (startCap != null && startCaps.contains(startCap)) link['start_cap'] = startCap;
    _associationLinks[index] = _normalizeLink(link);
    notifyListeners();
  }

  void undo() {
    if (_undoStack.isEmpty) return;
    _redoStack.add(_snapshot());
    _restore(_undoStack.removeLast());
    addLog('Annuler');
  }

  void redo() {
    if (_redoStack.isEmpty) return;
    _undoStack.add(_snapshot());
    _restore(_redoStack.removeLast());
    addLog('Répéter');
  }

  void addLog(String message) {
    _logMessages.add(message);
    if (_logMessages.length > 500) _logMessages = _logMessages.sublist(_logMessages.length - 500);
    notifyListeners();
  }

  void setError(String? e) {
    _lastError = e;
    notifyListeners();
  }

  void selectNone() {
    _selectedEntityIndices.clear();
    _selectedAssociationIndices.clear();
    _selectedLinkIndices.clear();
    _selectedInheritanceIndices.clear();
    notifyListeners();
  }

  void selectEntity(int index, {bool toggle = false}) {
    if (index < 0 || index >= _entities.length) return;
    if (toggle) {
      if (_selectedEntityIndices.contains(index)) {
        _selectedEntityIndices.remove(index);
      } else {
        _selectedEntityIndices.add(index);
      }
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
    } else {
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
      _selectedEntityIndices.add(index);
    }
    notifyListeners();
  }

  void selectAssociation(int index, {bool toggle = false}) {
    if (index < 0 || index >= _associations.length) return;
    if (toggle) {
      if (_selectedAssociationIndices.contains(index)) {
        _selectedAssociationIndices.remove(index);
      } else {
        _selectedAssociationIndices.add(index);
      }
      _selectedEntityIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
    } else {
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
      _selectedAssociationIndices.add(index);
    }
    notifyListeners();
  }

  void selectLink(int index, {bool toggle = false}) {
    if (index < 0 || index >= _associationLinks.length) return;
    if (toggle) {
      if (_selectedLinkIndices.contains(index)) {
        _selectedLinkIndices.remove(index);
      } else {
        _selectedLinkIndices.add(index);
      }
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedInheritanceIndices.clear();
    } else {
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
      _selectedLinkIndices.add(index);
    }
    notifyListeners();
  }

  void selectInheritance(int index, {bool toggle = false}) {
    if (index < 0 || index >= _inheritanceLinks.length) return;
    if (toggle) {
      if (_selectedInheritanceIndices.contains(index)) {
        _selectedInheritanceIndices.remove(index);
      } else {
        _selectedInheritanceIndices.add(index);
      }
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
    } else {
      _selectedEntityIndices.clear();
      _selectedAssociationIndices.clear();
      _selectedLinkIndices.clear();
      _selectedInheritanceIndices.clear();
      _selectedInheritanceIndices.add(index);
    }
    notifyListeners();
  }

  void selectAt(String type, int index) {
    if (type == 'entity') {
      selectEntity(index);
    } else if (type == 'association') {
      selectAssociation(index);
    } else if (type == 'link') {
      selectLink(index);
    } else if (type == 'inheritance') {
      selectInheritance(index);
    } else {
      selectNone();
    }
  }

  bool isEntitySelected(int index) => _selectedEntityIndices.contains(index);
  bool isAssociationSelected(int index) => _selectedAssociationIndices.contains(index);
  bool isLinkSelected(int index) => _selectedLinkIndices.contains(index);
  bool isInheritanceSelected(int index) => _selectedInheritanceIndices.contains(index);

  void loadFromCanvasFormat(Map<String, dynamic> data) {
    _pushUndo();
    clearMldMpdSqlCache();
    final rawEntities = (data['entities'] as List?) ?? [];
    final rawAssociations = (data['associations'] as List?) ?? [];
    _entities = List<Map<String, dynamic>>.from(
      rawEntities.map((e) => _normalizeLoadedEntity(Map<String, dynamic>.from(e as Map))),
    );
    _associations = List<Map<String, dynamic>>.from(
      rawAssociations.map((a) => _normalizeLoadedAssociation(Map<String, dynamic>.from(a as Map))),
    );
    _inheritanceLinks = List<Map<String, dynamic>>.from(
      (data['inheritance_links'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? [],
    );
    _associationLinks = List<Map<String, dynamic>>.from(
      (data['association_links'] as List?)?.map((e) => _normalizeLoadedLink(Map<String, dynamic>.from(e as Map))) ?? [],
    );
    _cifConstraints = List<Map<String, dynamic>>.from(
      (data['cif_constraints'] as List?)?.map((c) => Map<String, dynamic>.from(c as Map)) ?? [],
    );
    _inheritanceSymbolPositions.clear();
    final isp = data['inheritance_symbol_positions'] as Map<String, dynamic>?;
    if (isp != null && isp.isNotEmpty) for (final e in isp.entries) _inheritanceSymbolPositions[e.key] = Map<String, double>.from((e.value as Map).map((k, v) => MapEntry(k as String, (v as num).toDouble())));
    _selectedEntityIndices.clear();
    _selectedAssociationIndices.clear();
    _selectedLinkIndices.clear();
    _selectedInheritanceIndices.clear();
    notifyListeners();
  }

  static Map<String, dynamic> _normalizeLoadedEntity(Map<String, dynamic> e) {
    final out = Map<String, dynamic>.from(e);
    final pos = e['position'] as Map? ?? (e['x'] != null || e['y'] != null ? {'x': e['x'], 'y': e['y']} : null);
    out['position'] = {
      'x': (pos?['x'] as num?)?.toDouble() ?? 100.0,
      'y': (pos?['y'] as num?)?.toDouble() ?? 100.0,
    };
    out['id'] ??= 'e_${DateTime.now().millisecondsSinceEpoch}_${e['name']}';
    out['name'] ??= 'Entité';
    out['attributes'] = (out['attributes'] as List?)?.map((a) => Map<String, dynamic>.from(a as Map)).toList() ?? [];
    out['is_weak'] = e['is_weak'] == true;
    out['is_fictive'] = e['is_fictive'] == true;
    out['parent_entity'] = e['parent_entity'];
    final rawAngles = e['arm_angles'] as List?;
    out['arm_angles'] = rawAngles != null
        ? rawAngles.map((x) => (x as num).toDouble()).toList()
        : [0.0, 90.0, 180.0, 270.0];
    if (e['comment'] != null) out['comment'] = e['comment'];
    if (e['description'] != null) out['description'] = e['description'];
    return out;
  }

  static Map<String, dynamic> _normalizeLoadedLink(Map<String, dynamic> l) {
    final out = _normalizeLink(Map<String, dynamic>.from(l));
    out['arm_index'] = (l['arm_index'] as num?)?.toInt() ?? 0;
    out['entity_arm_index'] = (l['entity_arm_index'] as num?)?.toInt() ?? 0;
    return out;
  }

  static Map<String, dynamic> _normalizeLoadedAssociation(Map<String, dynamic> a) {
    final out = Map<String, dynamic>.from(a);
    final pos = a['position'] as Map? ?? (a['x'] != null || a['y'] != null ? {'x': a['x'], 'y': a['y']} : null);
    out['position'] = {
      'x': (pos?['x'] as num?)?.toDouble() ?? 300.0,
      'y': (pos?['y'] as num?)?.toDouble() ?? 300.0,
    };
    out['id'] ??= 'a_${DateTime.now().millisecondsSinceEpoch}_${a['name']}';
    out['name'] ??= 'Association';
    out['entities'] = List<String>.from(a['entities'] as List? ?? []);
    out['cardinalities'] = Map<String, String>.from(a['cardinalities'] as Map? ?? {});
    out['attributes'] = (out['attributes'] as List?) ?? [];
    final rawAngles = a['arm_angles'] as List?;
    out['arm_angles'] = rawAngles != null
        ? rawAngles.map((x) => (x as num).toDouble()).toList()
        : [0.0, 90.0, 180.0, 270.0];
    out['width'] = (a['width'] as num?)?.toDouble() ?? 260.0;
    out['height'] = (a['height'] as num?)?.toDouble() ?? 260.0;
    return out;
  }

  void addEntity(String name, double x, double y, {List<Map<String, dynamic>>? attributes}) {
    final trimmed = name.trim();
    if (trimmed.isEmpty) return;
    if (kDebugMode) debugPrint('[McdState] addEntity name=$trimmed x=$x y=$y');
    try {
      if (_entities.any((e) => (e['name'] as String?)?.trim() == trimmed)) {
        if (kDebugMode) debugPrint('[McdState] addEntity refusé: entité "$trimmed" existe déjà');
        return;
      }
      _pushUndo();
      clearMldMpdSqlCache();
      _entities.add({
        'id': 'e_${DateTime.now().millisecondsSinceEpoch}',
        'name': trimmed,
        'position': {'x': x.toDouble(), 'y': y.toDouble()},
        'attributes': attributes ?? [],
        'is_weak': false,
        'is_fictive': false,
        'parent_entity': null,
        'arm_angles': [0.0, 90.0, 180.0, 270.0],
        'width': 200.0,
      });
      addLog("Entité créée: $trimmed");
      notifyListeners();
      if (kDebugMode) debugPrint('[McdState] addEntity OK, total entities=${_entities.length}');
    } catch (e, st) {
      if (kDebugMode) {
        debugPrint('[McdState] addEntity ERROR: $e');
        debugPrint(st.toString());
      }
      rethrow;
    }
  }

  void addAssociation(String name, double x, double y) {
    final trimmed = name.trim();
    if (trimmed.isEmpty) return;
    if (kDebugMode) debugPrint('[McdState] addAssociation name=$trimmed x=$x y=$y');
    try {
      if (_associations.any((a) => (a['name'] as String?)?.trim() == trimmed)) {
        if (kDebugMode) debugPrint('[McdState] addAssociation refusé: association "$trimmed" existe déjà');
        return;
      }
      _pushUndo();
      clearMldMpdSqlCache();
      _associations.add({
        'id': 'a_${DateTime.now().millisecondsSinceEpoch}',
        'name': trimmed,
        'position': {'x': x.toDouble(), 'y': y.toDouble()},
        'attributes': [],
        'entities': [],
        'cardinalities': {},
        'arm_angles': [0.0, 90.0, 180.0, 270.0],
        'width': 260.0,
        'height': 260.0,
      });
      addLog("Association créée: $trimmed");
      notifyListeners();
      if (kDebugMode) debugPrint('[McdState] addAssociation OK, total associations=${_associations.length}');
    } catch (e, st) {
      if (kDebugMode) {
        debugPrint('[McdState] addAssociation ERROR: $e');
        debugPrint(st.toString());
      }
      rethrow;
    }
  }

  /// [arrowAtAssociation] true = tirage entité → association, pointe côté association.
  /// [arrowTipX], [arrowTipY] = point de relâchement en scène (pointe de flèche exactement là où l'utilisateur a relâché).
  /// [entitySide] = 'left' | 'right' selon le côté de l'entité d'où part (ou arrive) le lien.
  void addAssociationLink(String associationName, String entityName, String cardEntity, String cardAssoc, {
    bool arrowAtAssociation = false,
    double? arrowTipX,
    double? arrowTipY,
    String? entitySide,
  }) {
    final a = associationName.trim();
    final e = entityName.trim();
    if (a.isEmpty || e.isEmpty) return;
    final cEntity = _normalizeCardinality(cardEntity);
    final cAssoc = _normalizeCardinality(cardAssoc);
    if (_associationLinks.any((l) => (l['association'] as String?) == a && (l['entity'] as String?) == e)) {
      if (kDebugMode) debugPrint('[McdState] addAssociationLink: lien $a — $e existe déjà');
      return;
    }
    final linksForAssoc = _associationLinks.where((l) => (l['association'] as String?) == a).length;
    final linksForEntity = _associationLinks.where((l) => (l['entity'] as String?) == e).length;
    final assocIndex = _associations.indexWhere((x) => (x['name'] as String?) == a);
    final entityIndex = _entities.indexWhere((x) => (x['name'] as String?) == e);
    final assocMap = assocIndex >= 0 ? _associations[assocIndex] : null;
    final entityMap = entityIndex >= 0 ? _entities[entityIndex] : null;
    final armAngles = assocMap != null ? (assocMap['arm_angles'] as List?)?.cast<num>() ?? [0.0, 90.0, 180.0, 270.0] : [0.0, 90.0, 180.0, 270.0];
    final entityArmAngles = entityMap != null ? (_entities[entityIndex]['arm_angles'] as List?)?.cast<num>() ?? [0.0, 90.0, 180.0, 270.0] : [0.0, 90.0, 180.0, 270.0];
    // Bras le plus aligné vers l'entité (droite→gauche ou gauche→droite selon où est l'entité), pas 1er=bras0, 2e=bras1.
    final armIndex = (assocMap != null && entityMap != null)
        ? bestArmIndexForLink(assocMap, entityMap)
        : (linksForAssoc % armAngles.length);
    final entityArmIndex = (entityMap != null && assocMap != null)
        ? bestEntityArmIndexForLink(entityMap, assocMap)
        : (linksForEntity % entityArmAngles.length);
    _pushUndo();
    clearMldMpdSqlCache();
    final linkData = <String, dynamic>{
      'association': a,
      'entity': e,
      'card_entity': cEntity,
      'card_assoc': cAssoc,
      'arm_index': armIndex,
      'entity_arm_index': entityArmIndex,
      'arrow_at_association': arrowAtAssociation,
    };
    if (arrowTipX != null && arrowTipY != null) {
      linkData['arrow_tip_x'] = arrowTipX;
      linkData['arrow_tip_y'] = arrowTipY;
    }
    if (entitySide != null && const ['left', 'right', 'top', 'bottom'].contains(entitySide)) linkData['entity_side'] = entitySide;
    _associationLinks.add(_normalizeLink(linkData));
    _syncAssociationEntitiesFromLinks(a);
    addLog("Lien: $a — $e (entité: $cEntity, assoc: $cAssoc)");
    if (kDebugMode) debugPrint('[McdState] addAssociationLink OK: $a — $e armIndex=$armIndex entityArmIndex=$entityArmIndex arrowAtAssoc=$arrowAtAssociation');
    notifyListeners();
  }

  /// Met à jour association['entities'] pour refléter les liens actuels (une source de vérité).
  void _syncAssociationEntitiesFromLinks(String associationName) {
    final idx = _associations.indexWhere((x) => (x['name'] as String?) == associationName);
    if (idx < 0) return;
    final entityNames = _associationLinks
        .where((l) => (l['association'] as String?) == associationName)
        .map((l) => l['entity'] as String)
        .toSet()
        .toList();
    _associations[idx] = {..._associations[idx], 'entities': entityNames};
  }

  static const List<String> _mcdCardinalities = ['0,1', '1,1', '0,n', '1,n'];

  static String _normalizeCardinality(String c) {
    final s = c.trim().toLowerCase();
    if (_mcdCardinalities.contains(s)) return s;
    if (s == '1,n' || s == 'n,1') return '1,n';
    return '1,n';
  }

  void removeAssociationLinkAt(int index) {
    if (index < 0 || index >= _associationLinks.length) return;
    final link = _associationLinks[index];
    final assocName = link['association'] as String?;
    _pushUndo();
    clearMldMpdSqlCache();
    _associationLinks.removeAt(index);
    if (assocName != null) _syncAssociationEntitiesFromLinks(assocName);
    addLog('Lien supprimé');
    notifyListeners();
  }

  void moveEntity(int index, double x, double y) {
    if (index < 0 || index >= _entities.length) return;
    _entities[index] = {..._entities[index], 'position': {'x': x.toDouble(), 'y': y.toDouble()}};
    notifyListeners();
  }

  void moveAssociation(int index, double x, double y) {
    if (index < 0 || index >= _associations.length) return;
    _associations[index] = {..._associations[index], 'position': {'x': x.toDouble(), 'y': y.toDouble()}};
    notifyListeners();
  }

  /// Redimensionne la largeur d'une entité (min 120, max 400).
  void updateEntitySize(int index, double width) {
    if (index < 0 || index >= _entities.length) return;
    final w = width.clamp(120.0, 400.0);
    _entities[index] = {..._entities[index], 'width': w};
    notifyListeners();
  }

  void updateEntityAt(int index, Map<String, dynamic> entity) {
    if (index < 0 || index >= _entities.length) return;
    _pushUndo();
    clearMldMpdSqlCache();
    _entities[index] = Map<String, dynamic>.from(entity);
    notifyListeners();
  }

  /// Duplique une entité (nom "Copie de X", position décalée, nouvel id). Retourne l'index de la nouvelle entité.
  int duplicateEntity(int index) {
    if (index < 0 || index >= _entities.length) return -1;
    _pushUndo();
    clearMldMpdSqlCache();
    final src = _entities[index];
    final baseName = (src['name'] as String?)?.trim() ?? 'Entité';
    String newName = 'Copie de $baseName';
    int suffix = 1;
    while (_entities.any((e) => (e['name'] as String?)?.trim() == newName)) {
      newName = 'Copie de $baseName ($suffix)';
      suffix++;
    }
    final pos = src['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0.0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0.0;
    final copy = Map<String, dynamic>.from(src);
    copy['id'] = 'e_${DateTime.now().millisecondsSinceEpoch}';
    copy['name'] = newName;
    copy['position'] = {'x': x + 220.0, 'y': y + 100.0};
    copy['attributes'] = (src['attributes'] as List?)
        ?.map((a) => Map<String, dynamic>.from(a as Map))
        .toList() ?? [];
    _entities.add(copy);
    addLog('Entité dupliquée: $newName');
    notifyListeners();
    return _entities.length - 1;
  }

  void updateAssociationLinkCardinalities(int index, String cardEntity, String cardAssoc) {
    if (index < 0 || index >= _associationLinks.length) return;
    clearMldMpdSqlCache();
    _associationLinks[index] = {
      ..._associationLinks[index],
      'card_entity': _normalizeCardinality(cardEntity),
      'card_assoc': _normalizeCardinality(cardAssoc),
    };
    notifyListeners();
  }

  /// À appeler une fois au début d'un déplacement de poignée de lien (pour undo).
  void beginLinkAttachmentEdit() {
    _pushUndo();
  }

  /// Recalcule les accroches de tous les liens (entity_side, arm_index) selon les positions actuelles pour un rendu plus propre.
  /// Si [pushUndo] est false (ex. appel depuis applyAutoLayout), n'empile pas d'étape undo.
  void recenterLinks({bool pushUndo = true}) {
    if (_associationLinks.isEmpty) return;
    if (pushUndo) _pushUndo();
    clearMldMpdSqlCache();
    for (int i = 0; i < _associationLinks.length; i++) {
      final link = Map<String, dynamic>.from(_associationLinks[i]);
      final assocName = link['association'] as String?;
      final entityName = link['entity'] as String?;
      if (assocName == null || entityName == null) continue;
      Map<String, dynamic>? assoc;
      Map<String, dynamic>? ent;
      for (final a in _associations) { if ((a['name'] as String?) == assocName) { assoc = a; break; } }
      for (final e in _entities) { if ((e['name'] as String?) == entityName) { ent = e; break; } }
      if (assoc == null || ent == null) continue;
      final centerAssoc = associationCenter(assoc);
      final pos = ent['position'] as Map<String, dynamic>?;
      final ex = (pos?['x'] as num?)?.toDouble() ?? 0;
      final ey = (pos?['y'] as num?)?.toDouble() ?? 0;
      final w = (ent['width'] as num?)?.toDouble() ?? 200;
      final cx = ex + w / 2;
      final cy = ey + entityHeight(ent) / 2;
      final dx = centerAssoc.dx - cx;
      final dy = centerAssoc.dy - cy;
      link['entity_side'] = dx.abs() >= dy.abs() ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'bottom' : 'top');
      link['arm_index'] = bestArmIndexForLink(assoc, ent);
      _associationLinks[i] = _normalizeLink(link);
    }
    addLog('Liens recentrés');
    notifyListeners();
  }

  /// Applique un auto-layout (force-directed ou hiérarchique) puis recalcule les accroches des liens.
  /// [mode] : 'force' (Fruchterman-Reingold) ou 'hierarchical' (Sugiyama simplifié).
  void applyAutoLayout(String mode) {
    final allNodes = <LayoutNode>[];
    final edges = <({String a, String b})>[];
    final assocNames = {for (final a in _associations) (a['name'] as String?): true};

    for (final e in _entities) {
      final name = e['name'] as String? ?? '';
      final pos = e['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      final w = (e['width'] as num?)?.toDouble() ?? 200;
      final h = entityHeight(e);
      allNodes.add(LayoutNode(name, x + w / 2, y + h / 2, w / 2, h / 2));
    }
    for (final a in _associations) {
      final name = a['name'] as String? ?? '';
      final pos = a['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      final w = effectiveAssociationWidth(a);
      allNodes.add(LayoutNode(name, x + w / 2, y + w / 2, w / 2, w / 2));
    }
    // Pour le layout hiérarchique BarrelMCD : uniquement les liens association -> entité,
    // pour avoir deux couches nettes (entités en haut, associations en bas). Les liens d'héritage ne sont pas utilisés.
    for (final link in _associationLinks) {
      final ent = link['entity'] as String?;
      final assoc = link['association'] as String?;
      if (ent != null && assoc != null) edges.add((a: ent, b: assoc));
    }
    final edgesForHierarchical = List<({String a, String b})>.from(edges);
    // Pour le force-directed / circulaire on peut garder les mêmes arêtes ; pour hiérarchique on n'ajoute pas l'héritage
    for (final link in _inheritanceLinks) {
      final parent = link['parent'] as String?;
      final child = link['child'] as String?;
      if (parent != null && child != null) edges.add((a: parent, b: child));
    }

    if (allNodes.isEmpty) return;
    _pushUndo();
    clearMldMpdSqlCache();

    // Centrage du diagramme pour un rendu professionnel BarrelMCD.
    const targetCenter = Offset(450, 350);

    LayoutResult newCenters;
    if (mode == 'hierarchical') {
      newCenters = runHierarchicalLayout(
        nodes: allNodes,
        edges: edgesForHierarchical,
        isAssociation: (id) => assocNames[id] == true,
        targetCenter: targetCenter,
      );
    } else if (mode == 'circular') {
      newCenters = runCircularLayout(
        nodes: allNodes,
        targetCenter: targetCenter,
      );
    } else {
      newCenters = runForceDirectedLayout(
        nodes: allNodes,
        edges: edges,
        targetCenter: targetCenter,
      );
    }
    // S'assurer que chaque nœud a une position (fallback position actuelle si le layout en omet).
    final fullCenters = Map<String, Offset>.from(newCenters);
    for (final node in allNodes) {
      fullCenters.putIfAbsent(node.id, () => Offset(node.x, node.y));
    }
    newCenters = fullCenters;

    // Appliquer les nouvelles positions
    for (int i = 0; i < _entities.length; i++) {
      final e = _entities[i];
      final name = e['name'] as String? ?? '';
      final c = newCenters[name];
      final w = (e['width'] as num?)?.toDouble() ?? 200;
      final h = entityHeight(e);
      if (c != null) {
        _entities[i] = {...e, 'position': {'x': c.dx - w / 2, 'y': c.dy - h / 2}};
      }
    }
    for (int i = 0; i < _associations.length; i++) {
      final a = _associations[i];
      final name = a['name'] as String? ?? '';
      final c = newCenters[name];
      final w = effectiveAssociationWidth(a);
      if (c != null) {
        _associations[i] = {...a, 'position': {'x': c.dx - w / 2, 'y': c.dy - w / 2}};
      }
    }

    // Réinitialiser les pointes personnalisées des liens pour des traits droits (bord à bord).
    for (int i = 0; i < _associationLinks.length; i++) {
      final link = Map<String, dynamic>.from(_associationLinks[i]);
      link.remove('arrow_tip_x');
      link.remove('arrow_tip_y');
      _associationLinks[i] = _normalizeLink(link);
    }
    recenterLinks(pushUndo: false);
    final msg = mode == 'hierarchical'
        ? 'Auto-layout hiérarchique appliqué'
        : mode == 'circular'
            ? 'Auto-layout circulaire appliqué'
            : 'Auto-layout force-directed appliqué';
    addLog(msg);
    notifyListeners();
  }

  /// Propose des liens association–entité manquants selon la proximité (centre à centre).
  /// Pour chaque association, retourne jusqu'à [maxLinksPerAssociation] paires (association, entity)
  /// vers les entités les plus proches qui ne sont pas déjà liées à cette association.
  List<({String association, String entity})> suggestLinksByProximity({int maxLinksPerAssociation = 2}) {
    final result = <({String association, String entity})>[];
    for (final assoc in _associations) {
      final assocName = assoc['name'] as String? ?? '';
      final linkedEntities = _associationLinks
          .where((l) => (l['association'] as String?) == assocName)
          .map((l) => l['entity'] as String?)
          .whereType<String>()
          .toSet();
      final assocCenter = associationCenter(assoc);
      final candidates = <({String name, double dist})>[];
      for (final e in _entities) {
        final name = e['name'] as String? ?? '';
        if (linkedEntities.contains(name)) continue;
        final ec = entityCenterOffset(e);
        final dist = (ec.dx - assocCenter.dx) * (ec.dx - assocCenter.dx) +
            (ec.dy - assocCenter.dy) * (ec.dy - assocCenter.dy);
        candidates.add((name: name, dist: dist));
      }
      candidates.sort((a, b) => a.dist.compareTo(b.dist));
      for (var i = 0; i < candidates.length && i < maxLinksPerAssociation; i++) {
        result.add((association: assocName, entity: candidates[i].name));
      }
    }
    return result;
  }

  /// Applique les paramètres par défaut des flèches (marges + épaisseur) à tous les liens.
  void applyDefaultArrowParamsToAllLinks() {
    if (_associationLinks.isEmpty) return;
    _pushUndo();
    for (int i = 0; i < _associationLinks.length; i++) {
      _associationLinks[i] = {
        ..._associationLinks[i],
        'stroke_width': _defaultStrokeWidth,
      };
    }
    addLog('Paramètres par défaut des flèches appliqués à tous les liens');
    notifyListeners();
  }

  /// Améliore les liens sans déplacer les nœuds : supprime les pointes personnalisées puis recalcule les accroches.
  void improveLinksOnly() {
    if (_associationLinks.isEmpty) return;
    _pushUndo();
    clearMldMpdSqlCache();
    for (int i = 0; i < _associationLinks.length; i++) {
      final link = Map<String, dynamic>.from(_associationLinks[i]);
      link.remove('arrow_tip_x');
      link.remove('arrow_tip_y');
      _associationLinks[i] = _normalizeLink(link);
    }
    recenterLinks(pushUndo: false);
    addLog('Liens améliorés (accroches recentrées, pointes réinitialisées)');
    notifyListeners();
  }

  /// Applique l'épaisseur par défaut (defaultStrokeWidth) à tous les liens. Annulable.
  void applyDefaultStrokeWidthToAllLinks() {
    if (_associationLinks.isEmpty) return;
    _pushUndo();
    clearMldMpdSqlCache();
    final def = _defaultStrokeWidth.clamp(1.0, 6.0);
    for (int i = 0; i < _associationLinks.length; i++) {
      final link = Map<String, dynamic>.from(_associationLinks[i]);
      link['stroke_width'] = def;
      _associationLinks[i] = _normalizeLink(link);
    }
    addLog('Épaisseur par défaut appliquée à tous les liens');
    notifyListeners();
  }

  /// Met à jour les points d'accroche d'un lien (entité: side ; association: arm_index ; pointe: arrow_tip_x/y ; verrous).
  void updateAssociationLinkAttachment(int index, {
    int? armIndex,
    String? entitySide,
    double? entityRatio,
    double? arrowTipX,
    double? arrowTipY,
    bool? entityAttachmentLocked,
    bool? armAttachmentLocked,
  }) {
    if (index < 0 || index >= _associationLinks.length) return;
    final link = Map<String, dynamic>.from(_associationLinks[index]);
    if (armIndex != null) link['arm_index'] = armIndex;
    const sides = ['left', 'right', 'top', 'bottom'];
    if (entitySide != null && sides.contains(entitySide)) link['entity_side'] = entitySide;
    if (entityRatio != null && entityRatio >= 0 && entityRatio <= 1) link['entity_ratio'] = entityRatio;
    if (arrowTipX != null) link['arrow_tip_x'] = arrowTipX;
    if (arrowTipY != null) link['arrow_tip_y'] = arrowTipY;
    if (entityAttachmentLocked != null) link['entity_attachment_locked'] = entityAttachmentLocked;
    if (armAttachmentLocked != null) link['arm_attachment_locked'] = armAttachmentLocked;
    _associationLinks[index] = _normalizeLink(link);
    notifyListeners();
  }

  /// Met à jour le point de cassure d'un lien (polyline from → break → to). Passer null pour supprimer la cassure.
  void updateAssociationLinkBreakPoint(int index, double? breakX, double? breakY) {
    try {
      if (index < 0 || index >= _associationLinks.length) {
        debugPrint('[McdState] updateAssociationLinkBreakPoint index=$index out of range (length=${_associationLinks.length})');
        return;
      }
      final link = Map<String, dynamic>.from(_associationLinks[index]);
      if (breakX == null || breakY == null) {
        link.remove('break_x');
        link.remove('break_y');
      } else {
        link['break_x'] = breakX;
        link['break_y'] = breakY;
      }
      _associationLinks[index] = _normalizeLink(link);
      notifyListeners();
    } catch (e, st) {
      debugPrint('[McdState] updateAssociationLinkBreakPoint ERROR: $e');
      debugPrint(st.toString());
    }
  }

  /// Milieu du segment du lien (pour placer un point de cassure au centre). Retourne null si lien/entité/assoc introuvable.
  Offset? getLinkSegmentMidpoint(int linkIndex) {
    try {
      if (linkIndex < 0 || linkIndex >= _associationLinks.length) return null;
      final link = _associationLinks[linkIndex];
      final assocName = link['association'] as String?;
      final entityName = link['entity'] as String?;
      if (assocName == null || entityName == null) return null;
      Map<String, dynamic>? assoc;
      Map<String, dynamic>? entity;
      for (final a in _associations) {
        if (a['name'] == assocName) { assoc = a; break; }
      }
      for (final e in _entities) {
        if (e['name'] == entityName) { entity = e; break; }
      }
      if (assoc == null || entity == null) {
        debugPrint('[McdState] getLinkSegmentMidpoint: assoc=$assocName found=${assoc != null} entity=$entityName found=${entity != null}');
        return null;
      }
      final seg = getLinkSegment(assoc, entity, link);
      return Offset((seg.from.dx + seg.to.dx) / 2, (seg.from.dy + seg.to.dy) / 2);
    } catch (e, st) {
      debugPrint('[McdState] getLinkSegmentMidpoint($linkIndex) ERROR: $e');
      debugPrint(st.toString());
      return null;
    }
  }

  void addInheritanceLink(String parentName, String childName) {
    if (parentName == childName) return;
    if (_inheritanceLinks.any((l) => (l['child'] as String?) == childName)) return;
    _pushUndo();
    clearMldMpdSqlCache();
    _inheritanceLinks.add({'parent': parentName, 'child': childName});
    _entities = _entities.map((e) {
      if ((e['name'] as String?) == childName) return {...e, 'parent_entity': parentName};
      return Map<String, dynamic>.from(e);
    }).toList();
    addLog("Héritage: $childName hérite de $parentName");
    notifyListeners();
  }

  void removeInheritanceLinkAt(int index) {
    if (index < 0 || index >= _inheritanceLinks.length) return;
    final child = _inheritanceLinks[index]['child'] as String?;
    _pushUndo();
    clearMldMpdSqlCache();
    _inheritanceLinks.removeAt(index);
    if (child != null) {
      _entities = _entities.map((e) {
        if ((e['name'] as String?) == child) return {...e, 'parent_entity': null};
        return Map<String, dynamic>.from(e);
      }).toList();
    }
    addLog('Héritage supprimé');
    notifyListeners();
  }

  /// Ajoute une contrainte CIF/CIFF (type: functional, inter_association, unique, exclusion).
  void addCifConstraint(Map<String, dynamic> constraint) {
    _pushUndo();
    final name = (constraint['name'] as String?)?.trim() ?? 'CIF';
    final type = constraint['type'] as String?;
    const allowed = ['functional', 'inter_association', 'unique', 'exclusion'];
    final pos = constraint['position'] as Map<String, dynamic>?;
    _cifConstraints.add({
      'name': name,
      'type': allowed.contains(type) ? type : 'functional',
      'description': (constraint['description'] as String?)?.trim() ?? '',
      'entities': List<String>.from(constraint['entities'] as List? ?? []),
      'associations': List<String>.from(constraint['associations'] as List? ?? []),
      'attributes': List<String>.from(constraint['attributes'] as List? ?? []),
      'is_enabled': constraint['is_enabled'] != false,
      if (pos != null) 'position': Map<String, dynamic>.from(pos),
    });
    addLog('CIF ajoutée: $name');
    notifyListeners();
  }

  void removeCifConstraintAt(int index) {
    if (index < 0 || index >= _cifConstraints.length) return;
    _pushUndo();
    _cifConstraints.removeAt(index);
    addLog('CIF supprimée');
    notifyListeners();
  }

  void updateCifConstraintAt(int index, Map<String, dynamic> constraint) {
    if (index < 0 || index >= _cifConstraints.length) return;
    _pushUndo();
    const allowed = ['functional', 'inter_association', 'unique', 'exclusion'];
    final pos = constraint['position'] as Map<String, dynamic>?;
    final existing = _cifConstraints[index];
    _cifConstraints[index] = {
      'name': (constraint['name'] as String?)?.trim() ?? 'CIF',
      'type': allowed.contains(constraint['type'] as String?) ? constraint['type'] : 'functional',
      'description': (constraint['description'] as String?)?.trim() ?? '',
      'entities': List<String>.from(constraint['entities'] as List? ?? []),
      'associations': List<String>.from(constraint['associations'] as List? ?? []),
      'attributes': List<String>.from(constraint['attributes'] as List? ?? []),
      'is_enabled': constraint['is_enabled'] != false,
      'position': pos != null ? Map<String, dynamic>.from(pos) : (existing['position'] as Map<String, dynamic>?),
    };
    notifyListeners();
  }

  void updateAssociationAt(int index, Map<String, dynamic> association) {
    if (index < 0 || index >= _associations.length) return;
    _pushUndo();
    clearMldMpdSqlCache();
    final prev = _associations[index];
    final out = Map<String, dynamic>.from(association);
    out['arm_angles'] = association['arm_angles'] ?? prev['arm_angles'];
    out['width'] = (association['width'] as num?)?.toDouble() ?? (prev['width'] as num?)?.toDouble() ?? 260.0;
    out['height'] = (association['height'] as num?)?.toDouble() ?? (prev['height'] as num?)?.toDouble() ?? 260.0;
    _associations[index] = out;
    notifyListeners();
  }

  /// Met à jour la taille affichée de l'association (pour le dessin des liens).
  void updateAssociationSize(int index, double width, double height) {
    if (index < 0 || index >= _associations.length) return;
    _associations[index] = {..._associations[index], 'width': width, 'height': height};
    notifyListeners();
  }

  /// À appeler une fois au début d'une rotation de bras (pour undo).
  void beginArmAngleEdit() {
    _pushUndo();
  }

  /// Met à jour l'angle d'un bras (degrés). Ne fait rien si le bras est verrouillé. Ne pousse pas undo.
  void updateAssociationArmAngle(int index, int armIndex, double angleDegrees) {
    if (index < 0 || index >= _associations.length) return;
    final a = _associations[index];
    final locked = (a['arm_locked'] as List?)?.cast<bool>();
    if (locked != null && armIndex < locked.length && locked[armIndex]) return;
    final angles = List<double>.from((a['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()) ?? [0.0, 90.0, 180.0, 270.0]);
    if (armIndex < 0 || armIndex >= angles.length) return;
    angles[armIndex] = angleDegrees % 360;
    _associations[index] = {...a, 'arm_angles': angles};
    notifyListeners();
  }

  /// Met à jour l'angle d'un bras d'entité (degrés). 2 bras par défaut (gauche/droite), qui tournent autour du rectangle.
  void updateEntityArmAngle(int index, int armIndex, double angleDegrees) {
    if (index < 0 || index >= _entities.length) return;
    final ent = _entities[index];
    final angles = List<double>.from((ent['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()) ?? [0.0, 90.0, 180.0, 270.0]);
    if (armIndex < 0 || armIndex >= angles.length) return;
    angles[armIndex] = angleDegrees % 360;
    _entities[index] = {...ent, 'arm_angles': angles};
    notifyListeners();
  }

  /// Verrouille ou déverrouille un bras d'association (bloque la rotation quand verrouillé).
  void setAssociationArmLocked(int index, int armIndex, bool locked) {
    if (index < 0 || index >= _associations.length) return;
    final a = _associations[index];
    final angles = (a['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()).toList() ?? [0.0, 90.0, 180.0, 270.0];
    if (armIndex < 0 || armIndex >= angles.length) return;
    List<bool> locks = List<bool>.from((a['arm_locked'] as List?)?.cast<bool>() ?? List.filled(angles.length, false));
    if (locks.length != angles.length) locks = List.filled(angles.length, false);
    locks[armIndex] = locked;
    _associations[index] = {...a, 'arm_locked': locks};
    notifyListeners();
  }

  bool isAssociationArmLocked(int assocIndex, int armIndex) {
    if (assocIndex < 0 || assocIndex >= _associations.length) return false;
    final locks = (_associations[assocIndex]['arm_locked'] as List?)?.cast<bool>();
    if (locks == null || armIndex >= locks.length) return false;
    return locks[armIndex];
  }

  /// Fixe le nombre de bras (1, 2, 3, 4 ou plus). Répartit les angles uniformément. Réinitialise arm_locked.
  void setAssociationArmCount(int index, int count) {
    if (index < 0 || index >= _associations.length || count < 1) return;
    _pushUndo();
    final step = 360.0 / count;
    final angles = List.generate(count, (i) => (i * step) % 360.0);
    _associations[index] = {..._associations[index], 'arm_angles': angles, 'arm_locked': List.filled(count, false)};
    notifyListeners();
  }

  /// Supprime un bras. Les liens qui utilisaient un arm_index >= nouvelle longueur utilisent le dernier bras.
  void removeAssociationArm(int index, int armIndex) {
    if (index < 0 || index >= _associations.length) return;
    final angles = List<double>.from((_associations[index]['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()) ?? [0.0, 90.0, 180.0, 270.0]);
    if (armIndex < 0 || armIndex >= angles.length || angles.length <= 1) return;
    _pushUndo();
    angles.removeAt(armIndex);
    _associations[index] = {..._associations[index], 'arm_angles': angles};
    final assocName = _associations[index]['name'] as String?;
    for (final l in _associationLinks) {
      if (l['association'] != assocName) continue;
      int ai = (l['arm_index'] as num?)?.toInt() ?? 0;
      if (ai == armIndex) {
        l['arm_index'] = 0;
      } else if (ai > armIndex) {
        l['arm_index'] = ai - 1;
      }
    }
    notifyListeners();
  }

  /// Duplique une association (nom "Copie de X", position décalée, nouvel id).
  int duplicateAssociation(int index) {
    if (index < 0 || index >= _associations.length) return -1;
    _pushUndo();
    clearMldMpdSqlCache();
    final src = _associations[index];
    final baseName = (src['name'] as String?)?.trim() ?? 'Association';
    String newName = 'Copie de $baseName';
    int suffix = 1;
    while (_associations.any((a) => (a['name'] as String?)?.trim() == newName)) {
      newName = 'Copie de $baseName ($suffix)';
      suffix++;
    }
    final pos = src['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0.0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0.0;
    final copy = Map<String, dynamic>.from(src);
    copy['id'] = 'a_${DateTime.now().millisecondsSinceEpoch}';
    copy['name'] = newName;
    copy['position'] = {'x': x + 220.0, 'y': y + 100.0};
    copy['attributes'] = (src['attributes'] as List?)?.map((a) => Map<String, dynamic>.from(a as Map)).toList() ?? [];
    copy['entities'] = [];
    copy['cardinalities'] = {};
    copy['arm_angles'] = List<double>.from((src['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()) ?? [0.0, 90.0, 180.0, 270.0]);
    copy['width'] = (src['width'] as num?)?.toDouble() ?? 260.0;
    copy['height'] = (src['height'] as num?)?.toDouble() ?? 260.0;
    _associations.add(copy);
    addLog('Association dupliquée: $newName');
    notifyListeners();
    return _associations.length - 1;
  }

  void deleteSelected() {
    if (!hasSelection) return;
    _pushUndo();
    clearMldMpdSqlCache();

    // Suppression par ordre : héritages (indices décroissants), liens, associations, entités.
    final inhList = _selectedInheritanceIndices.toList()..sort((a, b) => b.compareTo(a));
    for (final i in inhList) {
      if (i >= 0 && i < _inheritanceLinks.length) {
        final child = _inheritanceLinks[i]['child'] as String?;
        _inheritanceLinks.removeAt(i);
        if (child != null) {
          _entities = _entities.map((e) {
            if ((e['name'] as String?) == child) return {...e, 'parent_entity': null};
            return Map<String, dynamic>.from(e);
          }).toList();
        }
      }
    }
    if (inhList.isNotEmpty) addLog('Héritage(s) supprimé(s)');

    final linkList = _selectedLinkIndices.toList()..sort((a, b) => b.compareTo(a));
    for (final i in linkList) {
      if (i >= 0 && i < _associationLinks.length) {
        final link = _associationLinks[i];
        _associationLinks.removeAt(i);
        final assocName = link['association'] as String?;
        if (assocName != null) _syncAssociationEntitiesFromLinks(assocName);
      }
    }
    if (linkList.isNotEmpty) addLog('Lien(s) supprimé(s)');

    final assocList = _selectedAssociationIndices.toList()..sort((a, b) => b.compareTo(a));
    final assocNamesToRemove = <String>{};
    for (final i in assocList) {
      if (i >= 0 && i < _associations.length) {
        assocNamesToRemove.add(_associations[i]['name'] as String? ?? '');
      }
    }
    for (final i in assocList) {
      if (i >= 0 && i < _associations.length) {
        _associations.removeAt(i);
      }
    }
    for (final name in assocNamesToRemove) {
      _associationLinks.removeWhere((l) => l['association'] == name);
    }
    if (assocList.isNotEmpty) addLog('Association(s) supprimée(s)');

    final entityList = _selectedEntityIndices.toList()..sort((a, b) => b.compareTo(a));
    final entityNamesToRemove = <String>{};
    for (final i in entityList) {
      if (i >= 0 && i < _entities.length) {
        entityNamesToRemove.add(_entities[i]['name'] as String? ?? '');
      }
    }
    for (final i in entityList) {
      if (i >= 0 && i < _entities.length) {
        _entities.removeAt(i);
      }
    }
    for (final name in entityNamesToRemove) {
      _associationLinks.removeWhere((l) => l['entity'] == name);
      _inheritanceLinks.removeWhere((l) => l['parent'] == name || l['child'] == name);
    }
    for (final a in _associations) _syncAssociationEntitiesFromLinks(a['name'] as String? ?? '');
    if (entityList.isNotEmpty) addLog('Entité(s) supprimée(s)');

    selectNone();
    notifyListeners();
  }

  void clear() {
    _pushUndo();
    clearMldMpdSqlCache();
    _cifConstraints = [];
    _inheritanceSymbolPositions.clear();
    _entities = [];
    _associations = [];
    _inheritanceLinks = [];
    _associationLinks = [];
    _selectedEntityIndices.clear();
    _selectedAssociationIndices.clear();
    _selectedLinkIndices.clear();
    _selectedInheritanceIndices.clear();
    addLog("Projet réinitialisé");
    notifyListeners();
  }

  String? getEntityNameByIndex(int index) {
    if (index < 0 || index >= _entities.length) return null;
    return _entities[index]['name'] as String?;
  }

  String? getAssociationNameByIndex(int index) {
    if (index < 0 || index >= _associations.length) return null;
    return _associations[index]['name'] as String?;
  }

  Future<Map<String, dynamic>?> parseMarkdown(String content) async {
    setError(null);
    try {
      final r = await _api.parseMarkdown(content);
      final canvas = r['canvas'] as Map<String, dynamic>?;
      if (canvas != null) loadFromCanvasFormat(canvas);
      return r;
    } on ApiException catch (e) {
      setError(e.body);
      return null;
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.parseMarkdown] API indisponible: $e\n$st');
      setError(null);
      return null;
    }
  }

  /// Parse « mots codés » (format BarrelMCD) ; retourne { canvas } sans modifier l'état tant qu'on n'appelle pas loadFromCanvasFormat.
  Future<Map<String, dynamic>?> parseMotsCodes(String content) async {
    setError(null);
    try {
      final r = await _api.parseMotsCodes(content);
      return r;
    } on ApiException catch (e) {
      setError(e.body);
      return null;
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.parseMotsCodes] API indisponible: $e\n$st');
      setError(null);
      return null;
    }
  }

  /// Valide le MCD courant ou [mcdOverride] si fourni (ex. canvas issu de mots codés non encore importé).
  Future<List<String>> validateMcd([Map<String, dynamic>? mcdOverride]) async {
    setError(null);
    try {
      final payload = mcdOverride ?? mcdData;
      final r = await _api.validateMcd(payload);
      return List<String>.from((r['errors'] as List?) ?? []);
    } on ApiException catch (e) {
      setError(e.body);
      return [];
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.validateMcd] API indisponible: $e\n$st');
      setError(null);
      return [];
    }
  }

  Future<String?> generateSql({String dbms = 'mysql'}) async {
    try {
      final r = await _api.mcdToSql(mcdData, dbms: dbms);
      final sql = r['sql'] as String?;
      if (sql != null && sql.isNotEmpty) _cachedSql[dbms] = sql;
      final sqlOriginal = r['sql_original'] as String?;
      if (sqlOriginal != null) _cachedSqlOriginal[dbms] = sqlOriginal;
      final tr = r['translations'] as List?;
      if (tr != null) _cachedSqlTranslations[dbms] = tr.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      setError(null);
      return sql;
    } on ApiException catch (e) {
      setError(e.body);
      return null;
    } catch (e, st) {
      if (kDebugMode) {
        if (_isConnectionRefused(e)) {
          debugPrint('[McdState.generateSql] API indisponible: connexion refusée');
        } else {
          debugPrint('[McdState.generateSql] ERROR: $e\n$st');
        }
      }
      setError(null);
      return null;
    }
  }

  static bool _isConnectionRefused(Object e) {
    final s = e.toString();
    return s.contains('Connexion refusée') || s.contains('Connection refused') || s.contains('SocketException');
  }

  Future<Map<String, dynamic>?> generateMld() async {
    try {
      final data = useInheritanceAndCifForTransposition ? mcdData : mcdDataForTransposition;
      if (kDebugMode) {
        debugPrint('[McdState.generateMld] entities=${(data['entities'] as List?)?.length ?? 0} associations=${(data['associations'] as List?)?.length ?? 0}');
      }
      final mld = await _api.mcdToMld(data);
      if (kDebugMode) debugPrint('[McdState.generateMld] response: ${mld != null ? "tables=${(mld['tables'] as Map?)?.length ?? 0}" : "null"}');
      if (mld != null) _cachedMld = Map<String, dynamic>.from(mld);
      setError(null);
      return mld;
    } on ApiException catch (e) {
      if (kDebugMode) debugPrint('[McdState.generateMld] ApiException: ${e.body}');
      setError(e.body);
      return null;
    } catch (e, st) {
      if (kDebugMode) {
        if (_isConnectionRefused(e)) {
          debugPrint('[McdState.generateMld] API indisponible: connexion refusée');
        } else {
          debugPrint('[McdState.generateMld] ERROR: $e\n$st');
        }
      }
      setError(null);
      return null;
    }
  }

  /// Génère le MPD (Modèle Physique de Données) à partir du MCD courant.
  Future<Map<String, dynamic>?> generateMpd({String dbms = 'mysql'}) async {
    try {
      final data = useInheritanceAndCifForTransposition ? mcdData : mcdDataForTransposition;
      if (kDebugMode) debugPrint('[McdState.generateMpd] dbms=$dbms entities=${(data['entities'] as List?)?.length ?? 0}');
      final r = await _api.mcdToMpd(data, dbms: dbms);
      final mpd = r['mpd'] as Map<String, dynamic>?;
      if (kDebugMode) debugPrint('[McdState.generateMpd] response: ${mpd != null ? "tables=${(mpd['tables'] as Map?)?.length ?? 0}" : "null"}');
      if (mpd != null) _cachedMpd[dbms] = Map<String, dynamic>.from(mpd);
      setError(null);
      return mpd;
    } on ApiException catch (e) {
      if (kDebugMode) debugPrint('[McdState.generateMpd] ApiException: ${e.body}');
      setError(e.body);
      return null;
    } catch (e, st) {
      if (kDebugMode) {
        if (_isConnectionRefused(e)) {
          debugPrint('[McdState.generateMpd] API indisponible: connexion refusée');
        } else {
          debugPrint('[McdState.generateMpd] ERROR: $e\n$st');
        }
      }
      setError(null);
      return null;
    }
  }

  /// Valide la création d'une association. Retourne la liste des erreurs (vide si OK).
  /// Si l'API est indisponible, retourne [] pour autoriser la création.
  Future<List<String>> validateCreateAssociation(String name) async {
    setError(null);
    try {
      final r = await _api.validateCreateAssociation(mcdData, name);
      return List<String>.from((r['errors'] as List?) ?? []);
    } on ApiException catch (e) {
      setError(e.body);
      return [e.body];
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.validateCreateAssociation] API indisponible: $e\n$st');
      setError(null);
      return [];
    }
  }

  /// Valide l'ajout d'un lien association–entité. Retourne la liste des erreurs (vide si OK).
  /// Si l'API est indisponible (ex. connexion refusée), retourne [] pour autoriser le lien.
  Future<List<String>> validateAddLink(
    String associationName,
    String entityName,
    String cardEntity,
    String cardAssoc,
  ) async {
    setError(null);
    try {
      final r = await _api.validateAddLink(
        mcdData,
        associationName,
        entityName,
        cardEntity,
        cardAssoc,
      );
      return List<String>.from((r['errors'] as List?) ?? []);
    } on ApiException catch (e) {
      setError(e.body);
      return [e.body];
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.validateAddLink] API indisponible: $e\n$st');
      setError(null);
      return [];
    }
  }

  /// Valide qu'après mise à jour (ex. ajout d'attributs), l'association reste cohérente (règle 1,1 + rubriques).
  Future<List<String>> validateAssociationAfterUpdate(
    String associationName,
    List<Map<String, dynamic>>? newAttributes,
  ) async {
    setError(null);
    try {
      final r = await _api.validateAssociationAfterUpdate(
        mcdData,
        associationName,
        newAttributes,
      );
      return List<String>.from((r['errors'] as List?) ?? []);
    } on ApiException catch (e) {
      setError(e.body);
      return [e.body];
    } catch (e, st) {
      if (kDebugMode) debugPrint('[McdState.validateAssociationAfterUpdate] API indisponible: $e\n$st');
      setError(null);
      return [];
    }
  }
}
