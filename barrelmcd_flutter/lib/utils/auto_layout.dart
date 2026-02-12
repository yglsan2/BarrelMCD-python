// Auto-layout pour MCD (BarrelMCD).
//
// Algorithmes : pipeline hiérarchique (rank, order, position), force-directed (Fruchterman–Reingold),
// layout circulaire, centrage du diagramme et espacements.

import 'dart:math' as math;
import 'package:flutter/material.dart' show Offset;

/// Résultat d'un layout : nouvelles positions (centre) par id de nœud.
typedef LayoutResult = Map<String, Offset>;

/// Centre le résultat du layout pour que la boîte englobante ait son centre en [targetCenter].
/// Évite les diagrammes décalés et donne un rendu professionnel BarrelMCD.
LayoutResult centerLayoutResult(
  LayoutResult result,
  List<LayoutNode> nodes, {
  Offset targetCenter = Offset.zero,
}) {
  if (result.isEmpty || nodes.isEmpty) return result;
  double minX = double.infinity;
  double maxX = double.negativeInfinity;
  double minY = double.infinity;
  double maxY = double.negativeInfinity;
  final idToNode = {for (final n in nodes) n.id: n};
  for (final id in result.keys) {
    final c = result[id]!;
    final n = idToNode[id];
    if (n == null) continue;
    final hw = n.halfW;
    final hh = n.halfH;
    if (c.dx - hw < minX) minX = c.dx - hw;
    if (c.dx + hw > maxX) maxX = c.dx + hw;
    if (c.dy - hh < minY) minY = c.dy - hh;
    if (c.dy + hh > maxY) maxY = c.dy + hh;
  }
  if (!minX.isFinite) return result;
  final centerX = (minX + maxX) / 2;
  final centerY = (minY + maxY) / 2;
  final dx = targetCenter.dx - centerX;
  final dy = targetCenter.dy - centerY;
  return mapMap(result, (id, c) => Offset(c.dx + dx, c.dy + dy));
}

LayoutResult mapMap(LayoutResult r, Offset Function(String id, Offset c) f) {
  return {for (final e in r.entries) e.key: f(e.key, e.value)};
}

/// Nœud pour le layout : id, centre actuel, demi-largeur et demi-hauteur (pour éviter chevauchements).
class LayoutNode {
  LayoutNode(this.id, this.x, this.y, this.halfW, this.halfH);
  final String id;
  double x;
  double y;
  final double halfW;
  final double halfH;
  Offset get center => Offset(x, y);
}

/// Force-directed (Fruchterman–Reingold).
/// Répulsion k²/d, attraction d²/k, gravité vers un centre FIXE (évite le nuage qui dérive),
/// refroidissement linéaire. Jitter quand distance nulle (évite nœuds superposés).
LayoutResult runForceDirectedLayout({
  required List<LayoutNode> nodes,
  required List<({String a, String b})> edges,
  int iterations = 150,
  double area = 900,
  double minDistance = 80,
  double gravityStrength = 0.08,
  Offset? targetCenter,
}) {
  if (nodes.isEmpty) return {};
  final n = nodes.length;
  final k = math.sqrt(area / n).clamp(50.0, 140.0);
  final initialTemp = area / 6;
  double temperature = initialTemp;
  final idToNode = {for (final node in nodes) node.id: node};
  // Centre de gravité FIXE : le graphe est attiré vers le centre, pas vers son propre barycentre
  final gravityCenter = targetCenter ?? Offset(area / 2, area / 2);

  for (int iter = 0; iter < iterations; iter++) {
    final disp = <String, Offset>{};
    for (final node in nodes) disp[node.id] = Offset.zero;

    // Répulsion : f_r = k²/d (Fruchterman–Reingold), avec jitter si dist ~ 0
    for (int i = 0; i < nodes.length; i++) {
      for (int j = i + 1; j < nodes.length; j++) {
        final a = nodes[i];
        final b = nodes[j];
        double dx = a.x - b.x;
        double dy = a.y - b.y;
        if (dx.abs() < 0.01) dx = 0.01 + (i % 10) * 0.02;
        if (dy.abs() < 0.01) dy = 0.01 + (j % 10) * 0.02;
        final dist = math.sqrt(dx * dx + dy * dy);
        if (dist < 0.01) continue;
        final minD = minDistance + a.halfW + a.halfH + b.halfW + b.halfH;
        double force = (k * k) / dist;
        if (dist < minD) force += (minD - dist) * 0.6;
        final ux = dx / dist;
        final uy = dy / dist;
        disp[a.id] = Offset(disp[a.id]!.dx + ux * force, disp[a.id]!.dy + uy * force);
        disp[b.id] = Offset(disp[b.id]!.dx - ux * force, disp[b.id]!.dy - uy * force);
      }
    }

    // Attraction : f_a = d²/k sur les arêtes
    for (final e in edges) {
      final a = idToNode[e.a];
      final b = idToNode[e.b];
      if (a == null || b == null) continue;
      double dx = a.x - b.x;
      double dy = a.y - b.y;
      final dist = math.sqrt(dx * dx + dy * dy);
      if (dist < 0.01) continue;
      final force = (dist * dist) / k;
      final ux = dx / dist;
      final uy = dy / dist;
      disp[a.id] = Offset(disp[a.id]!.dx - ux * force, disp[a.id]!.dy - uy * force);
      disp[b.id] = Offset(disp[b.id]!.dx + ux * force, disp[b.id]!.dy + uy * force);
    }

    // Gravité vers le centre FIXE (évite que tout parte dans un coin — comme les logiciels de schémas)
    for (final node in nodes) {
      final gx = gravityCenter.dx - node.x;
      final gy = gravityCenter.dy - node.y;
      disp[node.id] = Offset(
        disp[node.id]!.dx + gx * gravityStrength,
        disp[node.id]!.dy + gy * gravityStrength,
      );
    }

    // Déplacement limité par la température (refroidissement linéaire)
    for (final node in nodes) {
      final d = disp[node.id]!;
      final len = math.sqrt(d.dx * d.dx + d.dy * d.dy);
      if (len < 0.01) continue;
      final limit = math.min(len, temperature);
      node.x += (d.dx / len) * limit;
      node.y += (d.dy / len) * limit;
    }
    temperature = initialTemp * (1.0 - (iter + 1) / iterations);
  }

  var result = {for (final node in nodes) node.id: Offset(node.x, node.y)};
  if (targetCenter != null) result = centerLayoutResult(result, nodes, targetCenter: targetCenter);
  return result;
}

/// Layout hiérarchique BarrelMCD (rangs, ordre, position).
/// 1) Rangs par longest-path en partant des SOURCES (nodes sans prédécesseurs).
/// 2) Couches = un rang par niveau. 3) Ordre dans chaque couche = barycentre des voisins (réduction croisements).
/// 4) Position Y = cumul ranksep, X = cumul nodesep.
LayoutResult runHierarchicalLayout({
  required List<LayoutNode> nodes,
  required List<({String a, String b})> edges,
  required bool Function(String id) isAssociation,
  double nodesep = 150,
  double ranksep = 180,
  Offset? targetCenter,
}) {
  if (nodes.isEmpty) return {};
  final idToNode = {for (final n in nodes) n.id: n};

  // Graphe : arête (a, b) = a -> b (vers le bas en Y). MCD : entité -> association.
  final successors = <String, List<String>>{};
  final predecessors = <String, List<String>>{};
  for (final n in nodes) {
    successors[n.id] = [];
    predecessors[n.id] = [];
  }
  for (final e in edges) {
    if (!idToNode.containsKey(e.a) || !idToNode.containsKey(e.b)) continue;
    successors[e.a]!.add(e.b);
    predecessors[e.b]!.add(e.a);
  }

  // Rangs longest-path : partir des SOURCES (pas de prédécesseur), rank(v) = min(rank(w)-1) pour w successeur.
  final rank = <String, int>{};
  for (final n in nodes) rank[n.id] = 0;
  final visited = <String>{};
  int dfs(String v) {
    if (visited.contains(v)) return rank[v]!;
    visited.add(v);
    final succs = successors[v]!;
    if (succs.isEmpty) {
      rank[v] = 0;
      return 0;
    }
    int r = 999999;
    for (final w in succs) {
      final rw = dfs(w) - 1;
      if (rw < r) r = rw;
    }
    rank[v] = r;
    return r;
  }
  for (final n in nodes) {
    if (predecessors[n.id]!.isEmpty) dfs(n.id);
  }
  for (final n in nodes) {
    if (!visited.contains(n.id)) dfs(n.id);
  }

  final minRank = rank.values.fold<int>(999999, (a, b) => a < b ? a : b);
  for (final k in rank.keys) rank[k] = rank[k]! - minRank;
  final maxRank = rank.values.fold<int>(0, (a, b) => a > b ? a : b);

  final layers = <int, List<String>>{};
  for (int r = 0; r <= maxRank; r++) layers[r] = [];
  for (final e in rank.entries) {
    if (e.value >= 0 && e.value <= maxRank) layers[e.value]!.add(e.key);
  }

  // Ordre dans chaque couche : médiane des rangs des voisins, plusieurs passes.
  final order = <String, int>{};
  final layerList = [for (int r = 0; r <= maxRank; r++) layers[r]!];
  final lastLayer = layerList[maxRank];
  if (lastLayer.isNotEmpty) {
    final sorted = List<String>.from(lastLayer)..sort();
    for (int i = 0; i < sorted.length; i++) order[sorted[i]] = i;
  }
  for (int r = maxRank - 1; r >= 0; r--) {
    final layer = layerList[r];
    if (layer.isEmpty) continue;
    final positions = <String, double>{};
    for (final v in layer) {
      final succs = successors[v]!;
      if (succs.isEmpty) positions[v] = 0.0;
      else {
        double sum = 0;
        for (final w in succs) sum += (order[w] ?? 0).toDouble();
        positions[v] = sum / succs.length;
      }
    }
    final sorted = List<String>.from(layer)..sort((a, b) => (positions[a] ?? 0).compareTo(positions[b] ?? 0));
    for (int i = 0; i < sorted.length; i++) order[sorted[i]] = i;
  }
  for (int r = 1; r <= maxRank; r++) {
    final layer = layerList[r];
    if (layer.isEmpty) continue;
    final positions = <String, double>{};
    for (final v in layer) {
      final preds = predecessors[v]!;
      if (preds.isEmpty) positions[v] = 0.0;
      else {
        double sum = 0;
        for (final u in preds) sum += (order[u] ?? 0).toDouble();
        positions[v] = sum / preds.length;
      }
    }
    final sorted = List<String>.from(layer)..sort((a, b) => (positions[a] ?? 0).compareTo(positions[b] ?? 0));
    for (int i = 0; i < sorted.length; i++) order[sorted[i]] = i;
  }

  // Position : Y par rang, X par ordre (nodesep entre nœuds).
  final result = <String, Offset>{};
  double prevY = 0;
  for (int r = 0; r <= maxRank; r++) {
    final layer = List<String>.from(layers[r]!)..sort((a, b) => (order[a] ?? 0).compareTo(order[b] ?? 0));
    if (layer.isEmpty) continue;
    double maxHeight = 0;
    for (final id in layer) {
      final n = idToNode[id]!;
      final h = n.halfH * 2;
      if (h > maxHeight) maxHeight = h;
    }
    if (maxHeight < 40) maxHeight = 40;

    double x = 0;
    for (final id in layer) {
      final n = idToNode[id]!;
      result[id] = Offset(x + n.halfW, prevY + maxHeight / 2);
      x += (n.halfW * 2) + nodesep;
    }
    prevY += maxHeight + ranksep;
  }

  if (targetCenter != null) return centerLayoutResult(result, nodes, targetCenter: targetCenter);
  return result;
}

/// Layout circulaire BarrelMCD : tous les nœuds sur un cercle.
/// Robuste pour graphes petits ou sans arêtes ; évite les cas dégénérés du hiérarchique / force-directed.
LayoutResult runCircularLayout({
  required List<LayoutNode> nodes,
  Offset? targetCenter,
  double radius = 280,
}) {
  if (nodes.isEmpty) return {};
  final n = nodes.length;
  final result = <String, Offset>{};
  for (int i = 0; i < n; i++) {
    final node = nodes[i];
    final angle = 2 * math.pi * i / n - math.pi / 2;
    result[node.id] = Offset(
      radius * math.cos(angle),
      radius * math.sin(angle),
    );
  }
  if (targetCenter != null) return centerLayoutResult(result, nodes, targetCenter: targetCenter);
  return result;
}
