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
  List<Map<String, dynamic>> _associationLinks = [];
  List<String> _logMessages = [];
  String? _lastError;

  /// Sélection: index dans la liste correspondante, -1 si aucun. type: 'entity' | 'association' | 'link'
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
      'entities': _entities.map((e) => Map<String, dynamic>.from(e)).toList(),
      'associations': _associations.map((a) => Map<String, dynamic>.from(a)).toList(),
      'inheritance_links': _inheritanceLinks.map((l) => Map<String, dynamic>.from(l)).toList(),
      'association_links': _associationLinks.map((l) => Map<String, dynamic>.from(l)).toList(),
    };
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

  void selectAt(String type, int index) {
    if (type == 'entity') selectEntity(index);
    else if (type == 'association') selectAssociation(index);
    else if (type == 'link') selectLink(index);
    else selectNone();
  }

  bool isEntitySelected(int index) => _selectedType == 'entity' && _selectedIndex == index;
  bool isAssociationSelected(int index) => _selectedType == 'association' && _selectedIndex == index;
  bool isLinkSelected(int index) => _selectedType == 'link' && _selectedIndex == index;

  void loadFromCanvasFormat(Map<String, dynamic> data) {
    _pushUndo();
    _entities = List<Map<String, dynamic>>.from(
      (data['entities'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? [],
    );
    _associations = List<Map<String, dynamic>>.from(
      (data['associations'] as List?)?.map((e) => Map<String, dynamic>.from(e as Map)) ?? [],
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

  void addEntity(String name, double x, double y, {List<Map<String, dynamic>>? attributes}) {
    _pushUndo();
    _entities.add({
      'id': 'e_${DateTime.now().millisecondsSinceEpoch}',
      'name': name,
      'position': {'x': x, 'y': y},
      'attributes': attributes ?? [],
      'is_weak': false,
      'parent_entity': null,
    });
    addLog("Entité créée: $name");
    notifyListeners();
  }

  void addAssociation(String name, double x, double y) {
    _pushUndo();
    _associations.add({
      'id': 'a_${DateTime.now().millisecondsSinceEpoch}',
      'name': name,
      'position': {'x': x, 'y': y},
      'attributes': [],
      'entities': [],
      'cardinalities': {},
    });
    addLog("Association créée: $name");
    notifyListeners();
  }

  void addAssociationLink(String associationName, String entityName, String cardinality) {
    _pushUndo();
    _associationLinks.add({
      'association': associationName,
      'entity': entityName,
      'cardinality': cardinality,
    });
    addLog("Lien: $associationName — $entityName ($cardinality)");
    notifyListeners();
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
    _entities[index] = {..._entities[index], 'position': {'x': x, 'y': y}};
    notifyListeners();
  }

  void moveAssociation(int index, double x, double y) {
    if (index < 0 || index >= _associations.length) return;
    _associations[index] = {..._associations[index], 'position': {'x': x, 'y': y}};
    notifyListeners();
  }

  void updateEntityAt(int index, Map<String, dynamic> entity) {
    if (index < 0 || index >= _entities.length) return;
    _pushUndo();
    _entities[index] = Map<String, dynamic>.from(entity);
    notifyListeners();
  }

  void updateAssociationLinkCardinality(int index, String cardinality) {
    if (index < 0 || index >= _associationLinks.length) return;
    _associationLinks[index] = {..._associationLinks[index], 'cardinality': cardinality};
    notifyListeners();
  }

  void deleteSelected() {
    if (_selectedType == null) return;
    _pushUndo();
    if (_selectedType == 'entity') {
      if (_selectedIndex >= 0 && _selectedIndex < _entities.length) {
        final name = _entities[_selectedIndex]['name'] as String?;
        _entities.removeAt(_selectedIndex);
        _associationLinks.removeWhere((l) => l['entity'] == name);
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

  Future<List<String>> validateMcd() async {
    setError(null);
    try {
      final r = await _api.validateMcd(mcdData);
      return List<String>.from((r['errors'] as List?) ?? []);
    } on ApiException catch (e) {
      setError(e.body);
      return [];
    }
  }

  Future<String?> generateSql() async {
    setError(null);
    try {
      final r = await _api.mcdToSql(mcdData);
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
