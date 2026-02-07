import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../core/canvas_mode.dart';
import '../theme/app_theme.dart';
import 'entity_box.dart';
import 'association_diamond.dart';
import 'link_arrow.dart';

const double _entityWidth = 200;
const double _entityMinHeight = 80;
const double _diamondSize = 60;

/// Zone de dessin MCD interactive : créer/déplacer entités et associations, lier, zoom.
class McdCanvas extends StatefulWidget {
  const McdCanvas({super.key});

  @override
  State<McdCanvas> createState() => _McdCanvasState();
}

class _McdCanvasState extends State<McdCanvas> {
  final TransformationController _transform = TransformationController();
  static const double _gridSize = 20;
  int? _draggingEntityIndex;
  int? _draggingAssociationIndex;
  Offset? _dragStartPos;

  @override
  void dispose() {
    _transform.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final sceneWidth = constraints.maxWidth + 4000.0;
        final sceneHeight = constraints.maxHeight + 4000.0;
        return Stack(
          children: [
            InteractiveViewer(
              transformationController: _transform,
              minScale: 0.1,
              maxScale: 5.0,
              boundaryMargin: const EdgeInsets.all(2000),
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTapUp: (d) => _onCanvasTap(d, sceneWidth, sceneHeight),
                  child: Consumer<CanvasModeState>(
                  builder: (context, modeState, _) => CustomPaint(
                    painter: _GridPainter(showGrid: modeState.showGrid, gridSize: _gridSize),
                    size: Size(sceneWidth, sceneHeight),
                    child: Consumer2<McdState, CanvasModeState>(
                      builder: (context, state, modeState2, _) {
                        return Stack(
                          clipBehavior: Clip.none,
                          children: [
                            _buildLinks(state),
                            ...state.entities.asMap().entries.map((e) => _buildEntity(state, modeState2, e.key, e.value)),
                            ...state.associations.asMap().entries.map((a) => _buildAssociation(state, modeState2, a.key, a.value)),
                            _buildLogo(),
                          ],
                        );
                      },
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  void _onCanvasTap(TapUpDetails d, double sceneWidth, double sceneHeight) {
    final pos = d.localPosition;
    final state = context.read<McdState>();
    final modeState = context.read<CanvasModeState>();

    if (modeState.mode == CanvasMode.addEntity) {
      _showNewEntityDialog(pos.dx, pos.dy);
      return;
    }
    if (modeState.mode == CanvasMode.addAssociation) {
      _showNewAssociationDialog(pos.dx, pos.dy);
      return;
    }
    if (modeState.mode == CanvasMode.select) {
      state.selectNone();
    }
  }

  void _showNewEntityDialog(double x, double y) async {
    final name = await showDialog<String>(
      context: context,
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
    if (name != null && name.isNotEmpty && context.mounted) {
      final state = context.read<McdState>();
      final existing = state.entities.any((e) => (e['name'] as String?) == name);
      if (existing) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Une entité "$name" existe déjà.')));
        return;
      }
      state.addEntity(name, x, y);
    }
  }

  void _showNewAssociationDialog(double x, double y) async {
    final name = await showDialog<String>(
      context: context,
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
    if (name != null && name.isNotEmpty && context.mounted) {
      final state = context.read<McdState>();
      final existing = state.associations.any((a) => (a['name'] as String?) == name);
      if (existing) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Une association "$name" existe déjà.')));
        return;
      }
      state.addAssociation(name, x, y);
    }
  }

  void _onEntityTap(McdState state, CanvasModeState modeState, int index) {
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
  }

  void _onAssociationTap(McdState state, CanvasModeState modeState, int index) {
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
  }

  Future<void> _showCardinalityDialog(String associationName, String entityName) async {
    final card = await showDialog<String>(
      context: context,
      builder: (ctx) {
        String v = '1,n';
        return StatefulBuilder(
          builder: (ctx, setState) {
            return AlertDialog(
              title: const Text('Cardinalité'),
              content: DropdownButtonFormField<String>(
                value: v,
                decoration: const InputDecoration(labelText: 'Côté entité'),
                items: const [
                  DropdownMenuItem(value: '1,1', child: Text('1,1')),
                  DropdownMenuItem(value: '1,n', child: Text('1,n')),
                  DropdownMenuItem(value: '0,1', child: Text('0,1')),
                  DropdownMenuItem(value: '0,n', child: Text('0,n')),
                  DropdownMenuItem(value: 'n,1', child: Text('n,1')),
                  DropdownMenuItem(value: 'n,n', child: Text('n,n')),
                ],
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
    if (card != null && context.mounted) {
      context.read<McdState>().addAssociationLink(associationName, entityName, card);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lien $associationName — $entityName ($card) créé.')));
    }
  }

  Widget _buildLinks(McdState state) {
    final links = state.associationLinks;
    if (links.isEmpty) return const SizedBox.shrink();
    return CustomPaint(
      painter: _LinksPainter(
        entities: state.entities,
        associations: state.associations,
        links: links,
        selectedLinkIndex: state.selectedType == 'link' ? state.selectedIndex : -1,
      ),
      size: Size.infinite,
    );
  }

  Widget _buildEntity(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> entity) {
    final name = entity['name'] as String? ?? 'Entité';
    final pos = entity['position'] as Map<String, dynamic>?;
    final x = (pos?['x'] as num?)?.toDouble() ?? 100;
    final y = (pos?['y'] as num?)?.toDouble() ?? 100;
    final attrs = (entity['attributes'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final selected = state.isEntitySelected(index);
    final isSelectMode = modeState.mode == CanvasMode.select;

    return Positioned(
      left: x,
      top: y,
      child: GestureDetector(
        onTap: () => _onEntityTap(state, modeState, index),
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
          onTap: () => _onEntityTap(state, modeState, index),
        ),
      ),
    );
  }

  Widget _buildAssociation(McdState state, CanvasModeState modeState, int index, Map<String, dynamic> association) {
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
        child: AssociationDiamond(name: name, selected: selected),
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
                errorBuilder: (_, __, ___) => Icon(Icons.storage, color: AppTheme.primary, size: 24),
              ),
              const SizedBox(width: 6),
              Text(
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

}

class _GridPainter extends CustomPainter {
  _GridPainter({required this.showGrid, required this.gridSize});
  final bool showGrid;
  final double gridSize;

  @override
  void paint(Canvas canvas, Size size) {
    if (!showGrid) return;
    final minor = Paint()..color = AppTheme.gridMinor;
    final major = Paint()..color = AppTheme.gridMajor;
    const majorEvery = 5;
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
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
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
    return Offset(x + _diamondSize / 2, y + _diamondSize / 2);
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
