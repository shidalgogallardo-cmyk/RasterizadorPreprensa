#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PREPRESS PDF OPTIMIZER v4.0
Aplicación profesional para rasterizar PDFs de periódicos
- Rasterización con opciones 200/250/300 DPI
- Convierte todo a imagen (texto incluido)
- Respeta dimensiones originales
- Detecta elementos RGB y alerta
"""

import sys
import os
import time
import subprocess
import tempfile
from pathlib import Path
from datetime import timedelta
from typing import Optional, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QGroupBox, QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from pypdf import PdfReader
from PIL import Image


class PDFAnalyzer:
    """Analizador profesional de PDFs para preprensa"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.reader = PdfReader(pdf_path)
        
    def get_pdf_info(self) -> Dict:
        """Extrae información técnica del PDF"""
        info = {
            'num_pages': len(self.reader.pages),
            'color_spaces': set(),
            'has_rgb': False,
            'has_cmyk': False,
            'has_icc_profile': False,
            'icc_profile_name': 'Unknown',
            'page_width': None,
            'page_height': None,
            'page_width_cm': None,
            'page_height_cm': None,
        }
        
        if self.reader.pages:
            page = self.reader.pages[0]
            media_box = page.mediabox
            info['media_box'] = media_box
            info['page_width'] = float(media_box[2] - media_box[0])
            info['page_height'] = float(media_box[3] - media_box[1])
            # Convertir puntos a centímetros (1 punto = 0.0352778 cm)
            info['page_width_cm'] = round(info['page_width'] * 0.0352778, 2)
            info['page_height_cm'] = round(info['page_height'] * 0.0352778, 2)
            
            if "/Resources" in page:
                resources = page["/Resources"]
                
                if "/ColorSpace" in resources:
                    color_spaces = resources["/ColorSpace"]
                    if isinstance(color_spaces, dict):
                        for name, cs in color_spaces.items():
                            if isinstance(cs, list) and len(cs) > 0:
                                cs_name = str(cs[0]).lower()
                                info['color_spaces'].add(cs_name)
                                if 'rgb' in cs_name:
                                    info['has_rgb'] = True
                                if 'cmyk' in cs_name:
                                    info['has_cmyk'] = True
                
                if "/XObject" in resources:
                    xobjects = resources["/XObject"]
                    if isinstance(xobjects, dict):
                        for name, obj in xobjects.items():
                            if isinstance(obj, dict) and "/ColorSpace" in obj:
                                cs = str(obj["/ColorSpace"]).lower()
                                info['color_spaces'].add(cs)
                                if 'rgb' in cs:
                                    info['has_rgb'] = True
                                if 'cmyk' in cs:
                                    info['has_cmyk'] = True
            
            if "/OutputIntents" in self.reader.trailer:
                intents = self.reader.trailer["/OutputIntents"]
                if isinstance(intents, list) and len(intents) > 0:
                    intent = intents[0]
                    if "/DestOutputProfile" in intent:
                        info['has_icc_profile'] = True
        
        info['color_spaces'] = list(info['color_spaces']) if info['color_spaces'] else ['Unknown']
        return info


class RasterizationWorker(QThread):
    """Worker thread para rasterización sin bloquear GUI"""
    
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, pdf_path: str, output_path: str, dpi: int):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.dpi = dpi
        self.start_time = None
        self.elapsed_time = 0
        
    def run(self):
        try:
            self.start_time = time.time()
            self.status.emit("Iniciando rasterización...")
            self.progress.emit(10)
            
            self.status.emit(f"Convirtiendo PDF a imagen {self.dpi} DPI...")
            self.progress.emit(30)
            
            # Convertir PDF a PNG
            temp_png = self._pdf_to_png()
            self.progress.emit(60)
            
            self.status.emit("Guardando como PDF...")
            self.progress.emit(80)
            
            # Convertir PNG de vuelta a PDF
            self._png_to_pdf(temp_png)
            
            # Limpiar temporales
            try:
                os.remove(temp_png)
            except:
                pass
            
            self.elapsed_time = time.time() - self.start_time
            self.status.emit("Rasterización completada")
            self.progress.emit(100)
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
    
    def _pdf_to_png(self) -> str:
        """Convierte PDF a PNG de alta resolución"""
        temp_png = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
        
        try:
            cmd = [
                '/opt/homebrew/bin/gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER',
                '-sDEVICE=pngalpha',
                f'-r{self.dpi}',
                '-dDownScaleFactor=1',
                f'-sOutputFile={temp_png}',
                self.pdf_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise Exception(f"Ghostscript error: {result.stderr}")
            
            if not os.path.exists(temp_png):
                raise Exception("No se creó la imagen PNG")
            
            return temp_png
            
        except Exception as e:
            if os.path.exists(temp_png):
                os.remove(temp_png)
            raise Exception(f"Error en rasterización: {str(e)}")
    
    def _png_to_pdf(self, png_path: str):
        """Convierte PNG a PDF preservando resolución"""
        try:
            img = Image.open(png_path)
            
            # Convertir RGBA a RGB si es necesario
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar como PDF con resolución preservada
            dpi_info = (self.dpi, self.dpi)
            img.save(self.output_path, 'PDF', quality=95, dpi=dpi_info)
            
        except Exception as e:
            raise Exception(f"Error guardando PDF: {str(e)}")


class PrePressApp(QMainWindow):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrePress PDF Optimizer v4.0")
        self.setGeometry(100, 100, 1100, 850)
        
        self.current_pdf = None
        self.pdf_info = None
        self.worker = None
        self.processing = False
        
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Sección: Carga
        load_group = QGroupBox("1. Cargar PDF")
        load_layout = QHBoxLayout()
        self.load_btn = QPushButton("Seleccionar PDF")
        self.load_btn.clicked.connect(self.load_pdf)
        self.load_btn.setMinimumHeight(40)
        self.file_label = QLabel("No hay archivo cargado")
        load_layout.addWidget(self.load_btn)
        load_layout.addWidget(self.file_label, 1)
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Sección: Información
        info_group = QGroupBox("2. Información Detectada")
        info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(140)
        self.info_text.setStyleSheet("""
            background-color: #f5f5f5;
            border: 1px solid #ccc;
            padding: 10px;
            color: #1a1a1a;
            font-family: Menlo, Monaco, monospace;
            font-size: 11px;
        """)
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Sección: Advertencias
        self.warning_group = QGroupBox("Alertas")
        warning_layout = QVBoxLayout()
        self.warning_text = QTextEdit()
        self.warning_text.setReadOnly(True)
        self.warning_text.setMaximumHeight(80)
        self.warning_text.setStyleSheet("""
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            color: #856404;
            font-weight: bold;
        """)
        warning_layout.addWidget(self.warning_text)
        self.warning_group.setLayout(warning_layout)
        self.warning_group.setVisible(False)
        layout.addWidget(self.warning_group)
        
        # Sección: Configuración
        config_group = QGroupBox("3. Configuración")
        config_layout = QFormLayout()
        
        dpi_layout = QHBoxLayout()
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItem("200 DPI")
        self.dpi_combo.addItem("250 DPI")
        self.dpi_combo.addItem("300 DPI", 2)
        self.dpi_combo.setCurrentIndex(2)  # 300 DPI por defecto
        self.dpi_combo.setStyleSheet("color: #1a1a1a;")
        dpi_layout.addWidget(self.dpi_combo)
        dpi_layout.addStretch()
        
        config_layout.addRow("Resolución:", dpi_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Sección: Procesamiento
        progress_group = QGroupBox("4. Procesamiento")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        progress_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Esperando archivo...")
        self.status_label.setStyleSheet("color: #1a1a1a; font-weight: bold;")
        progress_layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("Iniciar Rasterización")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.cancel_btn)
        progress_layout.addLayout(button_layout)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Sección: Resultado
        result_group = QGroupBox("5. Resultado")
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(70)
        self.result_text.setStyleSheet("""
            background-color: #e8f5e9;
            border: 1px solid #4CAF50;
            color: #1a1a1a;
            font-family: Menlo, Monaco, monospace;
            font-size: 11px;
        """)
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        main_widget.setLayout(layout)
    
    def apply_styles(self):
        self.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #e0e0e0; border-radius: 5px; margin-top: 10px; padding-top: 15px; }")
    
    def get_selected_dpi(self) -> int:
        """Obtiene el DPI seleccionado del combo"""
        text = self.dpi_combo.currentText()
        return int(text.split()[0])
    
    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF Files (*.pdf)")
        
        if not file_path:
            return
        
        try:
            self.current_pdf = file_path
            self.file_label.setText(f"OK: {Path(file_path).name}")
            self.status_label.setText("Analizando PDF...")
            
            analyzer = PDFAnalyzer(file_path)
            self.pdf_info = analyzer.get_pdf_info()
            self._display_pdf_info()
            self.process_btn.setEnabled(True)
            self.status_label.setText("PDF cargado")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar: {str(e)}")
    
    def _display_pdf_info(self):
        if not self.pdf_info:
            return
        
        info = self.pdf_info
        info_text = f"""INFORMACION DEL PDF
==================================================

ESTRUCTURA:
   Paginas: {info['num_pages']}
   Medida: {info['page_width_cm']} x {info['page_height_cm']} cm

COLOR:
   Color Spaces: {', '.join(info['color_spaces'])}
   Contiene RGB: {'Si' if info['has_rgb'] else 'No'}
   Contiene CMYK: {'Si' if info['has_cmyk'] else 'No'}

ICC PROFILE:
   Incrustado: {'Si' if info['has_icc_profile'] else 'No'}
   Nombre: {info['icc_profile_name']}"""
        
        self.info_text.setText(info_text)
        
        warnings = []
        if info['has_rgb']:
            warnings.append("ALERTA RGB\nEste PDF tiene RGB (incompatible con CMYK preprensa)")
        
        if not info['has_icc_profile']:
            warnings.append("SIN ICC\nNo tiene perfil de color incrustado")
        
        if warnings:
            self.warning_group.setVisible(True)
            self.warning_text.setText('\n\n'.join(warnings))
        else:
            self.warning_group.setVisible(False)
    
    def start_processing(self):
        if not self.current_pdf:
            QMessageBox.warning(self, "Advertencia", "Carga un PDF primero")
            return
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF rasterizado",
            os.path.splitext(self.current_pdf)[0] + "_rasterized.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not output_path:
            return
        
        self.processing = True
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.load_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_text.clear()
        
        dpi = self.get_selected_dpi()
        
        self.worker = RasterizationWorker(self.current_pdf, output_path, dpi)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
        
        self.worker.start()
    
    def cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        self.processing = False
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.load_btn.setEnabled(True)
        self.status_label.setText("Cancelado")
        self.progress_bar.setValue(0)
    
    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str):
        self.status_label.setText(message)
    
    def processing_finished(self, output_path: str):
        self.processing = False
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.load_btn.setEnabled(True)
        
        elapsed = self.worker.elapsed_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        dpi = self.get_selected_dpi()
        
        result_msg = f"""COMPLETADO

Archivo: {Path(output_path).name}
Tamaño: {file_size:.2f} MB
Tiempo: {elapsed_str}

El PDF ha sido rasterizado a {dpi} DPI.
Toda la página está convertida a imagen."""
        
        self.result_text.setText(result_msg)
        
        reply = QMessageBox.question(self, "Completado",
            f"PDF guardado en:\n{output_path}\n\nAbrir carpeta?",
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            subprocess.Popen(['open', os.path.dirname(output_path)])
    
    def processing_error(self, error_msg: str):
        self.processing = False
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.load_btn.setEnabled(True)
        
        error_text = f"""ERROR

{error_msg}

Verifica:
1. Ghostscript instalado: brew install ghostscript
2. Espacio en disco disponible"""
        
        self.result_text.setText(error_text)
        self.result_text.setStyleSheet("""
            background-color: #ffebee;
            border: 1px solid #f44336;
            color: #c62828;
        """)


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet("""
        QLabel {
            color: palette(text);
        }
        QTextEdit {
            background-color: palette(base);
            color: palette(text);
            selection-background-color: #0078D7;
            selection-color: #FFFFFF;
        }
        QComboBox {
            background-color: palette(base);
            color: palette(text);
            border: 1px solid palette(mid);
            border-radius: 4px;
            padding: 3px;
        }
        QComboBox QAbstractItemView {
            background-color: palette(base);
            color: palette(text);
            selection-background-color: #0078D7;
            selection-color: #FFFFFF;
        }
    """)
        # Validación de Ghostscript
        gs_paths = ['gs', '/opt/homebrew/bin/gs', '/usr/local/bin/gs']
        gs_found = False
        for path in gs_paths:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True, timeout=5)
                gs_found = True
                break
            except:
                continue
                
        if not gs_found:
            QMessageBox.critical(None, "Error", 
                "Ghostscript no instalado o no encontrado.\n\nVerifica que esté instalado con Homebrew.")
            sys.exit(1)
        
        window = PrePressApp()
        window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        import traceback
        print("ERROR CRITICO AL INICIAR:")
        traceback.print_exc()
        input("Presiona Enter para salir...")

if __name__ == '__main__':
    main()
