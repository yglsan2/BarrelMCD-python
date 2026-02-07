import 'dart:convert';
import 'package:http/http.dart' as http;

/// Client HTTP pour l'API BarrelMCD (Python).
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

  /// POST /api/validate
  Future<Map<String, dynamic>> validateMcd(Map<String, dynamic> mcd) async {
    return post('/api/validate', {'mcd': mcd});
  }

  /// POST /api/to-mld
  Future<Map<String, dynamic>> mcdToMld(Map<String, dynamic> mcd) async {
    return post('/api/to-mld', {'mcd': mcd});
  }

  /// POST /api/to-sql
  Future<Map<String, dynamic>> mcdToSql(Map<String, dynamic> mcd) async {
    return post('/api/to-sql', {'mcd': mcd});
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
