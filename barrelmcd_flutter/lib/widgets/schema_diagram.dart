import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Données d'une table pour le schéma (MLD ou MPD).
class SchemaTableInfo {
  SchemaTableInfo({
    required this.name,
    required this.columns,
    required this.primaryKey,
    this.rect = Rect.zero,
  });
  final String name;
  final List<Map<String, dynamic>> columns;
  final List<String> primaryKey;
  Rect rect;
}

/// Lien FK pour le dessin.
class SchemaFkLink {
  SchemaFkLink({
    required this.fromTable,
    required this.toTable,
    required this.column,
    required this.referencedColumn,
  });
  final String fromTable;
  final String toTable;
  final String column;
  final String referencedColumn;
}

const double _cardWidth = 200.0;
const double _headerHeight = 28.0;
const double _rowHeight = 22.0;
const double _padding = 12.0;

/// Style graphique Barrel : zone claire, cartes blanches, liens nets (qualité d’image et de dessin).
class _BarrelDiagramStyle {
  static const Color diagramBackground = Color(0xFFF5F4F0);   // Zone graphique (fond)
  static const Color tableCardBg = Color(0xFFFFFFFF);         // Couleur table MLD
  static const Color tableCardBorder = Color(0xFF6B6B6B);    // Bordure table
  static const Color tableHeaderBg = Color(0xFFE2E8F0);      // En-tête de table
  static const Color tableHeaderBorder = Color(0xFF94A3B8);
  static const Color textPrimary = Color(0xFF1E293B);
  static const Color textSecondary = Color(0xFF64748B);       // Types
  static const Color linkStroke = Color(0xFF334155);         // Arcs FK
  static const Color pkAccent = Color(0xFF0F766E);            // # clé primaire
}

/// Normalise une colonne (peut être un Map ou un String nom de colonne).
Map<String, dynamic> _normalizeColumn(dynamic c) {
  if (c is Map<String, dynamic>) return c;
  if (c is Map) return Map<String, dynamic>.from(c);
  return {'name': c?.toString() ?? '', 'type': ''};
}

/// Extrait tables + FK depuis data (API MLD/MPD). Accepte tables en Map ou List.
({List<SchemaTableInfo> tables, List<SchemaFkLink> fks}) _parseSchemaData(Map<String, dynamic>? data) {
  final tables = <SchemaTableInfo>[];
  final fks = <SchemaFkLink>[];
  if (data == null || data is! Map) return (tables: tables, fks: fks);

  final rawTables = data['tables'];
  final rawFks = data['foreign_keys'];
  final fkList = rawFks is List ? rawFks : <dynamic>[];

  final Map<String, dynamic> tableMap = {};
  if (rawTables is Map<String, dynamic>) {
    tableMap.addAll(rawTables);
  } else if (rawTables is Map) {
    for (final e in rawTables.entries) {
      tableMap[e.key.toString()] = e.value is Map ? Map<String, dynamic>.from(e.value as Map) : <String, dynamic>{};
    }
  } else if (rawTables is List) {
    for (int i = 0; i < rawTables.length; i++) {
      final t = rawTables[i];
      if (t is Map) {
        final name = (t['name'] as String?) ?? 'table_$i';
        tableMap[name] = Map<String, dynamic>.from(t as Map);
      }
    }
  }

  for (final e in tableMap.entries) {
    try {
      final name = e.key.toString();
      final t = e.value;
      final rawCols = t['columns'];
      final colList = rawCols is List ? rawCols : <dynamic>[];
      final cols = colList.map((c) => _normalizeColumn(c)).toList();
      final pkRaw = t['primary_key'];
      final pkList = pkRaw is List ? pkRaw : <dynamic>[];
      final pk = pkList.map((x) => x.toString()).toList();
      tables.add(SchemaTableInfo(name: name, columns: cols, primaryKey: pk));
    } catch (_) { /* ignorer cette table si données inattendues */ }
  }

  for (final f in fkList) {
    try {
      final m = f is Map ? (f as Map).map((k, v) => MapEntry(k.toString(), v)) : <String, dynamic>{};
      final from = m['table'] as String?;
      final to = m['referenced_table'] as String?;
      final col = m['column'] as String? ?? '';
      final ref = m['referenced_column'] as String? ?? 'id';
      if (from != null && to != null && from.isNotEmpty && to.isNotEmpty) {
        fks.add(SchemaFkLink(fromTable: from, toTable: to, column: col, referencedColumn: ref));
      }
    } catch (_) { /* ignorer cette FK */ }
  }
  return (tables: tables, fks: fks);
}

/// Calcule le layout des tables (grille) et retourne les infos + dimensions totales.
({List<SchemaTableInfo> tables, List<SchemaFkLink> fks, double width, double height}) layoutSchema(
  Map<String, dynamic>? data,
) {
  final parsed = _parseSchemaData(data);
  final tables = parsed.tables;
  final fks = parsed.fks;
  if (tables.isEmpty) return (tables: tables, fks: fks, width: 400, height: 300);

  const gapX = 80.0;
  const gapY = 60.0;

  const colCount = 2;
  double maxW = 0;
  double maxH = 0;
  for (int i = 0; i < tables.length; i++) {
    final t = tables[i];
    final rowCount = t.columns.length;
    final h = (_headerHeight + rowCount * _rowHeight + _padding * 2).clamp(40.0, 2000.0);
    final row = i ~/ colCount;
    final col = i % colCount;
    final x = _padding + col * (_cardWidth + gapX);
    final y = _padding + row * (h + gapY);
    t.rect = Rect.fromLTWH(x, y, _cardWidth, h);
    if (x + _cardWidth > maxW) maxW = x + _cardWidth;
    if (y + h > maxH) maxH = y + h;
  }

  return (tables: tables, fks: fks, width: maxW + _padding, height: maxH + _padding);
}

/// Retourne les noms d'entités liées à une association (depuis [associationLinks] ou champ entities).
List<String> _entitiesForAssociation(
  Map<String, dynamic> association,
  List<Map<String, dynamic>>? associationLinks,
) {
  if (associationLinks != null && associationLinks.isNotEmpty) {
    final name = association['name'] as String? ?? '';
    final linked = associationLinks
        .where((l) => (l['association'] as String? ?? '') == name)
        .map((l) => l['entity'] as String? ?? '')
        .where((s) => s.isNotEmpty)
        .toSet()
        .toList();
    if (linked.isNotEmpty) return linked;
  }
  return (association['entities'] as List?)?.map((e) => e.toString()).toList() ?? [];
}

/// Parse une valeur en double (num, int ou String), sans lever d'exception.
double? _safeToDouble(dynamic v) {
  if (v == null) return null;
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v);
  return null;
}

/// Extrait un Offset depuis position (Map avec x,y ou List [x,y]) — évite les erreurs de cast (API / JSON).
Offset? _safePositionOffset(dynamic position) {
  if (position == null) return null;
  if (position is Map) {
    final x = _safeToDouble(position['x']);
    final y = _safeToDouble(position['y']);
    if (x != null && y != null && x.isFinite && y.isFinite) return Offset(x, y);
    return null;
  }
  if (position is List && position.length >= 2) {
    final x = _safeToDouble(position[0]);
    final y = _safeToDouble(position[1]);
    if (x != null && y != null && x.isFinite && y.isFinite) return Offset(x, y);
    return null;
  }
  return null;
}

/// Retourne le centre (x, y) d'une entité ou d'une association depuis le MCD (photo du MCD).
Offset? _mcdPositionForTable(
  String tableName,
  List<Map<String, dynamic>> entities,
  List<Map<String, dynamic>> associations,
  List<Map<String, dynamic>>? associationLinks,
) {
  final nameLower = tableName.toLowerCase();
  for (final e in entities) {
    if (e is! Map) continue;
    if ((e['name'] as String? ?? '').toLowerCase() == nameLower) {
      return _safePositionOffset(e['position']);
    }
  }
  final assocNameSanitized = nameLower.replaceAll(RegExp(r'[^\w\s]'), '').replaceAll(' ', '_');
  for (final a in associations) {
    if (a is! Map) continue;
    final an = (a['name'] as String? ?? '').toLowerCase().replaceAll(RegExp(r'[^\w\s]'), '').replaceAll(' ', '_');
    if (an == assocNameSanitized) {
      return _safePositionOffset(a['position']);
    }
  }
  final parts = nameLower.split('_');
  if (parts.length >= 2) {
    final e1 = parts[0], e2 = parts[1];
    for (final a in associations) {
      if (a is! Map) continue;
      final ents = _entitiesForAssociation(a, associationLinks);
      if (ents.length >= 2) {
        final e1m = ents[0].toLowerCase();
        final e2m = ents[1].toLowerCase();
        if ((e1m == e1 && e2m == e2) || (e1m == e2 && e2m == e1)) {
          return _safePositionOffset(a['position']);
        }
      }
    }
  }
  return null;
}

/// Calcule le layout MLD en réutilisant les positions du MCD (« photo du MCD »).
/// [mcdAssociationLinks] permet de déduire les entités par association pour placer les tables de liaison (n:n).
({List<SchemaTableInfo> tables, List<SchemaFkLink> fks, double width, double height}) layoutSchemaFromMcd(
  Map<String, dynamic>? data,
  List<Map<String, dynamic>> mcdEntities,
  List<Map<String, dynamic>> mcdAssociations, [
  List<Map<String, dynamic>>? mcdAssociationLinks,
]) {
  final result = layoutSchema(data);
  if (result.tables.isEmpty || (mcdEntities.isEmpty && mcdAssociations.isEmpty)) {
    return result;
  }
  final positions = <String, Offset>{};
  for (final t in result.tables) {
    final pos = _mcdPositionForTable(t.name, mcdEntities, mcdAssociations, mcdAssociationLinks);
    if (pos != null) positions[t.name] = pos;
  }
  if (positions.isEmpty) return result;

  double minX = double.infinity, minY = double.infinity;
  double maxX = double.negativeInfinity, maxY = double.negativeInfinity;
  for (final t in result.tables) {
    final center = positions[t.name];
    if (center == null) continue;
    final rowCount = t.columns.length;
    final h = _headerHeight + rowCount * _rowHeight + _padding * 2;
    final halfW = _cardWidth / 2, halfH = h / 2;
    minX = math.min(minX, center.dx - halfW);
    minY = math.min(minY, center.dy - halfH);
    maxX = math.max(maxX, center.dx + halfW);
    maxY = math.max(maxY, center.dy + halfH);
  }
  final offsetX = minX.isFinite ? minX : 0.0;
  final offsetY = minY.isFinite ? minY : 0.0;
  final rightEdge = maxX.isFinite ? maxX - offsetX : 0.0;
  double fallbackX = rightEdge + _padding;
  double fallbackY = _padding;
  for (final t in result.tables) {
    final center = positions[t.name];
    final rowCount = t.columns.length;
    final h = (_headerHeight + rowCount * _rowHeight + _padding * 2).clamp(40.0, 2000.0);
    final w = _cardWidth.clamp(80.0, 800.0);
    if (center != null) {
      t.rect = Rect.fromCenter(
        center: Offset(center.dx - offsetX, center.dy - offsetY),
        width: w,
        height: h,
      );
    } else {
      t.rect = Rect.fromLTWH(fallbackX, fallbackY, w, h);
      fallbackX += w + _padding;
    }
  }
  double extentW = 400.0;
  double extentH = 300.0;
  if (maxX.isFinite && minX.isFinite) extentW = (maxX - minX) + _padding * 2;
  if (maxY.isFinite && minY.isFinite) extentH = (maxY - minY) + _padding * 2;
  if (fallbackX > extentW) extentW = fallbackX + _cardWidth;
  extentW = extentW.clamp(400.0, 10000.0);
  extentH = extentH.clamp(300.0, 10000.0);
  return (tables: result.tables, fks: result.fks, width: extentW, height: extentH);
}

/// Peint les lignes de liaison (clés étrangères) entre les tables — style Barrel (qualité dessin).
class _SchemaLinesPainter extends CustomPainter {
  _SchemaLinesPainter({required this.tables, required this.fks});

  final List<SchemaTableInfo> tables;
  final List<SchemaFkLink> fks;

  @override
  void paint(Canvas canvas, Size size) {
    final nameToRect = {for (final t in tables) t.name: t.rect};

    final paint = Paint()
      ..color = _BarrelDiagramStyle.linkStroke
      ..strokeWidth = 1.8
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..isAntiAlias = true;

    const arrowSize = 9.0;

    for (final fk in fks) {
      final fromRect = nameToRect[fk.fromTable];
      final toRect = nameToRect[fk.toTable];
      if (fromRect == null || toRect == null) continue;

      final fromCenter = fromRect.center;
      final toCenter = toRect.center;
      final fromRight = fromRect.right > toRect.left;
      final start = Offset(
        fromRight ? fromRect.right : fromRect.left,
        fromCenter.dy,
      );
      final end = Offset(
        fromRight ? toRect.left : toRect.right,
        toCenter.dy,
      );

      // Arc lisse (Bézier)
      final midX = (start.dx + end.dx) / 2;
      final path = Path()
        ..moveTo(start.dx, start.dy)
        ..cubicTo(midX, start.dy, midX, end.dy, end.dx, end.dy);
      canvas.drawPath(path, paint);

      // Flèche nette côté table référencée (pointe vers la table)
      final dir = (end.dx - start.dx).sign;
      final arrowTip = Offset(end.dx, end.dy);
      final back = Offset(arrowTip.dx + dir * arrowSize, arrowTip.dy);
      final arrowPath = Path()
        ..moveTo(arrowTip.dx, arrowTip.dy)
        ..lineTo(back.dx, back.dy - arrowSize * 0.6)
        ..lineTo(back.dx, back.dy + arrowSize * 0.6)
        ..close();
      canvas.drawPath(arrowPath, Paint()
        ..color = _BarrelDiagramStyle.linkStroke
        ..style = PaintingStyle.fill
        ..isAntiAlias = true);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => true;
}

/// Carte d'une table (nom + colonnes) pour le schéma MLD/MPD — style Barrel.
/// Règles Merise : MLD = pas de types ; MPD = types. PK = # + gras ; FK = # + italique.
class _TableCard extends StatelessWidget {
  const _TableCard({
    required this.name,
    required this.columns,
    required this.primaryKey,
    this.foreignKeyColumns = const {},
    this.showTypes = true,
  });

  final String name;
  final List<Map<String, dynamic>> columns;
  final List<String> primaryKey;
  /// Noms des colonnes qui sont clés étrangères (affichées # + italique en MLD/MPD).
  final Set<String> foreignKeyColumns;
  final bool showTypes;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      decoration: BoxDecoration(
        color: _BarrelDiagramStyle.tableCardBg,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: _BarrelDiagramStyle.tableCardBorder, width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.12),
            blurRadius: 4,
            offset: const Offset(1, 1),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: BoxDecoration(
              color: _BarrelDiagramStyle.tableHeaderBg,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(3)),
              border: const Border(
                bottom: BorderSide(color: _BarrelDiagramStyle.tableHeaderBorder, width: 1),
              ),
            ),
            child: Text(
              name,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: _BarrelDiagramStyle.textPrimary,
                fontSize: 13,
                letterSpacing: 0.2,
              ),
            ),
          ),
          ...columns.asMap().entries.map((entry) {
            final c = entry.value;
            final isLastRow = entry.key == columns.length - 1;
            final colName = c['name'] as String? ?? '';
            final colType = c['type'] as String? ?? '';
            final isPk = primaryKey.contains(colName);
            final isFk = foreignKeyColumns.contains(colName);
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                border: isLastRow ? null : Border(
                  bottom: BorderSide(
                    color: _BarrelDiagramStyle.tableCardBorder.withOpacity(0.35),
                    width: 0.8,
                  ),
                ),
              ),
              child: Row(
                children: [
                  if (isPk || isFk)
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: Text(
                        '#',
                        style: TextStyle(
                          fontWeight: isPk ? FontWeight.w700 : FontWeight.w500,
                          color: _BarrelDiagramStyle.pkAccent,
                          fontSize: 12,
                          fontFamily: 'monospace',
                          fontStyle: isFk ? FontStyle.italic : FontStyle.normal,
                        ),
                      ),
                    ),
                  Expanded(
                    child: Text(
                      colName,
                      style: TextStyle(
                        color: _BarrelDiagramStyle.textPrimary,
                        fontSize: 12,
                        fontWeight: isPk ? FontWeight.w600 : FontWeight.normal,
                        fontStyle: isFk ? FontStyle.italic : FontStyle.normal,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (showTypes && colType.isNotEmpty)
                    Text(
                      colType,
                      style: const TextStyle(
                        color: _BarrelDiagramStyle.textSecondary,
                        fontSize: 10,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

/// Schéma graphique MLD ou MPD (tables + liaisons FK), style Barrel.
/// Si [mcdEntities] et [mcdAssociations] sont fournis, le MLD est affiché aux mêmes positions que le MCD (« photo du MCD »).
/// [mcdAssociationLinks] sert à placer les tables de liaison (n:n) sur l'association correspondante.
class SchemaDiagramView extends StatelessWidget {
  const SchemaDiagramView({
    super.key,
    required this.data,
    this.title = 'Schéma',
    this.showTypes = true,
    this.mcdEntities = const [],
    this.mcdAssociations = const [],
    this.mcdAssociationLinks,
  });

  final Map<String, dynamic>? data;
  final String title;
  final bool showTypes;
  /// Positions des entités MCD pour calquer le layout MLD.
  final List<Map<String, dynamic>> mcdEntities;
  /// Positions des associations MCD (tables de correspondance).
  final List<Map<String, dynamic>> mcdAssociations;
  /// Liens association ↔ entité pour déduire les entités par association (tables de liaison).
  final List<Map<String, dynamic>>? mcdAssociationLinks;

  @override
  Widget build(BuildContext context) {
    try {
      final layout = (mcdEntities.isNotEmpty || mcdAssociations.isNotEmpty)
          ? layoutSchemaFromMcd(data, mcdEntities, mcdAssociations, mcdAssociationLinks)
          : layoutSchema(data);
      if (layout.tables.isEmpty) {
        final d = data;
        if (d != null && (d['tables'] != null || d['foreign_keys'] != null)) {
          debugPrint('[SchemaDiagramView] data non null mais tables vides après parse: keys=${d.keys.toList()} tables type=${d['tables'].runtimeType}');
        }
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.table_chart, size: 48, color: AppTheme.textTertiary),
              const SizedBox(height: 12),
              Text(
                data == null ? 'Aucun schéma (vérifiez le serveur API)' : 'Aucune table',
                style: const TextStyle(color: AppTheme.textSecondary),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      }

      return LayoutBuilder(
        builder: (context, constraints) {
          final maxW = constraints.maxWidth.isFinite && constraints.maxWidth > 0 ? constraints.maxWidth : 800.0;
          final maxH = constraints.maxHeight.isFinite && constraints.maxHeight > 0 ? constraints.maxHeight : 600.0;
          // clamp(lower, upper) exige lower <= upper : si la zone est plus petite que 400x300, utiliser maxW/maxH comme min.
          final minW = math.min(400.0, maxW);
          final minH = math.min(300.0, maxH);
          final rawW = layout.width.isFinite && layout.width > 0 ? layout.width : 400.0;
          final rawH = layout.height.isFinite && layout.height > 0 ? layout.height : 300.0;
          final w = rawW.clamp(minW, maxW).toDouble();
          final h = rawH.clamp(minH, maxH).toDouble();
          return InteractiveViewer(
            minScale: 0.3,
            maxScale: 2.0,
            boundaryMargin: const EdgeInsets.all(80),
            child: RepaintBoundary(
              child: Container(
                width: w,
                height: h,
                color: _BarrelDiagramStyle.diagramBackground,
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    CustomPaint(
                      size: Size(w, h),
                      painter: _SchemaLinesPainter(tables: layout.tables, fks: layout.fks),
                    ),
                    ...layout.tables.map((t) {
                      final left = t.rect.left.isFinite ? t.rect.left : 0.0;
                      final top = t.rect.top.isFinite ? t.rect.top : 0.0;
                      final fkColumns = layout.fks
                          .where((fk) => fk.fromTable == t.name)
                          .map((fk) => fk.column)
                          .toSet();
                      return Positioned(
                          left: left,
                          top: top,
                          child: _TableCard(
                            name: t.name,
                            columns: t.columns,
                            primaryKey: t.primaryKey,
                            foreignKeyColumns: fkColumns,
                            showTypes: showTypes,
                          ),
                        );
                    }),
                  ],
                ),
              ),
            ),
          );
        },
      );
    } catch (e, st) {
      debugPrint('[SchemaDiagramView] ERROR: $e\n$st');
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 48, color: AppTheme.error),
            const SizedBox(height: 12),
            Text(
              'Erreur d\'affichage du schéma',
              style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(
                e.toString(),
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                textAlign: TextAlign.center,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      );
    }
  }
}
