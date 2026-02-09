import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/api_client.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/main_toolbar.dart';
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
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkApiHealth());
  }

  /// Consomme GET /health pour vérifier que l'API Python est joignable ; avertit l'utilisateur sinon.
  Future<void> _checkApiHealth() async {
    if (!mounted) return;
    final api = context.read<ApiClient>();
    final ok = await api.health();
    if (!mounted) return;
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('API BarrelMCD injoignable. Lancez le serveur Python (ex. port 8001) pour Valider, MLD/SQL, Import.'),
          duration: Duration(seconds: 5),
        ),
      );
    }
  }

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
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            backgroundColor: AppTheme.background,
            body: Column(
              children: [
                _buildHeader(context),
                MainToolbar(exportImageKey: _canvasRepaintKey, canvasKey: _canvasKey),
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
            errorBuilder: (_, __, ___) => const Icon(Icons.storage, color: AppTheme.primary, size: 28),
          ),
          const SizedBox(width: 10),
          const Text(
            'Barrel',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Text(
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
