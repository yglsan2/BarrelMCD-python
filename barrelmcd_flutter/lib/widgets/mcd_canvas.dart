import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../core/canvas_mode.dart';
import '../theme/app_theme.dart';
import '../screens/glossary_dialog.dart';
import '../screens/cif_panel.dart';
import '../screens/inheritance_panel.dart';
import 'entity_box.dart';
import 'association_oval.dart';
import 'link_arrow.dart';
import '../utils/link_geometry.dart';

/// Ouvre le dialogue complet d'édition d'une entité (propriétés + attributs), depuis le panneau Éléments.
Future<void> showEntityAttributesFor(BuildContext context, int entityIndex) async {
  final state = context.read<McdState>();
  if (entityIndex < 0 || entityIndex >= state.entities.length) return;
  final entity = state.entities[entityIndex];
  final edited = await showDialog<Map<String, dynamic>>(
    context: context,
    builder: (ctx) => _EntityEditorDialog(entity: Map<String, dynamic>.from(entity)),
  );
  if (edited != null && context.mounted) {
    state.updateEntityAt(entityIndex, edited);
  }
}

/// Ouvre le dialogue texte + nombre de bras + accès attributs (depuis Fichier ou canvas).
Future<void> showAssociationTextFor(BuildContext context, int associationIndex) async {
  final state = context.read<McdState>();
  if (associationIndex < 0 || associationIndex >= state.associations.length) return;
  final association = state.associations[associationIndex];
  final nameController = TextEditingController(text: association['name']?.toString() ?? 'Association');
  int armCount = (association['arm_angles'] as List?)?.length ?? 2;
  final result = await showDialog<Map<String, dynamic>>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setState) => AlertDialog(
        title: const Text('Texte et bras de l\'association'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: 'Nom (texte affiché)',
                  hintText: 'ex. passer commande',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              const Text('Nombre de bras (points de connexion)', style: TextStyle(fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ChoiceChip(
                  label: Text('$n'),
                  selected: armCount == n,
                  onSelected: (_) => setState(() => armCount = n),
                )).toList(),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () => Navigator.pop(ctx, {'openAttributes': true}),
                icon: const Icon(Icons.tune, size: 18),
                label: const Text('Modifier les attributs de l\'association'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(
            onPressed: () {
              final name = nameController.text.trim();
              Navigator.pop(ctx, {'name': name.isEmpty ? 'Association' : name, 'armCount': armCount});
            },
            child: const Text('OK'),
          ),
        ],
      ),
    ),
  );
  if (result == null || !context.mounted) return;
  if (result['openAttributes'] == true) {
    await showAssociationAttributesFor(context, associationIndex);
    return;
  }
  final a = Map<String, dynamic>.from(association);
  if (result['name'] != null) a['name'] = result['name'];
  state.updateAssociationAt(associationIndex, a);
  if (result['armCount'] != null) {
    state.setAssociationArmCount(associationIndex, result['armCount'] as int);
  }
}

/// Ouvre le dialogue des attributs d'une association (depuis le panneau Éléments).
Future<void> showAssociationAttributesFor(BuildContext context, int associationIndex) async {
  final state = context.read<McdState>();
  if (associationIndex < 0 || associationIndex >= state.associations.length) return;
  final association = state.associations[associationIndex];
  final attrs = List<Map<String, dynamic>>.from((association['attributes'] as List?) ?? []);
  final updated = await showDialog<List<Map<String, dynamic>>>(
    context: context,
    builder: (ctx) => _AttributeListDialog(
      title: 'Attributs de l\'association ${association['name']}',
      attributes: attrs,
      isEntity: false,
    ),
  );
  if (updated != null && context.mounted) {
    final a = Map<String, dynamic>.from(association);
    a['attributes'] = updated;
    state.updateAssociationAt(associationIndex, a);
  }
}

/// Activer pour logs détaillés et try/catch sur le canvas (pointer, grille, dialogs).
const bool _kCanvasDebug = false;
/// Toujours activer les logs des clics souris (pointer down/up, tap, exceptions) pour débogage.
const bool _kClicksLog = true;
/// Mode ultra verbose : log à chaque décision (early return, isTap, mode, branche prise) pour corriger les bugs de clic.
const bool _kVerboseCanvas = true;

/// Dimensions partagées avec EntityBox et AssociationDiamond pour que les liens visent le centre des formes.
const double _entityWidth = 200;
const double _entityMinHeight = 80;

/// Zone de dessin MCD interactive : créer/déplacer entités et associations, lier, zoom.
class McdCanvas extends StatefulWidget {
  const McdCanvas({super.key, this.repaintBoundaryKey});

  final GlobalKey? repaintBoundaryKey;

  /// Les 4 cardinalités du MCD Merise : (min, max) avec min ∈ {0,1}, max ∈ {1,n}.
  static const List<String> mcdCardinalities = ['0,1', '1,1', '0,n', '1,n'];

  /// Ouvre le dialogue d'édition des 2 cardinalités d'un lien (côté entité, côté association).
  static Future<void> showEditLinkCardinalitiesDialog(
    BuildContext context,
    int linkIndex,
    String currentCardEntity,
    String currentCardAssoc,
  ) async {
    final state = context.read<McdState>();
    String vEntity = McdCanvas.mcdCardinalities.contains(currentCardEntity) ? currentCardEntity : '1,n';
    String vAssoc = McdCanvas.mcdCardinalities.contains(currentCardAssoc) ? currentCardAssoc : '1,n';
    final result = await showDialog<({String cardEntity, String cardAssoc})>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setState) {
            return AlertDialog(
              title: const Text('Cardinalités du lien'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<String>(
                    initialValue: McdCanvas.mcdCardinalities.contains(vEntity) ? vEntity : '1,n',
                    decoration: const InputDecoration(labelText: 'Côté entité'),
                    items: McdCanvas.mcdCardinalities
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (s) { if (s != null) { vEntity = s; setState(() {}); } },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: McdCanvas.mcdCardinalities.contains(vAssoc) ? vAssoc : '1,n',
                    decoration: const InputDecoration(labelText: 'Côté association'),
                    items: McdCanvas.mcdCardinalities
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (s) { if (s != null) { vAssoc = s; setState(() {}); } },
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, (cardEntity: vEntity, cardAssoc: vAssoc)),
                  child: const Text('OK'),
                ),
              ],
            );
          },
        );
      },
    );
    if (result != null) state.updateAssociationLinkCardinalities(linkIndex, result.cardEntity, result.cardAssoc);
  }

  @override
  State<McdCanvas> createState() => McdCanvasState();
}

class McdCanvasState extends State<McdCanvas> {
  final TransformationController _transform = TransformationController();
  static const double _gridSize = 20;
  static const double _minScale = 0.1;
  static const double _maxScale = 5.0;
  bool _initialViewCentered = false;
  Offset? _lastTapForDebug;
  Offset? _pointerDownPosition;
  DateTime? _pointerDownTime;
  int _pointerDownButton = 0; // 1 = left, 2 = right (secondary)
  Offset? _outerDownPos;
  DateTime? _outerDownTime;
  int? _outerHitEntityIndex;
  int? _outerHitAssocIndex;
  int _outerPointerDownButton = 0;
  Offset? _dragStartScenePos;
  Offset? _dragEntityStartPos;
  Offset? _dragAssocStartPos;
  /// Positions de départ pour drag groupé (entités/associations sélectionnées).
  Map<int, Offset>? _dragEntityStartPositions;
  Map<int, Offset>? _dragAssocStartPositions;
  static const double _tapSlop = 40.0;
  static const Duration _tapMaxDuration = Duration(milliseconds: 600);
  int? _draggingEntityIndex;
  int? _draggingAssociationIndex;
  Offset? _dragStartPos;
  Offset? _lastLongPressPosition;
  double _lastViewportW = 0;
  double _lastViewportH = 0;
  double _lastSceneW = 0;
  double _lastSceneH = 0;
  bool _ctrlHeld = false;
  bool _newEntityDialogOpen = false;
  bool _newAssociationDialogOpen = false;

  /// Drag « tirer un lien » : source entité (true) ou association (false), index, position de départ et courante (scène).
  bool? _linkDragFromEntity;
  int? _linkDragSourceIndex;
  Offset? _linkDragStartScenePos;
  Offset? _linkDragCurrentScenePos;

  /// Déplacement d'une poignée de lien (entité ou association) quand un lien est sélectionné.
  String? _draggingLinkHandle; // 'entity' | 'association'
  int? _draggingLinkIndex;

  /// Rotation d'un bras d'association (glisser la pointe du bras autour du cercle invisible).
  int? _rotatingArmAssocIndex;
  int? _rotatingArmIndex;

  /// Glisser le segment d'un lien (déplacer la pointe / le lien entier, comme Barrel).
  bool _draggingLinkSegment = false;
  int? _draggingLinkSegmentIndex;

  /// Drag « en attente » : on ne commit qu'après un déplacement > _dragCommitSlop (tap = pas de drag, donc dialogue/modifier).
  static const double _dragCommitSlop = 18.0;
  int? _pendingDragEntityIndex;
  Offset? _pendingDragScenePos;
  Offset? _pendingDragEntityStartPos;
  int? _pendingDragAssocIndex;
  Offset? _pendingDragAssocStartPos;
  int? _pendingDragLinkSegmentIndex;

  /// Déplacement du symbole d'héritage (clé = nom entité parente).
  String? _draggingInheritanceSymbolParent;
  /// Déplacement d'une forme CIF (index dans cifConstraints).
  int? _draggingCifIndex;
  /// Offset pointeur → centre de la CIF au début du drag (pour ne pas faire sauter la forme).
  Offset? _cifDragOffset;

  @override
  void initState() {
    super.initState();
    HardwareKeyboard.instance.addHandler(_handleKeyEvent);
  }

  @override
  void dispose() {
    HardwareKeyboard.instance.removeHandler(_handleKeyEvent);
    _transform.dispose();
    super.dispose();
  }

  bool _handleKeyEvent(KeyEvent event) {
    final isControl = event.logicalKey == LogicalKeyboardKey.controlLeft ||
        event.logicalKey == LogicalKeyboardKey.controlRight;
    if (!isControl) return false;
    final newHeld = event is KeyDownEvent;
    if (_ctrlHeld != newHeld && mounted) {
      setState(() => _ctrlHeld = newHeld);
    }
    return false;
  }

  void zoomIn() {
    _applyZoom(1.25);
  }

  void zoomOut() {
    _applyZoom(1 / 1.25);
  }

  /// Ajuste la vue pour cadrer et recentrer tous les éléments (entités + associations).
  /// Si [state] est fourni, calcule la boîte englobante du contenu ; sinon comportement de secours.
  void fitToView([McdState? state]) {
    if (_lastViewportW <= 0 || _lastViewportH <= 0) return;
    double minX = double.infinity;
    double minY = double.infinity;
    double maxX = double.negativeInfinity;
    double maxY = double.negativeInfinity;
    if (state != null) {
      for (final e in state.entities) {
        final pos = e['position'] as Map<String, dynamic>?;
        final x = (pos?['x'] as num?)?.toDouble() ?? 0;
        final y = (pos?['y'] as num?)?.toDouble() ?? 0;
        final w = (e['width'] as num?)?.toDouble() ?? _entityWidth;
        final attrs = (e['attributes'] as List?) ?? [];
        final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
        final h = (e['height'] as num?)?.toDouble() ??
            (_entityMinHeight + (attrCount > 0 ? attrCount * _entityAttrLineHeight : 0));
        minX = math.min(minX, x);
        minY = math.min(minY, y);
        maxX = math.max(maxX, x + w);
        maxY = math.max(maxY, y + h);
      }
      for (final a in state.associations) {
        final pos = a['position'] as Map<String, dynamic>?;
        final x = (pos?['x'] as num?)?.toDouble() ?? 0;
        final y = (pos?['y'] as num?)?.toDouble() ?? 0;
        final diam = (a['width'] as num?)?.toDouble() ?? 260.0;
        final boxSize = diam + 2 * AssociationOval.armExtensionLength;
        minX = math.min(minX, x);
        minY = math.min(minY, y);
        maxX = math.max(maxX, x + boxSize);
        maxY = math.max(maxY, y + boxSize);
      }
    }
    const padding = 80.0;
    double contentW;
    double contentH;
    double centerX;
    double centerY;
    if (minX.isFinite && minY.isFinite && (state == null || state.entities.isNotEmpty || state.associations.isNotEmpty)) {
      contentW = (maxX - minX) + 2 * padding;
      contentH = (maxY - minY) + 2 * padding;
      centerX = (minX + maxX) / 2;
      centerY = (minY + maxY) / 2;
    } else {
      contentW = _lastViewportW;
      contentH = _lastViewportH;
      centerX = 0;
      centerY = 0;
    }
    final scaleX = _lastViewportW / contentW;
    final scaleY = _lastViewportH / contentH;
    final s = (scaleX < scaleY ? scaleX : scaleY).clamp(_minScale, _maxScale) * 0.92;
    final tx = _lastViewportW / 2 - centerX * s;
    final ty = _lastViewportH / 2 - centerY * s;
    _transform.value = Matrix4.identity()
      ..setEntry(0, 0, s)
      ..setEntry(1, 1, s)
      ..setEntry(0, 3, tx)
      ..setEntry(1, 3, ty);
  }

  /// Centre de la vue en coordonnées scène (pour créer entité/association au centre).
  Offset _getViewCenterScene() {
    if (_lastViewportW <= 0 || _lastViewportH <= 0) return Offset.zero;
    return _viewportToScene(Offset(_lastViewportW / 2, _lastViewportH / 2));
  }

  /// Ouvre le dialogue « Nouvelle entité » en plaçant l'entité au centre de la vue. Appelé depuis le menu Fichier.
  void addNewEntityAtViewCenter() {
    if (!mounted) return;
    final center = _getViewCenterScene();
    _showNewEntityDialog(center.dx, center.dy);
  }

  /// Ouvre le dialogue « Nouvelle association » au centre de la vue. Appelé depuis le menu Fichier.
  void addNewAssociationAtViewCenter() {
    if (!mounted) return;
    final center = _getViewCenterScene();
    _showNewAssociationDialog(center.dx, center.dy);
  }

  /// Hauteur approximative par ligne d'attribut dans EntityBox (padding + texte).
  static const double _entityAttrLineHeight = 24.0;

  /// Retourne l'index de l'entité dont la boîte contient [scenePos], ou null.
  /// La hauteur de la zone cliquable tient compte des attributs affichés (sinon les clics
  /// sur la zone « attributs » tombaient à côté et ne sélectionnaient pas l'entité).
  int? _entityIndexAtScene(McdState state, Offset scenePos) {
    for (int i = 0; i < state.entities.length; i++) {
      final e = state.entities[i];
      final pos = e['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      final w = (e['width'] as num?)?.toDouble() ?? _entityWidth;
      final attrs = (e['attributes'] as List?) ?? [];
      final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
      final h = (e['height'] as num?)?.toDouble() ??
          (_entityMinHeight + (attrCount > 0 ? attrCount * _entityAttrLineHeight : 0));
      if (scenePos.dx >= x && scenePos.dx <= x + w && scenePos.dy >= y && scenePos.dy <= y + h) return i;
    }
    return null;
  }

  /// Retourne l'index de l'association dont la boîte (cercle + bras) contient [scenePos], ou null.
  int? _associationIndexAtScene(McdState state, Offset scenePos) {
    for (int i = 0; i < state.associations.length; i++) {
      final a = state.associations[i];
      final pos = a['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      final diam = (a['width'] as num?)?.toDouble() ?? 260.0;
      final boxSize = diam + 2 * AssociationOval.armExtensionLength;
      if (scenePos.dx >= x && scenePos.dx <= x + boxSize && scenePos.dy >= y && scenePos.dy <= y + boxSize) return i;
    }
    return null;
  }

  static const double _armTipHitRadius = 18.0;

  /// Retourne (index association, index bras) si [scenePos] est sur une pointe de bras, sinon null.
  ({int assocIndex, int armIndex})? _armTipHitAtScene(McdState state, Offset scenePos) {
    for (int i = 0; i < state.associations.length; i++) {
      final a = state.associations[i];
      final center = _sceneAssociationCenter(a);
      final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
      final diam = (a['width'] as num?)?.toDouble() ?? 260.0;
      final armRadius = diam / 2 + AssociationOval.armExtensionLength;
      for (int j = 0; j < angles.length; j++) {
        final rad = angles[j].toDouble() * math.pi / 180;
        final tip = Offset(center.dx + armRadius * math.cos(rad), center.dy + armRadius * math.sin(rad));
        if ((scenePos - tip).distance <= _armTipHitRadius) return (assocIndex: i, armIndex: j);
      }
    }
    return null;
  }

  /// Convertit un point viewport (coordonnées du canvas visible) en coordonnées scène (pour placer entité/association).
  Offset _viewportToScene(Offset viewportPos) {
    final m = _transform.value;
    final scale = m.getRow(0)[0];
    final tx = m.getRow(0)[3];
    final ty = m.getRow(1)[3];
    if (scale.abs() < 1e-6) return viewportPos;
    return Offset(
      (viewportPos.dx - tx) / scale,
      (viewportPos.dy - ty) / scale,
    );
  }

  /// Départ de la prévisualisation du lien : centre du bord (entité ou assoc) + marge 10 px pour ne pas dépasser sur la forme.
  static const double _previewMargin = 10.0;

  Offset _previewLinkFrom(McdState state) {
    final cursor = _linkDragCurrentScenePos!;
    final idx = _linkDragSourceIndex;
    if (idx == null) return _linkDragStartScenePos!;
    Offset anchor;
    if (_linkDragFromEntity == true && idx < state.entities.length) {
      anchor = _sceneEntityLinkEndpoint(state.entities[idx], cursor);
    } else if (_linkDragFromEntity == false && idx < state.associations.length) {
      anchor = _sceneAssociationSimpleAttachment(state.associations[idx], cursor);
    } else {
      return _linkDragStartScenePos!;
    }
    final dx = cursor.dx - anchor.dx;
    final dy = cursor.dy - anchor.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return anchor;
    final ux = dx / dist;
    final uy = dy / dist;
    return Offset(anchor.dx + ux * _previewMargin, anchor.dy + uy * _previewMargin);
  }

  /// Point d'accroche sur l'entité pour le drag de lien (centre du bord qui fait face à [towardPoint]).
  Offset _sceneEntityLinkEndpoint(Map<String, dynamic> e, Offset towardPoint) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final w = (e['width'] as num?)?.toDouble() ?? _entityWidth;
    final attrs = (e['attributes'] as List?) ?? [];
    final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
    final h = (e['height'] as num?)?.toDouble() ??
        (_entityMinHeight + (attrCount > 0 ? attrCount * _entityAttrLineHeight : 0));
    final cx = x + w / 2;
    final cy = y + h / 2;
    final dx = towardPoint.dx - cx;
    final dy = towardPoint.dy - cy;
    if (dx.abs() >= dy.abs()) return Offset(dx > 0 ? x + w : x, cy);
    return Offset(cx, dy > 0 ? y + h : y);
  }

  /// Centre de l'association (pour point de départ du drag de lien).
  Offset _sceneAssociationCenter(Map<String, dynamic> a) {
    final pos = a['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final boxSize = w + 2 * AssociationOval.armExtensionLength;
    return Offset(x + boxSize / 2, y + boxSize / 2);
  }

  /// Accroche entité avec entity_side (left/right/top/bottom) si présent dans le lien.
  Offset _sceneEntityLinkEndpointWithSide(Map<String, dynamic> e, Map<String, dynamic> link, Offset towardPoint) {
    final side = link['entity_side'] as String?;
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final w = (e['width'] as num?)?.toDouble() ?? _entityWidth;
    final attrs = (e['attributes'] as List?) ?? [];
    final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
    final h = (e['height'] as num?)?.toDouble() ??
        (_entityMinHeight + (attrCount > 0 ? attrCount * _entityAttrLineHeight : 0));
    final cx = x + w / 2;
    final cy = y + h / 2;
    if (side == 'left') return Offset(x, cy);
    if (side == 'right') return Offset(x + w, cy);
    if (side == 'top') return Offset(cx, y);
    if (side == 'bottom') return Offset(cx, y + h);
    return _sceneEntityLinkEndpoint(e, towardPoint);
  }

  Offset _sceneAssociationSimpleAttachment(Map<String, dynamic> a, Offset entityPoint) {
    final center = _sceneAssociationCenter(a);
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final radius = w / 2;
    final dx = entityPoint.dx - center.dx;
    final dy = entityPoint.dy - center.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return Offset(center.dx + radius, center.dy);
    return Offset(center.dx + radius * (dx / dist), center.dy + radius * (dy / dist));
  }

  Offset _sceneAssociationArmPosition(Map<String, dynamic> a, Map<String, dynamic> link) {
    final center = _sceneAssociationCenter(a);
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final h = (a['height'] as num?)?.toDouble() ?? 260.0;
    final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
    final armIndex = (link['arm_index'] as num?)?.toInt() ?? 0;
    final angle = (armIndex < angles.length ? angles[armIndex].toDouble() : 0.0) * math.pi / 180;
    final radius = w / 2 + AssociationOval.armExtensionLength;
    return Offset(center.dx + radius * math.cos(angle), center.dy + radius * math.sin(angle));
  }

  /// Retourne (from, to) en scène pour le lien à [linkIndex], même logique que _LinksPainter (arrow_tip = point de relâchement).
  ({Offset from, Offset to}) _getLinkSegment(McdState state, int linkIndex, bool precisionMode) {
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) {
      return (from: Offset.zero, to: Offset.zero);
    }
    final link = state.associationLinks[linkIndex];
    final assocName = link['association'] as String?;
    final entityName = link['entity'] as String?;
    if (assocName == null || entityName == null) return (from: Offset.zero, to: Offset.zero);
    final assocIndex = state.associations.indexWhere((a) => (a['name'] as String?) == assocName);
    final entityIndex = state.entities.indexWhere((e) => (e['name'] as String?) == entityName);
    if (assocIndex < 0 || entityIndex < 0) return (from: Offset.zero, to: Offset.zero);
    final assoc = state.associations[assocIndex];
    final ent = state.entities[entityIndex];
    final center = _sceneAssociationCenter(assoc);
    final entityPt = _sceneEntityLinkEndpointWithSide(ent, link, center);
    final assocPt = _sceneAssociationSimpleAttachment(assoc, entityPt);
    final arrowAtAssociation = link['arrow_at_association'] == true;
    final tipX = (link['arrow_tip_x'] as num?)?.toDouble();
    final tipY = (link['arrow_tip_y'] as num?)?.toDouble();
    final hasStoredTip = tipX != null && tipY != null;
    if (hasStoredTip) {
      final arrowTip = Offset(tipX!, tipY!);
      if (arrowAtAssociation) {
        return (from: entityPt, to: arrowTip);
      } else {
        return (from: _sceneAssociationSimpleAttachment(assoc, arrowTip), to: arrowTip);
      }
    }
    if (arrowAtAssociation) return (from: entityPt, to: assocPt);
    return (from: assocPt, to: entityPt);
  }

  static const double _linkHitSegmentThreshold = 12.0;
  static const double _linkHandleHitRadius = 14.0;

  double _distancePointToSegment(Offset p, Offset a, Offset b) {
    final dx = b.dx - a.dx;
    final dy = b.dy - a.dy;
    final len = math.sqrt(dx * dx + dy * dy);
    if (len < 1e-6) return (p - a).distance;
    final t = ((p.dx - a.dx) * dx + (p.dy - a.dy) * dy) / (len * len).clamp(0.0, 1.0);
    final proj = Offset(a.dx + t * dx, a.dy + t * dy);
    return (p - proj).distance;
  }

  /// Index du lien dont le segment est le plus proche de [scenePos] (sous le seuil), ou null.
  int? _linkIndexAtScene(McdState state, Offset scenePos, bool precisionMode) {
    int? best;
    double bestDist = _linkHitSegmentThreshold + 1;
    for (int i = 0; i < state.associationLinks.length; i++) {
      final seg = _getLinkSegment(state, i, precisionMode);
      final d = _distancePointToSegment(scenePos, seg.from, seg.to);
      if (d < bestDist) {
        bestDist = d;
        best = i;
      }
    }
    return best;
  }

  static const double _inheritanceSymbolHitHalfW = 38.0;
  static const double _inheritanceSymbolHitHalfH = 28.0;

  /// Placement du symbole d'héritage (style UML/Merise) : centré au-dessus du parent, entre parent et enfants.
  /// Inclut aussi le symbole « standalone » (logo placable sans lien parent/enfant) s'il existe.
  List<({String parent, Offset center})> _getInheritanceSymbolLayout(McdState state) {
    final links = state.inheritanceLinks;
    final result = <({String parent, Offset center})>[];
    final byParent = <String, List<Map<String, dynamic>>>{};
    for (final link in links) {
      final p = link['parent'] as String? ?? '';
      byParent.putIfAbsent(p, () => []).add(link);
    }
    for (final entry in byParent.entries) {
      final parentIdx = state.entities.indexWhere((e) => (e['name'] as String?) == entry.key);
      if (parentIdx < 0 || entry.value.isEmpty) continue;
      final parentEnt = state.entities[parentIdx];
      final parentPos = parentEnt['position'] as Map<String, dynamic>?;
      final px = (parentPos?['x'] as num?)?.toDouble() ?? 0;
      final py = (parentPos?['y'] as num?)?.toDouble() ?? 0;
      final attrs = (parentEnt['attributes'] as List?) ?? [];
      final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
      final ph = (parentEnt['height'] as num?)?.toDouble() ?? (_entityMinHeight + (attrCount > 0 ? attrCount * _entityAttrLineHeight : 0));
      final parentCenterX = px + _entityWidth / 2;
      final parentBottomY = py + ph;
      final childNames = entry.value.map((l) => l['child'] as String?).whereType<String>().toList();
      if (childNames.isEmpty) continue;
      double sumY = 0;
      int count = 0;
      for (final childName in childNames) {
        final ci = state.entities.indexWhere((e) => (e['name'] as String?) == childName);
        if (ci < 0) continue;
        final c = state.entities[ci];
        final pos = c['position'] as Map<String, dynamic>?;
        sumY += (pos?['y'] as num?)?.toDouble() ?? 0;
        count++;
      }
      final avgChildTopY = count > 0 ? sumY / count : parentBottomY + 80;
      // Symbole centré au-dessus du parent (même X que parent), entre parent (bas) et enfants (haut), légèrement plus proche du parent (style UML/Merise).
      final defaultCenter = Offset(parentCenterX, parentBottomY + (avgChildTopY - parentBottomY) * 0.35);
      final stored = state.inheritanceSymbolPositions[entry.key];
      final center = stored != null
          ? Offset((stored['x'] as num?)?.toDouble() ?? defaultCenter.dx, (stored['y'] as num?)?.toDouble() ?? defaultCenter.dy)
          : defaultCenter;
      result.add((parent: entry.key, center: center));
    }
    final standalone = state.inheritanceSymbolPositions['_standalone'];
    if (standalone != null) {
      final x = (standalone['x'] as num?)?.toDouble() ?? 2500.0;
      final y = (standalone['y'] as num?)?.toDouble() ?? 2500.0;
      result.add((parent: '_standalone', center: Offset(x, y)));
    }
    return result;
  }

  String? _hitTestInheritanceSymbol(McdState state, Offset scenePos) {
    for (final item in _getInheritanceSymbolLayout(state)) {
      final rect = Rect.fromCenter(center: item.center, width: _inheritanceSymbolHitHalfW * 2, height: _inheritanceSymbolHitHalfH * 2);
      if (rect.contains(scenePos)) return item.parent;
    }
    return null;
  }

  Offset _getCifCenter(McdState state, int index) {
    const w = 88.0, h = 32.0, margin = 80.0, stepX = 48.0, stepY = 78.0;
    if (index < 0 || index >= state.cifConstraints.length) return Offset.zero;
    final c = state.cifConstraints[index];
    final pos = c['position'] as Map<String, dynamic>?;
    if (pos != null && pos['x'] != null && pos['y'] != null) {
      return Offset((pos['x'] as num).toDouble(), (pos['y'] as num).toDouble());
    }
    return Offset(margin + w / 2 + index * stepX, margin + h / 2 + index * stepY);
  }

  int? _hitTestCif(McdState state, Offset scenePos) {
    const w = 88.0, h = 32.0;
    for (int i = 0; i < state.cifConstraints.length; i++) {
      final center = _getCifCenter(state, i);
      final rect = Rect.fromCenter(center: center, width: w, height: h);
      if (rect.contains(scenePos)) return i;
    }
    return null;
  }

  void _applyZoom(double factor) {
    if (_lastViewportW <= 0 || _lastViewportH <= 0) return;
    final m = _transform.value;
    final scale = m.getRow(0)[0];
    final tx = m.getRow(0)[3];
    final ty = m.getRow(1)[3];
    final newScale = (scale * factor).clamp(_minScale, _maxScale);
    if (newScale == scale) return;
    final newTx = _lastViewportW / 2 - (_lastViewportW / 2 - tx) * (newScale / scale);
    final newTy = _lastViewportH / 2 - (_lastViewportH / 2 - ty) * (newScale / scale);
    _transform.value = Matrix4.identity()
      ..setEntry(0, 0, newScale)
      ..setEntry(1, 1, newScale)
      ..setEntry(0, 3, newTx)
      ..setEntry(1, 3, newTy);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final sceneWidth = constraints.maxWidth + 4000.0;
        final sceneHeight = constraints.maxHeight + 4000.0;
        final viewportW = constraints.maxWidth;
        final viewportH = constraints.maxHeight;
        _lastViewportW = viewportW;
        _lastViewportH = viewportH;
        _lastSceneW = sceneWidth;
        _lastSceneH = sceneHeight;
        if (!_initialViewCentered && viewportW > 0 && viewportH > 0) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted || _initialViewCentered) return;
            _initialViewCentered = true;
            final tx = viewportW / 2 - sceneWidth / 2;
            final ty = viewportH / 2 - sceneHeight / 2;
            _transform.value = Matrix4.identity()..translateByDouble(tx, ty, 0, 1.0);
          });
        }
        return Listener(
          behavior: HitTestBehavior.translucent,
          onPointerDown: (e) {
            _outerDownPos = e.localPosition;
            _outerDownTime = DateTime.now();
            _outerPointerDownButton = e.buttons;
            _outerHitEntityIndex = null;
            _outerHitAssocIndex = null;
            _dragStartScenePos = null;
            _dragEntityStartPos = null;
            _dragAssocStartPos = null;
            try {
              final scenePos = _viewportToScene(e.localPosition);
              final state = context.read<McdState>();
              final modeState = context.read<CanvasModeState>();
              final inhParent = _hitTestInheritanceSymbol(state, scenePos);
              final cifIdx = _hitTestCif(state, scenePos);
              if (inhParent != null || cifIdx != null) {
                _outerHitEntityIndex = null;
                _outerHitAssocIndex = null;
              } else {
                _outerHitEntityIndex = _entityIndexAtScene(state, scenePos);
                _outerHitAssocIndex = _associationIndexAtScene(state, scenePos);
              }
              final isRightButton = _outerPointerDownButton != 0 && (_outerPointerDownButton & kPrimaryMouseButton) == 0;
              // Mode Lien : tirer un trait depuis l'entité ou l'association (drag vers l'autre).
              if (!isRightButton && modeState.mode == CanvasMode.createLink) {
                if (_outerHitEntityIndex != null) {
                  _linkDragFromEntity = true;
                  _linkDragSourceIndex = _outerHitEntityIndex;
                  _linkDragStartScenePos = _sceneEntityLinkEndpoint(state.entities[_outerHitEntityIndex!], scenePos);
                  _linkDragCurrentScenePos = scenePos;
                  setState(() {});
                } else if (_outerHitAssocIndex != null) {
                  _linkDragFromEntity = false;
                  _linkDragSourceIndex = _outerHitAssocIndex;
                  _linkDragStartScenePos = _sceneAssociationCenter(state.associations[_outerHitAssocIndex!]);
                  _linkDragCurrentScenePos = scenePos;
                  setState(() {});
                }
              }
              // Mode Sélection : démarrer le drag d'une poignée de lien si on clique sur une poignée du lien sélectionné.
              if (!isRightButton && modeState.mode == CanvasMode.select &&
                  _outerHitEntityIndex == null && _outerHitAssocIndex == null) {
                final eff = modeState.linkPrecisionMode;
                final selLinkIndex = state.selectedType == 'link' ? state.selectedIndex : -1;
                if (selLinkIndex >= 0 && selLinkIndex < state.associationLinks.length) {
                  final seg = _getLinkSegment(state, selLinkIndex, eff);
                  if ((scenePos - seg.from).distance <= _linkHandleHitRadius) {
                    _draggingLinkHandle = 'association';
                    _draggingLinkIndex = selLinkIndex;
                    state.beginLinkAttachmentEdit();
                    setState(() {});
                  } else if ((scenePos - seg.to).distance <= _linkHandleHitRadius) {
                    _draggingLinkHandle = 'entity';
                    _draggingLinkIndex = selLinkIndex;
                    state.beginLinkAttachmentEdit();
                    setState(() {});
                  }
                }
              }
              // Mode Sélection : glisser une pointe de bras pour faire tourner le bras autour de l'association.
              if (!isRightButton && modeState.mode == CanvasMode.select) {
                final armHit = _armTipHitAtScene(state, scenePos);
                if (armHit != null) {
                  _rotatingArmAssocIndex = armHit.assocIndex;
                  _rotatingArmIndex = armHit.armIndex;
                  state.beginArmAngleEdit();
                  setState(() {});
                }
              }
              // Drag entité/association/lien en attente : on ne commit qu'au premier move > _dragCommitSlop (sinon = tap → dialogue ou modifier).
              if (!isRightButton && modeState.mode != CanvasMode.createLink && _rotatingArmAssocIndex == null) {
                if (_outerHitEntityIndex != null) {
                  final ent = state.entities[_outerHitEntityIndex!];
                  final pos = ent['position'] as Map<String, dynamic>?;
                  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                  _pendingDragEntityIndex = _outerHitEntityIndex;
                  _pendingDragScenePos = scenePos;
                  _pendingDragEntityStartPos = Offset(x, y);
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerDown: pending entity drag index=$_outerHitEntityIndex');
                } else if (_outerHitAssocIndex != null) {
                  final assoc = state.associations[_outerHitAssocIndex!];
                  final pos = assoc['position'] as Map<String, dynamic>?;
                  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                  _pendingDragAssocIndex = _outerHitAssocIndex;
                  _pendingDragScenePos = scenePos;
                  _pendingDragAssocStartPos = Offset(x, y);
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerDown: pending assoc drag index=$_outerHitAssocIndex');
                } else {
                  // Glisser un lien (segment) : dès qu'on ne clique ni sur entité ni sur association.
                  final linkIdx = _linkIndexAtScene(state, scenePos, modeState.linkPrecisionMode || _ctrlHeld);
                  if (linkIdx != null) {
                    _pendingDragLinkSegmentIndex = linkIdx;
                    _pendingDragScenePos = scenePos;
                    if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerDown: pending link segment drag index=$linkIdx');
                  }
                }
              }
              // Symboles héritage et formes CIF : clic droit = menu, clic gauche = déplacer (inhParent/cifIdx déjà calculés plus haut).
              if (_outerHitEntityIndex == null && _outerHitAssocIndex == null &&
                  _draggingEntityIndex == null && _draggingAssociationIndex == null &&
                  !_draggingLinkSegment && _draggingLinkHandle == null && _rotatingArmAssocIndex == null) {
                if (isRightButton) {
                  if (inhParent != null) {
                    _showInheritanceSymbolContextMenu(context, state, inhParent, e.localPosition);
                    return;
                  }
                  if (cifIdx != null) {
                    _showCifShapeContextMenu(context, state, cifIdx, e.localPosition);
                    return;
                  }
                } else {
                  if (inhParent != null) {
                    _draggingInheritanceSymbolParent = inhParent;
                    state.beginMoveInheritanceSymbol();
                    setState(() {});
                  } else if (cifIdx != null) {
                    _draggingCifIndex = cifIdx;
                    _cifDragOffset = scenePos - _getCifCenter(state, cifIdx);
                    state.beginMoveCifConstraint();
                    setState(() {});
                  }
                }
              }
            } catch (err, st) {
              debugPrint('[McdCanvas] OUTER Listener.onPointerDown ERROR: $err\n$st');
            }
            if (_kClicksLog) debugPrint('[McdCanvas] OUTER Listener.onPointerDown pos=${e.localPosition} buttons=${e.buttons} hitEntity=$_outerHitEntityIndex hitAssoc=$_outerHitAssocIndex');
          },
          onPointerMove: (e) {
            try {
              // Committer un drag en attente dès que le déplacement dépasse le seuil.
              final scenePosMove = _viewportToScene(e.localPosition);
              if (_pendingDragScenePos != null) {
                final dist = (scenePosMove - _pendingDragScenePos!).distance;
                if (dist > _dragCommitSlop) {
                  final state = context.read<McdState>();
                  final modeState = context.read<CanvasModeState>();
                  if (_pendingDragEntityIndex != null && _pendingDragEntityStartPos != null) {
                    _draggingEntityIndex = _pendingDragEntityIndex;
                    _dragStartScenePos = _pendingDragScenePos;
                    _dragEntityStartPos = _pendingDragEntityStartPos;
                    _dragEntityStartPositions = null;
                    _dragAssocStartPositions = null;
                    if (state.isEntitySelected(_pendingDragEntityIndex!)) {
                      _dragEntityStartPositions = {};
                      for (final i in state.selectedEntityIndices) {
                        if (i >= 0 && i < state.entities.length) {
                          final ent = state.entities[i];
                          final pos = ent['position'] as Map<String, dynamic>?;
                          final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                          final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                          _dragEntityStartPositions![i] = Offset(x, y);
                        }
                      }
                    } else {
                      _dragEntityStartPositions = {_pendingDragEntityIndex!: _pendingDragEntityStartPos!};
                    }
                    if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerMove: commit entity drag index=$_pendingDragEntityIndex positions=${_dragEntityStartPositions?.length}');
                  } else if (_pendingDragAssocIndex != null && _pendingDragAssocStartPos != null) {
                    _draggingAssociationIndex = _pendingDragAssocIndex;
                    _dragStartScenePos = _pendingDragScenePos;
                    _dragAssocStartPos = _pendingDragAssocStartPos;
                    _dragEntityStartPositions = null;
                    _dragAssocStartPositions = null;
                    if (state.isAssociationSelected(_pendingDragAssocIndex!)) {
                      _dragAssocStartPositions = {};
                      for (final i in state.selectedAssociationIndices) {
                        if (i >= 0 && i < state.associations.length) {
                          final a = state.associations[i];
                          final pos = a['position'] as Map<String, dynamic>?;
                          final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                          final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                          _dragAssocStartPositions![i] = Offset(x, y);
                        }
                      }
                    } else {
                      _dragAssocStartPositions = {_pendingDragAssocIndex!: _pendingDragAssocStartPos!};
                    }
                    if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerMove: commit assoc drag index=$_pendingDragAssocIndex positions=${_dragAssocStartPositions?.length}');
                  } else if (_pendingDragLinkSegmentIndex != null && _pendingDragLinkSegmentIndex! < state.associationLinks.length) {
                    _draggingLinkSegment = true;
                    _draggingLinkSegmentIndex = _pendingDragLinkSegmentIndex;
                    state.beginLinkAttachmentEdit();
                    final link = state.associationLinks[_draggingLinkSegmentIndex!];
                    final tipX = (link['arrow_tip_x'] as num?)?.toDouble();
                    final tipY = (link['arrow_tip_y'] as num?)?.toDouble();
                    if (tipX == null || tipY == null) {
                      final seg = _getLinkSegment(state, _draggingLinkSegmentIndex!, modeState.linkPrecisionMode || _ctrlHeld);
                      state.updateAssociationLinkAttachment(_draggingLinkSegmentIndex!, arrowTipX: seg.to.dx, arrowTipY: seg.to.dy);
                    }
                    if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerMove: commit link segment drag index=$_draggingLinkSegmentIndex');
                  }
                  _pendingDragEntityIndex = null;
                  _pendingDragScenePos = null;
                  _pendingDragEntityStartPos = null;
                  _pendingDragAssocIndex = null;
                  _pendingDragAssocStartPos = null;
                  _pendingDragLinkSegmentIndex = null;
                }
              }
              if (_rotatingArmAssocIndex != null && _rotatingArmIndex != null) {
                final state = context.read<McdState>();
                if (_rotatingArmAssocIndex! >= state.associations.length) {
                  _rotatingArmAssocIndex = null;
                  _rotatingArmIndex = null;
                  setState(() {});
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                final assoc = state.associations[_rotatingArmAssocIndex!];
                final center = _sceneAssociationCenter(assoc);
                final dx = scenePos.dx - center.dx;
                final dy = scenePos.dy - center.dy;
                double angleDeg = math.atan2(dy, dx) * 180 / math.pi;
                if (angleDeg < 0) angleDeg += 360;
                state.updateAssociationArmAngle(_rotatingArmAssocIndex!, _rotatingArmIndex!, angleDeg);
                setState(() {});
              }
              if (_linkDragSourceIndex != null && _linkDragStartScenePos != null) {
                final scenePos = _viewportToScene(e.localPosition);
                _linkDragCurrentScenePos = scenePos;
                setState(() {});
              }
              if (_draggingLinkHandle != null && _draggingLinkIndex != null) {
                final state = context.read<McdState>();
                if (_draggingLinkIndex! >= state.associationLinks.length) {
                  _draggingLinkHandle = null;
                  _draggingLinkIndex = null;
                  setState(() {});
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                final link = state.associationLinks[_draggingLinkIndex!];
                final arrowAtAssociation = link['arrow_at_association'] == true;
                if (_draggingLinkHandle == 'entity') {
                  // Poignée côté entité : entity_side selon position (left/right/top/bottom), même logique que à la création.
                  final entityName = link['entity'] as String?;
                  final ei = state.entities.indexWhere((x) => (x['name'] as String?) == entityName);
                  if (ei >= 0) {
                    final ent = state.entities[ei];
                    final pos = ent['position'] as Map<String, dynamic>?;
                    final ex = (pos?['x'] as num?)?.toDouble() ?? 0;
                    final ey = (pos?['y'] as num?)?.toDouble() ?? 0;
                    final w = (ent['width'] as num?)?.toDouble() ?? _entityWidth;
                    final h = entityHeight(ent);
                    final cx = ex + w / 2;
                    final cy = ey + h / 2;
                    final dx = scenePos.dx - cx;
                    final dy = scenePos.dy - cy;
                    final side = dx.abs() >= dy.abs() ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'bottom' : 'top');
                    state.updateAssociationLinkAttachment(
                      _draggingLinkIndex!,
                      entitySide: side,
                      arrowTipX: scenePos.dx,
                      arrowTipY: scenePos.dy,
                    );
                  }
                } else {
                  // Poignée côté association : soit angle du bras, soit (si pointe côté assoc) arrow_tip.
                  if (arrowAtAssociation) {
                    state.updateAssociationLinkAttachment(
                      _draggingLinkIndex!,
                      arrowTipX: scenePos.dx,
                      arrowTipY: scenePos.dy,
                    );
                  } else {
                    final assocName = link['association'] as String?;
                    final ai = state.associations.indexWhere((x) => (x['name'] as String?) == assocName);
                    if (ai >= 0) {
                      final assoc = state.associations[ai];
                      final center = _sceneAssociationCenter(assoc);
                      final angles = (assoc['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
                      if (angles.isNotEmpty) {
                        final dx = scenePos.dx - center.dx;
                        final dy = scenePos.dy - center.dy;
                        final angleDeg = math.atan2(dy, dx) * 180 / math.pi;
                        int best = 0;
                        double bestDiff = 360.0;
                        for (int i = 0; i < angles.length; i++) {
                          final a = angles[i].toDouble();
                          double diff = (angleDeg - a).abs();
                          if (diff > 180) diff = 360 - diff;
                          if (diff < bestDiff) {
                            bestDiff = diff;
                            best = i;
                          }
                        }
                        state.updateAssociationLinkAttachment(_draggingLinkIndex!, armIndex: best);
                      }
                    }
                  }
                }
                setState(() {});
              }
              if (_draggingLinkSegment && _draggingLinkSegmentIndex != null) {
                final state = context.read<McdState>();
                if (_draggingLinkSegmentIndex! >= state.associationLinks.length) {
                  _draggingLinkSegment = false;
                  _draggingLinkSegmentIndex = null;
                  setState(() {});
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                state.updateAssociationLinkAttachment(
                  _draggingLinkSegmentIndex!,
                  arrowTipX: scenePos.dx,
                  arrowTipY: scenePos.dy,
                );
                setState(() {});
              }
              if (_draggingInheritanceSymbolParent != null) {
                final state = context.read<McdState>();
                final scenePos = _viewportToScene(e.localPosition);
                state.setInheritanceSymbolPosition(_draggingInheritanceSymbolParent!, scenePos.dx, scenePos.dy);
                setState(() {});
              }
              if (_draggingCifIndex != null) {
                final state = context.read<McdState>();
                if (_draggingCifIndex! >= state.cifConstraints.length) {
                  _draggingCifIndex = null;
                  _cifDragOffset = null;
                  setState(() {});
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                final offset = _cifDragOffset ?? Offset.zero;
                state.setCifConstraintPosition(_draggingCifIndex!, scenePos.dx - offset.dx, scenePos.dy - offset.dy);
                setState(() {});
              }
              if (_draggingEntityIndex != null && _dragStartScenePos != null && _dragEntityStartPositions != null && _dragEntityStartPositions!.isNotEmpty) {
                final state = context.read<McdState>();
                final scenePos = _viewportToScene(e.localPosition);
                final delta = scenePos - _dragStartScenePos!;
                for (final entry in _dragEntityStartPositions!.entries) {
                  final i = entry.key;
                  if (i >= 0 && i < state.entities.length) {
                    final start = entry.value;
                    state.moveEntity(i, start.dx + delta.dx, start.dy + delta.dy);
                  }
                }
                setState(() {});
              } else if (_draggingAssociationIndex != null && _dragStartScenePos != null && _dragAssocStartPositions != null && _dragAssocStartPositions!.isNotEmpty) {
                final state = context.read<McdState>();
                final scenePos = _viewportToScene(e.localPosition);
                final delta = scenePos - _dragStartScenePos!;
                for (final entry in _dragAssocStartPositions!.entries) {
                  final i = entry.key;
                  if (i >= 0 && i < state.associations.length) {
                    final start = entry.value;
                    state.moveAssociation(i, start.dx + delta.dx, start.dy + delta.dy);
                  }
                }
                setState(() {});
              }
            } catch (err, st) {
              debugPrint('[McdCanvas] OUTER Listener.onPointerMove ERROR: $err\n$st');
            }
          },
          onPointerUp: (e) {
            if (_kClicksLog) debugPrint('[McdCanvas] OUTER Listener.onPointerUp pos=${e.localPosition}');
            try {
              final down = _outerDownPos;
              final downTime = _outerDownTime;
              final hitEntity = _outerHitEntityIndex;
              final hitAssoc = _outerHitAssocIndex;
              final button = _outerPointerDownButton;
              _outerDownPos = null;
              _outerDownTime = null;
              _outerPointerDownButton = 0;
              _pendingDragEntityIndex = null;
              _pendingDragScenePos = null;
              _pendingDragEntityStartPos = null;
              _pendingDragAssocIndex = null;
              _pendingDragAssocStartPos = null;
              _pendingDragLinkSegmentIndex = null;
              if (down == null || downTime == null) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp EARLY return: down=$down downTime=$downTime');
                return;
              }
              final wasDraggingEntity = _draggingEntityIndex != null;
              final wasDraggingAssoc = _draggingAssociationIndex != null;
              final wasDraggingLinkHandle = _draggingLinkHandle != null;
              final wasDraggingLinkSegment = _draggingLinkSegment;
              final wasDraggingInheritanceSymbol = _draggingInheritanceSymbolParent != null;
              final wasDraggingCif = _draggingCifIndex != null;
              if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp wasDragging: entity=$wasDraggingEntity assoc=$wasDraggingAssoc linkHandle=$wasDraggingLinkHandle linkSeg=$wasDraggingLinkSegment inh=$wasDraggingInheritanceSymbol cif=$wasDraggingCif hitEntity=$hitEntity hitAssoc=$hitAssoc');
              _draggingEntityIndex = null;
              _draggingAssociationIndex = null;
              _draggingLinkHandle = null;
              _draggingLinkIndex = null;
              _draggingLinkSegment = false;
              _draggingLinkSegmentIndex = null;
              _draggingInheritanceSymbolParent = null;
              _draggingCifIndex = null;
              _cifDragOffset = null;
              _dragStartScenePos = null;
              _dragEntityStartPos = null;
              _dragAssocStartPos = null;
              _dragEntityStartPositions = null;
              _dragAssocStartPositions = null;
              if (wasDraggingLinkHandle || wasDraggingLinkSegment || wasDraggingInheritanceSymbol || wasDraggingCif) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp EARLY return: wasDragging link/inh/cif');
                return;
              }
              // Fin d'un « tirer un lien » : si on relâche sur l'autre type (entité ou association), créer le lien.
              if (_linkDragSourceIndex != null && _linkDragFromEntity != null && _linkDragStartScenePos != null) {
                final state = context.read<McdState>();
                final scenePosUp = _viewportToScene(e.localPosition);
                final hitEntityUp = _entityIndexAtScene(state, scenePosUp);
                final hitAssocUp = _associationIndexAtScene(state, scenePosUp);
                String? associationName;
                String? entityName;
                if (_linkDragFromEntity! && hitAssocUp != null) {
                  entityName = state.getEntityNameByIndex(_linkDragSourceIndex!);
                  associationName = state.getAssociationNameByIndex(hitAssocUp);
                } else if (!_linkDragFromEntity! && hitEntityUp != null) {
                  associationName = state.getAssociationNameByIndex(_linkDragSourceIndex!);
                  entityName = state.getEntityNameByIndex(hitEntityUp);
                }
                final arrowAtAssociation = _linkDragFromEntity == true;
                // Point de relâchement = pointe de flèche exactement où l'utilisateur a relâché (comme Barrel).
                final arrowTipX = scenePosUp.dx;
                final arrowTipY = scenePosUp.dy;
                // Côté entité : bord qui fait face à l'autre extrémité (gauche/droite/haut/bas), même logique dans toutes les directions.
                String? entitySide;
                if (entityName != null) {
                  final ei = state.entities.indexWhere((x) => (x['name'] as String?) == entityName);
                  if (ei >= 0) {
                    final ent = state.entities[ei];
                    final pos = ent['position'] as Map<String, dynamic>?;
                    final ex = (pos?['x'] as num?)?.toDouble() ?? 0;
                    final ey = (pos?['y'] as num?)?.toDouble() ?? 0;
                    final w = (ent['width'] as num?)?.toDouble() ?? 200;
                    final h = entityHeight(ent);
                    final entityCenterX = ex + w / 2;
                    final entityCenterY = ey + h / 2;
                    final otherPoint = arrowAtAssociation ? scenePosUp : _linkDragStartScenePos!;
                    final dx = otherPoint.dx - entityCenterX;
                    final dy = otherPoint.dy - entityCenterY;
                    if (dx.abs() >= dy.abs()) {
                      entitySide = dx > 0 ? 'right' : 'left';
                    } else {
                      entitySide = dy > 0 ? 'bottom' : 'top';
                    }
                  }
                }
                _linkDragFromEntity = null;
                _linkDragSourceIndex = null;
                _linkDragStartScenePos = null;
                _linkDragCurrentScenePos = null;
                _draggingEntityIndex = null;
                _draggingAssociationIndex = null;
                _draggingLinkSegment = false;
                _draggingLinkSegmentIndex = null;
                setState(() {});
                if (associationName != null && entityName != null && context.mounted) {
                  _showCardinalityDialog(
                    associationName,
                    entityName,
                    arrowAtAssociation: arrowAtAssociation,
                    arrowTipX: arrowTipX,
                    arrowTipY: arrowTipY,
                    entitySide: entitySide,
                  );
                }
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp return: after link drag create');
                return;
              }
              if (wasDraggingEntity || wasDraggingAssoc || wasDraggingInheritanceSymbol || wasDraggingCif) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp EARLY return: wasDraggingEntity=$wasDraggingEntity wasDraggingAssoc=$wasDraggingAssoc (tap ignored, was drag)');
                return;
              }
              final delta = (e.localPosition - down).distance;
              final duration = DateTime.now().difference(downTime);
              final isTap = delta <= _tapSlop && duration <= _tapMaxDuration;
              if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp tap check: delta=$delta duration=${duration.inMilliseconds}ms _tapSlop=$_tapSlop _tapMaxDuration=${_tapMaxDuration.inMilliseconds}ms isTap=$isTap');
              if (!isTap) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp EARLY return: !isTap');
                return;
              }
              final modeState = context.read<CanvasModeState>();
              final state = context.read<McdState>();
              final mode = modeState.mode;
              final hasContent = state.entities.isNotEmpty || state.associations.isNotEmpty;
              final scenePos = _viewportToScene(e.localPosition);
              // Clic droit : kSecondaryMouseButton (2) ou bouton 3 sous Linux (bit 4), ou tout bouton non-primaire
              final isRightClick = button != 0 && (button & kPrimaryMouseButton) == 0;
              if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE onPointerUp TAP branch: mode=$mode isRightClick=$isRightClick button=$button hitEntity=$hitEntity hitAssoc=$hitAssoc');
              try {
              // Si clic droit mais hit inconnu au down, refaire le hit-test à l'up (transform peut différer)
              int? entityForRightClick = hitEntity;
              int? assocForRightClick = hitAssoc;
              if (isRightClick && entityForRightClick == null && assocForRightClick == null) {
                entityForRightClick = _entityIndexAtScene(state, scenePos);
                assocForRightClick = _associationIndexAtScene(state, scenePos);
                if (_kClicksLog && (entityForRightClick != null || assocForRightClick != null)) {
                  debugPrint('[McdCanvas] OUTER clic droit hit retry -> entity=$entityForRightClick assoc=$assocForRightClick');
                }
              }
              if (_kClicksLog && (hitEntity != null || hitAssoc != null)) {
                debugPrint('[McdCanvas] OUTER tap/click button=$button isRight=$isRightClick hitEntity=$hitEntity hitAssoc=$hitAssoc');
              }
              // Clic droit sur un lien (mode Sélection) : menu contextuel Supprimer / Modifier cardinalités (comme Barrel).
              if (isRightClick && mode == CanvasMode.select && hasContent) {
                final eff = modeState.linkPrecisionMode;
                final linkIndex = _linkIndexAtScene(state, scenePos, eff);
                if (linkIndex != null && context.mounted) {
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: link context menu (right click select)');
                  state.selectLink(linkIndex);
                  _showLinkContextMenu(context, state, linkIndex, e.localPosition);
                  return;
                }
              }
              // En mode Ajouter entité / Ajouter association, un clic gauche crée toujours au point cliqué
              // (même si le clic tombe sur une entité ou association existante — évite 5+ clics pour « sortir »).
              if (!isRightClick && mode == CanvasMode.addEntity) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: addEntity -> _showNewEntityDialog');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap (addEntity) -> nouvelle entité scene=$scenePos');
                _showNewEntityDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (!isRightClick && mode == CanvasMode.addAssociation) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: addAssociation -> _showNewAssociationDialog');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap (addAssociation) -> nouvelle association scene=$scenePos');
                _showNewAssociationDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (entityForRightClick != null) {
                if (isRightClick) {
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: entity right-click menu');
                  if (_kClicksLog) debugPrint('[McdCanvas] OUTER clic droit entité index=$entityForRightClick -> menu attributs + supprimer');
                  state.selectEntity(entityForRightClick);
                  _showEntityRightClickMenu(context, state, entityForRightClick, e.localPosition);
                  return;
                }
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: entity tap _onEntityTap');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap entité index=$entityForRightClick mode=$mode');
                _onEntityTap(state, modeState, entityForRightClick);
                return;
              }
              if (assocForRightClick != null) {
                if (isRightClick) {
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: assoc right-click menu');
                  if (_kClicksLog) debugPrint('[McdCanvas] OUTER clic droit association index=$assocForRightClick -> menu avec Supprimer');
                  state.selectAssociation(assocForRightClick);
                  _showAssociationRightClickMenu(context, state, assocForRightClick, e.localPosition);
                  return;
                }
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: assoc tap _onAssociationTap');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap association index=$assocForRightClick mode=$mode');
                _onAssociationTap(state, modeState, assocForRightClick);
                return;
              }
              // Clic sur le vide (ou sur un lien) : en Sélection, sélectionner le lien et ouvrir le menu (modifier / supprimer) ou désélectionner.
              if (mode == CanvasMode.select) {
                final eff = modeState.linkPrecisionMode;
                final linkIndex = _linkIndexAtScene(state, scenePos, eff);
                if (linkIndex != null && context.mounted) {
                  if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: select -> link menu (click on link)');
                  final linkToggle = HardwareKeyboard.instance.isControlPressed || HardwareKeyboard.instance.isMetaPressed;
                  state.selectLink(linkIndex, toggle: linkToggle);
                  _showLinkContextMenu(context, state, linkIndex, e.localPosition);
                  return;
                }
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: select -> selectNone (empty)');
                state.selectNone();
                return;
              }
              if (mode == CanvasMode.addEntity) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: addEntity (empty) -> _showNewEntityDialog');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> nouvelle entité scene=$scenePos');
                _showNewEntityDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (mode == CanvasMode.addAssociation) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: addAssociation (empty) -> _showNewAssociationDialog');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> nouvelle association scene=$scenePos');
                _showNewAssociationDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (mode == CanvasMode.createLink) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: createLink empty -> no-op');
                return;
              }
              if (!hasContent) {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: no content -> _showNewEntityDialog');
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> canvas vide');
                _showNewEntityDialog(scenePos.dx, scenePos.dy);
              } else {
                if (_kVerboseCanvas) debugPrint('[McdCanvas] VERBOSE branch: fallthrough (no branch taken) mode=$mode hasContent=$hasContent');
              }
              } catch (tapErr, tapSt) {
                debugPrint('[McdCanvas] OUTER Listener.onPointerUp TAP HANDLING ERROR: $tapErr');
                debugPrint(tapSt.toString());
              }
            } catch (err, st) {
              debugPrint('[McdCanvas] OUTER Listener.onPointerUp ERROR: $err\n$st');
            }
          },
          onPointerCancel: (_) {
            _draggingEntityIndex = null;
            _draggingAssociationIndex = null;
            _dragEntityStartPositions = null;
            _dragAssocStartPositions = null;
            _draggingLinkHandle = null;
            _draggingLinkIndex = null;
            _draggingLinkSegment = false;
            _draggingLinkSegmentIndex = null;
            _pendingDragEntityIndex = null;
            _pendingDragScenePos = null;
            _pendingDragEntityStartPos = null;
            _pendingDragAssocIndex = null;
            _pendingDragAssocStartPos = null;
            _pendingDragLinkSegmentIndex = null;
            _draggingInheritanceSymbolParent = null;
            _draggingCifIndex = null;
            _cifDragOffset = null;
            _linkDragFromEntity = null;
            _linkDragSourceIndex = null;
            _linkDragStartScenePos = null;
            _linkDragCurrentScenePos = null;
            _dragStartScenePos = null;
            _dragEntityStartPos = null;
            _dragAssocStartPos = null;
            _dragEntityStartPositions = null;
            _dragAssocStartPositions = null;
            _rotatingArmAssocIndex = null;
            _rotatingArmIndex = null;
            setState(() {});
          },
          child: Stack(
          children: [
            Consumer<CanvasModeState>(
              builder: (context, modeState, _) {
                final draggingElement = _draggingEntityIndex != null || _draggingAssociationIndex != null;
                final draggingLinkHandle = _draggingLinkHandle != null;
                final draggingLinkSegment = _draggingLinkSegment;
                final rotatingArm = _rotatingArmAssocIndex != null;
                return InteractiveViewer(
                transformationController: _transform,
                minScale: _minScale,
                maxScale: _maxScale,
                boundaryMargin: const EdgeInsets.all(2000),
                panEnabled: modeState.mode != CanvasMode.createLink && !draggingElement && !draggingLinkHandle && !draggingLinkSegment && !rotatingArm,
                scaleEnabled: true,
                child: OverflowBox(
                  alignment: Alignment.topLeft,
                  maxWidth: sceneWidth,
                  maxHeight: sceneHeight,
                  child: SizedBox(
                    width: sceneWidth,
                    height: sceneHeight,
                    child: Listener(
                      behavior: HitTestBehavior.opaque,
                      onPointerDown: (e) {
                        try {
                          _pointerDownPosition = e.localPosition;
                          _pointerDownTime = DateTime.now();
                          _pointerDownButton = e.buttons; // bitmask: kPrimaryButton, kSecondaryMouseButton, etc.
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerDown pos=${e.localPosition} buttons=${e.buttons}');
                        } catch (err, st) {
                          debugPrint('[McdCanvas] Listener.onPointerDown ERROR: $err\n$st');
                        }
                      },
                      onPointerUp: (e) {
                        try {
                          final down = _pointerDownPosition;
                          final downTime = _pointerDownTime;
                          final button = _pointerDownButton;
                          _pointerDownPosition = null;
                          _pointerDownTime = null;
                          _pointerDownButton = 0;
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerUp pos=${e.localPosition} down=$down');
                          if (down == null || downTime == null) return;
                          final delta = (e.localPosition - down).distance;
                          final duration = DateTime.now().difference(downTime);
                          final isTap = delta <= _tapSlop && duration <= _tapMaxDuration;
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerUp delta=$delta duration=${duration.inMilliseconds}ms isTap=$isTap button=$button');
                          if (!isTap) return;
                          final state = context.read<McdState>();
                          final modeState = context.read<CanvasModeState>();
                          final hitEntity = _entityIndexAtScene(state, e.localPosition);
                          final hitAssoc = _associationIndexAtScene(state, e.localPosition);
                          final isRightClick = (button & kSecondaryMouseButton) != 0; // clic droit
                          if (hitEntity != null) {
                            if (isRightClick) {
                              if (_kClicksLog) debugPrint('[McdCanvas] INNER clic droit entité index=$hitEntity -> dialogue attributs');
                              _showEntityAttributesDialog(context, state, hitEntity);
                              return;
                            }
                            // Clic gauche : le GestureDetector de l'entité appelle _onEntityTap (évite double appel).
                            return;
                          }
                          if (hitAssoc != null) {
                            if (isRightClick) {
                              if (_kClicksLog) debugPrint('[McdCanvas] INNER clic droit association index=$hitAssoc -> dialogue attributs');
                              _showAssociationAttributesDialog(context, state, hitAssoc);
                              return;
                            }
                            // Clic gauche : le GestureDetector de l'association appelle _onAssociationTap.
                            return;
                          }
                          // Ne pas appeler _onCanvasTap pour addEntity/addAssociation : le Listener EXTERNE
                          // gère déjà le clic avec _viewportToScene (une seule ouverture de dialogue, pas de doublon).
                          if (modeState.mode == CanvasMode.addEntity || modeState.mode == CanvasMode.addAssociation) {
                            return;
                          }
                          _onCanvasTap(e.localPosition, sceneWidth, sceneHeight);
                        } catch (err, st) {
                          debugPrint('[McdCanvas] Listener.onPointerUp ERROR: $err\n$st');
                        }
                      },
                      onPointerSignal: (e) {
                        if (e is PointerScrollEvent && e.scrollDelta.dy != 0) {
                          if (e.scrollDelta.dy < 0) {
                            zoomIn();
                          } else {
                            zoomOut();
                          }
                        }
                      },
                      child: Stack(
                      fit: StackFit.expand,
                      clipBehavior: Clip.none,
                      children: [
                        const Positioned.fill(
                          child: IgnorePointer(
                            child: ColoredBox(color: AppTheme.canvasBackground),
                          ),
                        ),
                        Positioned.fill(
                          child: IgnorePointer(
                            child: LayoutBuilder(
                              builder: (context, c) {
                                return CustomPaint(
                                  painter: _GridPainter(showGrid: modeState.showGrid, gridSize: _gridSize),
                                  size: Size(c.maxWidth, c.maxHeight),
                                );
                              },
                            ),
                          ),
                        ),
                        Consumer2<McdState, CanvasModeState>(
                          builder: (context, state, modeState2, _) {
                            final hasContent = state.entities.isNotEmpty || state.associations.isNotEmpty;
                            final effectivePrecision = modeState2.linkPrecisionMode ||
                                (modeState2.mode == CanvasMode.createLink && _ctrlHeld);
                            if (_kCanvasDebug && state.entities.length + state.associations.length > 0) {
                              debugPrint('[McdCanvas] build content: entities=${state.entities.length} associations=${state.associations.length}');
                            }
                            final stack = Stack(
                              clipBehavior: Clip.none,
                              children: [
                                // Prévisualisation : départ = centre du bord + marge 10 px, fin = curseur (même logique que les liens finaux).
                                if (_linkDragStartScenePos != null && _linkDragCurrentScenePos != null) ...[
                                  Positioned.fill(
                                    child: CustomPaint(
                                      painter: _LinkDragPreviewPainter(
                                        from: _previewLinkFrom(state),
                                        to: _linkDragCurrentScenePos!,
                                      ),
                                      size: Size(sceneWidth, sceneHeight),
                                    ),
                                  ),
                                ],
                                // Liens d'abord (sous les formes).
                                Positioned.fill(
                                  child: ClipRect(
                                    child: IgnorePointer(
                                      child: _buildLinks(state, modeState2, sceneWidth, sceneHeight, effectivePrecision),
                                    ),
                                  ),
                                ),
                                // Entités et associations au-dessus des liens.
                                ...state.entities.asMap().entries.map((e) => _buildEntity(state, modeState2, e.key, e.value)),
                                ...state.associations.asMap().entries.map((a) => _buildAssociation(state, modeState2, a.key, a.value, false)),
                                // Héritage et CIF au-dessus des entités/associations pour être visibles et déplaçables.
                                Positioned.fill(
                                  child: IgnorePointer(
                                    child: _buildInheritanceLinks(state, sceneWidth, sceneHeight),
                                  ),
                                ),
                                Positioned.fill(
                                  child: IgnorePointer(
                                    child: _buildCifShapes(state, sceneWidth, sceneHeight),
                                  ),
                                ),
                                // Zones cliquables sur les boîtes cardinalités du lien sélectionné (éditer / supprimer).
                                if (state.selectedType == 'link' &&
                                    state.selectedIndex >= 0 &&
                                    state.selectedIndex < state.associationLinks.length) ...[
                                  ..._buildCardinalityBoxHitAreas(state, state.selectedIndex, effectivePrecision),
                                  // Poignées visibles aux deux extrémités du lien (déplaçables comme Barrel).
                                  ..._buildLinkHandleHints(state, state.selectedIndex, effectivePrecision),
                                  _buildLinkMenuButton(state, state.selectedIndex, effectivePrecision),
                                ],
                                if (!hasContent)
                                  Positioned.fill(
                                    child: GestureDetector(
                                      behavior: HitTestBehavior.opaque,
                                      onTap: () {
                                        try {
                                          if (_kClicksLog) debugPrint('[McdCanvas] EmptyCanvas.GestureDetector.onTap');
                                          _showNewEntityDialog(sceneWidth / 2, sceneHeight / 2);
                                        } catch (e, st) {
                                          debugPrint('[McdCanvas] EmptyCanvas.onTap ERROR: $e\n$st');
                                        }
                                      },
                                    ),
                                  ),
                                _buildLogo(),
                                if (_kCanvasDebug) _buildDebugOverlay(modeState2),
                              ],
                            );
                            if (widget.repaintBoundaryKey != null) {
                              return RepaintBoundary(key: widget.repaintBoundaryKey, child: stack);
                            }
                            return stack;
                          },
                        ),
                      ],  // outer Stack children
                    ),  // Stack (Listener's child)
                  ),
                ),
                ),
              );
              },
            ),
          ],
        ),
        );
      },
    );
  }

  void _onCanvasTap(Offset localPosition, double sceneWidth, double sceneHeight) {
    if (_kClicksLog || _kCanvasDebug) {
      debugPrint('[McdCanvas] _onCanvasTap ENTRY pos=$localPosition scene=${sceneWidth}x$sceneHeight');
    }
    try {
      final state = context.read<McdState>();
      final modeState = context.read<CanvasModeState>();
      final mode = modeState.mode;
      final hasContent = state.entities.isNotEmpty || state.associations.isNotEmpty;
      if (_kClicksLog || _kCanvasDebug) {
        _lastTapForDebug = localPosition;
        if (mounted) setState(() {});
        debugPrint('[McdCanvas] _onCanvasTap mode=$mode hasContent=$hasContent');
      }
      if (!hasContent) {
        if (_kClicksLog) debugPrint('[McdCanvas] _onCanvasTap -> _showNewEntityDialog (vide)');
        _showNewEntityDialog(localPosition.dx, localPosition.dy);
        return;
      }
      if (mode == CanvasMode.addEntity) {
        if (_kClicksLog) debugPrint('[McdCanvas] _onCanvasTap -> _showNewEntityDialog');
        _showNewEntityDialog(localPosition.dx, localPosition.dy);
        return;
      }
      if (mode == CanvasMode.addAssociation) {
        if (_kClicksLog) debugPrint('[McdCanvas] _onCanvasTap -> _showNewAssociationDialog');
        _showNewAssociationDialog(localPosition.dx, localPosition.dy);
        return;
      }
      if (mode == CanvasMode.select) {
        final eff = modeState.linkPrecisionMode;
        final linkIndex = _linkIndexAtScene(state, localPosition, eff);
        if (linkIndex != null) {
          final linkToggle = HardwareKeyboard.instance.isControlPressed || HardwareKeyboard.instance.isMetaPressed;
          state.selectLink(linkIndex, toggle: linkToggle);
          return;
        }
        state.selectNone();
      }
    } catch (e, st) {
      debugPrint('[McdCanvas] _onCanvasTap ERROR: $e');
      debugPrint(st.toString());
      rethrow;
    }
  }

  void _showNewEntityDialog(double x, double y) async {
    if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] _showNewEntityDialog ENTRY x=$x y=$y');
    if (!mounted) return;
    if (_newEntityDialogOpen) return;
    _newEntityDialogOpen = true;
    try {
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] showDialog Nouvelle entité...');
      final name = await showDialog<String>(
        context: context,
        useRootNavigator: true,
        barrierDismissible: false,
        builder: (ctx) {
          final c = TextEditingController();
          return AlertDialog(
            title: const Text('Nouvelle entité'),
            content: TextField(
              controller: c,
              autofocus: true,
              decoration: const InputDecoration(labelText: 'Nom de l\'entité'),
              onSubmitted: (v) => Navigator.pop(ctx, v.trim().isEmpty ? null : v.trim()),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, c.text.trim().isEmpty ? null : c.text.trim()),
                child: const Text('Créer'),
              ),
            ],
          );
        },
      );
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] dialog entité fermé name=$name');
      if (name == null || name.isEmpty) return;
      if (!mounted) return;
      final stateAfter = context.read<McdState>();
      final trimmed = name.trim();
      if (trimmed.isEmpty) return;
      if (stateAfter.entities.any((e) => (e['name'] as String?)?.trim() == trimmed)) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Une entité "$trimmed" existe déjà.')));
        return;
      }
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] appel state.addEntity("$trimmed", $x, $y)');
      stateAfter.addEntity(trimmed, x, y);
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] entité ajoutée "$trimmed" à ($x, $y)');
    } catch (e, st) {
      debugPrint('[McdCanvas] _showNewEntityDialog ERROR: $e');
      debugPrint(st.toString());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    } finally {
      _newEntityDialogOpen = false;
    }
  }

  void _showNewAssociationDialog(double x, double y) async {
    if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] _showNewAssociationDialog ENTRY x=$x y=$y');
    if (!mounted) return;
    if (_newAssociationDialogOpen) return;
    _newAssociationDialogOpen = true;
    try {
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] showDialog Nouvelle association...');
      final name = await showDialog<String>(
        context: context,
        useRootNavigator: true,
        barrierDismissible: false,
        builder: (ctx) {
          final c = TextEditingController();
          return AlertDialog(
            title: const Text('Nouvelle association'),
            content: TextField(
              controller: c,
              autofocus: true,
              decoration: const InputDecoration(labelText: 'Nom de l\'association'),
              onSubmitted: (v) => Navigator.pop(ctx, v.trim().isEmpty ? null : v.trim()),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, c.text.trim().isEmpty ? null : c.text.trim()),
                child: const Text('Créer'),
              ),
            ],
          );
        },
      );
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] dialog association fermé name=$name');
      if (name == null || name.isEmpty) return;
      if (!mounted) return;
      final stateAfter = context.read<McdState>();
      final trimmed = name.trim();
      if (trimmed.isEmpty) return;
      // Valider la création côté API si disponible
      List<String> errors = [];
      try {
        errors = await stateAfter.validateCreateAssociation(trimmed);
      } catch (e) {
        debugPrint('[McdCanvas] validateCreateAssociation: $e');
        // API injoignable : on crée quand même l'association localement
      }
      if (errors.isNotEmpty && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errors.join('\n')),
            backgroundColor: Theme.of(context).colorScheme.errorContainer,
            duration: const Duration(seconds: 4),
          ),
        );
        return;
      }
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] appel state.addAssociation("$trimmed", $x, $y)');
      stateAfter.addAssociation(trimmed, x, y);
      if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] association ajoutée "$trimmed" à ($x, $y)');
    } catch (e, st) {
      debugPrint('[McdCanvas] _showNewAssociationDialog ERROR: $e');
      debugPrint(st.toString());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    } finally {
      _newAssociationDialogOpen = false;
    }
  }

  void _onEntityTap(McdState state, CanvasModeState modeState, int index) {
    try {
      if (_kClicksLog) debugPrint('[McdCanvas] _onEntityTap index=$index mode=${modeState.mode}');
      if (modeState.mode == CanvasMode.createLink) {
        final entityName = state.getEntityNameByIndex(index);
        if (entityName == null) return;
        if (modeState.linkFirstTarget == null) {
          modeState.setLinkFirstTarget(entityName);
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cliquez sur une association pour terminer le lien.')));
          }
        } else {
          final assocName = modeState.linkFirstTarget;
          modeState.clearLinkFirstTarget();
          if (assocName != null) _showCardinalityDialog(assocName, entityName);
        }
        return;
      }
      final toggle = HardwareKeyboard.instance.isControlPressed || HardwareKeyboard.instance.isMetaPressed;
      state.selectEntity(index, toggle: toggle);
    } catch (e, st) {
      debugPrint('[McdCanvas] _onEntityTap ERROR: $e');
      debugPrint(st.toString());
    }
  }

  void _onAssociationTap(McdState state, CanvasModeState modeState, int index) {
    try {
      if (_kClicksLog) debugPrint('[McdCanvas] _onAssociationTap index=$index mode=${modeState.mode}');
      if (modeState.mode == CanvasMode.createLink) {
      final assocName = state.getAssociationNameByIndex(index);
      if (assocName == null) return;
      if (modeState.linkFirstTarget == null) {
        modeState.setLinkFirstTarget(assocName);
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cliquez sur une entité pour terminer le lien.')));
        }
      } else {
        final entityName = modeState.linkFirstTarget;
        modeState.clearLinkFirstTarget();
        if (entityName != null) _showCardinalityDialog(assocName, entityName);
      }
      return;
    }
    final toggle = HardwareKeyboard.instance.isControlPressed || HardwareKeyboard.instance.isMetaPressed;
    state.selectAssociation(index, toggle: toggle);
    } catch (e, st) {
      debugPrint('[McdCanvas] _onAssociationTap ERROR: $e');
      debugPrint(st.toString());
    }
  }

  /// Dialogue cardinalités pour créer un arc (lien) association–entité (style Barrel).
  /// [arrowAtAssociation] true = tirage entité → association, pointe côté association (sens du tracé).
  /// [arrowTipX], [arrowTipY] = point de relâchement (pointe de flèche). [entitySide] = 'left'|'right' côté entité.
  Future<void> _showCardinalityDialog(String associationName, String entityName, {
    bool arrowAtAssociation = false,
    double? arrowTipX,
    double? arrowTipY,
    String? entitySide,
  }) async {
    final messenger = ScaffoldMessenger.of(context);
    final state = context.read<McdState>();
    final result = await showDialog<({String cardEntity, String cardAssoc})>(
      context: context,
      builder: (ctx) {
        String vEntity = '1,n';
        String vAssoc = '1,n';
        return StatefulBuilder(
          builder: (ctx, setState) {
            return AlertDialog(
              title: const Text('Cardinalités MCD (Merise)'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<String>(
                    key: ValueKey('card_entity_$vEntity'),
                    value: McdCanvas.mcdCardinalities.contains(vEntity) ? vEntity : '1,n',
                    decoration: const InputDecoration(
                      labelText: 'Côté entité',
                      hintText: '0,1 | 1,1 | 0,n | 1,n',
                    ),
                    items: McdCanvas.mcdCardinalities
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (s) {
                      if (s != null) { vEntity = s; setState(() {}); }
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    key: ValueKey('card_assoc_$vAssoc'),
                    value: McdCanvas.mcdCardinalities.contains(vAssoc) ? vAssoc : '1,n',
                    decoration: const InputDecoration(
                      labelText: 'Côté association',
                      hintText: '0,1 | 1,1 | 0,n | 1,n',
                    ),
                    items: McdCanvas.mcdCardinalities
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (s) {
                      if (s != null) { vAssoc = s; setState(() {}); }
                    },
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, (cardEntity: vEntity, cardAssoc: vAssoc)),
                  child: const Text('OK'),
                ),
              ],
            );
          },
        );
      },
    );
    if (result == null) return;
    // Logique Barrel : valider l'ajout du lien avant de l'enregistrer
    final errors = await state.validateAddLink(
      associationName,
      entityName,
      result.cardEntity,
      result.cardAssoc,
    );
    if (errors.isNotEmpty && context.mounted) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(errors.join('\n')),
          backgroundColor: Theme.of(context).colorScheme.errorContainer,
          duration: const Duration(seconds: 5),
        ),
      );
      return;
    }
    // Ajuster la pointe de flèche pour qu'elle soit à côté de la forme (pas dedans) avant enregistrement.
    double? finalTipX = arrowTipX;
    double? finalTipY = arrowTipY;
    if (arrowTipX != null && arrowTipY != null) {
      Map<String, dynamic>? assoc;
      Map<String, dynamic>? ent;
      for (final a in state.associations) {
        if ((a['name'] as String?) == associationName) { assoc = a; break; }
      }
      for (final e in state.entities) {
        if ((e['name'] as String?) == entityName) { ent = e; break; }
      }
      if (assoc != null && ent != null) {
        final armIndex = bestArmIndexForLink(assoc, ent);
        final fromAssoc = associationArmPosition(assoc, {'arm_index': armIndex});
        final fromEntity = entityLinkEndpoint(ent, fromAssoc, link: entitySide != null ? {'entity_side': entitySide} : null);
        final tip = Offset(arrowTipX!, arrowTipY!);
        final tipMargin = state.arrowTipMargin;
        if (arrowAtAssociation) {
          final snapped = snapTipToAssociationBoundary(fromEntity, tip, assoc, arrowTipMargin: tipMargin);
          finalTipX = snapped.dx;
          finalTipY = snapped.dy;
        } else {
          final snapped = snapTipToEntityBoundary(fromAssoc, tip, ent, arrowTipMargin: tipMargin);
          finalTipX = snapped.dx;
          finalTipY = snapped.dy;
        }
      }
    }
    state.addAssociationLink(
      associationName,
      entityName,
      result.cardEntity,
      result.cardAssoc,
      arrowAtAssociation: arrowAtAssociation,
      arrowTipX: finalTipX,
      arrowTipY: finalTipY,
      entitySide: entitySide,
    );
    state.selectNone();
    if (context.mounted) {
      messenger.showSnackBar(SnackBar(content: Text('Lien $associationName — $entityName (${result.cardEntity} / ${result.cardAssoc}) créé.')));
    }
  }

  Widget _buildLinks(McdState state, CanvasModeState modeState, double sceneWidth, double sceneHeight, bool effectivePrecision) {
    final links = state.associationLinks;
    if (links.isEmpty) return const SizedBox.shrink();
    return SizedBox(
      width: sceneWidth,
      height: sceneHeight,
      child: CustomPaint(
        painter: _LinksPainter(
          entities: state.entities,
          associations: state.associations,
          links: links,
          selectedLinkIndices: state.selectedLinkIndices,
          linkPrecisionMode: effectivePrecision,
          showUmlCardinalities: state.showUmlCardinalities,
          arrowStartMargin: state.arrowStartMargin,
          arrowTipMargin: state.arrowTipMargin,
          defaultStrokeWidth: state.defaultStrokeWidth,
        ),
        size: Size(sceneWidth, sceneHeight),
      ),
    );
  }

  /// Poignées visibles aux deux extrémités du lien sélectionné (indiquent qu'on peut les déplacer, comme Barrel).
  List<Widget> _buildLinkHandleHints(McdState state, int linkIndex, bool precisionMode) {
    final seg = _getLinkSegment(state, linkIndex, precisionMode);
    const r = 10.0;
    return [
      Positioned(
        left: seg.from.dx - r,
        top: seg.from.dy - r,
        width: r * 2,
        height: r * 2,
        child: IgnorePointer(
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.primary.withValues(alpha: 0.25),
              border: Border.all(color: AppTheme.primary, width: 2),
            ),
          ),
        ),
      ),
      Positioned(
        left: seg.to.dx - r,
        top: seg.to.dy - r,
        width: r * 2,
        height: r * 2,
        child: IgnorePointer(
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.primary.withValues(alpha: 0.25),
              border: Border.all(color: AppTheme.primary, width: 2),
            ),
          ),
        ),
      ),
    ];
  }

  /// Deux zones cliquables (assoc, entity) pour le lien sélectionné — édition des cardinalités.
  List<Widget> _buildCardinalityBoxHitAreas(McdState state, int linkIndex, bool precisionMode) {
    final seg = _getLinkSegment(state, linkIndex, precisionMode);
    final centers = LinkArrow.cardinalityBoxCenters(seg.from, seg.to);
    const w = LinkArrow.cardinalityBoxWidth + 10.0;
    const h = LinkArrow.cardinalityBoxHeight + 10.0;
    return [
      Positioned(
        left: centers.assocCenter.dx - w / 2,
        top: centers.assocCenter.dy - h / 2,
        width: w,
        height: h,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => _showEditCardinalityDialog(context, state, linkIndex, whichAssoc: true),
          child: const SizedBox.expand(),
        ),
      ),
      Positioned(
        left: centers.entityCenter.dx - w / 2,
        top: centers.entityCenter.dy - h / 2,
        width: w,
        height: h,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => _showEditCardinalityDialog(context, state, linkIndex, whichAssoc: false),
          child: const SizedBox.expand(),
        ),
      ),
    ];
  }

  /// Bouton « Menu » affiché près du segment du lien sélectionné (tap = ouvrir le menu contextuel).
  Widget _buildLinkMenuButton(McdState state, int linkIndex, bool precisionMode) {
    final seg = _getLinkSegment(state, linkIndex, precisionMode);
    final mid = Offset((seg.from.dx + seg.to.dx) / 2, (seg.from.dy + seg.to.dy) / 2);
    const size = 32.0;
    return Positioned(
      left: mid.dx - size / 2,
      top: mid.dy - size / 2,
      width: size,
      height: size,
      child: Material(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(size / 2),
        elevation: 2,
        child: InkWell(
          borderRadius: BorderRadius.circular(size / 2),
          onTap: () => _showLinkContextMenu(context, state, linkIndex, mid),
          child: const Icon(Icons.more_horiz, size: 20),
        ),
      ),
    );
  }

  /// Menu contextuel sur un lien (clic droit) : style (coudé, courbe, sens, épaisseur), cardinalités, Supprimer.
  void _showLinkContextMenu(BuildContext context, McdState state, int linkIndex, Offset localPosition) {
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) return;
    final link = state.associationLinks[linkIndex];
    final lineStyle = link['line_style'] as String? ?? 'straight';
    final arrowReversed = link['arrow_reversed'] == true;
    final box = context.findRenderObject() as RenderBox?;
    final globalPos = box?.localToGlobal(localPosition) ?? Offset.zero;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(globalPos.dx, globalPos.dy, globalPos.dx + 1, globalPos.dy + 1),
      items: [
        const PopupMenuItem(value: 'edit', child: ListTile(leading: Icon(Icons.edit), title: Text('Modifier cardinalités'))),
        const PopupMenuDivider(),
        PopupMenuItem(value: 'style_straight', child: ListTile(leading: Icon(lineStyle == 'straight' ? Icons.check : null, size: 20), title: const Text('Ligne droite'))),
        PopupMenuItem(value: 'style_elbow_h', child: ListTile(leading: Icon(lineStyle == 'elbow_h' ? Icons.check : null, size: 20), title: const Text('Ligne coudée (horizontal)'))),
        PopupMenuItem(value: 'style_elbow_v', child: ListTile(leading: Icon(lineStyle == 'elbow_v' ? Icons.check : null, size: 20), title: const Text('Ligne coudée (verticale)'))),
        PopupMenuItem(value: 'style_curved', child: ListTile(leading: Icon(lineStyle == 'curved' ? Icons.check : null, size: 20), title: const Text('Courbe (Bézier)'))),
        PopupMenuItem(value: 'arrow_reverse', child: ListTile(leading: Icon(arrowReversed ? Icons.check : null, size: 20), title: Text(arrowReversed ? 'Sens de la flèche : inversé' : 'Inverser la pointe de la flèche'))),
        const PopupMenuItem(value: 'stroke', child: ListTile(leading: Icon(Icons.line_weight), title: Text('Épaisseur du trait…'))),
        const PopupMenuDivider(),
        const PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete_outline, color: AppTheme.error), title: Text('Supprimer le lien', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600)))),
      ],
    ).then((value) {
      if (!context.mounted) return;
      if (value == null) return;
      if (value == 'delete') {
        state.removeAssociationLinkAt(linkIndex);
        state.selectNone();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Lien supprimé.')));
      } else if (value == 'edit') {
        _showEditCardinalityDialog(context, state, linkIndex, whichAssoc: true);
      } else if (value == 'style_straight') {
        state.updateLinkStyle(linkIndex, lineStyle: 'straight');
      } else if (value == 'style_elbow_h') {
        state.updateLinkStyle(linkIndex, lineStyle: 'elbow_h');
      } else if (value == 'style_elbow_v') {
        state.updateLinkStyle(linkIndex, lineStyle: 'elbow_v');
      } else if (value == 'style_curved') {
        state.updateLinkStyle(linkIndex, lineStyle: 'curved');
      } else if (value == 'arrow_reverse') {
        state.updateLinkStyle(linkIndex, arrowReversed: !arrowReversed);
      } else if (value == 'stroke') {
        _showLinkStrokeWidthDialog(context, state, linkIndex);
      }
    });
  }

  void _showInheritanceSymbolContextMenu(BuildContext context, McdState state, String parentName, Offset localPosition) {
    final box = context.findRenderObject() as RenderBox?;
    final globalPos = box?.localToGlobal(localPosition) ?? Offset.zero;
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(globalPos.dx, globalPos.dy, size.width - globalPos.dx, size.height - globalPos.dy),
      color: AppTheme.surface,
      items: [
        const PopupMenuItem(value: 'panel', child: ListTile(leading: Icon(Icons.account_tree, size: 20), title: Text('Ouvrir le panneau Héritage'), dense: true)),
        const PopupMenuItem(value: 'reset', child: ListTile(leading: Icon(Icons.restart_alt, size: 20), title: Text('Réinitialiser la position'), dense: true)),
        const PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete_outline, size: 20, color: AppTheme.error), title: Text('Supprimer les liens d\'héritage', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600)), dense: true)),
      ],
    ).then((value) {
      if (!context.mounted) return;
      if (value == 'panel') {
        InheritancePanel.show(context);
      } else if (value == 'reset') {
        state.clearInheritanceSymbolPosition(parentName);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Position du symbole réinitialisée')));
      } else if (value == 'delete') {
        state.removeInheritanceLinksForParent(parentName);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Liens d\'héritage pour $parentName supprimés')));
      }
    });
  }

  void _showCifShapeContextMenu(BuildContext context, McdState state, int cifIndex, Offset localPosition) {
    final box = context.findRenderObject() as RenderBox?;
    final globalPos = box?.localToGlobal(localPosition) ?? Offset.zero;
    final size = MediaQuery.of(context).size;
    final name = (state.cifConstraints[cifIndex]['name'] as String?) ?? 'CIF';
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(globalPos.dx, globalPos.dy, size.width - globalPos.dx, size.height - globalPos.dy),
      color: AppTheme.surface,
      items: [
        PopupMenuItem(value: 'edit', child: ListTile(leading: const Icon(Icons.edit, size: 20), title: Text('Modifier « $name »…'), dense: true)),
        const PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete_outline, size: 20, color: AppTheme.error), title: Text('Supprimer la CIF', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600)), dense: true)),
      ],
    ).then((value) {
      if (!context.mounted) return;
      if (value == 'edit') {
        CifPanel.showEditDialogForIndex(context, state, cifIndex);
      } else if (value == 'delete') {
        state.removeCifConstraintAt(cifIndex);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('CIF supprimée')));
      }
    });
  }

  Future<void> _showLinkStrokeWidthDialog(BuildContext context, McdState state, int linkIndex) async {
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) return;
    final link = state.associationLinks[linkIndex];
    final w0 = (link['stroke_width'] as num?)?.toDouble() ?? 2.5;
    final c = TextEditingController(text: w0.toStringAsFixed(1));
    final result = await showDialog<double>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Épaisseur du trait'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Valeur entre 1 et 6 (défaut 2,5).', style: TextStyle(fontSize: 12)),
            const SizedBox(height: 16),
            TextField(
              controller: c,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Épaisseur'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(
            onPressed: () {
              final v = (double.tryParse(c.text) ?? w0).clamp(1.0, 6.0);
              Navigator.pop(ctx, v);
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
    if (result != null && context.mounted) {
      state.updateLinkStyle(linkIndex, strokeWidth: result);
    }
  }

  /// Ouvre le dialogue d'édition d'une cardinalité (côté association ou entité) avec option de supprimer le lien.
  Future<void> _showEditCardinalityDialog(BuildContext context, McdState state, int linkIndex, {required bool whichAssoc}) async {
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) return;
    final link = state.associationLinks[linkIndex];
    final currentCard = whichAssoc
        ? (link['card_assoc'] as String? ?? '1,n')
        : (link['card_entity'] as String? ?? link['cardinality'] as String? ?? '1,n');
    String value = currentCard;
    final result = await showDialog<String?>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setState) {
            return AlertDialog(
              title: Text(whichAssoc ? 'Cardinalité côté association' : 'Cardinalité côté entité'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DropdownButtonFormField<String>(
                    value: McdCanvas.mcdCardinalities.contains(value) ? value : '1,n',
                    decoration: InputDecoration(
                      labelText: whichAssoc ? 'Côté association' : 'Côté entité',
                      border: const OutlineInputBorder(),
                    ),
                    items: McdCanvas.mcdCardinalities
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (s) {
                      if (s != null) {
                        value = s;
                        setState(() {});
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: () => Navigator.pop(ctx, 'delete'),
                    icon: const Icon(Icons.delete_outline, size: 18),
                    label: const Text('Supprimer le lien'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppTheme.error,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, value),
                  child: const Text('OK'),
                ),
              ],
            );
          },
        );
      },
    );
    if (!context.mounted) return;
    if (result == null) return;
    if (result == 'delete') {
      state.removeAssociationLinkAt(linkIndex);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Lien supprimé.')));
      return;
    }
    // Règle Barrel : 1,1 côté association interdit si l'association a des attributs (rubriques).
    if (whichAssoc && result == '1,1') {
      final assocName = link['association'] as String?;
      if (assocName != null) {
        final ai = state.associations.indexWhere((a) => (a['name'] as String?) == assocName);
        if (ai >= 0) {
          final attrs = state.associations[ai]['attributes'] as List?;
          if (attrs != null && attrs.isNotEmpty) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: const Text('La cardinalité 1,1 côté association est interdite lorsque l\'association a des attributs (règle Barrel).'),
                backgroundColor: Theme.of(context).colorScheme.errorContainer,
                duration: const Duration(seconds: 4),
              ),
            );
            return;
          }
        }
      }
    }
    if (whichAssoc) {
      state.updateAssociationLinkCardinalities(linkIndex, link['card_entity'] as String? ?? '1,n', result);
    } else {
      state.updateAssociationLinkCardinalities(linkIndex, result, link['card_assoc'] as String? ?? '1,n');
    }
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Cardinalité modifiée : $result')));
  }

  Widget _buildInheritanceLinks(McdState state, double sceneWidth, double sceneHeight) {
    final layout = _getInheritanceSymbolLayout(state);
    if (layout.isEmpty) return const SizedBox.shrink();
    return CustomPaint(
      painter: _InheritancePainter(
        entities: state.entities,
        links: state.inheritanceLinks,
        selectedInheritanceIndices: state.selectedInheritanceIndices,
        symbolPositions: state.inheritanceSymbolPositions,
      ),
      size: Size(sceneWidth, sceneHeight),
    );
  }

  Widget _buildCifShapes(McdState state, double sceneWidth, double sceneHeight) {
    final constraints = state.cifConstraints;
    if (constraints.isEmpty) return const SizedBox.shrink();
    return CustomPaint(
      painter: _CifShapesPainter(constraints: constraints),
      size: Size(sceneWidth, sceneHeight),
    );
  }

  /// Message d'accueil quand le canvas est vide. Toute la carte est cliquable pour créer la première entité.
  Widget _buildEmptyHint(double sceneWidth, double sceneHeight, VoidCallback onCreateFirstEntity) {
    return Positioned(
      left: sceneWidth / 2 - 200,
      top: sceneHeight / 2 - 100,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onCreateFirstEntity,
        child: Container(
          width: 400,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppTheme.surface.withValues(alpha: 0.95),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.primary.withValues(alpha: 0.5)),
          ),
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.schema, size: 48, color: AppTheme.primary),
              SizedBox(height: 12),
              Text(
                'BarrelMCD – Modèle conceptuel de données',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              SizedBox(height: 12),
              Icon(Icons.add_circle_outline, size: 32, color: AppTheme.primary),
              SizedBox(height: 8),
              Text(
                'Cliquez ici pour créer votre première entité',
                style: TextStyle(color: AppTheme.primary, fontSize: 12, fontWeight: FontWeight.w500),
              ),
              SizedBox(height: 12),
              Text(
                'Ou : bouton « Entité » dans la barre puis clic sur le canvas.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 11, height: 1.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Normalise la liste d'attributs pour EntityBox : uniquement des Map avec au moins 'name'.
  static List<Map<String, dynamic>> _normalizeAttributesForDisplay(List<dynamic>? raw) {
    if (raw == null) return [];
    final out = <Map<String, dynamic>>[];
    for (final a in raw) {
      if (a is! Map) continue;
      final m = Map<String, dynamic>.from(a);
      out.add(m);
    }
    return out;
  }

  Widget _buildEntity(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> entity) {
    if (_kCanvasDebug && index == 0) {
      debugPrint('[McdCanvas] _buildEntity index=0 name=${entity['name']} total=${state.entities.length}');
    }
    final name = entity['name'] as String? ?? 'Entité';
    final pos = entity['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 100;
    final y = (pos?['y'] as num?)?.toDouble() ?? 100;
    final attrs = _normalizeAttributesForDisplay(entity['attributes'] as List?);
    final isWeak = entity['is_weak'] == true;
    final isFictive = entity['is_fictive'] == true;
    final selected = state.isEntitySelected(index);
    final entityWidth = (entity['width'] as num?)?.toDouble() ?? _entityWidth;

    return Positioned(
      left: x,
      top: y,
      child: GestureDetector(
        onTap: () {
          if (modeState.mode == CanvasMode.createLink) return;
          _onEntityTap(state, modeState, index);
        },
        onSecondaryTap: () {
          if (_kClicksLog) debugPrint('[McdCanvas] GestureDetector entité onSecondaryTap index=$index -> dialogue attributs');
          _showEntityAttributesDialog(context, state, index);
        },
        onLongPressStart: (d) => _lastLongPressPosition = d.globalPosition,
        onLongPress: () => _onEntityLongPress(context, state, index, entity),
        // Déplacement par glisser géré uniquement par le Listener global (évite conflit après 2e lien, comme Barrel).
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            EntityBox(
              name: name,
              attributes: attrs,
              selected: selected,
              isWeak: isWeak,
              isFictive: isFictive,
              width: entityWidth,
              onTap: () {
                if (modeState.mode == CanvasMode.createLink) return;
                _onEntityTap(state, modeState, index);
              },
              onAttributesAreaTap: () => _showEntityAttributesDialog(context, state, index),
            ),
            if (selected) _buildEntityResizeHandle(index),
          ],
        ),
      ),
    );
  }

  static const double _entityMinWidth = 120.0;
  static const double _entityMaxWidth = 400.0;

  Widget _buildEntityResizeHandle(int index) {
    return Positioned(
      right: 0,
      bottom: 0,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onPanUpdate: (d) {
          final state = context.read<McdState>();
          if (index < 0 || index >= state.entities.length) return;
          final e = state.entities[index];
          final cw = (e['width'] as num?)?.toDouble() ?? _entityWidth;
          final nw = (cw + d.delta.dx).clamp(_entityMinWidth, _entityMaxWidth);
          state.updateEntitySize(index, nw);
        },
        child: Tooltip(
          message: 'Glisser pour redimensionner l\'entité',
          child: Container(
            width: _resizeHandleSize,
            height: _resizeHandleSize,
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: 0.2),
              border: Border.all(color: AppTheme.primary, width: 1.5),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Icon(Icons.open_in_full, size: 14, color: AppTheme.primary),
          ),
        ),
      ),
    );
  }

  /// Menu au clic droit sur une entité : Modifier les attributs, Supprimer (toujours supprimable).
  void _showEntityRightClickMenu(BuildContext context, McdState state, int index, Offset localPosition) {
    final box = context.findRenderObject() as RenderBox?;
    final globalPos = box?.localToGlobal(localPosition) ?? Offset.zero;
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(globalPos.dx, globalPos.dy, size.width - globalPos.dx, size.height - globalPos.dy),
      items: [
        const PopupMenuItem(value: 'attrs', child: Text('Modifier les attributs')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer l\'entité', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (v == 'attrs') {
        _showEntityAttributesDialog(context, state, index);
      } else if (v == 'delete') {
        state.selectEntity(index);
        state.deleteSelected();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Entité supprimée.')));
      }
    });
  }

  void _onEntityLongPress(BuildContext context, McdState state, int index, Map<String, dynamic> entity) {
    state.selectEntity(index);
    final pos = _lastLongPressPosition ?? Offset(MediaQuery.of(context).size.width / 2, 200);
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(pos.dx, pos.dy, size.width - pos.dx, size.height - pos.dy),
      items: [
        const PopupMenuItem(value: 'rename', child: Text('Renommer')),
        const PopupMenuItem(value: 'attrs', child: Text('Modifier les attributs')),
        const PopupMenuItem(value: 'resize', child: Text('Redimensionner…')),
        PopupMenuItem(value: 'weak', child: Text((entity['is_weak'] == true) ? 'Entité normale' : 'Entité faible')),
        PopupMenuItem(value: 'fictive', child: Text((entity['is_fictive'] == true) ? 'Entité réelle (générée MLD)' : 'Entité fictive (non générée MLD)')),
        const PopupMenuItem(value: 'inheritance', child: Text('Définir héritage...')),
        const PopupMenuItem(value: 'duplicate', child: Text('Dupliquer l\'entité')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer l\'entité', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (v == 'rename') {
        _showRenameEntityDialog(context, state, index);
      } else if (v == 'attrs') {
        _showEntityAttributesDialog(context, state, index);
      } else if (v == 'resize') {
        _showEntityResizeDialog(context, state, index);
      } else if (v == 'duplicate') {
        final newIndex = state.duplicateEntity(index);
        if (newIndex >= 0) state.selectEntity(newIndex);
      } else if (v == 'weak') {
        _toggleEntityWeak(context, state, index);
      } else if (v == 'fictive') {
        _toggleEntityFictive(context, state, index);
      } else if (v == 'inheritance') {
        _showInheritanceDialog(context, state, index);
      } else if (v == 'delete') {
        state.deleteSelected();
      }
    });
  }

  /// Menu au clic droit sur une association : Texte/bras, Attributs, Redimensionner, Supprimer (toujours supprimable).
  void _showAssociationRightClickMenu(BuildContext context, McdState state, int index, Offset localPosition) {
    final box = context.findRenderObject() as RenderBox?;
    final globalPos = box?.localToGlobal(localPosition) ?? Offset.zero;
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(globalPos.dx, globalPos.dy, size.width - globalPos.dx, size.height - globalPos.dy),
      items: [
        const PopupMenuItem(value: 'text', child: Text('Texte et bras…')),
        const PopupMenuItem(value: 'attrs', child: Text('Attributs…')),
        const PopupMenuItem(value: 'resize', child: Text('Redimensionner…')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer l\'association', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (index < 0 || index >= state.associations.length) return;
      final association = state.associations[index];
      if (v == 'text') {
        _showAssociationTextDialog(context, state, index, association);
      } else if (v == 'attrs') {
        _showAssociationAttributesDialog(context, state, index);
      } else if (v == 'resize') {
        _showAssociationResizeDialog(context, state, index);
      } else if (v == 'delete') {
        state.selectAssociation(index);
        state.deleteSelected();
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Association supprimée.')));
      }
    });
  }

  void _onAssociationLongPress(BuildContext context, McdState state, int index, Map<String, dynamic> association) {
    state.selectAssociation(index);
    final pos = _lastLongPressPosition ?? Offset(MediaQuery.of(context).size.width / 2, 200);
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(pos.dx, pos.dy, size.width - pos.dx, size.height - pos.dy),
      items: [
        const PopupMenuItem(value: 'text', child: Text('Modifier le texte')),
        const PopupMenuItem(value: 'rename', child: Text('Renommer')),
        const PopupMenuItem(value: 'resize', child: Text('Redimensionner…')),
        const PopupMenuItem(value: 'arms', child: Text('Nombre de bras (1, 2, 3, 4…)')),
        const PopupMenuItem(value: 'attrs', child: Text('Attributs d\'association')),
        const PopupMenuItem(value: 'duplicate', child: Text('Dupliquer l\'association')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer l\'association', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (v == 'text' || v == 'rename') {
        _showAssociationTextDialog(context, state, index, association);
      } else if (v == 'resize') {
        _showAssociationResizeDialog(context, state, index);
      } else if (v == 'arms') {
        _showAssociationArmCountDialog(context, state, index);
      } else if (v == 'attrs') {
        _showAssociationAttributesDialog(context, state, index);
      } else if (v == 'duplicate') {
        final newIndex = state.duplicateAssociation(index);
        if (newIndex >= 0) state.selectAssociation(newIndex);
      } else if (v == 'delete') {
        state.deleteSelected();
      }
    });
  }

  Future<void> _showAssociationResizeDialog(BuildContext context, McdState state, int index) async {
    if (index < 0 || index >= state.associations.length) return;
    final a = state.associations[index];
    final w0 = (a['width'] as num?)?.toDouble() ?? 260.0;
    final h0 = (a['height'] as num?)?.toDouble() ?? 260.0;
    final cW = TextEditingController(text: w0.toStringAsFixed(0));
    final cH = TextEditingController(text: h0.toStringAsFixed(0));
    final result = await showDialog<({double width, double height})>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Redimensionner l\'association'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Min ${AssociationOval.minDiameter.toInt()} px, max ${AssociationOval.maxDiameter.toInt()} px.', style: const TextStyle(fontSize: 12)),
              const SizedBox(height: 16),
              TextField(
                controller: cW,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: 'Largeur (${AssociationOval.minDiameter.toInt()}-${AssociationOval.maxDiameter.toInt()})'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: cH,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: 'Hauteur (${AssociationOval.minDiameter.toInt()}-${AssociationOval.maxDiameter.toInt()})'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(
              onPressed: () {
                final w = (double.tryParse(cW.text) ?? w0).clamp(AssociationOval.minDiameter, AssociationOval.maxDiameter);
                final h = (double.tryParse(cH.text) ?? h0).clamp(AssociationOval.minDiameter, AssociationOval.maxDiameter);
                Navigator.pop(ctx, (width: w, height: h));
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
    if (result != null && context.mounted) {
      state.updateAssociationSize(index, result.width, result.height);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Taille : ${result.width.toStringAsFixed(0)} × ${result.height.toStringAsFixed(0)}')));
    }
  }

  Future<void> _showEntityResizeDialog(BuildContext context, McdState state, int index) async {
    if (index < 0 || index >= state.entities.length) return;
    final e = state.entities[index];
    final w0 = (e['width'] as num?)?.toDouble() ?? _entityWidth;
    final cW = TextEditingController(text: w0.toStringAsFixed(0));
    final result = await showDialog<double>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Redimensionner l\'entité'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Largeur (${_entityMinWidth.toInt()}-${_entityMaxWidth.toInt()} px).', style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 16),
            TextField(
              controller: cW,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(labelText: 'Largeur (${_entityMinWidth.toInt()}-${_entityMaxWidth.toInt()})'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(
            onPressed: () {
              final w = (double.tryParse(cW.text) ?? w0).clamp(_entityMinWidth, _entityMaxWidth);
              Navigator.pop(ctx, w);
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
    if (result != null && context.mounted) {
      state.updateEntitySize(index, result);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Largeur : ${result.toStringAsFixed(0)} px')));
    }
  }

  Future<void> _showAssociationArmCountDialog(BuildContext context, McdState state, int index) async {
    int count = ((state.associations[index]['arm_angles'] as List?)?.length ?? 2).clamp(1, 8);
    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text('Nombre de bras'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Choisissez le nombre de points de connexion autour de l\'association.'),
              const SizedBox(height: 16),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 8,
                runSpacing: 8,
                children: [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ChoiceChip(
                  label: Text('$n'),
                  selected: count == n,
                  onSelected: (_) => setState(() => count = n),
                )).toList(),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () { state.setAssociationArmCount(index, count); Navigator.pop(ctx); }, child: const Text('OK')),
          ],
        ),
      ),
    );
  }

  Future<void> _showRenameEntityDialog(BuildContext context, McdState state, int index) async {
    final name = state.getEntityNameByIndex(index) ?? '';
    final c = TextEditingController(text: name);
    final newName = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Renommer l\'entité'),
        content: TextField(controller: c, decoration: const InputDecoration(labelText: 'Nom'), autofocus: true, onSubmitted: (v) => Navigator.pop(ctx, v.trim())),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')), FilledButton(onPressed: () => Navigator.pop(ctx, c.text.trim()), child: const Text('OK'))],
      ),
    );
    if (newName == null || newName.isEmpty) return;
    if (!context.mounted) return;
    final e = Map<String, dynamic>.from(state.entities[index]);
    e['name'] = newName;
    state.updateEntityAt(index, e);
  }

  // ignore: unused_element - utilisé depuis le menu Fichier ou à réutiliser
  Future<void> _showRenameAssociationDialog(BuildContext context, McdState state, int index) async {
    final name = state.getAssociationNameByIndex(index) ?? '';
    final c = TextEditingController(text: name);
    final newName = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Renommer l\'association'),
        content: TextField(controller: c, decoration: const InputDecoration(labelText: 'Nom'), autofocus: true, onSubmitted: (v) => Navigator.pop(ctx, v.trim())),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')), FilledButton(onPressed: () => Navigator.pop(ctx, c.text.trim()), child: const Text('OK'))],
      ),
    );
    if (newName == null || newName.isEmpty) return;
    if (!context.mounted) return;
    final a = Map<String, dynamic>.from(state.associations[index]);
    a['name'] = newName;
    state.updateAssociationAt(index, a);
  }

  void _toggleEntityWeak(BuildContext context, McdState state, int index) {
    final e = Map<String, dynamic>.from(state.entities[index]);
    e['is_weak'] = (e['is_weak'] == true) ? false : true;
    state.updateEntityAt(index, e);
  }

  void _toggleEntityFictive(BuildContext context, McdState state, int index) {
    final e = Map<String, dynamic>.from(state.entities[index]);
    e['is_fictive'] = (e['is_fictive'] == true) ? false : true;
    state.updateEntityAt(index, e);
  }

  Future<void> _showInheritanceDialog(BuildContext context, McdState state, int index) async {
    final childName = state.getEntityNameByIndex(index);
    if (childName == null) return;
    final parents = state.entities.map((e) => e['name'] as String?).where((n) => n != null && n != childName).cast<String>().toList();
    if (parents.isEmpty) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucune autre entité pour héritage.')));
      return;
    }
    final parentName = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Entité parente'),
        content: DropdownButtonFormField<String>(
          decoration: const InputDecoration(labelText: 'Parent (généralisation)'),
          items: parents.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
          onChanged: (v) => Navigator.pop(ctx, v),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler'))],
      ),
    );
    if (parentName != null && context.mounted) {
      state.addInheritanceLink(parentName, childName);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$childName hérite de $parentName')));
    }
  }

  Future<void> _showEntityAttributesDialog(BuildContext context, McdState state, int index) async {
    final entity = state.entities[index];
    final edited = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => _EntityEditorDialog(entity: Map<String, dynamic>.from(entity)),
    );
    if (edited != null && context.mounted) {
      state.updateEntityAt(index, edited);
    }
  }

  Future<void> _showAssociationAttributesDialog(BuildContext context, McdState state, int index) async {
    final association = state.associations[index];
    final attrs = List<Map<String, dynamic>>.from((association['attributes'] as List?) ?? []);
    final updated = await showDialog<List<Map<String, dynamic>>>(
      context: context,
      builder: (ctx) => _AttributeListDialog(
        title: 'Attributs de l\'association ${association['name']}',
        attributes: attrs,
        isEntity: false,
      ),
    );
    if (updated != null && context.mounted) {
      final a = Map<String, dynamic>.from(association);
      a['attributes'] = updated;
      // Si l'association a des attributs, valider la règle Barrel (pas de 1,1 côté association).
      if (updated.isNotEmpty) {
        final errors = await state.validateAssociationAfterUpdate(
          association['name'] as String? ?? '',
          updated,
        );
        if (errors.isNotEmpty) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(errors.join('\n')),
                backgroundColor: Theme.of(context).colorScheme.errorContainer,
                duration: const Duration(seconds: 5),
              ),
            );
          }
          return;
        }
      }
      state.updateAssociationAt(index, a);
    }
  }

  /// Ouvre le dialogue des attributs de l'entité sélectionnée (appelé depuis la barre d'outils).
  void openEntityAttributesDialog(BuildContext context) {
    final state = context.read<McdState>();
    if (state.selectedType != 'entity' || state.selectedIndex < 0 || state.selectedIndex >= state.entities.length) return;
    _showEntityAttributesDialog(context, state, state.selectedIndex);
  }

  /// Ouvre le dialogue des attributs de l'association sélectionnée (appelé depuis la barre d'outils).
  void openAssociationAttributesDialog(BuildContext context) {
    final state = context.read<McdState>();
    if (state.selectedType != 'association' || state.selectedIndex < 0 || state.selectedIndex >= state.associations.length) return;
    _showAssociationAttributesDialog(context, state, state.selectedIndex);
  }

  Widget _buildAssociation(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> association, bool showArms) {
    if (_kCanvasDebug && index == 0) {
      debugPrint('[McdCanvas] _buildAssociation index=0 name=${association['name']} total=${state.associations.length}');
    }
    final name = association['name'] as String? ?? 'Association';
    final pos = association['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 300;
    final y = (pos?['y'] as num?)?.toDouble() ?? 300;
    final diameter = (association['width'] as num?)?.toDouble() ?? 260.0;
    final armExt = AssociationOval.armExtensionLength;
    final boxSize = diameter + 2 * armExt;
    final centerX = boxSize / 2;
    final centerY = boxSize / 2;
    final armRadius = diameter / 2 + armExt;
    final armAngles = (association['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()).toList() ?? [0.0, 180.0];
    final selected = state.isAssociationSelected(index);

    return Positioned(
      left: x,
      top: y,
      child: GestureDetector(
        onTap: () {
          if (modeState.mode == CanvasMode.createLink) return;
          _onAssociationTap(state, modeState, index);
        },
        onSecondaryTap: () {
          if (_kClicksLog) debugPrint('[McdCanvas] association onSecondaryTap -> dialogue texte/attributs');
          _showAssociationTextDialog(context, state, index, association);
        },
        onLongPressStart: (d) => _lastLongPressPosition = d.globalPosition,
        onLongPress: () => _onAssociationLongPress(context, state, index, association),
        // Déplacement par glisser géré uniquement par le Listener global (comme Barrel).
        child: SizedBox(
          width: boxSize,
          height: boxSize,
          child: Stack(
            clipBehavior: Clip.none,
            children: [
              // 1) Cercle + bras dessinés ensemble dans l’oval (même centre = plus de décalage).
              Positioned(
                left: centerX - diameter / 2,
                top: centerY - diameter / 2,
                child: AssociationOval(
                  name: name,
                  selected: selected,
                  fixedDiameter: diameter,
                  armAngles: showArms ? armAngles : const [],
                  onSecondaryTap: () => _showAssociationTextDialog(context, state, index, association),
                  onSize: (ow, oh) {
                    if (ow != diameter || oh != diameter) {
                      state.updateAssociationSize(index, ow, oh);
                    }
                  },
                ),
              ),
              // Poignée de redimensionnement visible quand l'association est sélectionnée (à tout moment).
              if (selected) _buildAssociationResizeHandle(boxSize, index),
            ],
          ),
        ),
      ),
    );
  }

  static const double _resizeHandleSize = 24.0;

  Widget _buildAssociationResizeHandle(double boxSize, int index) {
    return Positioned(
      left: boxSize - _resizeHandleSize,
      top: boxSize - _resizeHandleSize,
      width: _resizeHandleSize,
      height: _resizeHandleSize,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onPanUpdate: (d) {
          final state = context.read<McdState>();
          if (index < 0 || index >= state.associations.length) return;
          final a = state.associations[index];
          final cw = (a['width'] as num?)?.toDouble() ?? 260.0;
          final ch = (a['height'] as num?)?.toDouble() ?? 260.0;
          final nw = (cw + d.delta.dx).clamp(AssociationOval.minDiameter, AssociationOval.maxDiameter);
          final nh = (ch + d.delta.dy).clamp(AssociationOval.minDiameter, AssociationOval.maxDiameter);
          state.updateAssociationSize(index, nw, nh);
        },
        child: Tooltip(
          message: 'Glisser pour redimensionner l\'association',
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.primary.withValues(alpha: 0.2),
              border: Border.all(color: AppTheme.primary, width: 1.5),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Icon(Icons.open_in_full, size: 14, color: AppTheme.primary),
          ),
        ),
      ),
    );
  }

  /// Zone au bout du bras (petit) pour le faire tourner par glissement.
  Widget _buildArmDragZone(double centerX, double centerY, double armRadius, double angleDeg, void Function(double) onAngleChanged) {
    final rad = angleDeg * math.pi / 180;
    final px = centerX + armRadius * math.cos(rad);
    final py = centerY + armRadius * math.sin(rad);
    const zoneSize = 28.0;
    return Positioned(
      left: px - zoneSize / 2,
      top: py - zoneSize / 2,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onPanStart: (_) {},
        onPanUpdate: (d) {
          final fingerX = px - zoneSize / 2 + d.localPosition.dx;
          final fingerY = py - zoneSize / 2 + d.localPosition.dy;
          final v = Offset(fingerX - centerX, fingerY - centerY);
          double angle = math.atan2(v.dy, v.dx) * 180 / math.pi;
          if (angle < 0) angle += 360;
          onAngleChanged(angle);
        },
        child: Tooltip(
          message: 'Glisser pour faire tourner le bras autour de l\'association',
          child: Container(
            width: zoneSize,
            height: zoneSize,
            color: Colors.transparent,
          ),
        ),
      ),
    );
  }

  // ignore: unused_element - variante de zone de drag du bras, conservée pour usage futur
  Widget _buildArmHandle({
    required double centerX,
    required double centerY,
    required double armRadius,
    required double angleDeg,
    required void Function(double angleDeg) onAngleChanged,
    required VoidCallback onSecondaryTap,
  }) {
    final rad = angleDeg * 3.14159265359 / 180;
    final px = centerX + armRadius * math.cos(rad);
    final py = centerY + armRadius * math.sin(rad);
    const handleRadius = 10.0;
    return Positioned(
      left: px - handleRadius,
      top: py - handleRadius,
      child: GestureDetector(
        onSecondaryTap: onSecondaryTap,
        onPanStart: (_) {},
        onPanUpdate: (d) {
          final fingerX = px - handleRadius + d.localPosition.dx;
          final fingerY = py - handleRadius + d.localPosition.dy;
          final v = Offset(fingerX - centerX, fingerY - centerY);
          double angle = math.atan2(v.dy, v.dx) * 180 / math.pi;
          if (angle < 0) angle += 360;
          onAngleChanged(angle);
        },
        child: Tooltip(
          message: 'Glisser pour tourner le bras. Clic droit : supprimer ce bras.',
          child: Container(
            width: handleRadius * 2,
            height: handleRadius * 2,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.primary.withValues(alpha: 0.4),
              border: Border.all(color: AppTheme.primary, width: 1.5),
            ),
          ),
        ),
      ),
    );
  }

  // ignore: unused_element - clic droit sur bras pour supprimer, conservé pour usage futur
  void _onArmSecondaryTap(BuildContext context, McdState state, int assocIndex, int armIndex, int armCount) {
    if (armCount <= 1) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Il doit rester au moins un bras.')));
      return;
    }
    showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Supprimer ce bras ?'),
        content: const Text('Le lien éventuellement attaché à ce bras sera réaffecté au premier bras.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Supprimer')),
        ],
      ),
    ).then((ok) {
      if (ok == true && context.mounted) state.removeAssociationArm(assocIndex, armIndex);
    });
  }

  Future<void> _showAssociationTextDialog(BuildContext context, McdState state, int index, Map<String, dynamic> association) async {
    final nameController = TextEditingController(text: association['name']?.toString() ?? 'Association');
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Nom de l\'association'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: 'Nom',
                hintText: 'ex. passer commande',
                border: OutlineInputBorder(),
              ),
              autofocus: true,
            ),
            const SizedBox(height: 12),
            TextButton.icon(
              onPressed: () => Navigator.pop(ctx, {'openAttributes': true}),
              icon: const Icon(Icons.tune, size: 18),
              label: const Text('Attributs de l\'association…'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(
            onPressed: () {
              final name = nameController.text.trim();
              Navigator.pop(ctx, {'name': name.isEmpty ? 'Association' : name});
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
    if (result == null) return;
    if (result['openAttributes'] == true) {
      if (context.mounted) _showAssociationAttributesDialog(context, state, index);
      return;
    }
    if (result['name'] != null) {
      final a = Map<String, dynamic>.from(association);
      a['name'] = result['name'];
      state.updateAssociationAt(index, a);
    }
  }

  Widget _buildLogo() {
    return Positioned(
      left: 20,
      top: 20,
      child: IgnorePointer(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.black26,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: AppTheme.textTertiary.withValues(alpha: 0.3)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Image.asset(
                'assets/images/logo.png',
                width: 24,
                height: 24,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) => const Icon(Icons.storage, color: AppTheme.primary, size: 24),
              ),
              const SizedBox(width: 6),
              const Text(
                'BarrelMCD',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDebugOverlay(CanvasModeState modeState) {
    final mode = modeState.mode;
    final modeStr = switch (mode) {
      CanvasMode.select => 'Sélection',
      CanvasMode.addEntity => 'Entité (E)',
      CanvasMode.addAssociation => 'Association (A)',
      CanvasMode.createLink => 'Lien (L)',
    };
    final last = _lastTapForDebug;
    return Positioned(
      left: 20,
      top: 55,
      child: IgnorePointer(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.black87,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: AppTheme.primary, width: 1),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('DEBUG', style: TextStyle(color: AppTheme.warning, fontSize: 10, fontWeight: FontWeight.bold)),
              Text('Mode: $modeStr', style: const TextStyle(color: Colors.white, fontSize: 11)),
              Text('Dernier clic: ${last != null ? '(${last.dx.toStringAsFixed(0)}, ${last.dy.toStringAsFixed(0)})' : '—'}', style: const TextStyle(color: Colors.white70, fontSize: 10)),
              const Text('Grille: voir console [McdCanvas]', style: TextStyle(color: Colors.white54, fontSize: 9)),
            ],
          ),
        ),
      ),
    );
  }

}

class _GridPainter extends CustomPainter {
  _GridPainter({required this.showGrid, required this.gridSize});
  final bool showGrid;
  final double gridSize;

  static int _paintCount = 0;

  @override
  void paint(Canvas canvas, Size size) {
    if (_kCanvasDebug && _paintCount < 5) {
      _paintCount++;
      debugPrint('[McdCanvas] _GridPainter.paint #$_paintCount showGrid=$showGrid size=${size.width}x${size.height}');
    }
    if (!showGrid) return;
    const majorEvery = 5;
    final minor = Paint()
      ..color = AppTheme.gridMinor
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    final major = Paint()
      ..color = AppTheme.gridMajor
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;
    for (double x = 0; x <= size.width; x += gridSize) {
      final isMajor = (x / gridSize).round() % majorEvery == 0;
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), isMajor ? major : minor);
    }
    for (double y = 0; y <= size.height; y += gridSize) {
      final isMajor = (y / gridSize).round() % majorEvery == 0;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), isMajor ? major : minor);
    }
  }

  @override
  bool shouldRepaint(covariant _GridPainter oldDelegate) =>
      oldDelegate.showGrid != showGrid || oldDelegate.gridSize != gridSize;
}

/// Dessine le petit bras : un trait du bord du cercle d'association jusqu'au cercle invisible.
class _BrasPainter extends CustomPainter {
  _BrasPainter({
    required this.center,
    required this.associationRadius,
    required this.armRadius,
    required this.angleDeg,
  });
  final Offset center;
  final double associationRadius;
  final double armRadius;
  final double angleDeg;

  @override
  void paint(Canvas canvas, Size size) {
    final rad = angleDeg * math.pi / 180;
    final from = Offset(
      center.dx + associationRadius * math.cos(rad),
      center.dy + associationRadius * math.sin(rad),
    );
    final to = Offset(
      center.dx + armRadius * math.cos(rad),
      center.dy + armRadius * math.sin(rad),
    );
    canvas.drawLine(
      from,
      to,
      Paint()
        ..color = AppTheme.primary
        ..strokeWidth = 2
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke,
    );
  }

  @override
  bool shouldRepaint(covariant _BrasPainter oldDelegate) =>
      oldDelegate.angleDeg != angleDeg ||
      oldDelegate.associationRadius != associationRadius ||
      oldDelegate.armRadius != armRadius;
}

/// Prévisualisation pendant le tirage d'un lien : trait + chevron. [from] = centre du bord (mis à jour selon le curseur).
class _LinkDragPreviewPainter extends CustomPainter {
  _LinkDragPreviewPainter({required this.from, required this.to});
  final Offset from;
  final Offset to;

  @override
  void paint(Canvas canvas, Size size) {
    final dx = to.dx - from.dx;
    final dy = to.dy - from.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return;
    final ux = dx / dist;
    final uy = dy / dist;
    final paint = Paint()
      ..color = AppTheme.primary.withValues(alpha: 0.85)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(from, to, paint);
    const arrowSize = 10.0;
    final angle = math.atan2(uy, ux);
    final left = Offset(
      to.dx - arrowSize * math.cos(angle) + arrowSize * 0.6 * math.sin(angle),
      to.dy - arrowSize * math.sin(angle) - arrowSize * 0.6 * math.cos(angle),
    );
    final right = Offset(
      to.dx - arrowSize * math.cos(angle) - arrowSize * 0.6 * math.sin(angle),
      to.dy - arrowSize * math.sin(angle) + arrowSize * 0.6 * math.cos(angle),
    );
    final path = Path()..moveTo(to.dx, to.dy)..lineTo(left.dx, left.dy)..lineTo(right.dx, right.dy)..close();
    canvas.drawPath(path, Paint()..color = paint.color..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = paint.color..style = PaintingStyle.stroke..strokeWidth = 1.5);
  }

  @override
  bool shouldRepaint(covariant _LinkDragPreviewPainter oldDelegate) =>
      oldDelegate.from != from || oldDelegate.to != to;
}

class _LinksPainter extends CustomPainter {
  _LinksPainter({
    required this.entities,
    required this.associations,
    required this.links,
    this.selectedLinkIndices = const {},
    this.linkPrecisionMode = false,
    this.showUmlCardinalities = false,
    this.arrowStartMargin = 10.0,
    this.arrowTipMargin = 12.0,
    this.defaultStrokeWidth = 2.5,
  });

  final List<Map<String, dynamic>> entities;
  final List<Map<String, dynamic>> associations;
  final List<Map<String, dynamic>> links;
  final Set<int> selectedLinkIndices;
  final bool linkPrecisionMode;
  /// Si true, afficher les cardinalités en notation UML (0..1, 1..*) au lieu du MCD (0,1, 1,n).
  final bool showUmlCardinalities;
  final double arrowStartMargin;
  final double arrowTipMargin;
  final double defaultStrokeWidth;

  /// Hauteur d'une entité (comme _entityIndexAtScene) pour centrer le lien.
  double _entityHeight(Map<String, dynamic> e) {
    final attrs = (e['attributes'] as List?) ?? [];
    final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
    return (e['height'] as num?)?.toDouble() ??
        (_entityMinHeight + (attrCount > 0 ? attrCount * 24.0 : 0));
  }

  /// Point d'ancrage du lien sur l'entité : bras (entity_arm_index) ou bord gauche/droit.
  Offset _entityLinkEndpoint(Map<String, dynamic> e, Offset associationArmPos, [Map<String, dynamic>? link]) {
    return entityLinkEndpoint(e, associationArmPos, link: link, entityWidth: _entityWidth);
  }

  /// Centre de l'association (centre du cercle visible et du cercle invisible).
  Offset _associationCenter(Map<String, dynamic> a) {
    final pos = a['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final boxSize = w + 2 * AssociationOval.armExtensionLength;
    return Offset(x + boxSize / 2, y + boxSize / 2);
  }

  /// En mode Simple : point sur le bord du cercle de l'association vers l'entité (lien droit centre → entité).
  Offset _associationSimpleAttachment(Map<String, dynamic> a, Offset entitySidePoint) {
    final center = _associationCenter(a);
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final radius = w / 2;
    final dx = entitySidePoint.dx - center.dx;
    final dy = entitySidePoint.dy - center.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return Offset(center.dx + radius, center.dy);
    return Offset(center.dx + radius * (dx / dist), center.dy + radius * (dy / dist));
  }

  Offset _associationArmPosition(Map<String, dynamic> a, Map<String, dynamic> link) {
    final center = _associationCenter(a);
    final w = (a['width'] as num?)?.toDouble() ?? 260.0;
    final h = (a['height'] as num?)?.toDouble() ?? 260.0;
    final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
    final armIndex = (link['arm_index'] as num?)?.toInt() ?? 0;
    final angle = (armIndex < angles.length ? angles[armIndex].toDouble() : 0.0);
    return armPositionFromCenter(center, angle, w, h);
  }

  double _associationArmAngle(Map<String, dynamic> a, Map<String, dynamic> link) {
    final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
    final armIndex = (link['arm_index'] as num?)?.toInt() ?? 0;
    return (armIndex < angles.length ? angles[armIndex].toDouble() : 0.0);
  }

  Map<String, dynamic>? _findEntity(String name) {
    for (final e in entities) {
      if (e['name'] == name) return e;
    }
    return null;
  }

  Map<String, dynamic>? _findAssociation(String name) {
    for (final a in associations) {
      if (a['name'] == name) return a;
    }
    return null;
  }

  @override
  void paint(Canvas canvas, Size size) {
    // Clip à la scène : évite qu'un lien (ex. 2e flèche avec coordonnées aberrantes) déborde et "bouffe" le dessin.
    canvas.save();
    canvas.clipRect(Rect.fromLTWH(0, 0, size.width, size.height));
    for (int i = 0; i < links.length; i++) {
      final link = links[i];
      final assocName = link['association'] as String?;
      final entityName = link['entity'] as String?;
      if (assocName == null || entityName == null) continue;
      final assoc = _findAssociation(assocName);
      final ent = _findEntity(entityName);
      if (assoc == null || ent == null) continue;
      final center = _associationCenter(assoc);
      final entityPt = _entityLinkEndpoint(ent, center, link);
      final assocPt = _associationSimpleAttachment(assoc, entityPt);
      final cardEntity = link['card_entity'] as String? ?? link['cardinality'] as String? ?? '1,n';
      final cardAssoc = link['card_assoc'] as String? ?? '1,n';
      final arrowAtAssociation = link['arrow_at_association'] == true;
      final tipX = (link['arrow_tip_x'] as num?)?.toDouble();
      final tipY = (link['arrow_tip_y'] as num?)?.toDouble();
      final hasStoredTip = tipX != null && tipY != null;
      final arrowTip = hasStoredTip ? Offset(tipX!, tipY!) : null;
      // Pointe de flèche = point de relâchement (là où l'utilisateur a relâché), pas un point calculé sur la forme.
      final Offset from;
      final Offset to;
      final String cardFrom;
      final String cardTo;
      if (arrowTip != null) {
        if (arrowAtAssociation) {
          from = entityPt;
          to = arrowTip;
          cardFrom = cardEntity;
          cardTo = cardAssoc;
        } else {
          from = _associationSimpleAttachment(assoc, arrowTip);
          to = arrowTip;
          cardFrom = cardAssoc;
          cardTo = cardEntity;
        }
      } else {
        if (arrowAtAssociation) {
          from = entityPt;
          to = assocPt;
          cardFrom = cardEntity;
          cardTo = cardAssoc;
        } else {
          from = assocPt;
          to = entityPt;
          cardFrom = cardAssoc;
          cardTo = cardEntity;
        }
      }
      // Début = ancre (centre du bord). Fin = snap au bord cible + marge (link_geometry).
      final Offset effectiveFrom = from;
      Offset effectiveTo = (arrowAtAssociation)
          ? snapTipToAssociationBoundary(from, to, assoc, arrowTipMargin: arrowTipMargin)
          : snapTipToEntityBoundary(from, to, ent, entityWidth: _entityWidth, arrowTipMargin: arrowTipMargin);
      // Secours uniquement pour flèche vers l'entité : si la pointe est derrière [from], segment minimal.
      // Pour flèche vers l'association (droite→gauche) : ne jamais remplacer la pointe snapée, sinon elle "remonte".
      if (!arrowAtAssociation) {
        final dx = to.dx - from.dx;
        final dy = to.dy - from.dy;
        final distTo = math.sqrt(dx * dx + dy * dy);
        if (distTo >= 1e-6) {
          final ux = dx / distTo;
          final uy = dy / distTo;
          final segDx = effectiveTo.dx - from.dx;
          final segDy = effectiveTo.dy - from.dy;
          if (segDx * ux + segDy * uy <= 0) {
            final minLen = arrowStartMargin + 2.0;
            effectiveTo = Offset(from.dx + ux * minLen, from.dy + uy * minLen);
          }
        }
      }
      // Longueur minimale du segment : si association et entité sont très proches (ex. lien à droite),
      // le snap peut écraser le segment et les formes (point, flèche) se superposent en tache.
      double segDx = effectiveTo.dx - effectiveFrom.dx;
      double segDy = effectiveTo.dy - effectiveFrom.dy;
      double segDist = math.sqrt(segDx * segDx + segDy * segDy);
      if (segDist < kMinLinkSegmentLength && segDist >= 1e-6) {
        final scale = kMinLinkSegmentLength / segDist;
        effectiveTo = Offset(
          effectiveFrom.dx + segDx * scale,
          effectiveFrom.dy + segDy * scale,
        );
      }
      final displayFrom = showUmlCardinalities ? McdState.mcdToUmlCardinality(cardFrom) : cardFrom;
      final displayTo = showUmlCardinalities ? McdState.mcdToUmlCardinality(cardTo) : cardTo;
      final selected = selectedLinkIndices.contains(i);
      final lineStyle = link['line_style'] as String? ?? 'straight';
      final curved = lineStyle == 'curved';
      List<Offset> controlPoints = const [];
      if (lineStyle == 'elbow_h') {
        controlPoints = [Offset(effectiveTo.dx, effectiveFrom.dy)];
      } else if (lineStyle == 'elbow_v') {
        controlPoints = [Offset(effectiveFrom.dx, effectiveTo.dy)];
      }
      final arrowReversed = link['arrow_reversed'] == true;
      final strokeW = (link['stroke_width'] as num?)?.toDouble() ?? defaultStrokeWidth;
      final arrowHead = link['arrow_head'] as String? ?? 'arrow';
      final startCap = link['start_cap'] as String? ?? 'dot';
      LinkArrow.paintWithCapsules(
        canvas,
        from: effectiveFrom,
        to: effectiveTo,
        cardinalityEntity: displayTo,
        cardinalityAssoc: displayFrom,
        associationArmAngleDeg: 0,
        selected: selected,
        curved: curved,
        controlPoints: controlPoints,
        arrowReversed: arrowReversed,
        strokeWidth: strokeW.clamp(1.0, 6.0),
        arrowHead: arrowHead,
        startCap: startCap,
        arrowStartMargin: arrowStartMargin,
      );
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _LinksPainter oldDelegate) => true;
}

class _InheritancePainter extends CustomPainter {
  _InheritancePainter({
    required this.entities,
    required this.links,
    this.selectedInheritanceIndices = const {},
    this.symbolPositions = const {},
  });

  final List<Map<String, dynamic>> entities;
  final List<Map<String, dynamic>> links;
  final Set<int> selectedInheritanceIndices;
  final Map<String, Map<String, double>> symbolPositions;

  static const double _symbolWidth = 72.0;
  static const double _symbolTextHeight = 28.0;
  static const double _socleHeight = 14.0;
  static const double _arrowSize = 8.0;

  Offset _entityCenter(Map<String, dynamic> e) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    return Offset(x + _entityWidth / 2, y + _entityMinHeight / 2);
  }

  Offset _entityBottomCenter(Map<String, dynamic> e) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final attrs = (e['attributes'] as List?) ?? [];
    final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
    final h = (e['height'] as num?)?.toDouble() ??
        (_entityMinHeight + (attrCount > 0 ? attrCount * 24.0 : 0));
    return Offset(x + _entityWidth / 2, y + h);
  }

  Offset _entityTopCenter(Map<String, dynamic> e) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    return Offset(x + _entityWidth / 2, y);
  }

  Map<String, dynamic>? _findEntity(String name) {
    for (final e in entities) {
      if (e['name'] == name) return e;
    }
    return null;
  }

  void _drawInheritanceSymbol(Canvas canvas, Offset center, bool selected, String label) {
    final color = selected ? AppTheme.secondary : AppTheme.primary.withValues(alpha: 0.9);
    final stroke = Paint()
      ..color = color
      ..strokeWidth = selected ? 2.0 : 1.2
      ..style = PaintingStyle.stroke;
    final fill = Paint()..color = color.withValues(alpha: 0.15)..style = PaintingStyle.fill;
    final halfW = _symbolWidth / 2;
    final textTop = center.dy - _symbolTextHeight - _socleHeight;
    final socleY = textTop + _symbolTextHeight;
    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(center.dx - halfW, textTop, _symbolWidth, _symbolTextHeight),
      const Radius.circular(6),
    );
    canvas.drawRRect(rect, fill);
    canvas.drawRRect(rect, stroke);
    final paragraphBuilder = ui.ParagraphBuilder(ui.ParagraphStyle(
      fontSize: 12,
      fontWeight: FontWeight.w600,
      fontFamily: 'sans-serif',
    ))..pushStyle(ui.TextStyle(color: color));
    paragraphBuilder.addText(label);
    final paragraph = paragraphBuilder.build()..layout(ui.ParagraphConstraints(width: _symbolWidth - 8));
    canvas.drawParagraph(
      paragraph,
      Offset(center.dx - paragraph.width / 2, textTop + (_symbolTextHeight - paragraph.height) / 2),
    );
    canvas.drawLine(
      Offset(center.dx - halfW, socleY),
      Offset(center.dx + halfW, socleY),
      stroke,
    );
    const nArrows = 5;
    for (int i = 0; i < nArrows; i++) {
      final t = (i + 1) / (nArrows + 1);
      final ax = center.dx - halfW + t * _symbolWidth;
      final path = Path()
        ..moveTo(ax, socleY)
        ..lineTo(ax - _arrowSize / 2, socleY + _arrowSize)
        ..lineTo(ax + _arrowSize / 2, socleY + _arrowSize)
        ..close();
      canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
      canvas.drawPath(path, stroke);
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final byParent = <String, List<Map<String, dynamic>>>{};
    for (final link in links) {
      final p = link['parent'] as String? ?? '';
      byParent.putIfAbsent(p, () => []).add(link);
    }
    for (final entry in byParent.entries) {
      final parent = _findEntity(entry.key);
      final childrenLinks = entry.value;
      if (parent == null || childrenLinks.isEmpty) continue;
      final parentCenter = _entityCenter(parent);
      final parentBottom = _entityBottomCenter(parent);
      final children = childrenLinks
          .map((l) => _findEntity(l['child'] as String? ?? ''))
          .whereType<Map<String, dynamic>>()
          .toList();
      if (children.isEmpty) continue;
      final childCenters = children.map((c) => _entityTopCenter(c)).toList();
      final avgY = childCenters.map((e) => e.dy).reduce((a, b) => a + b) / childCenters.length;
      // Symbole centré au-dessus du parent (style UML/Merise), entre parent et enfants.
      final defaultY = parentBottom.dy + (avgY - parentBottom.dy) * 0.35;
      final defaultCenter = Offset(parentCenter.dx, defaultY);
      final stored = symbolPositions[entry.key];
      final symbolCenter = stored != null
          ? Offset((stored['x'] as num?)?.toDouble() ?? defaultCenter.dx, (stored['y'] as num?)?.toDouble() ?? defaultCenter.dy)
          : defaultCenter;
      final selected = selectedInheritanceIndices.any((idx) =>
          idx >= 0 && idx < links.length && (links[idx]['parent'] as String?) == entry.key);
      _drawInheritanceSymbol(canvas, symbolCenter, selected, 'Héritage');
      final stroke = Paint()
        ..color = selected ? AppTheme.secondary : AppTheme.primary.withValues(alpha: 0.8)
        ..strokeWidth = selected ? 2.5 : 1.5
        ..style = PaintingStyle.stroke;
      final symbolTop = symbolCenter.dy - _symbolTextHeight - _socleHeight;
      canvas.drawLine(parentBottom, Offset(symbolCenter.dx, symbolTop), stroke);
      final symbolBottom = symbolCenter.dy - _socleHeight + _arrowSize;
      for (final to in childCenters) {
        canvas.drawLine(Offset(symbolCenter.dx, symbolBottom), to, stroke);
      }
    }
    for (final entry in symbolPositions.entries) {
      if (byParent.containsKey(entry.key)) continue;
      final pos = entry.value;
      final x = (pos['x'] as num?)?.toDouble() ?? 2500.0;
      final y = (pos['y'] as num?)?.toDouble() ?? 2500.0;
      _drawInheritanceSymbol(canvas, Offset(x, y), false, 'Héritage');
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

/// Formes CIF/CIFF sur le canvas — rectangle arrondi avec libellé (convention MCD).
class _CifShapesPainter extends CustomPainter {
  _CifShapesPainter({required this.constraints});

  final List<Map<String, dynamic>> constraints;

  static const double _defaultWidth = 88.0;
  static const double _defaultHeight = 32.0;
  static const double _margin = 80.0;
  static const double _stepX = 48.0;
  static const double _stepY = 78.0;

  /// Retourne le centre de la forme (pour dessin et drag).
  Offset _center(int index) {
    final c = constraints[index];
    final pos = c['position'] as Map<String, dynamic>?;
    if (pos != null) {
      final x = (pos['x'] as num?)?.toDouble();
      final y = (pos['y'] as num?)?.toDouble();
      if (x != null && y != null) return Offset(x, y);
    }
    return Offset(_margin + _defaultWidth / 2 + index * _stepX, _margin + _defaultHeight / 2 + index * _stepY);
  }

  Offset _position(int index) {
    final center = _center(index);
    return Offset(center.dx - _defaultWidth / 2, center.dy - _defaultHeight / 2);
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (int i = 0; i < constraints.length; i++) {
      final c = constraints[i];
      final enabled = c['is_enabled'] != false;
      final name = (c['name'] as String?)?.trim().isNotEmpty == true
          ? (c['name'] as String).trim()
          : 'CIF';
      final pos = _position(i);
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTWH(pos.dx, pos.dy, _defaultWidth, _defaultHeight),
        const Radius.circular(8),
      );
      final color = enabled ? AppTheme.associationSelected : AppTheme.textTertiary;
      final fill = Paint()..color = color.withValues(alpha: 0.2)..style = PaintingStyle.fill;
      final stroke = Paint()
        ..color = color
        ..strokeWidth = 1.5
        ..style = PaintingStyle.stroke;
      canvas.drawRRect(rect, fill);
      canvas.drawRRect(rect, stroke);
      final paragraphBuilder = ui.ParagraphBuilder(ui.ParagraphStyle(
        fontSize: 11,
        fontWeight: FontWeight.w600,
        fontFamily: 'sans-serif',
      ))..pushStyle(ui.TextStyle(color: color));
      paragraphBuilder.addText(name);
      final paragraph = paragraphBuilder.build()..layout(ui.ParagraphConstraints(width: _defaultWidth - 10));
      canvas.drawParagraph(
        paragraph,
        Offset(pos.dx + (_defaultWidth - paragraph.width) / 2, pos.dy + (_defaultHeight - paragraph.height) / 2),
      );
    }
  }

  @override
  bool shouldRepaint(covariant _CifShapesPainter oldDelegate) =>
      oldDelegate.constraints != constraints;
}

/// Types SQL/Merise étendus (alignement Barrel : Oracle, SQL Server, MySQL, PostgreSQL).
const List<String> _kAttributeTypes = [
  'VARCHAR(255)',
  'VARCHAR(100)',
  'VARCHAR(50)',
  'VARCHAR(500)',
  'VARCHAR(4000)',
  'VARCHAR2(255)',
  'VARCHAR2(4000)',
  'NVARCHAR(255)',
  'NVARCHAR(500)',
  'NVARCHAR(max)',
  'CHAR(1)',
  'CHAR(10)',
  'CHAR(255)',
  'NCHAR(1)',
  'NCHAR(255)',
  'INTEGER',
  'INT',
  'BIGINT',
  'SMALLINT',
  'TINYINT',
  'INT IDENTITY(1,1)',
  'SERIAL',
  'BIGSERIAL',
  'DECIMAL(10,2)',
  'DECIMAL(15,4)',
  'DECIMAL(19,4)',
  'NUMERIC(10,2)',
  'NUMERIC(18,4)',
  'DATE',
  'DATETIME',
  'DATETIME2',
  'TIMESTAMP',
  'TIME',
  'TEXT',
  'BOOLEAN',
  'FLOAT',
  'DOUBLE',
  'REAL',
  'BLOB',
  'UUID',
];

/// Retourne true si le type accepte une longueur (VARCHAR, CHAR, NVARCHAR, etc.).
bool _attributeTypeHasLength(String type) {
  final t = type.toUpperCase();
  return t.startsWith('VARCHAR') || t.startsWith('VARCHAR2') ||
      t.startsWith('NVARCHAR') || t.startsWith('CHAR') || t.startsWith('NCHAR');
}

/// Retourne true si le type accepte précision et échelle (DECIMAL, NUMERIC).
bool _attributeTypeHasPrecisionScale(String type) {
  final t = type.toUpperCase();
  return t.startsWith('DECIMAL') || t.startsWith('NUMERIC');
}

/// Extrait la longueur d'un type VARCHAR(n), CHAR(n), etc., ou 255 par défaut.
int _parseTypeLength(String type) {
  final match = RegExp(r'\(\s*(\d+)\s*\)').firstMatch(type);
  if (match != null) return int.tryParse(match.group(1)!) ?? 255;
  if (type.toUpperCase().contains('NVARCHAR(MAX)')) return 0; // max = pas de limite fixe
  return 255;
}

/// Extrait précision et échelle d'un type DECIMAL(p,s) ou NUMERIC(p,s). Retour (precision, scale).
(int, int) _parseTypePrecisionScale(String type) {
  final match = RegExp(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)').firstMatch(type);
  if (match != null) {
    final p = int.tryParse(match.group(1)!) ?? 10;
    final s = int.tryParse(match.group(2)!) ?? 2;
    return (p, s);
  }
  return (10, 2);
}

/// Retourne true si le type est un entier (pour proposer l’option auto-incrément).
bool _attributeTypeIsInteger(String type) {
  final t = type.toUpperCase();
  return t.startsWith('INT') || t == 'BIGINT' || t.startsWith('BIGINT') ||
      t == 'SMALLINT' || t.startsWith('SMALLINT') || t == 'TINYINT' ||
      t.startsWith('SERIAL') || t.startsWith('BIGSERIAL') || t.contains('IDENTITY');
}

/// Dialog complet d'édition d'une entité : nom, faible, fictive, commentaire + liste d'attributs (type, PK, obligatoire, commentaire).
class _EntityEditorDialog extends StatefulWidget {
  const _EntityEditorDialog({required this.entity});

  final Map<String, dynamic> entity;

  @override
  State<_EntityEditorDialog> createState() => _EntityEditorDialogState();
}

class _EntityEditorDialogState extends State<_EntityEditorDialog> {
  late TextEditingController _nameController;
  late TextEditingController _commentController;
  late List<Map<String, dynamic>> _attrs;
  late bool _isWeak;
  late bool _isFictive;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.entity['name']?.toString() ?? '');
    _commentController = TextEditingController(text: widget.entity['comment']?.toString() ?? widget.entity['description']?.toString() ?? '');
    _attrs = (widget.entity['attributes'] as List?)
        ?.map((a) => Map<String, dynamic>.from(a as Map))
        .toList() ?? [];
    for (final a in _attrs) {
      a['name'] = a['name']?.toString() ?? '';
      a['type'] = a['type']?.toString() ?? 'VARCHAR(255)';
      a['is_primary_key'] = a['is_primary_key'] == true;
      if (!a.containsKey('nullable')) a['nullable'] = true;
      a['description'] = a['description']?.toString() ?? a['comment']?.toString() ?? '';
      a['default_value'] = a['default_value']?.toString() ?? '';
      a['is_unique'] = a['is_unique'] == true;
    }
    _isWeak = widget.entity['is_weak'] == true;
    _isFictive = widget.entity['is_fictive'] == true;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _commentController.dispose();
    super.dispose();
  }

  void _onPrimaryKeyChanged(int index) {
    setState(() {
      for (int i = 0; i < _attrs.length; i++) {
        _attrs[i]['is_primary_key'] = (i == index);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final maxContentHeight = MediaQuery.sizeOf(context).height * 0.75;
    return AlertDialog(
      title: const Text('Propriétés de l\'entité'),
      content: SizedBox(
        width: 820,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: maxContentHeight),
          child: SingleChildScrollView(
            child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Nom de l\'entité',
                  hintText: 'ex. Client, Produit',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  SizedBox(
                    width: 200,
                    child: CheckboxListTile(
                      value: _isWeak,
                      title: const Text('Entité faible', style: TextStyle(fontSize: 13)),
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      onChanged: (v) => setState(() => _isWeak = v == true),
                    ),
                  ),
                  Expanded(
                    child: CheckboxListTile(
                      value: _isFictive,
                      title: const Text('Entité fictive (non générée MLD)', style: TextStyle(fontSize: 13)),
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      onChanged: (v) => setState(() => _isFictive = v == true),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _commentController,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Commentaire (optionnel)',
                  hintText: 'Description de l\'entité',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 20),
              const Divider(height: 1),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.list_alt, size: 20, color: AppTheme.primary),
                  const SizedBox(width: 8),
                  Text('Attributs', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppTheme.primary)),
                  const SizedBox(width: 6),
                  Tooltip(
                    message: 'Clé primaire, clé secondaire, obligatoire : voir le lexique',
                    child: IconButton(
                      icon: const Icon(Icons.help_outline, size: 20, color: AppTheme.primary),
                      onPressed: () => GlossaryDialog.show(context),
                      style: IconButton.styleFrom(
                        minimumSize: const Size(32, 32),
                        padding: EdgeInsets.zero,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _attributeTableHeader(),
              ..._attrs.asMap().entries.map((e) => _entityAttrRow(e.key, e.value)),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () {
                  setState(() => _attrs.add({
                    'name': '',
                    'type': 'VARCHAR(255)',
                    'is_primary_key': _attrs.every((a) => a['is_primary_key'] != true),
                    'nullable': true,
                    'is_unique': false,
                    'default_value': '',
                    'description': '',
                    'size': null,
                    'precision': null,
                    'scale': null,
                    'auto_increment': false,
                  }));
                },
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Ajouter un attribut'),
              ),
            ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
        FilledButton(
          onPressed: () {
            final name = _nameController.text.trim();
            if (name.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Le nom de l\'entité est obligatoire.')));
              return;
            }
            final e = Map<String, dynamic>.from(widget.entity);
            e['name'] = name;
            e['is_weak'] = _isWeak;
            e['is_fictive'] = _isFictive;
            e['comment'] = _commentController.text.trim();
            if ((e['comment'] as String?)?.isEmpty ?? true) e.remove('comment');
            e['attributes'] = _attrs.map((a) {
              final m = Map<String, dynamic>.from(a);
              m['name'] = (m['name']?.toString() ?? '').trim();
              final typeStr = m['type']?.toString() ?? 'VARCHAR(255)';
              m['type'] = typeStr;
              m['is_primary_key'] = m['is_primary_key'] == true;
              m['nullable'] = m['nullable'] != false;
              m['is_unique'] = m['is_unique'] == true;
              m['auto_increment'] = m['auto_increment'] == true;
              if (_attributeTypeHasLength(typeStr)) {
                final len = m['size'] != null ? int.tryParse(m['size'].toString()) : null;
                m['size'] = len ?? _parseTypeLength(typeStr);
              } else {
                m.remove('size');
              }
              if (_attributeTypeHasPrecisionScale(typeStr)) {
                final ps = _parseTypePrecisionScale(typeStr);
                m['precision'] = int.tryParse(m['precision']?.toString() ?? '') ?? ps.$1;
                m['scale'] = int.tryParse(m['scale']?.toString() ?? '') ?? ps.$2;
              } else {
                m.remove('precision');
                m.remove('scale');
              }
              final def = (m['default_value'] as String?)?.toString().trim() ?? '';
              if (def.isEmpty) {
                m.remove('default_value');
              } else {
                m['default_value'] = def;
              }
              if ((m['description'] as String?)?.toString().trim().isEmpty ?? true) {
                m.remove('description');
              }
              return m;
            }).toList();
            Navigator.pop(context, e);
          },
          child: const Text('Enregistrer'),
        ),
      ],
    );
  }

  Widget _attributeTableHeader() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          SizedBox(width: 120, child: Text('Nom', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          SizedBox(width: 110, child: Text('Type', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          SizedBox(width: 40, child: Tooltip(message: 'Longueur (VARCHAR, CHAR…)', child: Text('Long.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 36, child: Tooltip(message: 'Précision (DECIMAL, NUMERIC)', child: Text('Préc.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 4),
          SizedBox(width: 32, child: Tooltip(message: 'Échelle (décimales)', child: Text('Éch.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 52, child: Tooltip(message: 'Clé primaire. Voir Aide → Lexique.', child: Text('Clé prim.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 52, child: Tooltip(message: 'Obligatoire (NOT NULL).', child: Text('Oblig.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 52, child: Tooltip(message: 'Clé secondaire / Unique.', child: Text('Clé sec.', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 36, child: Tooltip(message: 'Auto-incrément (entiers)', child: Text('Auto', style: Theme.of(context).textTheme.titleSmall))),
          const SizedBox(width: 6),
          SizedBox(width: 72, child: Text('Défaut', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          Expanded(child: Text('Commentaire', style: Theme.of(context).textTheme.titleSmall)),
        ],
      ),
    );
  }

  Widget _entityAttrRow(int index, Map<String, dynamic> attr) {
    final typeStr = attr['type']?.toString() ?? 'VARCHAR(255)';
    final isCustomType = !_kAttributeTypes.contains(typeStr);
    final hasLength = _attributeTypeHasLength(typeStr);
    final length = _parseTypeLength(typeStr);
    final hasPrecisionScale = _attributeTypeHasPrecisionScale(typeStr);
    final ps = _parseTypePrecisionScale(typeStr);
    final precision = attr['precision'] != null ? int.tryParse(attr['precision'].toString()) : null;
    final scale = attr['scale'] != null ? int.tryParse(attr['scale'].toString()) : null;
    final precVal = precision ?? ps.$1;
    final scaleVal = scale ?? ps.$2;
    final isIntegerType = _attributeTypeIsInteger(typeStr);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: TextFormField(
              decoration: const InputDecoration(
                hintText: 'nom_attribut',
                border: OutlineInputBorder(),
                isDense: true,
                contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 10),
              ),
              initialValue: attr['name']?.toString() ?? '',
              onChanged: (v) => _attrs[index]['name'] = v,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ConstrainedBox(
              constraints: const BoxConstraints(minWidth: 100),
              child: DropdownButtonFormField<String>(
                initialValue: isCustomType ? '__custom__' : typeStr,
                isExpanded: true,
                decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 8)),
                items: [
                  ..._kAttributeTypes.map((t) => DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 11), overflow: TextOverflow.ellipsis))),
                  const DropdownMenuItem(value: '__custom__', child: Text('Autre...', style: TextStyle(fontSize: 11))),
                ],
                onChanged: (v) {
                  setState(() {
                    if (v != null && v != '__custom__') _attrs[index]['type'] = v;
                  });
                },
              ),
            ),
          ),
          if (isCustomType) ...[
            const SizedBox(width: 6),
            SizedBox(
              width: 100,
              child: TextFormField(
                decoration: const InputDecoration(hintText: 'Type', border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 8)),
                initialValue: typeStr,
                onChanged: (v) => _attrs[index]['type'] = v.isEmpty ? 'VARCHAR(255)' : v,
              ),
            ),
          ],
          const SizedBox(width: 8),
          SizedBox(
            width: 40,
            child: hasLength
                ? TextFormField(
                    decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 8)),
                    keyboardType: TextInputType.number,
                    initialValue: length.toString(),
                    onChanged: (v) {
                      final n = int.tryParse(v);
                      if (n != null && n > 0) {
                        _attrs[index]['type'] = typeStr.replaceFirst(RegExp(r'\(\s*\d+\s*\)'), '($n)');
                        if (!typeStr.contains('(')) _attrs[index]['type'] = typeStr.startsWith('VARCHAR') ? 'VARCHAR($n)' : 'CHAR($n)';
                      }
                      _attrs[index]['size'] = n;
                    },
                  )
                : const SizedBox(),
          ),
          const SizedBox(width: 6),
          SizedBox(
            width: 36,
            child: hasPrecisionScale
                ? TextFormField(
                    decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 8)),
                    keyboardType: TextInputType.number,
                    initialValue: precVal.toString(),
                    onChanged: (v) {
                      final p = int.tryParse(v);
                      if (p != null && p >= 0) {
                        _attrs[index]['precision'] = p;
                        final s = int.tryParse(_attrs[index]['scale']?.toString() ?? '') ?? scaleVal;
                        _attrs[index]['type'] = typeStr.startsWith('NUMERIC') ? 'NUMERIC($p,$s)' : 'DECIMAL($p,$s)';
                      }
                    },
                  )
                : const SizedBox(),
          ),
          const SizedBox(width: 4),
          SizedBox(
            width: 32,
            child: hasPrecisionScale
                ? TextFormField(
                    decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 4, vertical: 8)),
                    keyboardType: TextInputType.number,
                    initialValue: scaleVal.toString(),
                    onChanged: (v) {
                      final s = int.tryParse(v);
                      if (s != null && s >= 0) {
                        _attrs[index]['scale'] = s;
                        final p = int.tryParse(_attrs[index]['precision']?.toString() ?? '') ?? precVal;
                        _attrs[index]['type'] = typeStr.startsWith('NUMERIC') ? 'NUMERIC($p,$s)' : 'DECIMAL($p,$s)';
                      }
                    },
                  )
                : const SizedBox(),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 52,
            child: Tooltip(
              message: 'Clé primaire : identifie chaque occurrence. Voir Aide → Lexique.',
              child: CheckboxListTile(
                value: attr['is_primary_key'] == true,
                title: const Text('', style: TextStyle(fontSize: 11)),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (v) {
                  if (v == true) _onPrimaryKeyChanged(index);
                  else setState(() => _attrs[index]['is_primary_key'] = false);
                },
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 52,
            child: Tooltip(
              message: 'Obligatoire : valeur requise (NOT NULL). Voir Aide → Lexique.',
              child: CheckboxListTile(
                value: attr['nullable'] != true,
                title: const Text('', style: TextStyle(fontSize: 11)),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (v) => setState(() => _attrs[index]['nullable'] = v != true),
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 52,
            child: Tooltip(
              message: 'Clé secondaire / Unique : valeur non répétable. Voir Aide → Lexique.',
              child: CheckboxListTile(
                value: attr['is_unique'] == true,
                title: const Text('', style: TextStyle(fontSize: 11)),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (v) => setState(() => _attrs[index]['is_unique'] = v == true),
              ),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 36,
            child: isIntegerType
                ? Tooltip(
                    message: 'Auto-incrément (IDENTITY / AUTO_INCREMENT selon SGBD).',
                    child: CheckboxListTile(
                      value: attr['auto_increment'] == true,
                      title: const Text('', style: TextStyle(fontSize: 11)),
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      onChanged: (v) => setState(() => _attrs[index]['auto_increment'] = v == true),
                    ),
                  )
                : const SizedBox(),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 72,
            child: TextFormField(
              decoration: const InputDecoration(
                hintText: 'Défaut',
                border: OutlineInputBorder(),
                isDense: true,
                contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 8),
              ),
              initialValue: attr['default_value']?.toString() ?? '',
              onChanged: (v) => _attrs[index]['default_value'] = v,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextFormField(
              decoration: const InputDecoration(
                hintText: 'Optionnel',
                border: OutlineInputBorder(),
                isDense: true,
                contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              ),
              initialValue: attr['description']?.toString() ?? '',
              onChanged: (v) => _attrs[index]['description'] = v,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppTheme.error, size: 20),
            tooltip: 'Supprimer l\'attribut',
            onPressed: () => setState(() => _attrs.removeAt(index)),
          ),
        ],
      ),
    );
  }
}

/// Dialog pour éditer la liste d'attributs (entité ou association), style Barrel.
class _AttributeListDialog extends StatefulWidget {
  const _AttributeListDialog({required this.title, required this.attributes, required this.isEntity});

  final String title;
  final List<Map<String, dynamic>> attributes;
  final bool isEntity;

  @override
  State<_AttributeListDialog> createState() => _AttributeListDialogState();
}

class _AttributeListDialogState extends State<_AttributeListDialog> {
  late List<Map<String, dynamic>> _attrs;

  @override
  void initState() {
    super.initState();
    _attrs = widget.attributes.map((a) {
      final m = Map<String, dynamic>.from(a);
      if (!m.containsKey('nullable')) m['nullable'] = true;
      m['description'] = m['description']?.toString() ?? m['comment']?.toString() ?? '';
      return m;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: widget.isEntity ? 520 : 640,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: [
                  SizedBox(width: 160, child: Text('Nom', style: Theme.of(context).textTheme.titleSmall)),
                  const SizedBox(width: 8),
                  SizedBox(width: 140, child: Text('Type', style: Theme.of(context).textTheme.titleSmall)),
                  if (widget.isEntity) SizedBox(width: 70, child: Text('Clé P.', style: Theme.of(context).textTheme.titleSmall)),
                  if (!widget.isEntity) ...[const SizedBox(width: 8), SizedBox(width: 60, child: Text('Oblig.', style: Theme.of(context).textTheme.titleSmall)), const SizedBox(width: 8), Expanded(child: Text('Commentaire', style: Theme.of(context).textTheme.titleSmall))],
                ],
              ),
            ),
            ..._attrs.asMap().entries.map((e) => _attrRow(e.key, e.value)),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () {
                setState(() => _attrs.add({
                  'name': '',
                  'type': 'VARCHAR(255)',
                  'is_primary_key': false,
                  'nullable': true,
                  'description': '',
                }));
              },
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Ajouter un attribut'),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
        FilledButton(onPressed: () => Navigator.pop(context, _attrs), child: const Text('OK')),
      ],
    );
  }

  Widget _attrRow(int index, Map<String, dynamic> attr) {
    final typeStr = attr['type']?.toString() ?? 'VARCHAR(255)';
    final isCustomType = !_kAttributeTypes.contains(typeStr);
    if (!attr.containsKey('nullable')) attr['nullable'] = true;
    attr['description'] = attr['description']?.toString() ?? attr['comment']?.toString() ?? '';
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 160,
            child: TextFormField(
              decoration: const InputDecoration(
                hintText: 'nom_attribut',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              initialValue: attr['name']?.toString() ?? '',
              onChanged: (v) => _attrs[index]['name'] = v,
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 140,
            child: DropdownButtonFormField<String>(
              initialValue: isCustomType ? '__custom__' : typeStr,
              decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
              items: [
                ..._kAttributeTypes.map((t) => DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 12)))),
                const DropdownMenuItem(value: '__custom__', child: Text('Autre...', style: TextStyle(fontSize: 12))),
              ],
              onChanged: (v) {
                setState(() {
                  if (v != null && v != '__custom__') _attrs[index]['type'] = v;
                });
              },
            ),
          ),
          if (isCustomType) ...[
            const SizedBox(width: 6),
            SizedBox(
              width: 100,
              child: TextFormField(
                decoration: const InputDecoration(hintText: 'Type', border: OutlineInputBorder(), isDense: true),
                initialValue: typeStr,
                onChanged: (v) => _attrs[index]['type'] = v.isEmpty ? 'VARCHAR(255)' : v,
              ),
            ),
          ],
          if (widget.isEntity) ...[
            const SizedBox(width: 8),
            SizedBox(
              width: 70,
              child: CheckboxListTile(
                value: attr['is_primary_key'] == true,
                title: const Text('', style: TextStyle(fontSize: 11)),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (v) => setState(() => _attrs[index]['is_primary_key'] = v == true),
              ),
            ),
          ],
          if (!widget.isEntity) ...[
            const SizedBox(width: 8),
            SizedBox(
              width: 60,
              child: CheckboxListTile(
                value: attr['nullable'] != true,
                title: const Text('', style: TextStyle(fontSize: 11)),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (v) => setState(() => _attrs[index]['nullable'] = v != true),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                decoration: const InputDecoration(hintText: 'Optionnel', border: OutlineInputBorder(), isDense: true),
                initialValue: attr['description']?.toString() ?? '',
                onChanged: (v) => _attrs[index]['description'] = v,
              ),
            ),
          ],
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppTheme.error),
            tooltip: 'Supprimer l\'attribut',
            onPressed: () => setState(() => _attrs.removeAt(index)),
          ),
        ],
      ),
    );
  }
}
