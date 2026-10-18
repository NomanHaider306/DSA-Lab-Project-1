"""
Scraper Tab: Automated multi-source scraper and interactive URL-based scraper (SSRF-protected).
Runs scraping tasks on a background QThread worker with start/pause/resume/stop controls,
deduplication, live progress, and one-click URL extraction.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QGroupBox, QSpinBox, QPlainTextEdit,
    QGridLayout, QFrame, QMessageBox, QScrollArea, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional
from scraper.worker import ScraperWorker
from scraper.url_scraper import URLScraper
from models.game import Game


class ScraperTab(QWidget):
    data_updated = pyqtSignal()  # Signal to trigger dashboard and library refresh

    PRESET_URLS = [
        ("Cyberpunk 2077", "https://store.steampowered.com/app/1091500/Cyberpunk_2077/"),
        ("Dota 2", "https://store.steampowered.com/app/570/Dota_2/"),
        ("Counter-Strike 2", "https://store.steampowered.com/app/730/CounterStrike_2/"),
        ("Hollow Knight", "https://store.steampowered.com/app/367520/Hollow_Knight/"),
        ("Overwatch 2", "https://www.freetogame.com/overwatch-2"),
        ("Genshin Impact", "https://www.freetogame.com/genshin-impact"),
    ]

    def __init__(self, data_service, parent=None):
        super().__init__(parent)
        self.data_service = data_service
        self.worker: Optional[ScraperWorker] = None
        self.extracted_url_game: Optional[Game] = None

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # -------------------------------------------------------------
        # Section 1: Interactive URL-Based Game Scraper (Primary)
        # -------------------------------------------------------------
        url_group = QGroupBox("Interactive URL Game Scraper (Live Scraping & Extraction)")
        url_layout = QVBoxLayout(url_group)
        url_layout.setContentsMargins(10, 10, 10, 10)
        url_layout.setSpacing(8)

        # Quick preset chips
        preset_box = QHBoxLayout()
        preset_box.setSpacing(4)
        lbl_presets = QLabel("Quick Presets:")
        lbl_presets.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase;")
        preset_box.addWidget(lbl_presets)

        for label, url in self.PRESET_URLS:
            btn_chip = QPushButton(label)
            btn_chip.setObjectName("secondaryBtn")
            btn_chip.setStyleSheet("font-size: 10px; padding: 2px 7px; min-height: 14px;")
            btn_chip.clicked.connect(lambda checked, u=url: self._fill_and_scrape(u))
            preset_box.addWidget(btn_chip)
        preset_box.addStretch()
        url_layout.addLayout(preset_box)

        # Input Row
        url_input_row = QHBoxLayout()
        url_input_row.setSpacing(6)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste any video game URL (Steam store, FreeToGame, CheapShark, etc.)...")
        self.url_input.returnPressed.connect(self._scrape_and_save_url)
        url_input_row.addWidget(self.url_input, stretch=3)

        self.btn_scrape_save = QPushButton("Scrape & Save to DB")
        self.btn_scrape_save.setObjectName("successBtn")
        self.btn_scrape_save.setToolTip("Fetch URL live, parse metadata with BeautifulSoup, and insert directly into database.")
        self.btn_scrape_save.clicked.connect(self._scrape_and_save_url)
        url_input_row.addWidget(self.btn_scrape_save)

        self.btn_preview_only = QPushButton("Preview Only")
        self.btn_preview_only.setObjectName("secondaryBtn")
        self.btn_preview_only.clicked.connect(self._preview_url)
        url_input_row.addWidget(self.btn_preview_only)

        url_layout.addLayout(url_input_row)

        self.lbl_url_status = QLabel("Enter a supported game page URL above or click a quick preset to scrape.")
        self.lbl_url_status.setStyleSheet("color: #64748b; font-size: 11px;")
        url_layout.addWidget(self.lbl_url_status)

        # Preview Frame for Extracted URL Record
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px;")
        preview_layout = QHBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(6, 4, 6, 4)

        self.lbl_preview_info = QLabel("No record extracted yet.")
        self.lbl_preview_info.setStyleSheet("color: #475569; font-size: 11px;")
        preview_layout.addWidget(self.lbl_preview_info, stretch=3)

        self.btn_save_url_game = QPushButton("Save to Database")
        self.btn_save_url_game.setObjectName("successBtn")
        self.btn_save_url_game.setEnabled(False)
        self.btn_save_url_game.clicked.connect(self._save_extracted_game)
        preview_layout.addWidget(self.btn_save_url_game)

        url_layout.addWidget(self.preview_frame)
        main_layout.addWidget(url_group)

        # -------------------------------------------------------------
        # Section 2: Automated Multi-Source Batch Scraper
        # -------------------------------------------------------------
        scraper_group = QGroupBox("Automated Multi-Source Batch Scraper")
        scraper_layout = QVBoxLayout(scraper_group)
        scraper_layout.setContentsMargins(10, 10, 10, 10)
        scraper_layout.setSpacing(8)

        # Controls Row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        lbl_source = QLabel("Target Source:")
        lbl_source.setStyleSheet("font-size: 11px; color: #334155; font-weight: 600;")
        ctrl_row.addWidget(lbl_source)

        self.combo_source = QComboBox()
        self.combo_source.addItem("All Sources (Auto-Orchestrated)", "all")
        self.combo_source.addItem("SteamSpy Public API (Pages 15+)", "steamspy")
        self.combo_source.addItem("CheapShark Deals API", "cheapshark")
        self.combo_source.addItem("FreeToGame Catalog", "freetogame")
        ctrl_row.addWidget(self.combo_source)

        ctrl_row.addSpacing(6)

        lbl_target = QLabel("New Records to Scrape:")
        lbl_target.setStyleSheet("font-size: 11px; color: #334155; font-weight: 600;")
        ctrl_row.addWidget(lbl_target)

        self.spin_target = QSpinBox()
        self.spin_target.setRange(10, 10000)
        self.spin_target.setSingleStep(50)
        self.spin_target.setValue(100)
        ctrl_row.addWidget(self.spin_target)

        ctrl_row.addSpacing(8)

        self.btn_start = QPushButton("Start Scraper")
        self.btn_start.setObjectName("successBtn")
        self.btn_start.clicked.connect(self._start_scraper)
        ctrl_row.addWidget(self.btn_start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("secondaryBtn")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._pause_scraper)
        ctrl_row.addWidget(self.btn_pause)

        self.btn_resume = QPushButton("Resume")
        self.btn_resume.setObjectName("secondaryBtn")
        self.btn_resume.setEnabled(False)
        self.btn_resume.clicked.connect(self._resume_scraper)
        ctrl_row.addWidget(self.btn_resume)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("dangerBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_scraper)
        ctrl_row.addWidget(self.btn_stop)

        ctrl_row.addStretch()
        scraper_layout.addLayout(ctrl_row)

        # Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        scraper_layout.addWidget(self.progress_bar)

        # Stats Cards Grid
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(8)
        stats_grid.setVerticalSpacing(4)
        self.lbl_stat_db = self._add_stat(stats_grid, "Database Total", "0", 0, 0, "#0f172a")
        self.lbl_stat_new = self._add_stat(stats_grid, "Newly Added", "0", 0, 1, "#059669")
        self.lbl_stat_dupes = self._add_stat(stats_grid, "Duplicates Skipped", "0", 0, 2, "#d97706")
        self.lbl_stat_errors = self._add_stat(stats_grid, "Errors / Retries", "0", 0, 3, "#dc2626")
        self.lbl_stat_source = self._add_stat(stats_grid, "Current Source", "Idle", 0, 4, "#0f172a")
        self.lbl_stat_time = self._add_stat(stats_grid, "Elapsed Time", "0.0s", 0, 5, "#475569")
        scraper_layout.addLayout(stats_grid)

        # Live Activity Log
        lbl_log = QLabel("Activity Log:")
        lbl_log.setStyleSheet("font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.3px;")
        scraper_layout.addWidget(lbl_log)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(110)
        scraper_layout.addWidget(self.log_text)

        main_layout.addWidget(scraper_group)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        # Initialize current count
        self.update_db_counter()

    def _add_stat(self, grid: QGridLayout, title: str, val: str, r: int, c: int, color_hex: str) -> QLabel:
        frame = QFrame()
        frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px;")
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(6, 4, 6, 4)
        vbox.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px;")
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"color: {color_hex}; font-size: 13px; font-weight: 700;")

        vbox.addWidget(t_lbl)
        vbox.addWidget(v_lbl)
        grid.addWidget(frame, r, c)
        return v_lbl

    def update_db_counter(self):
        total = self.data_service.get_total_count()
        self.lbl_stat_db.setText(f"{total:,}")

    def _fill_and_scrape(self, url: str):
        self.url_input.setText(url)
        self._scrape_and_save_url()

    def _start_scraper(self):
        target = self.spin_target.value()
        source_choice = self.combo_source.currentData()
        self.lbl_stat_source.setText("Starting...")
        self.progress_bar.setValue(0)
        self.lbl_stat_new.setText("0")
        self.lbl_stat_dupes.setText("0")
        self.lbl_stat_errors.setText("0")

        self.worker = ScraperWorker(target_to_add=target, source_filter=source_choice, repo=self.data_service.repo, parent=self)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.log_message.connect(self._on_log)
        self.worker.finished_scraping.connect(self._on_finished)
        self.worker.stopped_scraping.connect(self._on_stopped)
        self.worker.error_occurred.connect(self._on_error)

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.log_text.appendPlainText(f">>> Scraping worker thread launched: Target = {target} new records from '{self.combo_source.currentText()}'.")
        self.worker.start()

    def _pause_scraper(self):
        if self.worker:
            self.worker.pause()
            self.lbl_stat_source.setText("Paused")
            self.btn_pause.setEnabled(False)
            self.btn_resume.setEnabled(True)

    def _resume_scraper(self):
        if self.worker:
            self.worker.resume()
            self.lbl_stat_source.setText("Resuming...")
            self.btn_pause.setEnabled(True)
            self.btn_resume.setEnabled(False)

    def _stop_scraper(self):
        if self.worker:
            self.worker.stop()
            self.btn_pause.setEnabled(False)
            self.btn_resume.setEnabled(False)
            self.btn_stop.setEnabled(False)

    def _on_progress(self, collected: int, target: int, added: int, dupes: int, errors: int, source: str, elapsed: float):
        pct = min(100, int((added / target) * 100)) if target > 0 else 0
        self.progress_bar.setValue(pct)
        self.lbl_stat_db.setText(f"{collected:,}")
        self.lbl_stat_new.setText(f"{added:,}")
        self.lbl_stat_dupes.setText(f"{dupes:,}")
        self.lbl_stat_errors.setText(f"{errors}")
        self.lbl_stat_source.setText(source)
        self.lbl_stat_time.setText(f"{elapsed:.1f}s")
        self.data_updated.emit()

    def _on_log(self, msg: str):
        self.log_text.appendPlainText(msg)

    def _on_finished(self, added: int, dupes: int, errors: int):
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.lbl_stat_source.setText("Complete")
        self.progress_bar.setValue(100)
        self.log_text.appendPlainText(f">>> Session finished! Added: {added:,}, Duplicates: {dupes:,}, Errors: {errors}")
        self.data_service.invalidate_cache()
        self.data_updated.emit()
        QMessageBox.information(
            self, "Scraper Finished",
            f"Scraping session completed!\n\n"
            f"• Newly Added to Database: {added:,} games\n"
            f"• Duplicates Skipped: {dupes:,} games\n"
            f"• Errors: {errors}\n\n"
            f"All newly added games are immediately visible in your Game Library!"
        )

    def _on_stopped(self):
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.lbl_stat_source.setText("Stopped")
        self.log_text.appendPlainText(">>> Scraping stopped by user.")
        self.data_service.invalidate_cache()
        self.data_updated.emit()

    def _on_error(self, err: str):
        self.log_text.appendPlainText(f"[ERROR] {err}")
        QMessageBox.critical(self, "Scraper Error", err)

    def _preview_url(self):
        url = self.url_input.text().strip()
        if not url:
            self.lbl_url_status.setText("Please enter or paste a valid game URL.")
            return

        self.lbl_url_status.setText("Validating URL security and fetching page...")
        game, err = URLScraper.scrape_url(url)
        if err:
            self.lbl_url_status.setText(f"<span style='color:#dc2626;'>[Failed] {err}</span>")
            self.btn_save_url_game.setEnabled(False)
            self.extracted_url_game = None
            self.lbl_preview_info.setText(f"Error: {err}")
            return

        self.extracted_url_game = game
        self.lbl_url_status.setText("<span style='color:#059669;'>[Success] Metadata extracted! Click 'Save to Database' to persist.</span>")
        self.lbl_preview_info.setText(
            f"<b>Title:</b> {game.title} | <b>Developer:</b> {game.developer or 'N/A'} | "
            f"<b>Rating:</b> {game.rating or 'N/A'}% | <b>Price:</b> ${game.price or 0.0:.2f} | "
            f"<b>Genres:</b> {game.genres or 'N/A'}"
        )
        self.btn_save_url_game.setEnabled(True)

    def _scrape_and_save_url(self):
        """One-click scrape and save directly into the database."""
        url = self.url_input.text().strip()
        if not url:
            self.lbl_url_status.setText("Please enter or paste a valid game URL.")
            return

        self.lbl_url_status.setText("Fetching and scraping page metadata live...")
        game, err = URLScraper.scrape_url(url)
        if err:
            self.lbl_url_status.setText(f"<span style='color:#dc2626;'>[Scrape Failed] {err}</span>")
            self.lbl_preview_info.setText(f"Error: {err}")
            self.btn_save_url_game.setEnabled(False)
            return

        self.extracted_url_game = game
        self.lbl_preview_info.setText(
            f"<b>Title:</b> {game.title} | <b>Developer:</b> {game.developer or 'N/A'} | "
            f"<b>Rating:</b> {game.rating or 'N/A'}% | <b>Price:</b> ${game.price or 0.0:.2f} | "
            f"<b>Genres:</b> {game.genres or 'N/A'}"
        )

        # Directly save to SQLite
        game_id = self.data_service.insert_single_game(game)
        if game_id:
            self.lbl_url_status.setText(f"<span style='color:#059669; font-weight:700;'>✓ Successfully scraped & saved '{game.title}' to database (ID: #{game_id})!</span>")
            self.log_text.appendPlainText(f"[URL Scraper] Successfully extracted and saved '{game.title}' (ID: #{game_id}) from {url}.")
            self.btn_save_url_game.setEnabled(False)
            self.update_db_counter()
            self.data_updated.emit()
            QMessageBox.information(
                self, "Game Saved",
                f"Successfully extracted and saved:\n\n"
                f"• Title: {game.title}\n"
                f"• Developer: {game.developer or 'N/A'}\n"
                f"• Release Date: {game.release_date or 'N/A'}\n"
                f"• Price: ${game.price or 0.0:.2f}\n"
                f"• Rating: {game.rating or 'N/A'}%\n\n"
                f"Saved into SQLite database with Game ID #{game_id}!"
            )
        else:
            self.lbl_url_status.setText(f"<span style='color:#d97706;'>Notice: '{game.title}' was scraped cleanly, but is already present in your database.</span>")
            self.btn_save_url_game.setEnabled(False)

    def _save_extracted_game(self):
        if not self.extracted_url_game:
            return

        game_id = self.data_service.insert_single_game(self.extracted_url_game)
        if game_id:
            QMessageBox.information(self, "Game Saved", f"Successfully saved '{self.extracted_url_game.title}' into database with Game ID: {game_id}!")
            self.btn_save_url_game.setEnabled(False)
            self.update_db_counter()
            self.data_updated.emit()
        else:
            QMessageBox.warning(self, "Duplicate Game", f"'{self.extracted_url_game.title}' is already present in the database. Skipped duplicate.")
