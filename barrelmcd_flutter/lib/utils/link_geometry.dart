import 'dart:math' as math;
import 'package:flutter/material.dart' show Offset, Rect;
import '../widgets/association_oval.dart';

/// Géométrie des liens MCD (Barrel + DrawDB).
/// Un lien = un arc entre une association et une entité.
/// Une seule source de vérité pour les points d'accroche : association (pointe du bras) et entité (bras ou bord).
/// Utilisé par le canvas (hit-test, segment, drag) et par le painter des liens.

const double kEntityWidth = 200.0;
const double kEntityMinHeight = 80.0;
const double kEntityAttrLineHeight = 24.0;

/// Diamètre effectif du cercle d'association (min = cercle visible, pas de décalage).
double effectiveAssociationWidth(Map<String, dynamic> a) {
  final w = (a['width'] as num?)?.toDouble() ?? 260.0;
  return math.max(AssociationOval.minDiameter, w);
}

/// Centre du cercle d'association en coordonnées scène.
Offset associationCenter(Map<String, dynamic> a) {
  final pos = a['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = effectiveAssociationWidth(a);
  final boxSize = w + 2 * AssociationOval.armExtensionLength;
  return Offset(x + boxSize / 2, y + boxSize / 2);
}

/// Position de la pointe du bras sur l'association (point d'accroche du lien).
Offset associationArmPosition(Map<String, dynamic> a, Map<String, dynamic> link) {
  final center = associationCenter(a);
  final w = effectiveAssociationWidth(a);
  final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
  final armIndex = (link['arm_index'] as num?)?.toInt() ?? 0;
  final angle = (armIndex < angles.length ? angles[armIndex].toDouble() : 0.0);
  return armPositionFromCenter(center, angle, w, w);
}

/// Hauteur d'une entité (header + lignes d'attributs), comme DrawDB tableHeaderHeight + fields * tableFieldHeight.
double entityHeight(Map<String, dynamic> e) {
  final attrs = (e['attributes'] as List?) ?? [];
  final attrCount = attrs.every((a) => a is Map) ? attrs.length : 0;
  return (e['height'] as num?)?.toDouble() ??
      (kEntityMinHeight + (attrCount > 0 ? attrCount * kEntityAttrLineHeight : 0));
}

/// Extension des bras d'entité (hors du rectangle), comme armExtensionLength pour l'association.
const double kEntityArmExtension = 12.0;

/// Position sur le contour du rectangle de l'entité à l'angle [angleDeg] (0 = droite, 90 = bas, 180 = gauche, 270 = haut).
/// Retourne (point sur le bord, normale sortante unitaire).
({Offset position, Offset normal}) entityArmPositionAndNormal(
  Map<String, dynamic> e,
  double angleDeg, {
  double? entityWidth,
}) {
  final pos = e['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = entityWidth ?? (e['width'] as num?)?.toDouble() ?? kEntityWidth;
  final h = entityHeight(e);
  final cx = x + w / 2;
  final cy = y + h / 2;
  final hw = w / 2;
  final hh = h / 2;
  final rad = angleDeg * math.pi / 180;
  final cos = math.cos(rad);
  final sin = math.sin(rad);
  double t = double.infinity;
  if (cos > 0.001) t = math.min(t, hw / cos);
  if (cos < -0.001) t = math.min(t, -hw / cos);
  if (sin > 0.001) t = math.min(t, hh / sin);
  if (sin < -0.001) t = math.min(t, -hh / sin);
  if (t == double.infinity) t = 0;
  final px = cx + t * cos;
  final py = cy + t * sin;
  Offset normal = Offset.zero;
  if (t == hw / cos && cos > 0) normal = const Offset(1, 0);
  else if (t == -hw / cos && cos < 0) normal = const Offset(-1, 0);
  else if (t == hh / sin && sin > 0) normal = const Offset(0, 1);
  else if (t == -hh / sin && sin < 0) normal = const Offset(0, -1);
  else {
    if (cos.abs() > sin.abs()) normal = Offset(cos > 0 ? 1 : -1, 0);
    else normal = Offset(0, sin > 0 ? 1 : -1);
  }
  return (position: Offset(px, py), normal: normal);
}

/// Pointe du bras d'entité (bord + extension vers l'extérieur), pour accroche du lien.
Offset entityArmTipPosition(Map<String, dynamic> e, double angleDeg, {double? entityWidth, double extension = kEntityArmExtension}) {
  final arm = entityArmPositionAndNormal(e, angleDeg, entityWidth: entityWidth);
  return Offset(arm.position.dx + arm.normal.dx * extension, arm.position.dy + arm.normal.dy * extension);
}

/// Point d'accroche du lien sur l'entité.
/// Priorité 1 : entity_side (left/right/top/bottom) = côté où part/arrive le lien — toujours respecté.
/// Priorité 2 : bras (entity_arm_index) si pas de entity_side.
/// Priorité 3 : associationArmPos pour choisir le bord le plus proche (gauche/droite/haut/bas).
Offset entityLinkEndpoint(
  Map<String, dynamic> e,
  Offset associationArmPos, {
  Map<String, dynamic>? link,
  double? entityWidth,
}) {
  final pos = e['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = entityWidth ?? (e['width'] as num?)?.toDouble() ?? kEntityWidth;
  final h = entityHeight(e);
  final centerX = x + w / 2;
  final centerY = y + h / 2;
  final leftX = x;
  final rightX = x + w;
  final topY = y;
  final bottomY = y + h;
  final side = link?['entity_side'] as String?;
  if (side == 'left') return Offset(leftX, centerY);
  if (side == 'right') return Offset(rightX, centerY);
  if (side == 'top') return Offset(centerX, topY);
  if (side == 'bottom') return Offset(centerX, bottomY);
  final armAngles = (e['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()).toList();
  final entityArmIndex = (link?['entity_arm_index'] as num?)?.toInt();
  if (armAngles != null && armAngles.isNotEmpty && entityArmIndex != null && entityArmIndex >= 0 && entityArmIndex < armAngles.length) {
    return entityArmTipPosition(e, armAngles[entityArmIndex], entityWidth: entityWidth);
  }
  // Choisir le bord le plus proche de l'association (même logique dans toutes les directions).
  final dx = associationArmPos.dx - centerX;
  final dy = associationArmPos.dy - centerY;
  if (dx.abs() >= dy.abs()) return dx < 0 ? Offset(leftX, centerY) : Offset(rightX, centerY);
  return dy < 0 ? Offset(centerX, topY) : Offset(centerX, bottomY);
}

/// Angle du bras en degrés (pour affichage optionnel du lien).
double associationArmAngle(Map<String, dynamic> a, Map<String, dynamic> link) {
  final angles = (a['arm_angles'] as List?)?.cast<num>() ?? [0.0, 180.0];
  final armIndex = (link['arm_index'] as num?)?.toInt() ?? 0;
  return (armIndex < angles.length ? angles[armIndex].toDouble() : 0.0);
}

/// Segment complet du lien en scène : (from = pointe du bras, to = bord entité).
/// Méthode unique pour dessin et hit-test (comme DrawDB calcPath utilise les mêmes entrées).
({Offset from, Offset to}) getLinkSegment(
  Map<String, dynamic> assoc,
  Map<String, dynamic> entity,
  Map<String, dynamic> link,
) {
  final from = associationArmPosition(assoc, link);
  final to = entityLinkEndpoint(entity, from, link: link);
  return (from: from, to: to);
}

/// Indice du bras d'association le plus aligné avec la direction vers l'entité (pour que le lien parte du bon côté).
int bestArmIndexForLink(Map<String, dynamic> assoc, Map<String, dynamic> entity) {
  final center = associationCenter(assoc);
  final pos = entity['position'] as Map<String, dynamic>?;
  final ex = (pos?['x'] as num?)?.toDouble() ?? 0;
  final ey = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = (entity['width'] as num?)?.toDouble() ?? kEntityWidth;
  final h = entityHeight(entity);
  final entityCenter = Offset(ex + w / 2, ey + h / 2);
  final dx = entityCenter.dx - center.dx;
  final dy = entityCenter.dy - center.dy;
  double angleDeg = math.atan2(dy, dx) * 180 / math.pi;
  if (angleDeg < 0) angleDeg += 360;
  final angles = (assoc['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()).toList() ?? [0.0, 180.0];
  int best = 0;
  double bestDiff = 360;
  for (int i = 0; i < angles.length; i++) {
    double a = angles[i];
    double diff = (angleDeg - a).abs();
    if (diff > 180) diff = 360 - diff;
    if (diff < bestDiff) {
      bestDiff = diff;
      best = i;
    }
  }
  return best;
}

/// Indice du bras d'entité le plus aligné avec la direction vers l'association (lien part du bon côté de l'entité).
int bestEntityArmIndexForLink(Map<String, dynamic> entity, Map<String, dynamic> assoc) {
  final entityCenter = entityCenterOffset(entity);
  final assocCenter = associationCenter(assoc);
  final dx = assocCenter.dx - entityCenter.dx;
  final dy = assocCenter.dy - entityCenter.dy;
  double angleDeg = math.atan2(dy, dx) * 180 / math.pi;
  if (angleDeg < 0) angleDeg += 360;
  final angles = (entity['arm_angles'] as List?)?.cast<num>().map((n) => n.toDouble()).toList() ?? [0.0, 90.0, 180.0, 270.0];
  int best = 0;
  double bestDiff = 360;
  for (int i = 0; i < angles.length; i++) {
    double a = angles[i];
    double diff = (angleDeg - a).abs();
    if (diff > 180) diff = 360 - diff;
    if (diff < bestDiff) {
      bestDiff = diff;
      best = i;
    }
  }
  return best;
}

Offset entityCenterOffset(Map<String, dynamic> e) {
  final pos = e['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = (e['width'] as num?)?.toDouble() ?? kEntityWidth;
  final h = entityHeight(e);
  return Offset(x + w / 2, y + h / 2);
}

/// Marge au début du trait (départ depuis l'ancre), utilisée par LinkArrow.
const double kArrowStartMargin = 10.0;
/// Marge pour que la pointe et le chevron s'arrêtent juste avant la forme (jamais dedans).
const double kArrowTipMargin = 12.0;
/// Longueur minimale du segment affiché pour éviter un lien « écrasé » (tache) quand association et entité sont très proches.
const double kMinLinkSegmentLength = 48.0;

/// Rectangle englobant d'une entité en coordonnées scène.
Rect entityRect(Map<String, dynamic> e, {double? entityWidth}) {
  final pos = e['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = entityWidth ?? (e['width'] as num?)?.toDouble() ?? kEntityWidth;
  final h = entityHeight(e);
  return Rect.fromLTWH(x, y, w, h);
}

/// Intersection du rayon [origin] + t*[dir] (t>0) avec le rectangle [rect]. Retourne le point d'impact et la normale sortante, ou null.
({Offset point, Offset normal})? rayRectIntersection(Offset origin, Offset dir, Rect rect) {
  final dx = dir.dx;
  final dy = dir.dy;
  final len = math.sqrt(dx * dx + dy * dy);
  if (len < 1e-6) return null;
  final ux = dx / len;
  final uy = dy / len;
  double tMin = double.infinity;
  Offset normal = Offset.zero;
  if (ux.abs() > 1e-6) {
    if (ux > 0) {
      final t = (rect.right - origin.dx) / ux;
      if (t > 0 && t < tMin && rect.top <= origin.dy + t * uy && origin.dy + t * uy <= rect.bottom) {
        tMin = t;
        normal = const Offset(1, 0);
      }
    } else {
      final t = (rect.left - origin.dx) / ux;
      if (t > 0 && t < tMin && rect.top <= origin.dy + t * uy && origin.dy + t * uy <= rect.bottom) {
        tMin = t;
        normal = const Offset(-1, 0);
      }
    }
  }
  if (uy.abs() > 1e-6) {
    if (uy > 0) {
      final t = (rect.bottom - origin.dy) / uy;
      if (t > 0 && t < tMin && rect.left <= origin.dx + t * ux && origin.dx + t * ux <= rect.right) {
        tMin = t;
        normal = const Offset(0, 1);
      }
    } else {
      final t = (rect.top - origin.dy) / uy;
      if (t > 0 && t < tMin && rect.left <= origin.dx + t * ux && origin.dx + t * ux <= rect.right) {
        tMin = t;
        normal = const Offset(0, -1);
      }
    }
  }
  if (tMin == double.infinity) return null;
  return (point: Offset(origin.dx + tMin * ux, origin.dy + tMin * uy), normal: normal);
}

/// Intersection du rayon [origin] + t*[dir] (t>0) avec le cercle.
/// Retourne le premier impact (entrée si origin dehors, sortie si origin dedans) et la normale sortante.
({Offset point, Offset normal})? rayCircleIntersection(Offset origin, Offset dir, Offset center, double radius) {
  final dx = dir.dx;
  final dy = dir.dy;
  final len = math.sqrt(dx * dx + dy * dy);
  if (len < 1e-6) return null;
  final ux = dx / len;
  final uy = dy / len;
  final ex = origin.dx - center.dx;
  final ey = origin.dy - center.dy;
  final a = ux * ux + uy * uy;
  final b = 2 * (ex * ux + ey * uy);
  final c = ex * ex + ey * ey - radius * radius;
  final disc = b * b - 4 * a * c;
  if (disc < 0) return null;
  final sqrtDisc = math.sqrt(disc);
  double t = (-b - sqrtDisc) / (2 * a);
  if (t <= 0) t = (-b + sqrtDisc) / (2 * a);
  if (t <= 0) return null;
  final px = origin.dx + t * ux;
  final py = origin.dy + t * uy;
  final nx = (px - center.dx) / radius;
  final ny = (py - center.dy) / radius;
  return (point: Offset(px, py), normal: Offset(nx, ny));
}

/// Retourne le point où doit finir la flèche : intersection rayon (from→tip) avec le bord de l'entité,
/// puis marge le long du rayon (extérieur si [from] dans le rect, sinon recul avant le bord).
/// [arrowTipMargin] optionnel : marge en px (défaut [kArrowTipMargin]).
Offset snapTipToEntityBoundary(Offset from, Offset tip, Map<String, dynamic> entity, {double? entityWidth, double? arrowTipMargin}) {
  final margin = arrowTipMargin ?? kArrowTipMargin;
  final rect = entityRect(entity, entityWidth: entityWidth);
  final dir = Offset(tip.dx - from.dx, tip.dy - from.dy);
  final len = math.sqrt(dir.dx * dir.dx + dir.dy * dir.dy);
  if (len < 1e-6) return tip;
  final ux = dir.dx / len;
  final uy = dir.dy / len;
  final hit = rayRectIntersection(from, dir, rect);
  if (hit == null) {
    return Offset(tip.dx - ux * margin, tip.dy - uy * margin);
  }
  final fromInside = rect.contains(Offset(from.dx, from.dy));
  if (fromInside) {
    return Offset(
      hit.point.dx + hit.normal.dx * margin,
      hit.point.dy + hit.normal.dy * margin,
    );
  }
  final hitDist = math.sqrt(
    (hit.point.dx - from.dx) * (hit.point.dx - from.dx) +
    (hit.point.dy - from.dy) * (hit.point.dy - from.dy),
  );
  if (hitDist > len + 1) {
    return Offset(tip.dx - ux * margin, tip.dy - uy * margin);
  }
  return Offset(hit.point.dx - ux * margin, hit.point.dy - uy * margin);
}

/// Cercle d'association : centre et rayon effectif (demi-largeur + extension).
({Offset center, double radius}) associationCircle(Map<String, dynamic> a) {
  final pos = a['position'] as Map<String, dynamic>?;
  final x = (pos?['x'] as num?)?.toDouble() ?? 0;
  final y = (pos?['y'] as num?)?.toDouble() ?? 0;
  final w = (a['width'] as num?)?.toDouble() ?? 260.0;
  final boxSize = w + 2 * AssociationOval.armExtensionLength;
  final center = Offset(x + boxSize / 2, y + boxSize / 2);
  final radius = w / 2;
  return (center: center, radius: radius);
}

/// Retourne le point où doit finir la flèche : intersection rayon (from→tip) avec le cercle d'association,
/// puis marge. Intersection la plus proche de [from]. La pointe ne dépasse jamais [tip] (même longueur max).
/// [arrowTipMargin] optionnel : marge en px (défaut [kArrowTipMargin]).
Offset snapTipToAssociationBoundary(Offset from, Offset tip, Map<String, dynamic> assoc, {double? arrowTipMargin}) {
  final margin = arrowTipMargin ?? kArrowTipMargin;
  final circle = associationCircle(assoc);
  final dir = Offset(tip.dx - from.dx, tip.dy - from.dy);
  final len = math.sqrt(dir.dx * dir.dx + dir.dy * dir.dy);
  if (len < 1e-6) return tip;
  final ux = dir.dx / len;
  final uy = dir.dy / len;
  final ex = from.dx - circle.center.dx;
  final ey = from.dy - circle.center.dy;
  final a = ux * ux + uy * uy;
  final b = 2 * (ex * ux + ey * uy);
  final c = ex * ex + ey * ey - circle.radius * circle.radius;
  final disc = b * b - 4 * a * c;
  if (disc < 0) {
    return Offset(tip.dx - ux * margin, tip.dy - uy * margin);
  }
  final sqrtDisc = math.sqrt(disc);
  final t1 = (-b - sqrtDisc) / (2 * a);
  final t2 = (-b + sqrtDisc) / (2 * a);
  double t = t1 > 0 ? t1 : (t2 > 0 ? t2 : -1);
  if (t <= 0) return Offset(tip.dx - ux * margin, tip.dy - uy * margin);
  if (t > len) {
    return Offset(tip.dx - ux * margin, tip.dy - uy * margin);
  }
  final hitX = from.dx + t * ux;
  final hitY = from.dy + t * uy;
  final result = Offset(hitX - ux * margin, hitY - uy * margin);
  if ((result.dx - from.dx) * dir.dx + (result.dy - from.dy) * dir.dy <= 0) {
    return Offset(from.dx + ux * margin, from.dy + uy * margin);
  }
  return result;
}

/// Début de flèche côté entité : place [start] au bord du rect + marge (rayon [to] → [start]), pour que le trait ne rentre pas dans l'entité.
/// [arrowTipMargin] optionnel : marge en px (défaut [kArrowTipMargin]).
Offset snapStartToEntityBoundary(Offset to, Offset start, Map<String, dynamic> entity, {double? entityWidth, double? arrowTipMargin}) {
  final margin = arrowTipMargin ?? kArrowTipMargin;
  final rect = entityRect(entity, entityWidth: entityWidth);
  final dir = Offset(start.dx - to.dx, start.dy - to.dy);
  final len = math.sqrt(dir.dx * dir.dx + dir.dy * dir.dy);
  if (len < 1e-6) return start;
  final hit = rayRectIntersection(to, dir, rect);
  if (hit == null) return start;
  return Offset(
    hit.point.dx + hit.normal.dx * margin,
    hit.point.dy + hit.normal.dy * margin,
  );
}

/// Début de flèche côté association : place [start] au bord du cercle + marge (rayon [to] → [start]).
/// [arrowTipMargin] optionnel : marge en px (défaut [kArrowTipMargin]).
Offset snapStartToAssociationBoundary(Offset to, Offset start, Map<String, dynamic> assoc, {double? arrowTipMargin}) {
  final margin = arrowTipMargin ?? kArrowTipMargin;
  final circle = associationCircle(assoc);
  final dir = Offset(start.dx - to.dx, start.dy - to.dy);
  final hit = rayCircleIntersection(to, dir, circle.center, circle.radius);
  if (hit == null) return start;
  return Offset(
    hit.point.dx + hit.normal.dx * margin,
    hit.point.dy + hit.normal.dy * margin,
  );
}
