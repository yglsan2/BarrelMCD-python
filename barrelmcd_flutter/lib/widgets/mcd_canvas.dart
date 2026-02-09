import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../core/canvas_mode.dart';
import '../theme/app_theme.dart';
import 'entity_box.dart';
import 'association_diamond.dart';
import 'link_arrow.dart';

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

/// Dimensions partagées avec EntityBox et AssociationDiamond pour que les liens visent le centre des formes.
const double _entityWidth = 200;
const double _entityMinHeight = 80;

/// Zone de dessin MCD interactive : créer/déplacer entités et associations, lier, zoom.
class McdCanvas extends StatefulWidget {
  const McdCanvas({super.key, this.repaintBoundaryKey});

  final GlobalKey? repaintBoundaryKey;

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
  Offset? _overlayTapDownPos;
  DateTime? _overlayTapDownTime;
  Offset? _outerDownPos;
  DateTime? _outerDownTime;
  int? _outerHitEntityIndex;
  int? _outerHitAssocIndex;
  Offset? _dragStartScenePos;
  Offset? _dragEntityStartPos;
  Offset? _dragAssocStartPos;
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

  @override
  void dispose() {
    _transform.dispose();
    super.dispose();
  }

  void zoomIn() {
    _applyZoom(1.25);
  }

  void zoomOut() {
    _applyZoom(1 / 1.25);
  }

  void fitToView() {
    if (_lastViewportW <= 0 || _lastViewportH <= 0 || _lastSceneW <= 0 || _lastSceneH <= 0) return;
    final scaleX = _lastViewportW / _lastSceneW;
    final scaleY = _lastViewportH / _lastSceneH;
    final s = (scaleX < scaleY ? scaleX : scaleY).clamp(_minScale, _maxScale) * 0.95;
    final tx = _lastViewportW / 2 - _lastSceneW / 2 * s;
    final ty = _lastViewportH / 2 - _lastSceneH / 2 * s;
    _transform.value = Matrix4.identity()
      ..setEntry(0, 0, s)
      ..setEntry(1, 1, s)
      ..setEntry(0, 3, tx)
      ..setEntry(1, 3, ty);
  }

  /// Retourne l'index de l'entité dont la boîte contient [scenePos], ou null.
  int? _entityIndexAtScene(McdState state, Offset scenePos) {
    for (int i = 0; i < state.entities.length; i++) {
      final e = state.entities[i];
      final pos = e['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      final w = (e['width'] as num?)?.toDouble() ?? _entityWidth;
      final h = (e['height'] as num?)?.toDouble() ?? _entityMinHeight;
      if (scenePos.dx >= x && scenePos.dx <= x + w && scenePos.dy >= y && scenePos.dy <= y + h) return i;
    }
    return null;
  }

  /// Retourne l'index de l'association dont le losange contient [scenePos], ou null.
  int? _associationIndexAtScene(McdState state, Offset scenePos) {
    const w = 96.0;
    const h = 96.0;
    for (int i = 0; i < state.associations.length; i++) {
      final a = state.associations[i];
      final pos = a['position'] as Map<String, dynamic>?;
      final x = (pos?['x'] as num?)?.toDouble() ?? 0;
      final y = (pos?['y'] as num?)?.toDouble() ?? 0;
      if (scenePos.dx >= x && scenePos.dx <= x + w && scenePos.dy >= y && scenePos.dy <= y + h) return i;
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
          behavior: HitTestBehavior.opaque,
          onPointerDown: (e) {
            _outerDownPos = e.localPosition;
            _outerDownTime = DateTime.now();
            _outerHitEntityIndex = null;
            _outerHitAssocIndex = null;
            _dragStartScenePos = null;
            _dragEntityStartPos = null;
            _dragAssocStartPos = null;
            try {
              final scenePos = _viewportToScene(e.localPosition);
              final state = context.read<McdState>();
              final modeState = context.read<CanvasModeState>();
              _outerHitEntityIndex = _entityIndexAtScene(state, scenePos);
              _outerHitAssocIndex = _associationIndexAtScene(state, scenePos);
              // Déplacement au glisser : possible dès qu'on clique sur une entité/association (tous modes).
              if (_outerHitEntityIndex != null) {
                final ent = state.entities[_outerHitEntityIndex!];
                final pos = ent['position'] as Map<String, dynamic>?;
                final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                _draggingEntityIndex = _outerHitEntityIndex;
                _dragStartScenePos = scenePos;
                _dragEntityStartPos = Offset(x, y);
              } else if (_outerHitAssocIndex != null) {
                final assoc = state.associations[_outerHitAssocIndex!];
                final pos = assoc['position'] as Map<String, dynamic>?;
                final x = (pos?['x'] as num?)?.toDouble() ?? 0;
                final y = (pos?['y'] as num?)?.toDouble() ?? 0;
                _draggingAssociationIndex = _outerHitAssocIndex;
                _dragStartScenePos = scenePos;
                _dragAssocStartPos = Offset(x, y);
              }
            } catch (err, st) {
              debugPrint('[McdCanvas] OUTER Listener.onPointerDown ERROR: $err\n$st');
            }
            if (_kClicksLog) debugPrint('[McdCanvas] OUTER Listener.onPointerDown pos=${e.localPosition}');
          },
          onPointerMove: (e) {
            try {
              if (_draggingEntityIndex != null && _dragStartScenePos != null && _dragEntityStartPos != null) {
                final state = context.read<McdState>();
                if (_draggingEntityIndex! >= state.entities.length) {
                  _draggingEntityIndex = null;
                  _dragStartScenePos = null;
                  _dragEntityStartPos = null;
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                final delta = scenePos - _dragStartScenePos!;
                final newPos = _dragEntityStartPos! + delta;
                state.moveEntity(_draggingEntityIndex!, newPos.dx, newPos.dy);
                setState(() {});
              } else if (_draggingAssociationIndex != null && _dragStartScenePos != null && _dragAssocStartPos != null) {
                final state = context.read<McdState>();
                if (_draggingAssociationIndex! >= state.associations.length) {
                  _draggingAssociationIndex = null;
                  _dragStartScenePos = null;
                  _dragAssocStartPos = null;
                  return;
                }
                final scenePos = _viewportToScene(e.localPosition);
                final delta = scenePos - _dragStartScenePos!;
                final newPos = _dragAssocStartPos! + delta;
                state.moveAssociation(_draggingAssociationIndex!, newPos.dx, newPos.dy);
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
              _outerDownPos = null;
              _outerDownTime = null;
              if (down == null || downTime == null) return;
              final wasDraggingEntity = _draggingEntityIndex != null;
              final wasDraggingAssoc = _draggingAssociationIndex != null;
              _draggingEntityIndex = null;
              _draggingAssociationIndex = null;
              _dragStartScenePos = null;
              _dragEntityStartPos = null;
              _dragAssocStartPos = null;
              if (wasDraggingEntity || wasDraggingAssoc) return;
              final delta = (e.localPosition - down).distance;
              final duration = DateTime.now().difference(downTime);
              final isTap = delta <= _tapSlop && duration <= _tapMaxDuration;
              if (!isTap) return;
              final modeState = context.read<CanvasModeState>();
              final state = context.read<McdState>();
              final mode = modeState.mode;
              final hasContent = state.entities.isNotEmpty || state.associations.isNotEmpty;
              final scenePos = _viewportToScene(e.localPosition);
              // Clic sur un élément : sélection ou lien (selon le mode), dans tous les cas on le gère ici.
              if (hitEntity != null) {
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap entité index=$hitEntity mode=$mode');
                _onEntityTap(state, modeState, hitEntity);
                return;
              }
              if (hitAssoc != null) {
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap association index=$hitAssoc mode=$mode');
                _onAssociationTap(state, modeState, hitAssoc);
                return;
              }
              // Clic sur le vide
              if (mode == CanvasMode.select) {
                state.selectNone();
                return;
              }
              if (mode == CanvasMode.addEntity) {
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> nouvelle entité scene=$scenePos');
                _showNewEntityDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (mode == CanvasMode.addAssociation) {
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> nouvelle association scene=$scenePos');
                _showNewAssociationDialog(scenePos.dx, scenePos.dy);
                return;
              }
              if (mode == CanvasMode.createLink) {
                // Rien sur le vide en mode Lien
                return;
              }
              if (!hasContent) {
                if (_kClicksLog) debugPrint('[McdCanvas] OUTER tap -> canvas vide');
                _showNewEntityDialog(scenePos.dx, scenePos.dy);
              }
            } catch (err, st) {
              debugPrint('[McdCanvas] OUTER Listener.onPointerUp ERROR: $err\n$st');
            }
          },
          child: Stack(
          children: [
            Consumer<CanvasModeState>(
              builder: (context, modeState, _) => InteractiveViewer(
                transformationController: _transform,
                minScale: _minScale,
                maxScale: _maxScale,
                boundaryMargin: const EdgeInsets.all(2000),
                panEnabled: modeState.mode == CanvasMode.select,
                scaleEnabled: modeState.mode == CanvasMode.select,
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
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerDown pos=${e.localPosition}');
                        } catch (err, st) {
                          debugPrint('[McdCanvas] Listener.onPointerDown ERROR: $err\n$st');
                        }
                      },
                      onPointerUp: (e) {
                        try {
                          final down = _pointerDownPosition;
                          final downTime = _pointerDownTime;
                          _pointerDownPosition = null;
                          _pointerDownTime = null;
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerUp pos=${e.localPosition} down=$down');
                          if (down == null || downTime == null) return;
                          final delta = (e.localPosition - down).distance;
                          final duration = DateTime.now().difference(downTime);
                          final isTap = delta <= _tapSlop && duration <= _tapMaxDuration;
                          if (_kClicksLog) debugPrint('[McdCanvas] Listener.onPointerUp delta=$delta duration=${duration.inMilliseconds}ms isTap=$isTap');
                          if (isTap) {
                            _onCanvasTap(e.localPosition, sceneWidth, sceneHeight);
                          }
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
                            if (_kCanvasDebug && state.entities.length + state.associations.length > 0) {
                              debugPrint('[McdCanvas] build content: entities=${state.entities.length} associations=${state.associations.length}');
                            }
                            final stack = Stack(
                              clipBehavior: Clip.none,
                              children: [
                                // Liens en IgnorePointer pour ne pas absorber les clics (CustomPaint occupe toute la scène).
                                IgnorePointer(
                                  child: _buildLinks(state, sceneWidth, sceneHeight),
                                ),
                                IgnorePointer(
                                  child: _buildInheritanceLinks(state, sceneWidth, sceneHeight),
                                ),
                                // Overlay cliquable en mode Entité/Association (sous les formes) : GestureDetector pour que l'arène des gestes reconnaisse le tap.
                                if (modeState2.mode == CanvasMode.addEntity || modeState2.mode == CanvasMode.addAssociation)
                                  Positioned.fill(
                                    child: GestureDetector(
                                      behavior: HitTestBehavior.translucent,
                                      onTapDown: (d) {
                                        try {
                                          _overlayTapDownPos = d.localPosition;
                                          if (_kClicksLog) debugPrint('[McdCanvas] Overlay.onTapDown pos=${d.localPosition} mode=${modeState2.mode}');
                                        } catch (err, st) {
                                          debugPrint('[McdCanvas] Overlay.onTapDown ERROR: $err\n$st');
                                        }
                                      },
                                      onTap: () {
                                        try {
                                          if (_overlayTapDownPos == null) return;
                                          final pos = _overlayTapDownPos!;
                                          _overlayTapDownPos = null;
                                          if (_kClicksLog) debugPrint('[McdCanvas] Overlay.onTap pos=$pos');
                                          if (modeState2.mode == CanvasMode.addEntity) {
                                            _showNewEntityDialog(pos.dx, pos.dy);
                                          } else if (modeState2.mode == CanvasMode.addAssociation) {
                                            _showNewAssociationDialog(pos.dx, pos.dy);
                                          }
                                        } catch (err, st) {
                                          debugPrint('[McdCanvas] Overlay.onTap ERROR: $err\n$st');
                                        }
                                      },
                                      child: const ColoredBox(color: Color(0x01000000)),
                                    ),
                                  ),
                                ...state.entities.asMap().entries.map((e) => _buildEntity(state, modeState2, e.key, e.value)),
                                ...state.associations.asMap().entries.map((a) => _buildAssociation(state, modeState2, a.key, a.value)),
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
                                if (!hasContent) _buildEmptyHint(sceneWidth, sceneHeight, () => _showNewEntityDialog(sceneWidth / 2, sceneHeight / 2)),
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
                      ],
                    ),
                  ),
                ),
                ),
              ),
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
    }
  }

  void _showNewAssociationDialog(double x, double y) async {
    if (_kClicksLog || _kCanvasDebug) debugPrint('[McdCanvas] _showNewAssociationDialog ENTRY x=$x y=$y');
    if (!mounted) return;
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
      if (stateAfter.associations.any((a) => (a['name'] as String?)?.trim() == trimmed)) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Une association "$trimmed" existe déjà.')));
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
      state.selectEntity(index);
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
    state.selectAssociation(index);
    } catch (e, st) {
      debugPrint('[McdCanvas] _onAssociationTap ERROR: $e');
      debugPrint(st.toString());
    }
  }

  /// Les 4 cardinalités du MCD Merise : (min, max) avec min ∈ {0,1}, max ∈ {1,n}.
  static const List<String> _mcdCardinalities = ['0,1', '1,1', '0,n', '1,n'];

  Future<void> _showCardinalityDialog(String associationName, String entityName) async {
    final messenger = ScaffoldMessenger.of(context);
    final state = context.read<McdState>();
    final card = await showDialog<String>(
      context: context,
      builder: (ctx) {
        String v = '1,n';
        return StatefulBuilder(
          builder: (ctx, setState) {
            return AlertDialog(
              title: const Text('Cardinalité (MCD Merise)'),
              content: DropdownButtonFormField<String>(
                // ignore: deprecated_member_use
                value: _mcdCardinalities.contains(v) ? v : '1,n',
                decoration: const InputDecoration(
                  labelText: 'Côté entité',
                  hintText: '0,1 | 1,1 | 0,n | 1,n',
                ),
                items: _mcdCardinalities
                    .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                    .toList(),
                onChanged: (s) {
                  if (s != null) {
                    v = s;
                    setState(() {});
                  }
                },
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
                FilledButton(
                  onPressed: () => Navigator.pop(ctx, v),
                  child: const Text('OK'),
                ),
              ],
            );
          },
        );
      },
    );
    if (card == null) return;
    state.addAssociationLink(associationName, entityName, card);
    messenger.showSnackBar(SnackBar(content: Text('Lien $associationName — $entityName ($card) créé.')));
  }

  Widget _buildLinks(McdState state, double sceneWidth, double sceneHeight) {
    final links = state.associationLinks;
    if (links.isEmpty) return const SizedBox.shrink();
    return CustomPaint(
      painter: _LinksPainter(
        entities: state.entities,
        associations: state.associations,
        links: links,
        selectedLinkIndex: state.selectedType == 'link' ? state.selectedIndex : -1,
      ),
      size: Size(sceneWidth, sceneHeight),
    );
  }

  Widget _buildInheritanceLinks(McdState state, double sceneWidth, double sceneHeight) {
    final links = state.inheritanceLinks;
    if (links.isEmpty) return const SizedBox.shrink();
    return CustomPaint(
      painter: _InheritancePainter(
        entities: state.entities,
        links: links,
        selectedIndex: state.selectedType == 'inheritance' ? state.selectedIndex : -1,
      ),
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
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.schema, size: 48, color: AppTheme.primary),
              const SizedBox(height: 12),
              const Text(
                'BarrelMCD – Modèle conceptuel de données',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 12),
              const Icon(Icons.add_circle_outline, size: 32, color: AppTheme.primary),
              const SizedBox(height: 8),
              const Text(
                'Cliquez ici pour créer votre première entité',
                style: TextStyle(color: AppTheme.primary, fontSize: 12, fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 12),
              const Text(
                'Ou : bouton « Entité » dans la barre puis clic sur le canvas.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 11, height: 1.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEntity(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> entity) {
    if (_kCanvasDebug && index == 0) {
      debugPrint('[McdCanvas] _buildEntity index=0 name=${entity['name']} total=${state.entities.length}');
    }
    final name = entity['name'] as String? ?? 'Entité';
    final pos = entity['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 100;
    final y = (pos?['y'] as num?)?.toDouble() ?? 100;
    final attrs = (entity['attributes'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final isWeak = entity['is_weak'] == true;
    final isFictive = entity['is_fictive'] == true;
    final selected = state.isEntitySelected(index);
    final isSelectMode = modeState.mode == CanvasMode.select;

    return Positioned(
      left: x,
      top: y,
      child: GestureDetector(
        onTap: () => _onEntityTap(state, modeState, index),
        onLongPressStart: (d) => _lastLongPressPosition = d.globalPosition,
        onLongPress: () => _onEntityLongPress(context, state, index, entity),
        onPanStart: isSelectMode ? (_) { _draggingEntityIndex = index; _dragStartPos = Offset(x, y); } : null,
        onPanUpdate: isSelectMode && _draggingEntityIndex == index
            ? (d) {
                if (_dragStartPos == null) return;
                final nx = (_dragStartPos!.dx + d.delta.dx).clamp(0.0, 10000.0);
                final ny = (_dragStartPos!.dy + d.delta.dy).clamp(0.0, 10000.0);
                state.moveEntity(index, nx, ny);
                _dragStartPos = Offset(nx, ny);
              }
            : null,
        onPanEnd: isSelectMode ? (_) { _draggingEntityIndex = null; _dragStartPos = null; } : null,
        child: EntityBox(
          name: name,
          attributes: attrs,
          selected: selected,
          isWeak: isWeak,
          isFictive: isFictive,
          onTap: () => _onEntityTap(state, modeState, index),
        ),
      ),
    );
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
        PopupMenuItem(value: 'weak', child: Text((entity['is_weak'] == true) ? 'Entité normale' : 'Entité faible')),
        PopupMenuItem(value: 'fictive', child: Text((entity['is_fictive'] == true) ? 'Entité réelle (générée MLD)' : 'Entité fictive (non générée MLD)')),
        const PopupMenuItem(value: 'inheritance', child: Text('Définir héritage...')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer', style: TextStyle(color: AppTheme.error))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (v == 'rename') {
        _showRenameEntityDialog(context, state, index);
      } else if (v == 'attrs') {
        _showEntityAttributesDialog(context, state, index);
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

  void _onAssociationLongPress(BuildContext context, McdState state, int index, Map<String, dynamic> association) {
    state.selectAssociation(index);
    final pos = _lastLongPressPosition ?? Offset(MediaQuery.of(context).size.width / 2, 200);
    final size = MediaQuery.of(context).size;
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(pos.dx, pos.dy, size.width - pos.dx, size.height - pos.dy),
      items: [
        const PopupMenuItem(value: 'rename', child: Text('Renommer')),
        const PopupMenuItem(value: 'attrs', child: Text('Attributs d\'association')),
        const PopupMenuItem(value: 'duplicate', child: Text('Dupliquer l\'association')),
        const PopupMenuItem(value: 'delete', child: Text('Supprimer', style: TextStyle(color: AppTheme.error))),
      ],
    ).then((v) {
      if (!context.mounted) return;
      if (v == 'rename') {
        _showRenameAssociationDialog(context, state, index);
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

  Widget _buildAssociation(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> association) {
    if (_kCanvasDebug && index == 0) {
      debugPrint('[McdCanvas] _buildAssociation index=0 name=${association['name']} total=${state.associations.length}');
    }
    final name = association['name'] as String? ?? 'Association';
    final pos = association['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 300;
    final y = (pos?['y'] as num?)?.toDouble() ?? 300;
    final selected = state.isAssociationSelected(index);
    final isSelectMode = modeState.mode == CanvasMode.select;

    return Positioned(
      left: x,
      top: y,
        child: GestureDetector(
        onTap: () => _onAssociationTap(state, modeState, index),
        onLongPressStart: (d) => _lastLongPressPosition = d.globalPosition,
        onLongPress: () => _onAssociationLongPress(context, state, index, association),
        onPanStart: isSelectMode ? (_) { _draggingAssociationIndex = index; _dragStartPos = Offset(x, y); } : null,
        onPanUpdate: isSelectMode && _draggingAssociationIndex == index
            ? (d) {
                if (_dragStartPos == null) return;
                final nx = (_dragStartPos!.dx + d.delta.dx).clamp(0.0, 10000.0);
                final ny = (_dragStartPos!.dy + d.delta.dy).clamp(0.0, 10000.0);
                state.moveAssociation(index, nx, ny);
                _dragStartPos = Offset(nx, ny);
              }
            : null,
        onPanEnd: isSelectMode ? (_) { _draggingAssociationIndex = null; _dragStartPos = null; } : null,
        child: AssociationDiamond(
          name: name,
          selected: selected,
          attributes: (association['attributes'] as List?)?.cast<Map<String, dynamic>>() ?? [],
        ),
      ),
    );
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

class _LinksPainter extends CustomPainter {
  _LinksPainter({
    required this.entities,
    required this.associations,
    required this.links,
    this.selectedLinkIndex = -1,
  });

  final List<Map<String, dynamic>> entities;
  final List<Map<String, dynamic>> associations;
  final List<Map<String, dynamic>> links;
  final int selectedLinkIndex;

  Offset _entityCenter(Map<String, dynamic> e) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    return Offset(x + _entityWidth / 2, y + _entityMinHeight / 2);
  }

  Offset _associationCenter(Map<String, dynamic> a) {
    final pos = a['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    final half = AssociationDiamond.diamondDisplayWidth / 2;
    return Offset(x + half, y + half);
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
    for (int i = 0; i < links.length; i++) {
      final link = links[i];
      final assocName = link['association'] as String?;
      final entityName = link['entity'] as String?;
      if (assocName == null || entityName == null) continue;
      final assoc = _findAssociation(assocName);
      final ent = _findEntity(entityName);
      if (assoc == null || ent == null) continue;
      final from = _associationCenter(assoc);
      final to = _entityCenter(ent);
      final card = link['cardinality'] as String? ?? '1,n';
      final selected = i == selectedLinkIndex;
      LinkArrow.paint(canvas, from: from, to: to, cardinality: card, selected: selected);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _InheritancePainter extends CustomPainter {
  _InheritancePainter({
    required this.entities,
    required this.links,
    this.selectedIndex = -1,
  });

  final List<Map<String, dynamic>> entities;
  final List<Map<String, dynamic>> links;
  final int selectedIndex;

  Offset _entityCenter(Map<String, dynamic> e) {
    final pos = e['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 0;
    final y = (pos?['y'] as num?)?.toDouble() ?? 0;
    return Offset(x + _entityWidth / 2, y + _entityMinHeight / 2);
  }

  Map<String, dynamic>? _findEntity(String name) {
    for (final e in entities) {
      if (e['name'] == name) return e;
    }
    return null;
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (int i = 0; i < links.length; i++) {
      final parent = _findEntity(links[i]['parent'] as String? ?? '');
      final child = _findEntity(links[i]['child'] as String? ?? '');
      if (parent == null || child == null) continue;
      final from = _entityCenter(parent);
      final to = _entityCenter(child);
      final selected = i == selectedIndex;
      final paint = Paint()
        ..color = selected ? AppTheme.secondary : AppTheme.primary.withValues(alpha: 0.8)
        ..strokeWidth = selected ? 2.5 : 1.5
        ..style = PaintingStyle.stroke;
      canvas.drawLine(from, to, paint);
      // Petit triangle côté enfant (héritage)
      final v = to - from;
      final len = v.distance;
      if (len > 10) {
        final u = Offset(v.dx / len, v.dy / len);
        final tip = to - u * 12.0;
        final perp = Offset(-u.dy, u.dx);
        final p1 = tip + perp * 6;
        final p2 = tip - perp * 6;
        final path = Path()..moveTo(to.dx, to.dy)..lineTo(p1.dx, p1.dy)..lineTo(p2.dx, p2.dy)..close();
        canvas.drawPath(path, Paint()..color = paint.color..style = PaintingStyle.fill);
        canvas.drawPath(path, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

/// Types SQL/Merise courants (style Looping / JMerise).
const List<String> _kAttributeTypes = [
  'VARCHAR(255)',
  'VARCHAR(100)',
  'VARCHAR(50)',
  'VARCHAR(500)',
  'CHAR(1)',
  'CHAR(10)',
  'INTEGER',
  'BIGINT',
  'SMALLINT',
  'DECIMAL(10,2)',
  'DECIMAL(15,4)',
  'NUMERIC(10,2)',
  'DATE',
  'DATETIME',
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

/// Retourne true si le type accepte une longueur (VARCHAR, CHAR).
bool _attributeTypeHasLength(String type) {
  final t = type.toUpperCase();
  return t.startsWith('VARCHAR') || t.startsWith('CHAR');
}

/// Extrait la longueur d'un type VARCHAR(n) ou CHAR(n), ou 255 par défaut.
int _parseTypeLength(String type) {
  final match = RegExp(r'\(\s*(\d+)\s*\)').firstMatch(type);
  if (match != null) return int.tryParse(match.group(1)!) ?? 255;
  return 255;
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
    return AlertDialog(
      title: const Text('Propriétés de l\'entité'),
      content: SizedBox(
        width: 820,
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
                  CheckboxListTile(
                    value: _isFictive,
                    title: const Text('Entité fictive (non générée MLD)', style: TextStyle(fontSize: 13)),
                    contentPadding: EdgeInsets.zero,
                    controlAffinity: ListTileControlAffinity.leading,
                    onChanged: (v) => setState(() => _isFictive = v == true),
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
                  }));
                },
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Ajouter un attribut'),
              ),
            ],
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
              m['type'] = m['type']?.toString() ?? 'VARCHAR(255)';
              m['is_primary_key'] = m['is_primary_key'] == true;
              m['nullable'] = m['nullable'] != false;
              m['is_unique'] = m['is_unique'] == true;
              final def = (m['default_value'] as String?)?.toString().trim() ?? '';
              if (def.isEmpty) m.remove('default_value'); else m['default_value'] = def;
              if ((m['description'] as String?)?.toString().trim().isEmpty ?? true) m.remove('description');
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
          SizedBox(width: 48, child: Text('Long.', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          SizedBox(width: 40, child: Text('Clé P.', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          SizedBox(width: 48, child: Text('Oblig.', style: Theme.of(context).textTheme.titleSmall)),
          const SizedBox(width: 6),
          SizedBox(width: 48, child: Text('Unique', style: Theme.of(context).textTheme.titleSmall)),
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
          SizedBox(
            width: 130,
            child: DropdownButtonFormField<String>(
              value: isCustomType ? '__custom__' : typeStr,
              decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 8)),
              items: [
                ..._kAttributeTypes.map((t) => DropdownMenuItem(value: t, child: Text(t, style: const TextStyle(fontSize: 11)))),
                const DropdownMenuItem(value: '__custom__', child: Text('Autre...', style: TextStyle(fontSize: 11))),
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
                decoration: const InputDecoration(hintText: 'Type', border: OutlineInputBorder(), isDense: true, contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 8)),
                initialValue: typeStr,
                onChanged: (v) => _attrs[index]['type'] = v.isEmpty ? 'VARCHAR(255)' : v,
              ),
            ),
          ],
          const SizedBox(width: 8),
          SizedBox(
            width: 56,
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
                    },
                  )
                : const SizedBox(),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 44,
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
          const SizedBox(width: 8),
          SizedBox(
            width: 48,
            child: CheckboxListTile(
              value: attr['nullable'] != true,
              title: const Text('', style: TextStyle(fontSize: 11)),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) => setState(() => _attrs[index]['nullable'] = v != true),
            ),
          ),
          const SizedBox(width: 8),
          SizedBox(
            width: 48,
            child: CheckboxListTile(
              value: attr['is_unique'] == true,
              title: const Text('', style: TextStyle(fontSize: 11)),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (v) => setState(() => _attrs[index]['is_unique'] = v == true),
            ),
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

/// Dialog pour éditer la liste d'attributs (entité ou association), style Looping.
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
              value: isCustomType ? '__custom__' : typeStr,
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
