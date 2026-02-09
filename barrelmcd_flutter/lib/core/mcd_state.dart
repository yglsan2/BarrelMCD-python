import 'api_client.dart';
import 'package:flutter/foundation.dart';

/// État global du MCD (entités, associations, liens) pour l'UI Flutter.
class McdState extends ChangeNotifier {
  McdState({required ApiClient api}) : _api = api;

  final ApiClient _api;
  static const int _maxHistory = 50;

  List<Map<String, dynamic>> _entities = [];
  List<Map<String, dynamic>> _associations = [];
  List<Map<String, dynamic>> _inheritanceLinks = [];
  /// Lien entre une association et une entité (côté Merise: association <-> entité avec cardinalité).
  /// Cardinalités MCD : 4 seulement — 0,1 | 1,1 | 0,n | 1,n
  List<Map<String, dynamic>> _associationLinks = [];
  List<String> _logMessages = [];
  String? _lastError;

  /// Sélection: index dans la liste correspondante, -1 si aucun. type: 'entity' | 'association' | 'link' | 'inheritance'
  String? _selectedType;
  int _selectedIndex = -1;
  String? get selectedType => _selectedType;
  int get selectedIndex => _selectedIndex;

  final List<Map<String, dynamic>> _undoStack = [];
  final List<Map<String, dynamic>> _redoStack = [];

  List<Map<String, dynamic>> get entities => List.unmodifiable(_entities);
  List<Map<String, dynamic>> get associations => List.unmodifiable(_associations);
  List<Map<String, dynamic>> get inheritanceLinks => List.unmodifiable(_inheritanceLinks);
  List<Map<String, dynamic>> get associationLinks => List.unmodifiable(_associationLinks);
  List<String> get logMessages => List.unmodifiable(_logMessages);
  String? get lastError => _lastError;
  bool get canUndo => _undoStack.isNotEmpty;
  bool get canRedo => _redoStack.isNotEmpty;

  /// Format MCD pour l'API: associations avec entities/cardinalities remplis depuis associationLinks.
  Map<String, dynamic> get mcdData {
    final assocWithLinks = <Map<String, dynamic>>[];
    for (final a in _associations) {
      final name = a['name'] as String? ?? '';
      final linksToThis = _associationLinks.where((l) => l['association'] == name).toList();
      final entityNames = linksToThis.map((l) => l['entity'] as String).toSet().toList();
      final cardinalities = <String, String>{};
      for (final l in linksToThis) {
        cardinalities[l['entity'] as String] = l['cardinality'] as String? ?? '1,n';
      }
      assocWithLinks.add({
        ...a,
        'entities': entityNames,
        'cardinalities': cardinalities,
      });
    }
    return {
      'entities': _entities,
      'associations': assocWithLinks,
      'inheritance_links': _inheritanceLinks,
      'association_links': _associationLinks,
    };
  }

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
    _associationLinks = (snap['association_links'] as List?)?.map((l) => Map<String, dynamic>.from(l as Map)).toList() ?? [];
    _selectedType = null;
    _selectedIndex = -1;
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
    _selectedType = null;
    _selectedIndex = -1;
    notifyListeners();
  }

  void selectEntity(int index) {
    if (index < 0 || index >= _entities.length) return;
    _selectedType = 'entity';
    _selectedIndex = index;
    notifyListeners();
  }

  void selectAssociation(int index) {
    if (index < 0 || index >= _associations.length) return;
    _selectedType = 'association';
    _selectedIndex = index;
    notifyListeners();
  }

  void selectLink(int index) {
    if (index < 0 || index >= _associationLinks.length) return;
    _selectedType = 'link';
    _selectedIndex = index;
    notifyListeners();
  }

  void selectInheritance(int index) {
    if (index < 0 || index >= _inheritanceLinks.length) return;
    _selectedType = 'inheritance';
    _selectedIndex = index;
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

  bool isEntitySelected(int index) => _selectedType == 'entity' && _selectedIndex == index;
  bool isAssociationSelected(int index) => _selectedType == 'association' && _selectedIndex == index;
  bool isLinkSelected(int index) => _selectedType == 'link' && _selectedIndex == index;
  bool isInheritanceSelected(int index) => _selectedType == 'inheritance' && _selectedIndex == index;

  void loadFromCanvasFormat(Map<String, dynamic> data) {
    _pushUndo();
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
      (data['association_links'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? [],
    );
    _selectedType = null;
    _selectedIndex = -1;
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
    if (e['comment'] != null) out['comment'] = e['comment'];
    if (e['description'] != null) out['description'] = e['description'];
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
      _entities.add({
        'id': 'e_${DateTime.now().millisecondsSinceEpoch}',
        'name': trimmed,
        'position': {'x': x.toDouble(), 'y': y.toDouble()},
        'attributes': attributes ?? [],
        'is_weak': false,
        'is_fictive': false,
        'parent_entity': null,
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
      _associations.add({
        'id': 'a_${DateTime.now().millisecondsSinceEpoch}',
        'name': trimmed,
        'position': {'x': x.toDouble(), 'y': y.toDouble()},
        'attributes': [],
        'entities': [],
        'cardinalities': {},
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

  void addAssociationLink(String associationName, String entityName, String cardinality) {
    final a = associationName.trim();
    final e = entityName.trim();
    if (a.isEmpty || e.isEmpty) return;
    final card = _normalizeCardinality(cardinality);
    if (_associationLinks.any((l) => (l['association'] as String?) == a && (l['entity'] as String?) == e)) {
      if (kDebugMode) debugPrint('[McdState] addAssociationLink: lien $a — $e existe déjà');
      return;
    }
    _pushUndo();
    _associationLinks.add({
      'association': a,
      'entity': e,
      'cardinality': card,
    });
    addLog("Lien: $a — $e ($card)");
    notifyListeners();
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
    _pushUndo();
    _associationLinks.removeAt(index);
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

  void updateEntityAt(int index, Map<String, dynamic> entity) {
    if (index < 0 || index >= _entities.length) return;
    _pushUndo();
    _entities[index] = Map<String, dynamic>.from(entity);
    notifyListeners();
  }

  /// Duplique une entité (nom "Copie de X", position décalée, nouvel id). Retourne l'index de la nouvelle entité.
  int duplicateEntity(int index) {
    if (index < 0 || index >= _entities.length) return -1;
    _pushUndo();
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

  void updateAssociationLinkCardinality(int index, String cardinality) {
    if (index < 0 || index >= _associationLinks.length) return;
    _associationLinks[index] = {..._associationLinks[index], 'cardinality': cardinality};
    notifyListeners();
  }

  void addInheritanceLink(String parentName, String childName) {
    if (parentName == childName) return;
    if (_inheritanceLinks.any((l) => (l['child'] as String?) == childName)) return;
    _pushUndo();
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

  void updateAssociationAt(int index, Map<String, dynamic> association) {
    if (index < 0 || index >= _associations.length) return;
    _pushUndo();
    _associations[index] = Map<String, dynamic>.from(association);
    notifyListeners();
  }

  /// Duplique une association (nom "Copie de X", position décalée, nouvel id).
  int duplicateAssociation(int index) {
    if (index < 0 || index >= _associations.length) return -1;
    _pushUndo();
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
    _associations.add(copy);
    addLog('Association dupliquée: $newName');
    notifyListeners();
    return _associations.length - 1;
  }

  void deleteSelected() {
    if (_selectedType == null) return;
    _pushUndo();
    if (_selectedType == 'entity') {
      if (_selectedIndex >= 0 && _selectedIndex < _entities.length) {
        final name = _entities[_selectedIndex]['name'] as String?;
        _entities.removeAt(_selectedIndex);
        _associationLinks.removeWhere((l) => l['entity'] == name);
        _inheritanceLinks.removeWhere((l) => l['parent'] == name || l['child'] == name);
        addLog('Entité supprimée: $name');
      }
    } else if (_selectedType == 'association') {
      if (_selectedIndex >= 0 && _selectedIndex < _associations.length) {
        final name = _associations[_selectedIndex]['name'] as String?;
        _associations.removeAt(_selectedIndex);
        _associationLinks.removeWhere((l) => l['association'] == name);
        addLog('Association supprimée: $name');
      }
    } else if (_selectedType == 'link') {
      if (_selectedIndex >= 0 && _selectedIndex < _associationLinks.length) {
        _associationLinks.removeAt(_selectedIndex);
        addLog('Lien supprimé');
      }
    } else if (_selectedType == 'inheritance') {
      if (_selectedIndex >= 0 && _selectedIndex < _inheritanceLinks.length) {
        removeInheritanceLinkAt(_selectedIndex);
      }
    }
    _selectedType = null;
    _selectedIndex = -1;
    notifyListeners();
  }

  void clear() {
    _pushUndo();
    _entities = [];
    _associations = [];
    _inheritanceLinks = [];
    _associationLinks = [];
    _selectedType = null;
    _selectedIndex = -1;
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
    }
  }

  /// Parse « mots codés » (style Mocodo) ; retourne { canvas } sans modifier l'état tant qu'on n'appelle pas loadFromCanvasFormat.
  Future<Map<String, dynamic>?> parseMotsCodes(String content) async {
    setError(null);
    try {
      final r = await _api.parseMotsCodes(content);
      return r;
    } on ApiException catch (e) {
      setError(e.body);
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
    }
  }

  Future<String?> generateSql({String dbms = 'mysql'}) async {
    setError(null);
    try {
      final r = await _api.mcdToSql(mcdData, dbms: dbms);
      return r['sql'] as String?;
    } on ApiException catch (e) {
      setError(e.body);
      return null;
    }
  }

  Future<Map<String, dynamic>?> generateMld() async {
    setError(null);
    try {
      return await _api.mcdToMld(mcdData);
    } on ApiException catch (e) {
      setError(e.body);
      return null;
    }
  }
}
