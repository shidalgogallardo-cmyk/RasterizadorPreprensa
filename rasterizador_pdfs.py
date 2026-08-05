import sys
import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QFrame, QComboBox,
    QRadioButton, QButtonGroup, QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import fitz  # PyMuPDF
from PIL import Image
import pikepdf
import img2pdf

MAX_BATCH_PAGES = 32


class AppRasterizador(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_path = ""              # modo individual
        self.batch_paths = []           # modo lote
        self.output_dir = ""
        self.icc_path = ""
        self.mode = "individual"        # "individual" | "lote"
        self.setAcceptDrops(True)
        self.initUI()
        self.auto_detect_wan_ifra_icc()

    def initUI(self):
        self.setWindowTitle("Rasterizador de PDFs")
        self.setMinimumSize(580, 560)
        self.resize(580, 640)

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
            QFrame.dropzone {
                background-color: #FFFFFF;
                border: 2px dashed #C7D2FE;
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
            QPushButton#primaryBtn:hover { background-color: #047857; }
            QPushButton#primaryBtn:disabled { background-color: #D1D5DB; color: #9CA3AF; }
            QPushButton#secondaryBtn {
                background-color: #E0E7FF;
                color: #3730A3;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid #C7D2FE;
            }
            QPushButton#secondaryBtn:hover { background-color: #C7D2FE; }
            QPushButton#clearBtn {
                background-color: #FEE2E2;
                color: #991B1B;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid #FCA5A5;
            }
            QPushButton#clearBtn:hover { background-color: #FCA5A5; }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: 600;
                color: #1F2937;
            }
            QRadioButton {
                font-size: 12px;
                font-weight: 600;
                color: #374151;
            }
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        header_layout = QVBoxLayout()
        title = QLabel("Rasterizador de PDFs")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        subtitle = QLabel("Incrustación Garantizada • DeviceCMYK")
        subtitle.setStyleSheet("font-size: 12px; color: #6B7280;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # Tarjeta ICC
        card_icc = QFrame()
        card_icc.setProperty("class", "card")
        card_icc_layout = QHBoxLayout(card_icc)
        card_icc_layout.setContentsMargins(12, 10, 12, 10)
        self.label_icc = QLabel("Buscando perfil WAN-IFRA en carpeta local...")
        self.label_icc.setStyleSheet("color: #D97706; font-size: 12px; font-weight: 500;")
        card_icc_layout.addWidget(self.label_icc)
        main_layout.addWidget(card_icc)

        # Tarjeta modo (individual / lote)
        card_mode = QFrame()
        card_mode.setProperty("class", "card")
        card_mode_layout = QHBoxLayout(card_mode)
        card_mode_layout.setContentsMargins(12, 10, 12, 10)

        self.radio_individual = QRadioButton("Individual")
        self.radio_lote = QRadioButton(f"Por Lote (máx. {MAX_BATCH_PAGES} páginas)")
        self.radio_individual.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_individual)
        self.mode_group.addButton(self.radio_lote)
        self.radio_individual.toggled.connect(self.on_mode_changed)

        mode_label = QLabel("Modo de rasterización:")
        mode_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        card_mode_layout.addWidget(mode_label)
        card_mode_layout.addStretch()
        card_mode_layout.addWidget(self.radio_individual)
        card_mode_layout.addWidget(self.radio_lote)
        main_layout.addWidget(card_mode)

        # Tarjeta archivo(s) - modo INDIVIDUAL
        self.card_file = QFrame()
        self.card_file.setProperty("class", "dropzone")
        card_file_layout = QVBoxLayout(self.card_file)
        card_file_layout.setContentsMargins(12, 10, 12, 10)

        file_top_layout = QHBoxLayout()
        self.label_pdf = QLabel("Ningún PDF seleccionado  ·  arrastra aquí o usa el botón")
        self.label_pdf.setStyleSheet("color: #6B7280; font-size: 12px;")

        btn_select_pdf = QPushButton("Buscar PDF")
        btn_select_pdf.setObjectName("secondaryBtn")
        btn_select_pdf.clicked.connect(self.select_pdf)

        self.btn_clear_pdf = QPushButton("Limpiar PDF")
        self.btn_clear_pdf.setObjectName("clearBtn")
        self.btn_clear_pdf.setVisible(False)
        self.btn_clear_pdf.clicked.connect(self.clear_pdf)

        file_top_layout.addWidget(self.label_pdf, 1)
        file_top_layout.addWidget(btn_select_pdf)
        file_top_layout.addWidget(self.btn_clear_pdf)

        self.label_dims = QLabel("Medidas del PDF: --")
        self.label_dims.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 500;")

        card_file_layout.addLayout(file_top_layout)
        card_file_layout.addWidget(self.label_dims)
        main_layout.addWidget(self.card_file)

        # Tarjeta archivo(s) - modo LOTE
        self.card_batch = QFrame()
        self.card_batch.setProperty("class", "dropzone")
        card_batch_layout = QVBoxLayout(self.card_batch)
        card_batch_layout.setContentsMargins(12, 10, 12, 10)

        batch_top_layout = QHBoxLayout()
        batch_hint = QLabel("Arrastra varios PDFs aquí o usa el botón")
        batch_hint.setStyleSheet("color: #6B7280; font-size: 12px;")
        btn_add_batch = QPushButton("Agregar PDFs")
        btn_add_batch.setObjectName("secondaryBtn")
        btn_add_batch.clicked.connect(self.add_batch_pdfs)
        btn_clear_batch = QPushButton("Limpiar Lista")
        btn_clear_batch.setObjectName("clearBtn")
        btn_clear_batch.clicked.connect(self.clear_batch)
        batch_top_layout.addWidget(batch_hint, 1)
        batch_top_layout.addWidget(btn_add_batch)
        batch_top_layout.addWidget(btn_clear_batch)

        self.batch_list = QListWidget()
        self.batch_list.setFixedHeight(120)
        self.batch_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.label_batch_total = QLabel(f"Total: 0 páginas de {MAX_BATCH_PAGES} máx.  ·  se entregará como .zip")
        self.label_batch_total.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 500;")

        card_batch_layout.addLayout(batch_top_layout)
        card_batch_layout.addWidget(self.batch_list)
        card_batch_layout.addWidget(self.label_batch_total)
        main_layout.addWidget(self.card_batch)
        self.card_batch.setVisible(False)

        # Tarjeta DPI
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

        # Tarjeta carpeta destino
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

        # Botón principal
        self.btn_process = QPushButton("Comenzar Rasterización CMYK")
        self.btn_process.setObjectName("primaryBtn")
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_file)
        main_layout.addWidget(self.btn_process)

        # Estado
        self.status = QLabel("Estado: Esperando configuración...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color: #4B5563; font-size: 12px; font-weight: 500;")
        main_layout.addWidget(self.status)

        self.setLayout(main_layout)

    # ---------- Drag & Drop ----------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            pdfs = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
            if pdfs:
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        pdfs = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
        if not pdfs:
            return
        if self.mode == "individual":
            self.load_single_pdf(pdfs[0])
        else:
            self.add_files_to_batch(pdfs)

    # ---------- Modo ----------
    def on_mode_changed(self):
        self.mode = "individual" if self.radio_individual.isChecked() else "lote"
        self.card_file.setVisible(self.mode == "individual")
        self.card_batch.setVisible(self.mode == "lote")
        self.check_ready()

    # ---------- ICC ----------
    def auto_detect_wan_ifra_icc(self):
        if getattr(sys, 'frozen', False):
            # PyInstaller (onedir/onefile) expone la carpeta de recursos empaquetados
            # en sys._MEIPASS. Desde PyInstaller 6.x, en modo onedir los archivos
            # añadidos con --add-data quedan en Contents/MacOS/_internal, NO junto
            # al ejecutable — por eso NO se debe usar os.path.dirname(sys.executable).
            current_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))

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

    # ---------- Modo individual ----------
    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
        if file_path:
            self.load_single_pdf(file_path)

    def load_single_pdf(self, file_path):
        self.pdf_path = file_path
        filename = os.path.basename(file_path)
        self.label_pdf.setText(f"📄 {filename}")
        self.label_pdf.setStyleSheet("color: #111827; font-weight: 600; font-size: 12px;")
        self.btn_clear_pdf.setVisible(True)

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

    def clear_pdf(self):
        self.pdf_path = ""
        self.label_pdf.setText("Ningún PDF seleccionado  ·  arrastra aquí o usa el botón")
        self.label_pdf.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.label_dims.setText("Medidas del PDF: --")
        self.label_dims.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 500;")
        self.btn_clear_pdf.setVisible(False)
        self.status.setText("Estado: Esperando selección de PDF...")
        self.status.setStyleSheet("color: #4B5563; font-size: 12px; font-weight: 500;")
        self.check_ready()

    # ---------- Modo lote ----------
    def add_batch_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar PDFs", "", "Archivos PDF (*.pdf)")
        if files:
            self.add_files_to_batch(files)

    def add_files_to_batch(self, files):
        for f in files:
            if f not in self.batch_paths:
                self.batch_paths.append(f)

        if not self.output_dir and self.batch_paths:
            self.output_dir = os.path.dirname(self.batch_paths[0])
            self.label_dir.setText(f"📁 {os.path.basename(self.output_dir)}/")
            self.label_dir.setStyleSheet("color: #374151; font-size: 12px;")

        self.refresh_batch_list()

    def refresh_batch_list(self):
        self.batch_list.clear()
        total_pages = 0
        for f in self.batch_paths:
            n = 0
            dims_text = ""
            try:
                doc = fitz.open(f)
                n = len(doc)
                rect = doc.load_page(0).rect
                w_mm = round(rect.width * 25.4 / 72.0, 1)
                h_mm = round(rect.height * 25.4 / 72.0, 1)
                dims_text = f"{w_mm} × {h_mm} mm"
                doc.close()
            except Exception:
                dims_text = "medidas no disponibles"
            total_pages += n

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 4, 6, 4)

            # Mismo estilo que self.label_pdf (nombre del PDF en modo individual)
            label_name = QLabel(f"📄 {os.path.basename(f)}  ({n} pág.)")
            label_name.setStyleSheet("color: #111827; font-weight: 600; font-size: 12px;")

            # Mismo estilo que self.label_dims (dimensión en modo individual)
            label_dim = QLabel(f"📏 {dims_text}")
            label_dim.setStyleSheet("color: #2563EB; font-weight: 600; font-size: 11px;")

            row_layout.addWidget(label_name, 1)
            row_layout.addWidget(label_dim)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.batch_list.addItem(item)
            self.batch_list.setItemWidget(item, row)

        color = "#DC2626" if total_pages > MAX_BATCH_PAGES else "#4B5563"
        self.label_batch_total.setText(f"Total: {total_pages} páginas de {MAX_BATCH_PAGES} máx.  ·  se entregará como .zip")
        self.label_batch_total.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600;")
        self.check_ready()

    def clear_batch(self):
        self.batch_paths = []
        self.refresh_batch_list()
        self.status.setText("Estado: Esperando selección de PDFs...")
        self.status.setStyleSheet("color: #4B5563; font-size: 12px; font-weight: 500;")

    def get_batch_total_pages(self):
        total = 0
        for f in self.batch_paths:
            try:
                doc = fitz.open(f)
                total += len(doc)
                doc.close()
            except Exception:
                pass
        return total

    # ---------- Carpeta destino ----------
    def select_output_dir(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
        if selected_dir:
            self.output_dir = selected_dir
            self.label_dir.setText(f"📁 {os.path.basename(selected_dir)}/")
            self.label_dir.setStyleSheet("color: #374151; font-size: 12px;")

    # ---------- Estado general ----------
    def check_ready(self):
        has_icc = bool(self.icc_path)
        if self.mode == "individual":
            has_files = bool(self.pdf_path)
            over_limit = False
        else:
            has_files = bool(self.batch_paths)
            over_limit = self.get_batch_total_pages() > MAX_BATCH_PAGES if has_files else False

        if has_icc and has_files and not over_limit:
            self.btn_process.setEnabled(True)
            self.status.setText("Estado: Listo para procesar.")
            self.status.setStyleSheet("color: #059669; font-weight: 500;")
        else:
            self.btn_process.setEnabled(False)
            if not has_icc:
                self.status.setText("Estado: Coloque el perfil WAN-IFRA en la carpeta del script.")
                self.status.setStyleSheet("color: #DC2626; font-weight: 500;")
            elif over_limit:
                self.status.setText(f"Estado: El lote supera el máximo de {MAX_BATCH_PAGES} páginas.")
                self.status.setStyleSheet("color: #DC2626; font-weight: 500;")

    # ---------- Rasterización de un solo PDF (reutilizada por ambos modos) ----------
    def rasterize_single_pdf(self, pdf_path, icc_bytes, target_dpi, progress_prefix="",
                              output_dir_override=None, output_filename=None):
        temp_tiff_paths = []
        try:
            doc_in = fitz.open(pdf_path)
            total_pages = len(doc_in)
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]

            target_dir = output_dir_override if output_dir_override else self.output_dir
            final_name = output_filename if output_filename else f"{base_name}_rasterizado.pdf"
            output_pdf_path = os.path.join(target_dir, final_name)

            for page_num in range(total_pages):
                self.status.setText(f"{progress_prefix}Rasterizando página {page_num + 1} de {total_pages}...")
                QApplication.processEvents()

                page_in = doc_in.load_page(page_num)
                pix = page_in.get_pixmap(dpi=target_dpi, colorspace=fitz.csCMYK, alpha=False)
                img_cmyk = Image.frombytes("CMYK", [pix.width, pix.height], pix.samples)

                temp_tiff = os.path.join(target_dir, f"_temp_{base_name}_p{page_num}.tif")
                img_cmyk.save(
                    temp_tiff, format="TIFF", dpi=(target_dpi, target_dpi),
                    icc_profile=icc_bytes, compression="tiff_deflate"
                )
                temp_tiff_paths.append(temp_tiff)

            doc_in.close()

            self.status.setText(f"{progress_prefix}Empaquetando PDF con perfil WAN-IFRA...")
            QApplication.processEvents()

            layout_fun = img2pdf.get_fixed_dpi_layout_fun((target_dpi, target_dpi))
            pdf_bytes = img2pdf.convert(temp_tiff_paths, layout_fun=layout_fun)
            with open(output_pdf_path, "wb") as f:
                f.write(pdf_bytes)

            with pikepdf.open(output_pdf_path, allow_overwriting_input=True) as pdf_out:
                icc_stream = pdf_out.make_stream(icc_bytes)
                icc_stream.N = 4
                icc_stream.Alternate = pikepdf.Name.DeviceCMYK
                output_intent = pikepdf.Dictionary(
                    Type=pikepdf.Name.OutputIntent,
                    S=pikepdf.Name.GTS_PDFX,
                    OutputConditionIdentifier=pikepdf.String(os.path.basename(self.icc_path)),
                    RegistryName=pikepdf.String("http://www.color.org"),
                    DestOutputProfile=icc_stream
                )
                pdf_out.Root.OutputIntents = pdf_out.make_indirect([output_intent])
                pdf_out.save(output_pdf_path)

            return output_pdf_path

        finally:
            for t in temp_tiff_paths:
                if os.path.exists(t):
                    os.remove(t)

    # ---------- Procesamiento principal ----------
    def process_file(self):
        if not self.icc_path or not self.output_dir:
            return

        target_dpi = int(self.combo_dpi.currentText().split()[0])
        self.btn_process.setEnabled(False)
        QApplication.processEvents()

        with open(self.icc_path, "rb") as f:
            icc_bytes = f.read()

        try:
            if self.mode == "individual":
                if not self.pdf_path:
                    return
                out = self.rasterize_single_pdf(self.pdf_path, icc_bytes, target_dpi)
                QMessageBox.information(
                    self, "Éxito",
                    f"¡PDF CMYK procesado correctamente!\n\n"
                    f"• Perfil incrustado: {os.path.basename(self.icc_path)}\n"
                    f"• Resolución: {target_dpi} DPI\n"
                    f"• Espacio de color: DeviceCMYK (ICCBased) + OutputIntent\n"
                    f"• Archivo: {os.path.basename(out)}"
                )
                self.status.setText(f"Listo: {os.path.basename(out)}")
                self.status.setStyleSheet("color: #059669; font-weight: bold;")

            else:
                total_files = len(self.batch_paths)
                work_dir = tempfile.mkdtemp(prefix="rasterizador_lote_")
                temp_output_paths = []

                try:
                    for idx, pdf_path in enumerate(self.batch_paths, start=1):
                        prefix = f"[{idx}/{total_files}] "
                        original_name = os.path.basename(pdf_path)  # sin sufijo "_rasterizado"
                        out = self.rasterize_single_pdf(
                            pdf_path, icc_bytes, target_dpi, progress_prefix=prefix,
                            output_dir_override=work_dir, output_filename=original_name
                        )
                        temp_output_paths.append(out)

                    self.status.setText("Empaquetando lote en ZIP...")
                    QApplication.processEvents()

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_path = os.path.join(self.output_dir, f"Lote_Rasterizado_{timestamp}.zip")

                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        for p in temp_output_paths:
                            zf.write(p, arcname=os.path.basename(p))

                finally:
                    shutil.rmtree(work_dir, ignore_errors=True)

                QMessageBox.information(
                    self, "Éxito - Lote",
                    f"¡Lote de {total_files} PDF(s) procesado correctamente!\n\n"
                    f"• Perfil incrustado: {os.path.basename(self.icc_path)}\n"
                    f"• Resolución: {target_dpi} DPI\n"
                    f"• Cada PDF conserva su nombre original dentro del ZIP\n"
                    f"• Archivo: {os.path.basename(zip_path)}"
                )
                self.status.setText(f"Listo: {os.path.basename(zip_path)}")
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
