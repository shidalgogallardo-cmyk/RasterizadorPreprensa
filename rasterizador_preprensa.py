import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QFrame, QComboBox
)
from PyQt6.QtCore import Qt
import fitz  # PyMuPDF
from PIL import Image, ImageChops


class AppRasterizador(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ""
        self.output_dir = ""
        self.icc_path = ""
        self.initUI()
        self.auto_detect_wan_ifra_icc()

    def initUI(self):
        self.setWindowTitle("Rasterizador Preprensa WAN-IFRA")
        self.setFixedSize(540, 480)

        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                color: #1F2937;
            }
            QFrame.card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
            QPushButton#primaryBtn {
                background-color: #059669;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background-color: #047857;
            }
            QPushButton#primaryBtn:disabled {
                background-color: #D1D5DB;
                color: #9CA3AF;
            }
            QPushButton#secondaryBtn {
                background-color: #E0E7FF;
                color: #3730A3;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid #C7D2FE;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #C7D2FE;
            }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 600;
                color: #1F2937;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Encabezado
        header_layout = QVBoxLayout()
        title = QLabel("Rasterizador Preprensa WAN-IFRA")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        subtitle = QLabel("Polaridad CMYK Corregida • Perfil WAN-IFRA Incrustado")
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Tarjeta 1: Perfil ICC
        card_icc = QFrame()
        card_icc.setProperty("class", "card")
        card_icc_layout = QHBoxLayout(card_icc)
        card_icc_layout.setContentsMargins(12, 10, 12, 10)

        self.label_icc = QLabel("Buscando perfil WAN-IFRA en carpeta local...")
        self.label_icc.setStyleSheet("color: #D97706; font-size: 12px; font-weight: 500;")
        card_icc_layout.addWidget(self.label_icc)
        main_layout.addWidget(card_icc)

        # Tarjeta 2: Selección de Archivo PDF
        card_file = QFrame()
        card_file.setProperty("class", "card")
        card_file_layout = QVBoxLayout(card_file)
        card_file_layout.setContentsMargins(12, 10, 12, 10)

        file_top_layout = QHBoxLayout()
        self.label_pdf = QLabel("Ningún PDF seleccionado")
        self.label_pdf.setStyleSheet("color: #6B7280; font-size: 12px;")
        btn_select_pdf = QPushButton("Buscar PDF")
        btn_select_pdf.setObjectName("secondaryBtn")
        btn_select_pdf.clicked.connect(self.select_pdf)
        file_top_layout.addWidget(self.label_pdf, 1)
        file_top_layout.addWidget(btn_select_pdf)

        self.label_dims = QLabel("Medidas del PDF: --")
        self.label_dims.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 500;")

        card_file_layout.addLayout(file_top_layout)
        card_file_layout.addWidget(self.label_dims)
        main_layout.addWidget(card_file)

        # Tarjeta 3: Configuración de Resolución (DPI)
        card_dpi = QFrame()
        card_dpi.setProperty("class", "card")
        card_dpi_layout = QHBoxLayout(card_dpi)
        card_dpi_layout.setContentsMargins(12, 10, 12, 10)

        label_dpi_title = QLabel("Resolución de salida (DPI):")
        label_dpi_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        
        self.combo_dpi = QComboBox()
        self.combo_dpi.addItems(["300 DPI", "250 DPI", "200 DPI"])

        card_dpi_layout.addWidget(label_dpi_title)
        card_dpi_layout.addStretch()
        card_dpi_layout.addWidget(self.combo_dpi)
        main_layout.addWidget(card_dpi)

        # Tarjeta 4: Carpeta de Destino
        card_dir = QFrame()
        card_dir.setProperty("class", "card")
        card_dir_layout = QHBoxLayout(card_dir)
        card_dir_layout.setContentsMargins(12, 10, 12, 10)

        self.label_dir = QLabel("Carpeta destino: Misma del archivo origen")
        self.label_dir.setStyleSheet("color: #6B7280; font-size: 12px;")
        btn_select_dir = QPushButton("Cambiar Carpeta")
        btn_select_dir.setObjectName("secondaryBtn")
        btn_select_dir.clicked.connect(self.select_output_dir)

        card_dir_layout.addWidget(self.label_dir, 1)
        card_dir_layout.addWidget(btn_select_dir)
        main_layout.addWidget(card_dir)

        # Botón de Acción Principal
        self.btn_process = QPushButton("Comenzar Rasterización CMYK")
        self.btn_process.setObjectName("primaryBtn")
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_file)
        main_layout.addWidget(self.btn_process)

        # Barra de Estado
        self.status = QLabel("Estado: Esperando configuración...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #4B5563; font-size: 12px; font-weight: 500;")
        main_layout.addWidget(self.status)

        self.setLayout(main_layout)

    def auto_detect_wan_ifra_icc(self):
        current_dir = os.getcwd()
        icc_files = [f for f in os.listdir(current_dir) if f.lower().endswith(('.icc', '.icm'))]
        wan_matches = [f for f in icc_files if any(k in f.lower() for k in ["wan", "ifra", "newspaper", "isoleat", "isonewspaper"])]
        
        if wan_matches:
            self.icc_path = os.path.join(current_dir, wan_matches[0])
        elif icc_files:
            self.icc_path = os.path.join(current_dir, icc_files[0])
        else:
            self.icc_path = ""

        if self.icc_path:
            filename = os.path.basename(self.icc_path)
            self.label_icc.setText(f"🎨 Perfil Autodetectado: {filename}")
            self.label_icc.setStyleSheet("color: #059669; font-weight: bold; font-size: 12px;")
        else:
            self.label_icc.setText("❌ NO se encontró el perfil ICC WAN-IFRA en la carpeta local")
            self.label_icc.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 12px;")

        self.check_ready()

    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
        if file_path:
            self.pdf_path = file_path
            filename = os.path.basename(file_path)
            self.label_pdf.setText(f"📄 {filename}")
            self.label_pdf.setStyleSheet("color: #111827; font-weight: 600; font-size: 12px;")
            
            try:
                doc = fitz.open(file_path)
                total_pages = len(doc)
                page = doc.load_page(0)
                rect = page.rect
                
                w_mm = round(rect.width * 25.4 / 72.0, 1)
                h_mm = round(rect.height * 25.4 / 72.0, 1)
                
                self.label_dims.setText(f"📏 Dimensión: {w_mm} × {h_mm} mm  •  Total: {total_pages} pág(s)")
                self.label_dims.setStyleSheet("color: #2563EB; font-weight: 600; font-size: 11px;")
                doc.close()
            except Exception:
                self.label_dims.setText("📏 No se pudieron leer las dimensiones del PDF")

            if not self.output_dir:
                self.output_dir = os.path.dirname(file_path)
                self.label_dir.setText(f"📁 {os.path.basename(self.output_dir)}/")
                self.label_dir.setStyleSheet("color: #374151; font-size: 12px;")

            self.check_ready()

    def select_output_dir(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if selected_dir:
            self.output_dir = selected_dir
            self.label_dir.setText(f"📁 {os.path.basename(selected_dir)}/")
            self.label_dir.setStyleSheet("color: #374151; font-size: 12px;")

    def check_ready(self):
        if self.pdf_path and self.icc_path:
            self.btn_process.setEnabled(True)
            self.status.setText("Estado: Listo para procesar.")
            self.status.setStyleSheet("color: #059669; font-weight: 500;")
        else:
            self.btn_process.setEnabled(False)
            if not self.icc_path:
                self.status.setText("Estado: Coloque el perfil WAN-IFRA en la carpeta del script.")
                self.status.setStyleSheet("color: #DC2626; font-weight: 500;")

    def process_file(self):
        if not self.pdf_path or not self.output_dir or not self.icc_path:
            return

        target_dpi = int(self.combo_dpi.currentText().split()[0])

        self.btn_process.setEnabled(False)
        self.status.setText(f"Procesando a {target_dpi} DPI en CMYK nativo...")
        self.status.setStyleSheet("color: #2563EB; font-weight: bold;")
        QApplication.processEvents()

        try:
            doc_in = fitz.open(self.pdf_path)
            total_pages = len(doc_in)
            
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            output_pdf_path = os.path.join(self.output_dir, f"{base_name}_rasterizado.pdf")
            
            with open(self.icc_path, "rb") as f:
                icc_bytes = f.read()

            pil_images = []

            for page_num in range(total_pages):
                self.status.setText(f"Página {page_num + 1} de {total_pages} (@ {target_dpi} DPI CMYK)...")
                QApplication.processEvents()

                page = doc_in.load_page(page_num)

                # 1. Extraer matriz CMYK nativa de 4 canales
                pix = page.get_pixmap(dpi=target_dpi, colorspace=fitz.csCMYK, alpha=False)

                # 2. Cargar en Pillow
                img = Image.frombytes("CMYK", (pix.width, pix.height), pix.samples)

                # 3. Invertir la polaridad de tintas para corregir el efecto negativo en PDF/Adobe
                img_corrected = ImageChops.invert(img)

                pil_images.append(img_corrected)

            self.status.setText("Guardando PDF CMYK estandarizado...")
            QApplication.processEvents()

            # 4. Guardar PDF final con perfil WAN-IFRA
            if pil_images:
                pil_images[0].save(
                    output_pdf_path,
                    "PDF",
                    resolution=target_dpi,
                    save_all=True,
                    append_images=pil_images[1:],
                    icc_profile=icc_bytes
                )

            doc_in.close()

            icc_filename = os.path.basename(self.icc_path)
            QMessageBox.information(
                self, 
                "Éxito Preprensa", 
                f"¡PDF CMYK procesado correctamente!\n\n"
                f"• Perfil incrustado: {icc_filename}\n"
                f"• Resolución: {target_dpi} DPI\n"
                f"• Espacio de color: CMYK (4 Canales Positivos)\n"
                f"• Archivo: {os.path.basename(output_pdf_path)}"
            )
            self.status.setText(f"Listo: {os.path.basename(output_pdf_path)}")
            self.status.setStyleSheet("color: #059669; font-weight: bold;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
            self.status.setText("Error durante la conversión.")
            self.status.setStyleSheet("color: #DC2626; font-weight: bold;")
        finally:
            self.btn_process.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = AppRasterizador()
    ventana.show()
    sys.exit(app.exec())