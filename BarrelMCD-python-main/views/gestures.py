from PyQt5.QtCore import QObject, pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QKeySequence, QShortcut, QGestureRecognizer, QGestureEvent
from PyQt5.QtWidgets import QWidget

class GestureManager(QObject):
    """Gestionnaire de gestes tactiles et raccourcis clavier"""
    
    # Signaux pour les gestes
    pinch_zoom = pyqtSignal(float)  # Facteur de zoom
    pan_started = pyqtSignal()
    pan_moved = pyqtSignal(QPointF)  # Delta de mouvement
    pan_ended = pyqtSignal()
    double_tap = pyqtSignal(QPointF)  # Position du double tap
    long_press = pyqtSignal(QPointF)  # Position de l'appui long
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent = parent
        self.setup_shortcuts()
        self.setup_gestures()
        
    def setup_shortcuts(self):
        """Configure les raccourcis clavier"""
        # Zoom
        QShortcut(QKeySequence.ZoomIn, self.parent).activated.connect(
            lambda: self.parent.zoom_in()
        )
        QShortcut(QKeySequence.ZoomOut, self.parent).activated.connect(
            lambda: self.parent.zoom_out()
        )
        
        # Navigation
        QShortcut(QKeySequence.MoveToNextChar, self.parent).activated.connect(
            lambda: self.parent.pan_right()
        )
        QShortcut(QKeySequence.MoveToPreviousChar, self.parent).activated.connect(
            lambda: self.parent.pan_left()
        )
        QShortcut(QKeySequence.MoveToNextLine, self.parent).activated.connect(
            lambda: self.parent.pan_down()
        )
        QShortcut(QKeySequence.MoveToPreviousLine, self.parent).activated.connect(
            lambda: self.parent.pan_up()
        )
        
        # Actions
        QShortcut(QKeySequence.New, self.parent).activated.connect(
            lambda: self.parent.new_diagram()
        )
        QShortcut(QKeySequence.Open, self.parent).activated.connect(
            lambda: self.parent.open_diagram()
        )
        QShortcut(QKeySequence.Save, self.parent).activated.connect(
            lambda: self.parent.save_diagram()
        )
        QShortcut(QKeySequence.SaveAs, self.parent).activated.connect(
            lambda: self.parent.save_diagram_as()
        )
        
        # Édition
        QShortcut(QKeySequence.Undo, self.parent).activated.connect(
            lambda: self.parent.undo()
        )
        QShortcut(QKeySequence.Redo, self.parent).activated.connect(
            lambda: self.parent.redo()
        )
        QShortcut(QKeySequence.Delete, self.parent).activated.connect(
            lambda: self.parent.delete_selected()
        )
        
    def setup_gestures(self):
        """Configure les gestes tactiles"""
        # Activation des gestes
        self.parent.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)
        
        # Pinch pour le zoom
        pinch = QGestureRecognizer()
        pinch.setGestureType(Qt.GestureType.PinchGesture)
        self.parent.grabGesture(pinch)
        
        # Pan pour le déplacement
        pan = QGestureRecognizer()
        pan.setGestureType(Qt.GestureType.PanGesture)
        self.parent.grabGesture(pan)
        
        # Double tap pour le zoom
        double_tap = QGestureRecognizer()
        double_tap.setGestureType(Qt.GestureType.TapGesture)
        double_tap.setGestureProperty("tapCount", 2)
        self.parent.grabGesture(double_tap)
        
        # Appui long pour le menu contextuel
        long_press = QGestureRecognizer()
        long_press.setGestureType(Qt.GestureType.TapAndHoldGesture)
        self.parent.grabGesture(long_press)
        
    def eventFilter(self, obj, event):
        """Filtre les événements pour gérer les gestes"""
        if isinstance(event, QGestureEvent):
            for gesture in event.gestures():
                if gesture.gestureType() == Qt.GestureType.PinchGesture:
                    self.pinch_zoom.emit(gesture.totalScaleFactor())
                elif gesture.gestureType() == Qt.GestureType.PanGesture:
                    if gesture.state() == Qt.GestureState.GestureStarted:
                        self.pan_started.emit()
                    elif gesture.state() == Qt.GestureState.GestureUpdated:
                        self.pan_moved.emit(gesture.delta())
                    elif gesture.state() == Qt.GestureState.GestureFinished:
                        self.pan_ended.emit()
                elif gesture.gestureType() == Qt.GestureType.TapGesture:
                    if gesture.tapCount() == 2:
                        self.double_tap.emit(gesture.position())
                elif gesture.gestureType() == Qt.GestureType.TapAndHoldGesture:
                    self.long_press.emit(gesture.position())
        return super().eventFilter(obj, event) 