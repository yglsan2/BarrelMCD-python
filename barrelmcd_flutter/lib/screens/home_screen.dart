import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/main_toolbar.dart';
import '../widgets/export_toolbar.dart';
import '../widgets/mcd_canvas.dart';
import 'markdown_import_screen.dart';

/// Écran principal : barre d'outils + canvas MCD (équivalent MainWindow Python).
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey _canvasRepaintKey = GlobalKey();
  final GlobalKey<McdCanvasState> _canvasKey = GlobalKey<McdCanvasState>();

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: const <ShortcutActivator, Intent>{
        SingleActivator(LogicalKeyboardKey.delete): _DeleteIntent(),
        SingleActivator(LogicalKeyboardKey.backspace): _DeleteIntent(),
        SingleActivator(LogicalKeyboardKey.keyZ, control: true): _UndoIntent(),
        SingleActivator(LogicalKeyboardKey.keyY, control: true): _RedoIntent(),
        SingleActivator(LogicalKeyboardKey.keyN, control: true): _NewIntent(),
        SingleActivator(LogicalKeyboardKey.keyO, control: true): _OpenIntent(),
        SingleActivator(LogicalKeyboardKey.keyS, control: true): _SaveIntent(),
        SingleActivator(LogicalKeyboardKey.keyM, control: true): _MarkdownIntent(),
        SingleActivator(LogicalKeyboardKey.keyF): _FitIntent(),
        SingleActivator(LogicalKeyboardKey.keyL, control: true): _AutoLayoutIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          _DeleteIntent: CallbackAction<_DeleteIntent>(onInvoke: (_) {
            context.read<McdState>().deleteSelected();
            return null;
          }),
          _UndoIntent: CallbackAction<_UndoIntent>(onInvoke: (_) {
            final state = context.read<McdState>();
            if (state.canUndo) state.undo();
            return null;
          }),
          _RedoIntent: CallbackAction<_RedoIntent>(onInvoke: (_) {
            final state = context.read<McdState>();
            if (state.canRedo) state.redo();
            return null;
          }),
          _NewIntent: CallbackAction<_NewIntent>(onInvoke: (_) {
            MainToolbar.triggerNew(context);
            return null;
          }),
          _OpenIntent: CallbackAction<_OpenIntent>(onInvoke: (_) {
            MainToolbar.triggerOpen(context);
            return null;
          }),
          _SaveIntent: CallbackAction<_SaveIntent>(onInvoke: (_) {
            MainToolbar.triggerSave(context);
            return null;
          }),
          _MarkdownIntent: CallbackAction<_MarkdownIntent>(onInvoke: (_) {
            Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MarkdownImportScreen()));
            return null;
          }),
          _FitIntent: CallbackAction<_FitIntent>(onInvoke: (_) {
            _canvasKey.currentState?.fitToView(context.read<McdState>());
            return null;
          }),
          _AutoLayoutIntent: CallbackAction<_AutoLayoutIntent>(onInvoke: (_) {
            MainToolbar.showAutoLayoutDialog(context, canvasKey: _canvasKey);
            return null;
          }),
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            backgroundColor: AppTheme.background,
            body: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Column(
                children: [
                  _buildHeader(context),
                  MainToolbar(exportImageKey: _canvasRepaintKey, canvasKey: _canvasKey),
                  const ExportToolbar(),
                  Expanded(
                    child: Container(
                      color: AppTheme.canvasBackground,
                      child: McdCanvas(key: _canvasKey, repaintBoundaryKey: _canvasRepaintKey),
                    ),
                  ),
                  _buildStatusBar(context),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    const logoSize = 14.0;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      color: AppTheme.toolbarBg,
      child: Row(
        children: [
          SizedBox(
            width: logoSize,
            height: logoSize,
            child: Image.asset(
              'assets/images/logo.png',
              fit: BoxFit.contain,
              errorBuilder: (_, __, ___) => const Icon(Icons.storage, color: AppTheme.primary, size: logoSize),
            ),
          ),
          const SizedBox(width: 5),
          const Text(
            'Barrel',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.2,
            ),
          ),
          const Text(
            'MCD',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBar(BuildContext context) {
    return Consumer<McdState>(
      builder: (_, state, __) {
        return Container(
          height: 28,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          color: AppTheme.surfaceDark,
          alignment: Alignment.centerLeft,
          child: Text(
            state.lastError ?? (state.selectedType == 'link' ? 'Lien sélectionné — Suppr : supprimer | Clic droit : menu' : 'Prêt'),
            style: TextStyle(
              color: state.lastError != null ? AppTheme.error : AppTheme.textTertiary,
              fontSize: 12,
            ),
          ),
        );
      },
    );
  }

}

class _DeleteIntent extends Intent {
  const _DeleteIntent();
}
class _UndoIntent extends Intent {
  const _UndoIntent();
}
class _RedoIntent extends Intent {
  const _RedoIntent();
}
class _NewIntent extends Intent {
  const _NewIntent();
}
class _OpenIntent extends Intent {
  const _OpenIntent();
}
class _SaveIntent extends Intent {
  const _SaveIntent();
}
class _MarkdownIntent extends Intent {
  const _MarkdownIntent();
}
class _FitIntent extends Intent {
  const _FitIntent();
}
class _AutoLayoutIntent extends Intent {
  const _AutoLayoutIntent();
}