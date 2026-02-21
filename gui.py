"""
Form-based GUI for Steganography Tool 
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
from datetime import datetime
import os
from typing import Optional
import sqlite3
import json
import binascii

from src.steganography_engine import SteganographyEngine
from src.encryption_manager import EncryptionManager
from src.database_manager import DatabaseManager

class SteganographyGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Secure Data Hider - Steganography Tool")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.engine = SteganographyEngine()
        self.encryption_manager = EncryptionManager()
        self.db_manager = DatabaseManager()
        
        # Session tracking
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.db_manager.start_session(self.session_id, "GUI", "Steganography Tool")
        
        # State variables
        self.cover_image_path = None
        self.secret_file_path = None
        self.output_path = None
        self.current_tab = None
        
        # Status variable
        self.status_var = tk.StringVar(value="Ready")
        self.current_extracted_data = None  # Store extracted data for conversion
        
        self.setup_styles()
        self.create_widgets()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.root.configure(bg='#f0f0f0')
        
        style.configure('Title.TLabel', 
                       font=('Helvetica', 18, 'bold'),
                       background='#f0f0f0',
                       foreground='#2c3e50')
        
        style.configure('Section.TLabelframe', 
                       padding=10,
                       relief='solid',
                       borderwidth=1,
                       background='#ffffff')
        
        style.configure('Section.TLabelframe.Label',
                       font=('Helvetica', 10, 'bold'),
                       foreground='#34495e')
        
        style.configure('Action.TButton',
                       font=('Helvetica', 10, 'bold'),
                       padding=8)
        
        style.map('Action.TButton',
                 background=[('active', '#27ae60'), ('!active', '#2ecc71')],
                 foreground=[('active', 'white'), ('!active', 'white')])
    
    def create_scrollable_frame(self, parent):
        """Create a scrollable frame"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        
        # Create scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        
        # Bind mousewheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)
        
        # Bind canvas resize
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', _on_canvas_configure)
        
        # Pack canvas and scrollbars
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        
        return scrollable_frame
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = tk.Frame(main_container, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, 
                              text="🔒 Secure Data Hider",
                              font=('Helvetica', 20, 'bold'),
                              bg='#f0f0f0',
                              fg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_frame,
                                text="Steganography Tool with AES Encryption",
                                font=('Helvetica', 10),
                                bg='#f0f0f0',
                                fg='#7f8c8d')
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_encode = ttk.Frame(notebook)
        self.tab_decode = ttk.Frame(notebook)
        self.tab_history = ttk.Frame(notebook)
        self.tab_settings = ttk.Frame(notebook)
        
        notebook.add(self.tab_encode, text='Encode Data')
        notebook.add(self.tab_decode, text='Decode Data')
        notebook.add(self.tab_history, text='Operation History')
        notebook.add(self.tab_settings, text='Settings')
        
        # Bind tab change event
        notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Setup each tab
        self.setup_encode_tab()
        self.setup_decode_tab()  # This now has the fixed functions
        self.setup_history_tab()
        self.setup_settings_tab()
        
        # Status bar
        status_frame = tk.Frame(main_container, bg='#ffffff', height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)
        
        status_indicator = tk.Label(status_frame,
                                   text="●",
                                   font=('Helvetica', 10),
                                   bg='#ffffff',
                                   fg='#27ae60')
        status_indicator.pack(side=tk.LEFT, padx=(10, 5))
        
        status_label = tk.Label(status_frame,
                              textvariable=self.status_var,
                              font=('Helvetica', 9),
                              bg='#ffffff',
                              fg='#34495e')
        status_label.pack(side=tk.LEFT)
        
        version_label = tk.Label(status_frame,
                                text="v1.0",
                                font=('Helvetica', 8),
                                bg='#ffffff',
                                fg='#95a5a6')
        version_label.pack(side=tk.RIGHT, padx=10)
    
    def setup_encode_tab(self):
        """Setup encode data tab"""
        # Create scrollable frame
        scrollable_frame = self.create_scrollable_frame(self.tab_encode)
        
        # Main container for encode tab
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Cover image selection
        cover_frame = ttk.LabelFrame(main_frame, 
                                    text="1. Select Cover Image",
                                    style='Section.TLabelframe')
        cover_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Browse row
        browse_frame = tk.Frame(cover_frame, bg='#ffffff')
        browse_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.cover_path_var = tk.StringVar()
        cover_entry = tk.Entry(browse_frame, textvariable=self.cover_path_var,
                              font=('Helvetica', 9), bg='#f8f9fa',
                              relief='solid', borderwidth=1)
        cover_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=5)
        
        browse_btn = tk.Button(browse_frame, text="Browse...",
                              command=self.browse_cover_image,
                              bg='#3498db', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=15, pady=5)
        browse_btn.pack(side=tk.RIGHT)
        
        # Preview
        preview_frame = tk.Frame(cover_frame, bg='#ffffff')
        preview_frame.pack(pady=(0, 10))
        
        self.cover_preview_label = tk.Label(preview_frame, text="No image selected",
                                           font=('Helvetica', 9), bg='#ecf0f1',
                                           width=50, height=8, relief='solid',
                                           borderwidth=1)
        self.cover_preview_label.pack()
        
        # Secret data selection
        secret_frame = ttk.LabelFrame(main_frame,
                                     text="2. Select Secret Data",
                                     style='Section.TLabelframe')
        secret_frame.pack(fill=tk.X, pady=(0, 10))
        
        secret_content = tk.Frame(secret_frame, bg='#ffffff')
        secret_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Data type selection
        type_frame = tk.Frame(secret_content, bg='#ffffff')
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.data_type = tk.StringVar(value="text")
        
        text_radio = tk.Radiobutton(type_frame, text="Text Message",
                                   variable=self.data_type, value="text",
                                   bg='#ffffff', font=('Helvetica', 9))
        text_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        file_radio = tk.Radiobutton(type_frame, text="File",
                                   variable=self.data_type, value="file",
                                   bg='#ffffff', font=('Helvetica', 9))
        file_radio.pack(side=tk.LEFT)
        
        # Text input
        self.secret_text = scrolledtext.ScrolledText(secret_content, height=5,
                                                     font=('Helvetica', 9),
                                                     bg='#f8f9fa',
                                                     relief='solid',
                                                     borderwidth=1)
        self.secret_text.pack(fill=tk.X, pady=(0, 10))
        
        # File input
        file_frame = tk.Frame(secret_content, bg='#ffffff')
        file_frame.pack(fill=tk.X)
        
        self.secret_path_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.secret_path_var,
                            font=('Helvetica', 9), bg='#f8f9fa',
                            state='readonly', relief='solid', borderwidth=1)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=5)
        
        file_browse = tk.Button(file_frame, text="Browse...",
                               command=self.browse_secret_file,
                               bg='#3498db', fg='white', relief='flat',
                               font=('Helvetica', 9), padx=15, pady=5)
        file_browse.pack(side=tk.RIGHT)
        
        # Encryption options
        encryption_frame = ttk.LabelFrame(main_frame,
                                         text="3. Encryption Options",
                                         style='Section.TLabelframe')
        encryption_frame.pack(fill=tk.X, pady=(0, 10))
        
        encrypt_content = tk.Frame(encryption_frame, bg='#ffffff')
        encrypt_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.encryption_var = tk.BooleanVar(value=False)
        encrypt_check = tk.Checkbutton(encrypt_content, text="Enable Encryption",
                                       variable=self.encryption_var,
                                       bg='#ffffff', font=('Helvetica', 9))
        encrypt_check.pack(anchor=tk.W)
        
        pass_frame = tk.Frame(encrypt_content, bg='#ffffff')
        pass_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(pass_frame, text="Password:",
                bg='#ffffff', font=('Helvetica', 9)).pack(side=tk.LEFT)
        
        self.password_var = tk.StringVar()
        pass_entry = tk.Entry(pass_frame, textvariable=self.password_var,
                             show="*", bg='#f8f9fa', font=('Helvetica', 9),
                             relief='solid', borderwidth=1)
        pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), ipady=3)
        
        # Steganography options
        stego_frame = ttk.LabelFrame(main_frame,
                                    text="4. Steganography Options",
                                    style='Section.TLabelframe')
        stego_frame.pack(fill=tk.X, pady=(0, 10))
        
        stego_content = tk.Frame(stego_frame, bg='#ffffff')
        stego_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Bits per pixel
        bits_frame = tk.Frame(stego_content, bg='#ffffff')
        bits_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(bits_frame, text="Bits per pixel:",
                bg='#ffffff', font=('Helvetica', 9)).pack(side=tk.LEFT)
        
        self.bits_var = tk.IntVar(value=1)
        bits_combo = ttk.Combobox(bits_frame, textvariable=self.bits_var,
                                 values=[1, 2, 3], width=5, state='readonly')
        bits_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Compression
        self.compression_var = tk.BooleanVar(value=True)
        compress_check = tk.Checkbutton(stego_content, text="Enable Compression",
                                       variable=self.compression_var,
                                       bg='#ffffff', font=('Helvetica', 9))
        compress_check.pack(anchor=tk.W)
        
        # Output options
        output_frame = ttk.LabelFrame(main_frame,
                                     text="5. Output Options",
                                     style='Section.TLabelframe')
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        output_content = tk.Frame(output_frame, bg='#ffffff')
        output_content.pack(fill=tk.X, padx=10, pady=10)
        
        out_frame = tk.Frame(output_content, bg='#ffffff')
        out_frame.pack(fill=tk.X)
        
        self.output_path_var = tk.StringVar()
        out_entry = tk.Entry(out_frame, textvariable=self.output_path_var,
                            font=('Helvetica', 9), bg='#f8f9fa',
                            relief='solid', borderwidth=1)
        out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=5)
        
        out_browse = tk.Button(out_frame, text="Browse...",
                              command=self.browse_output,
                              bg='#3498db', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=15, pady=5)
        out_browse.pack(side=tk.RIGHT)
        
        # Encode button
        btn_frame = tk.Frame(main_frame, bg='#f0f0f0')
        btn_frame.pack(pady=15)
        
        encode_btn = tk.Button(btn_frame, text="ENCODE DATA",
                              command=self.encode_data,
                              bg='#27ae60', fg='white', relief='flat',
                              font=('Helvetica', 11, 'bold'),
                              padx=30, pady=8)
        encode_btn.pack()
        
        # Progress bar
        self.progress_encode = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_encode.pack(fill=tk.X, pady=(0, 5))
    
    def setup_decode_tab(self):
        """Setup decode data tab - FULLY FIXED VERSION"""
        # Create scrollable frame
        scrollable_frame = self.create_scrollable_frame(self.tab_decode)
        
        # Main container for decode tab
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Stego image selection
        stego_frame = ttk.LabelFrame(main_frame,
                                    text="1. Select Stego Image",
                                    style='Section.TLabelframe')
        stego_frame.pack(fill=tk.X, pady=(0, 10))
        
        browse_frame = tk.Frame(stego_frame, bg='#ffffff')
        browse_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.stego_path_var = tk.StringVar()
        stego_entry = tk.Entry(browse_frame, textvariable=self.stego_path_var,
                              font=('Helvetica', 9), bg='#f8f9fa',
                              relief='solid', borderwidth=1)
        stego_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=5)
        
        stego_browse = tk.Button(browse_frame, text="Browse...",
                                command=self.browse_stego_image,
                                bg='#3498db', fg='white', relief='flat',
                                font=('Helvetica', 9), padx=15, pady=5)
        stego_browse.pack(side=tk.RIGHT)
        
        # Preview
        preview_frame = tk.Frame(stego_frame, bg='#ffffff')
        preview_frame.pack(pady=(0, 10))
        
        self.stego_preview_label = tk.Label(preview_frame, text="No image selected",
                                           font=('Helvetica', 9), bg='#ecf0f1',
                                           width=50, height=8, relief='solid',
                                           borderwidth=1)
        self.stego_preview_label.pack()
        
        # Decryption options
        decryption_frame = ttk.LabelFrame(main_frame,
                                         text="2. Decryption Options",
                                         style='Section.TLabelframe')
        decryption_frame.pack(fill=tk.X, pady=(0, 10))
        
        decrypt_content = tk.Frame(decryption_frame, bg='#ffffff')
        decrypt_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Password field
        pass_frame = tk.Frame(decrypt_content, bg='#ffffff')
        pass_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(pass_frame, text="Password (if encrypted):",
                bg='#ffffff', font=('Helvetica', 9)).pack(anchor=tk.W)
        
        self.decode_password_var = tk.StringVar()
        pass_entry = tk.Entry(pass_frame, textvariable=self.decode_password_var,
                             show="*", bg='#f8f9fa', font=('Helvetica', 9),
                             relief='solid', borderwidth=1)
        pass_entry.pack(fill=tk.X, pady=(5, 0), ipady=3)
        
        # Output options
        output_frame = ttk.LabelFrame(main_frame,
                                     text="3. Output Options",
                                     style='Section.TLabelframe')
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        output_content = tk.Frame(output_frame, bg='#ffffff')
        output_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.decode_output_option = tk.StringVar(value="text")
        
        text_radio = tk.Radiobutton(output_content, text="Display as text",
                                   variable=self.decode_output_option,
                                   value="text", bg='#ffffff',
                                   font=('Helvetica', 9))
        text_radio.pack(anchor=tk.W)
        
        file_radio = tk.Radiobutton(output_content, text="Save to file",
                                   variable=self.decode_output_option,
                                   value="file", bg='#ffffff',
                                   font=('Helvetica', 9))
        file_radio.pack(anchor=tk.W, pady=(5, 0))
        
        file_frame = tk.Frame(output_content, bg='#ffffff')
        file_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.decode_output_path_var = tk.StringVar()
        file_entry = tk.Entry(file_frame, textvariable=self.decode_output_path_var,
                            font=('Helvetica', 9), bg='#f8f9fa',
                            relief='solid', borderwidth=1)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        
        file_browse = tk.Button(file_frame, text="Browse...",
                               command=self.browse_decode_output,
                               bg='#3498db', fg='white', relief='flat',
                               font=('Helvetica', 9), padx=10, pady=3)
        file_browse.pack(side=tk.RIGHT)
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame,
                                      text="4. Extracted Data",
                                      style='Section.TLabelframe')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        results_content = tk.Frame(results_frame, bg='#ffffff')
        results_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text widget for results
        self.results_text = scrolledtext.ScrolledText(results_content, height=10,
                                                     font=('Courier', 10),
                                                     bg='#f8f9fa',
                                                     relief='solid',
                                                     borderwidth=1)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Button frame for conversions
        button_frame = tk.Frame(results_content, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Convert button - FIXED version
        convert_btn = tk.Button(button_frame, text="🔄 Convert to Text", 
                               command=self.convert_to_text,
                               bg='#3498db', fg='white', relief='flat',
                               font=('Helvetica', 9), padx=10, pady=3)
        convert_btn.pack(side=tk.LEFT, padx=2)
        
        # Save as binary button
        save_binary_btn = tk.Button(button_frame, text="💾 Save as Binary", 
                                   command=self.save_as_binary,
                                   bg='#e67e22', fg='white', relief='flat',
                                   font=('Helvetica', 9), padx=10, pady=3)
        save_binary_btn.pack(side=tk.LEFT, padx=2)
        
        # Decode button
        btn_frame = tk.Frame(main_frame, bg='#f0f0f0')
        btn_frame.pack(pady=10)
        
        decode_btn = tk.Button(btn_frame, text="DECODE DATA",
                              command=self.decode_data,
                              bg='#27ae60', fg='white', relief='flat',
                              font=('Helvetica', 11, 'bold'),
                              padx=30, pady=8)
        decode_btn.pack()
        
        # Progress bar
        self.progress_decode = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_decode.pack(fill=tk.X, pady=(0, 5))
    
    def setup_history_tab(self):
        """Setup operation history tab"""
        # Create scrollable frame
        scrollable_frame = self.create_scrollable_frame(self.tab_history)
        
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Toolbar
        toolbar = tk.Frame(main_frame, bg='#ffffff', relief='solid', borderwidth=1)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        refresh_btn = tk.Button(toolbar, text="Refresh",
                               command=self.refresh_history,
                               bg='#3498db', fg='white', relief='flat',
                               font=('Helvetica', 9), padx=10, pady=5)
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        clear_btn = tk.Button(toolbar, text="Clear History",
                             command=self.clear_history,
                             bg='#e74c3c', fg='white', relief='flat',
                             font=('Helvetica', 9), padx=10, pady=5)
        clear_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        export_btn = tk.Button(toolbar, text="Export to CSV",
                              command=self.export_history,
                              bg='#27ae60', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=10, pady=5)
        export_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Treeview frame
        tree_frame = tk.Frame(main_frame, bg='#ffffff', relief='solid', borderwidth=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview
        columns = ('id', 'timestamp', 'operation', 'input', 'output', 'size', 'success')
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.history_tree.heading('id', text='ID')
        self.history_tree.heading('timestamp', text='Timestamp')
        self.history_tree.heading('operation', text='Operation')
        self.history_tree.heading('input', text='Input File')
        self.history_tree.heading('output', text='Output File')
        self.history_tree.heading('size', text='Data Size')
        self.history_tree.heading('success', text='Success')
        
        # Define column widths
        self.history_tree.column('id', width=50)
        self.history_tree.column('timestamp', width=150)
        self.history_tree.column('operation', width=100)
        self.history_tree.column('input', width=200)
        self.history_tree.column('output', width=200)
        self.history_tree.column('size', width=80)
        self.history_tree.column('success', width=60)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Details frame
        details_frame = ttk.LabelFrame(main_frame,
                                      text="Operation Details",
                                      style='Section.TLabelframe')
        details_frame.pack(fill=tk.X)
        
        details_content = tk.Frame(details_frame, bg='#ffffff')
        details_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.details_text = scrolledtext.ScrolledText(details_content, height=6,
                                                     font=('Courier', 9),
                                                     bg='#f8f9fa',
                                                     relief='solid',
                                                     borderwidth=1)
        self.details_text.pack(fill=tk.X)
        
        # Bind selection event
        self.history_tree.bind('<<TreeviewSelect>>', self.on_history_select)
        
        # Load initial history
        self.refresh_history()
    
    def setup_settings_tab(self):
        """Setup settings tab"""
        # Create scrollable frame
        scrollable_frame = self.create_scrollable_frame(self.tab_settings)
        
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # General settings
        general_frame = ttk.LabelFrame(main_frame,
                                      text="General Settings",
                                      style='Section.TLabelframe')
        general_frame.pack(fill=tk.X, pady=(0, 10))
        
        general_content = tk.Frame(general_frame, bg='#ffffff')
        general_content.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(general_content, text="Default output directory:",
                bg='#ffffff', font=('Helvetica', 9)).pack(anchor=tk.W)
        
        dir_frame = tk.Frame(general_content, bg='#ffffff')
        dir_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.default_dir_var = tk.StringVar(value=os.path.expanduser("~/Documents"))
        dir_entry = tk.Entry(dir_frame, textvariable=self.default_dir_var,
                            bg='#f8f9fa', font=('Helvetica', 9),
                            relief='solid', borderwidth=1)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=3)
        
        dir_browse = tk.Button(dir_frame, text="Browse...",
                              command=self.browse_default_dir,
                              bg='#3498db', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=10, pady=3)
        dir_browse.pack(side=tk.RIGHT)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(main_frame,
                                   text="Performance Settings",
                                   style='Section.TLabelframe')
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        perf_content = tk.Frame(perf_frame, bg='#ffffff')
        perf_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Max threads
        thread_frame = tk.Frame(perf_content, bg='#ffffff')
        thread_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(thread_frame, text="Max threads:",
                bg='#ffffff', font=('Helvetica', 9)).pack(side=tk.LEFT)
        
        self.max_threads_var = tk.IntVar(value=4)
        thread_spin = ttk.Spinbox(thread_frame, from_=1, to=16,
                                 textvariable=self.max_threads_var,
                                 width=10)
        thread_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Compression level
        comp_frame = tk.Frame(perf_content, bg='#ffffff')
        comp_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(comp_frame, text="Compression level:",
                bg='#ffffff', font=('Helvetica', 9)).pack(side=tk.LEFT)
        
        self.compression_level_var = tk.IntVar(value=6)
        comp_scale = ttk.Scale(comp_frame, from_=1, to=9,
                              variable=self.compression_level_var,
                              orient=tk.HORIZONTAL,
                              length=200)
        comp_scale.pack(side=tk.LEFT, padx=(10, 10))
        
        comp_label = tk.Label(comp_frame, textvariable=self.compression_level_var,
                             bg='#ffffff', font=('Helvetica', 9))
        comp_label.pack(side=tk.LEFT)
        
        # Database settings
        db_frame = ttk.LabelFrame(main_frame,
                                 text="Database Management",
                                 style='Section.TLabelframe')
        db_frame.pack(fill=tk.X, pady=(0, 10))
        
        db_content = tk.Frame(db_frame, bg='#ffffff')
        db_content.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = tk.Frame(db_content, bg='#ffffff')
        btn_frame.pack()
        
        optimize_btn = tk.Button(btn_frame, text="Optimize Database",
                                command=self.optimize_database,
                                bg='#3498db', fg='white', relief='flat',
                                font=('Helvetica', 9), padx=10, pady=5)
        optimize_btn.pack(side=tk.LEFT, padx=2)
        
        backup_btn = tk.Button(btn_frame, text="Backup Database",
                              command=self.backup_database,
                              bg='#27ae60', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=10, pady=5)
        backup_btn.pack(side=tk.LEFT, padx=2)
        
        verify_btn = tk.Button(btn_frame, text="Verify File Integrity",
                              command=self.verify_integrity,
                              bg='#e67e22', fg='white', relief='flat',
                              font=('Helvetica', 9), padx=10, pady=5)
        verify_btn.pack(side=tk.LEFT, padx=2)
        
        # Save button
        save_btn = tk.Button(main_frame, text="Save Settings",
                            command=self.save_settings,
                            bg='#27ae60', fg='white', relief='flat',
                            font=('Helvetica', 11, 'bold'),
                            padx=30, pady=8)
        save_btn.pack(pady=15)
    
    # ========== HELPER FUNCTIONS ==========
    
    def browse_cover_image(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Cover Image",
                                             filetypes=filetypes)
        if filename:
            self.cover_path_var.set(filename)
            self.preview_image(filename, self.cover_preview_label)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
    
    def browse_secret_file(self):
        filename = filedialog.askopenfilename(title="Select Secret File")
        if filename:
            self.secret_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
    
    def browse_output(self):
        filetypes = [("PNG files", "*.png"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(title="Save Output Image",
                                               defaultextension=".png",
                                               filetypes=filetypes)
        if filename:
            self.output_path_var.set(filename)
    
    def browse_stego_image(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="Select Stego Image",
                                             filetypes=filetypes)
        if filename:
            self.stego_path_var.set(filename)
            self.preview_image(filename, self.stego_preview_label)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
    
    def browse_decode_output(self):
        filename = filedialog.asksaveasfilename(title="Save Extracted Data",
                                               defaultextension=".txt",
                                               filetypes=[("All files", "*.*")])
        if filename:
            self.decode_output_path_var.set(filename)
    
    def browse_default_dir(self):
        directory = filedialog.askdirectory(title="Select Default Output Directory")
        if directory:
            self.default_dir_var.set(directory)
    
    def encode_data(self):
        if not self.cover_path_var.get():
            messagebox.showerror("Error", "Please select a cover image")
            return
        
        secret_data = self.secret_text.get("1.0", tk.END).strip()
        secret_file = self.secret_path_var.get()
        
        if not secret_data and not secret_file:
            messagebox.showerror("Error", "Please provide secret data or select a file")
            return
        
        if secret_file and self.data_type.get() == "file":
            try:
                with open(secret_file, 'rb') as f:
                    secret_bytes = f.read()
                self.status_var.set(f"📁 Loading file: {os.path.basename(secret_file)}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot read secret file: {str(e)}")
                return
        else:
            secret_bytes = secret_data.encode('utf-8')
        
        # Show key if encryption is enabled but no password provided
        show_key = False
        if self.encryption_var.get():
            password = self.password_var.get()
            if not password:
                # Auto-generate key
                import secrets
                key = secrets.token_bytes(32)
                self.password_var.set(key.hex())
                show_key = True
                messagebox.showinfo("Encryption Key", 
                                   f"Your auto-generated encryption key is:\n{key.hex()}\n\nSAVE THIS KEY to decrypt your message!")
            
            encrypted_data, key = self.encryption_manager.encrypt_data(secret_bytes, self.password_var.get())
            secret_bytes = encrypted_data
        
        self.progress_encode.start()
        self.status_var.set("Encoding data...")
        
        threading.Thread(target=self._encode_thread,
                        args=(secret_bytes,),
                        daemon=True).start()
    
    def _encode_thread(self, secret_bytes):
        try:
            output_path = self.output_path_var.get()
            if not output_path:
                output_path = f"stego_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.output_path_var.set(output_path)
            
            success, message = self.engine.embed_data(
                cover_image_path=self.cover_path_var.get(),
                secret_data=secret_bytes,
                output_path=output_path,
                bits_per_pixel=self.bits_var.get(),
                use_compression=self.compression_var.get()
            )
            
            metadata = {
                'bits_per_pixel': self.bits_var.get(),
                'compression': self.compression_var.get(),
                'encryption': self.encryption_var.get()
            }
            
            self.db_manager.log_operation(
                operation_type='embed',
                input_file=self.cover_path_var.get(),
                output_file=output_path,
                data_size=len(secret_bytes),
                encryption_used=self.encryption_var.get(),
                success=success,
                metadata=metadata
            )
            
            if success:
                import hashlib
                with open(output_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                self.db_manager.store_file_hash(output_path, file_hash)
            
            self.root.after(0, self._encode_complete, success, message)
            
        except Exception as e:
            self.root.after(0, self._encode_complete, False, f"Encoding error: {str(e)}")
    
    def _encode_complete(self, success, message):
        self.progress_encode.stop()
        
        if success:
            messagebox.showinfo("Success", message)
            self.status_var.set("Encoding completed successfully")
        else:
            messagebox.showerror("Error", message)
            self.status_var.set("Encoding failed")
    
    # ========== DECODE FUNCTIONS ==========
    
    def decode_data(self):
        """Decode data from image"""
        if not self.stego_path_var.get():
            messagebox.showerror("Error", "Please select a stego image")
            return
        
        self.progress_decode.start()
        self.status_var.set("Decoding data...")
        
        threading.Thread(target=self._decode_thread, daemon=True).start()
    
    def _decode_thread(self):
        """Thread for decoding"""
        try:
            extracted_data, message = self.engine.extract_data(
                stego_image_path=self.stego_path_var.get()
            )
            
            if extracted_data is None:
                self.root.after(0, self._decode_complete, False, message, None)
                return
            
            # Store the extracted data for later use
            self.current_extracted_data = extracted_data
            
            # Try decryption if password provided
            password = self.decode_password_var.get()
            if password:
                try:
                    decrypted_data, decrypt_msg = self.encryption_manager.decrypt_data(
                        extracted_data, password=password
                    )
                    if decrypted_data:
                        extracted_data = decrypted_data
                        self.current_extracted_data = extracted_data
                        message += f"\n{decrypt_msg}"
                    else:
                        self.root.after(0, self._decode_complete, False, decrypt_msg, extracted_data)
                        return
                except Exception as e:
                    self.root.after(0, self._decode_complete, False, f"Decryption error: {str(e)}", extracted_data)
                    return
            
            # Save to file if requested
            if self.decode_output_option.get() == "file" and self.decode_output_path_var.get():
                with open(self.decode_output_path_var.get(), 'wb') as f:
                    f.write(extracted_data)
                message += f"\nData saved to: {self.decode_output_path_var.get()}"
            
            # Log operation
            self.db_manager.log_operation(
                operation_type='extract',
                input_file=self.stego_path_var.get(),
                data_size=len(extracted_data),
                encryption_used=bool(password),
                success=True
            )
            
            self.root.after(0, self._decode_complete, True, message, extracted_data)
            
        except Exception as e:
            self.root.after(0, self._decode_complete, False, f"Decoding error: {str(e)}", None)
    
    def _decode_complete(self, success, message, extracted_data):
        """Called when decoding completes - FIXED VERSION"""
        self.progress_decode.stop()
        
        if success and extracted_data:
            self.results_text.delete("1.0", tk.END)
            
            # Store the data for conversion buttons
            self.current_extracted_data = extracted_data
            
            # TRY TEXT FIRST - This is the key fix!
            try:
                # Try to decode as UTF-8 text
                text_data = extracted_data.decode('utf-8')
                # Check if it's reasonable text (printable characters)
                if all(ord(c) < 128 or c.isprintable() for c in text_data):
                    self.results_text.insert("1.0", text_data)
                    message += f"\n\n✅ Text message ({len(text_data)} characters)"
                    self.status_var.set("✅ Text message extracted")
                else:
                    # Contains non-printable characters, show as hex
                    hex_data = extracted_data.hex()
                    formatted_hex = ' '.join(hex_data[i:i+2] for i in range(0, min(len(hex_data), 100), 2))
                    if len(hex_data) > 100:
                        formatted_hex += "..."
                    self.results_text.insert("1.0", f"HEX: {formatted_hex}\n\nThis appears to be binary data. Click 'Convert to Text' if this should be readable.")
                    message += f"\n\n⚠️ Binary data ({len(extracted_data)} bytes)"
                    self.status_var.set("⚠️ Binary data - try Convert button")
            except UnicodeDecodeError:
                # Not UTF-8 text, show as hex
                hex_data = extracted_data.hex()
                formatted_hex = ' '.join(hex_data[i:i+2] for i in range(0, min(len(hex_data), 100), 2))
                if len(hex_data) > 100:
                    formatted_hex += "..."
                self.results_text.insert("1.0", f"HEX: {formatted_hex}")
                message += f"\n\n⚠️ Binary data ({len(extracted_data)} bytes)"
                self.status_var.set("⚠️ Binary data - try Convert button")
            
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
            self.status_var.set("❌ Decoding failed")
    
    def convert_to_text(self):
        """Convert the stored binary data to text - FIXED VERSION"""
        if self.current_extracted_data:
            try:
                # Directly use the stored bytes
                text = self.current_extracted_data.decode('utf-8')
                self.results_text.delete("1.0", tk.END)
                self.results_text.insert("1.0", text)
                self.status_var.set("✅ Converted to text")
                messagebox.showinfo("Success", "Data converted to text successfully!")
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    text = self.current_extracted_data.decode('latin-1')
                    self.results_text.delete("1.0", tk.END)
                    self.results_text.insert("1.0", text)
                    self.status_var.set("✅ Converted using Latin-1")
                    messagebox.showinfo("Success", "Data converted using Latin-1 encoding")
                except:
                    try:
                        text = self.current_extracted_data.decode('cp1252')
                        self.results_text.delete("1.0", tk.END)
                        self.results_text.insert("1.0", text)
                        self.status_var.set("✅ Converted using Windows-1252")
                        messagebox.showinfo("Success", "Data converted using Windows-1252 encoding")
                    except:
                        messagebox.showinfo("Info", "Data appears to be binary and cannot be converted to text")
        else:
            messagebox.showinfo("Info", "No data to convert. Decode first!")
    
    def save_as_binary(self):
        """Save the extracted data as binary file"""
        if self.current_extracted_data:
            filename = filedialog.asksaveasfilename(
                defaultextension=".bin",
                filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'wb') as f:
                    f.write(self.current_extracted_data)
                messagebox.showinfo("Success", f"Data saved to {filename}")
                self.status_var.set(f"✅ Saved to {os.path.basename(filename)}")
        else:
            messagebox.showinfo("Info", "No data to save. Decode first!")
    
    # ========== HISTORY FUNCTIONS ==========
    
    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        history = self.db_manager.get_operation_history(limit=100)
        
        for record in history:
            input_file = record['input_file'] or ''
            output_file = record['output_file'] or ''
            if len(input_file) > 30:
                input_file = '...' + input_file[-27:]
            if len(output_file) > 30:
                output_file = '...' + output_file[-27:]
            
            self.history_tree.insert('', 'end', values=(
                record['id'],
                record['timestamp'][:19] if record['timestamp'] else '',
                record['operation_type'],
                input_file,
                output_file,
                f"{record['data_size']}B" if record['data_size'] else '',
                '✓' if record['success'] else '✗'
            ))
        
        self.status_var.set(f"Loaded {len(history)} history records")
    
    def on_history_select(self, event):
        selection = self.history_tree.selection()
        if not selection:
            return
        
        item = self.history_tree.item(selection[0])
        record_id = item['values'][0]
        
        conn = sqlite3.connect(self.db_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM operations WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        conn.close()
        
        if record:
            details = f"Operation ID: {record['id']}\n"
            details += f"Timestamp: {record['timestamp']}\n"
            details += f"Type: {record['operation_type']}\n"
            details += f"Input: {record['input_file'] or 'N/A'}\n"
            details += f"Output: {record['output_file'] or 'N/A'}\n"
            details += f"Data Size: {record['data_size'] or 'N/A'} bytes\n"
            details += f"Encryption: {'Yes' if record['encryption_used'] else 'No'}\n"
            details += f"Success: {'Yes' if record['success'] else 'No'}\n"
            
            if record['error_message']:
                details += f"Error: {record['error_message']}\n"
            
            if record['metadata']:
                metadata = json.loads(record['metadata'])
                details += f"\nMetadata:\n"
                for key, value in metadata.items():
                    details += f"  {key}: {value}\n"
            
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", details)
    
    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all operation history?"):
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM operations')
            conn.commit()
            conn.close()
            self.refresh_history()
            self.status_var.set("History cleared")
    
    def export_history(self):
        import csv
        
        filename = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            history = self.db_manager.get_operation_history(limit=1000)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'timestamp', 'operation_type', 'input_file',
                             'output_file', 'data_size', 'encryption_used',
                             'success', 'error_message']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in history:
                    writer.writerow(record)
            
            messagebox.showinfo("Success", f"History exported to {filename}")
            self.status_var.set(f"Exported to {os.path.basename(filename)}")
    
    # ========== SETTINGS FUNCTIONS ==========
    
    def optimize_database(self):
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('VACUUM')
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Database optimized successfully")
        self.status_var.set("Database optimized")
    
    def backup_database(self):
        import shutil
        import datetime
        
        backup_dir = filedialog.askdirectory(title="Select Backup Directory")
        if backup_dir:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"steganography_backup_{timestamp}.db")
            
            shutil.copy2(self.db_manager.db_path, backup_path)
            messagebox.showinfo("Success", f"Database backed up to {backup_path}")
            self.status_var.set(f"Backed up to {os.path.basename(backup_path)}")
    
    def verify_integrity(self):
        filename = filedialog.askopenfilename(title="Select File to Verify")
        if filename:
            result = self.db_manager.verify_file_integrity(filename)
            
            if result['verified']:
                messagebox.showinfo("Integrity Verified",
                                  f"File integrity verified successfully!\n"
                                  f"Hash: {result['current_hash'][:16]}...")
                self.status_var.set("Integrity verified")
            else:
                messagebox.showwarning("Integrity Check Failed",
                                     f"File integrity could not be verified.\n"
                                     f"Error: {result.get('error', 'Unknown error')}")
                self.status_var.set("Integrity check failed")
    
    def save_settings(self):
        self.engine.max_threads = self.max_threads_var.get()
        self.engine.compression_level = self.compression_level_var.get()
        messagebox.showinfo("Success", "Settings saved successfully")
        self.status_var.set("Settings saved")
    
    def preview_image(self, image_path, label):
        try:
            img = Image.open(image_path)
            max_size = (200, 150)
            img.thumbnail(max_size)
            photo = ImageTk.PhotoImage(img)
            label.configure(image=photo, text='')
            label.image = photo
        except Exception as e:
            label.configure(text=f"Cannot preview: {str(e)[:30]}...")
    
    def on_tab_changed(self, event):
        notebook = event.widget
        tab_text = notebook.tab(notebook.select(), "text")
        
        if "History" in tab_text:
            self.refresh_history()
    
    def on_closing(self):
        self.db_manager.end_session(self.session_id)
        self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()


def main():
    app = SteganographyGUI()
    app.run()


if __name__ == "__main__":
    main()