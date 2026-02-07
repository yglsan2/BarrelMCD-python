import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/main_toolbar.dart';
import '../widgets/mcd_canvas.dart';
import 'markdown_import_screen.dart';

/// Écran principal : barre d'outils + canvas MCD (équivalent MainWindow Python).
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: const <ShortcutActivator, Intent>{
        SingleActivator(LogicalKeyboardKey.delete): _DeleteIntent(),
        SingleActivator(LogicalKeyboardKey.backspace): _DeleteIntent(),
        SingleActivator(LogicalKeyboardKey.keyZ, control: true): _UndoIntent(),
        SingleActivator(LogicalKeyboardKey.keyY, control: true): _RedoIntent(),
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
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            backgroundColor: AppTheme.background,
            body: Column(
              children: [
                _buildHeader(context),
                const MainToolbar(),
                Expanded(
                  child: Container(
                    color: AppTheme.canvasBackground,
                    child: const McdCanvas(),
                  ),
                ),
                _buildStatusBar(context),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: AppTheme.toolbarBg,
      child: Row(
        children: [
          Image.asset(
            'assets/images/logo.png',
            width: 28,
            height: 28,
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => Icon(Icons.storage, color: AppTheme.primary, size: 28),
          ),
          const SizedBox(width: 10),
          Text(
            'Barrel',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            'MCD',
            style: TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 16,
              fontWeight: FontWeight.bold,
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
            state.lastError ?? 'Prêt',
            style: TextStyle(
              color: state.lastError != null ? AppTheme.error : AppTheme.textTertiary,
              fontSize: 12,
            ),
          ),
        );
      },
    );
  }

  static void openMarkdownImport(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (ctx) => const MarkdownImportScreen(),
      ),
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
