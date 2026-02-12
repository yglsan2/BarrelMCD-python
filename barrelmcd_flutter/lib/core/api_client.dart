import 'dart:convert';
import 'package:http/http.dart' as http;

/// Client HTTP pour l'API BarrelMCD (Python).
/// Chaque méthode appelle un endpoint du backend ; aucune logique métier (validation, parsing, MCD→MLD→SQL) n'est dupliquée ici.
/// Voir docs/VERIFICATION_API_FLUTTER.md pour la correspondance endpoints ↔ consommation Flutter.
class ApiClient {
  ApiClient({required this.baseUrl});

  final String baseUrl;

  Future<Map<String, dynamic>> get(String path) async {
    final uri = Uri.parse('$baseUrl$path');
    final response = await http.get(uri);
    return _handleResponse(response);
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    final uri = Uri.parse('$baseUrl$path');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return _handleResponse(response);
  }

  static Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw ApiException(
      statusCode: response.statusCode,
      body: response.body,
    );
  }

  Future<bool> health() async {
    try {
      final r = await get('/health');
      return r['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  /// POST /api/parse-markdown
  Future<Map<String, dynamic>> parseMarkdown(String content) async {
    return post('/api/parse-markdown', {'content': content});
  }

  /// POST /api/parse-mots-codes — mots codés format BarrelMCD → format canvas
  Future<Map<String, dynamic>> parseMotsCodes(String content) async {
    return post('/api/parse-mots-codes', {'content': content});
  }

  /// POST /api/validate
  Future<Map<String, dynamic>> validateMcd(Map<String, dynamic> mcd) async {
    return post('/api/validate', {'mcd': mcd});
  }

  /// POST /api/validate-create-association — logique Barrel
  Future<Map<String, dynamic>> validateCreateAssociation(Map<String, dynamic> mcd, String name) async {
    return post('/api/validate-create-association', {'mcd': mcd, 'name': name});
  }

  /// POST /api/validate-add-link — logique Barrel
  Future<Map<String, dynamic>> validateAddLink(
    Map<String, dynamic> mcd,
    String associationName,
    String entityName,
    String cardEntity,
    String cardAssoc,
  ) async {
    return post('/api/validate-add-link', {
      'mcd': mcd,
      'association_name': associationName,
      'entity_name': entityName,
      'card_entity': cardEntity,
      'card_assoc': cardAssoc,
    });
  }

  /// POST /api/validate-association-after-update — logique Barrel (1,1 + rubriques)
  Future<Map<String, dynamic>> validateAssociationAfterUpdate(
    Map<String, dynamic> mcd,
    String associationName,
    List<Map<String, dynamic>>? newAttributes,
  ) async {
    return post('/api/validate-association-after-update', {
      'mcd': mcd,
      'association_name': associationName,
      'new_attributes': newAttributes,
    });
  }

  /// POST /api/to-mld
  Future<Map<String, dynamic>> mcdToMld(Map<String, dynamic> mcd) async {
    return post('/api/to-mld', {'mcd': mcd});
  }

  /// POST /api/to-mpd — dbms: mysql | postgresql | sqlite | sqlserver
  Future<Map<String, dynamic>> mcdToMpd(Map<String, dynamic> mcd, {String dbms = 'mysql'}) async {
    return post('/api/to-mpd', {'mcd': mcd, 'dbms': dbms});
  }

  /// POST /api/to-sql — dbms: mysql | postgresql | sqlite
  Future<Map<String, dynamic>> mcdToSql(Map<String, dynamic> mcd, {String dbms = 'mysql'}) async {
    return post('/api/to-sql', {'mcd': mcd, 'dbms': dbms});
  }

  /// POST /api/analyze-data
  Future<Map<String, dynamic>> analyzeData(dynamic data, {String formatType = 'json'}) async {
    return post('/api/analyze-data', {'data': data, 'format_type': formatType});
  }
}

class ApiException implements Exception {
  ApiException({required this.statusCode, required this.body});
  final int statusCode;
  final String body;
  @override
  String toString() => 'ApiException($statusCode): $body';
}
