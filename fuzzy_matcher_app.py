#!/usr/bin/env python3
"""
Fuzzy Matcher - Standalone Mac Application
A simple, self-contained fuzzy matching tool for Excel files.

Usage: Double-click the app, it will automatically find and process FuzzyMatch_Tool.xlsm
"""

import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox, filedialog
import pandas as pd
import logging
import glob
from pathlib import Path

# Import our fuzzy matching logic
from fuzzy_matcher import run_specific_match, preprocess_data


class FuzzyMatcherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fuzzy Matcher")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.setup_ui()
        
        # Redirect logging to GUI after UI is set up
        self.setup_logging_to_gui()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="🔍 Fuzzy Matcher", 
            font=("Arial", 18, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Description
        desc_text = (
            "This tool performs fuzzy matching on Excel data with three methods:\n"
            "• Full Name matching\n"
            "• Last Name + Address matching\n" 
            "• Full Address matching\n\n"
            "Click 'Auto-Find & Process' to automatically locate and process\n"
            "your FuzzyMatch_Tool.xlsm file, or 'Choose File' to select manually."
        )
        desc_label = tk.Label(self.root, text=desc_text, justify=tk.LEFT, pady=10)
        desc_label.pack()
        
        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # Auto-find button
        auto_button = tk.Button(
            button_frame,
            text="🎯 Auto-Find & Process",
            command=self.auto_find_and_process,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            width=20
        )
        auto_button.pack(pady=5)
        
        # Manual file selection button
        manual_button = tk.Button(
            button_frame,
            text="📁 Choose File",
            command=self.choose_file_and_process,
            bg="#2196F3", 
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
            width=20
        )
        manual_button.pack(pady=5)
        
        # Status text area
        self.status_text = tk.Text(
            self.root, 
            height=8, 
            width=60,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#f0f0f0"
        )
        self.status_text.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Add initial message
        self.log_message("Ready to process Excel files! 🚀")
        
    def log_message(self, message):
        """Add a message to the status text area"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
        
    def setup_logging_to_gui(self):
        """Redirect logging messages to the GUI text area"""
        class GUILogHandler(logging.Handler):
            def __init__(self, gui_app):
                super().__init__()
                self.gui_app = gui_app
                
            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Extract just the message part (remove timestamp and level)
                    if " - INFO - " in msg:
                        msg = msg.split(" - INFO - ", 1)[1]
                    self.gui_app.log_message(msg)
                except Exception:
                    pass  # Ignore logging errors
        
        # Add our custom handler to the root logger
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(gui_handler)
        
    def auto_find_and_process(self):
        """Automatically find and process the Excel file"""
        self.log_message("\n🔍 Searching for FuzzyMatch_Tool.xlsm...")
        
        # Search in common locations
        search_paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"), 
            os.path.expanduser("~/Downloads"),
            "/Applications",
            os.getcwd()
        ]
        
        found_files = []
        for search_path in search_paths:
            if os.path.exists(search_path):
                pattern = os.path.join(search_path, "**", "*FuzzyMatch*.xlsm")
                files = glob.glob(pattern, recursive=True)
                found_files.extend(files)
                
        if not found_files:
            self.log_message("❌ No FuzzyMatch_Tool.xlsm found in common locations")
            self.log_message("📁 Please use 'Choose File' to select manually")
            return
            
        if len(found_files) == 1:
            file_path = found_files[0]
            self.log_message(f"✅ Found: {os.path.basename(file_path)}")
            self.process_file(file_path)
        else:
            self.log_message(f"📋 Found {len(found_files)} files:")
            for f in found_files:
                self.log_message(f"  • {f}")
            self.log_message("🎯 Using the first one...")
            self.process_file(found_files[0])
            
    def choose_file_and_process(self):
        """Let user choose the Excel file manually"""
        file_path = filedialog.askopenfilename(
            title="Select FuzzyMatch_Tool.xlsm file",
            filetypes=[("Excel files", "*.xlsm *.xlsx"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            self.log_message(f"📁 Selected: {os.path.basename(file_path)}")
            self.process_file(file_path)
        else:
            self.log_message("❌ No file selected")
            
    def process_file(self, file_path):
        """Process the selected Excel file"""
        try:
            self.log_message(f"\n🔧 Processing: {os.path.basename(file_path)}")
            
            # Read all sheets
            self.log_message("📊 Reading Excel sheets...")
            all_sheets = pd.read_excel(file_path, sheet_name=None)
            
            # Filter out results sheets
            data_sheets = {k: v for k, v in all_sheets.items() 
                          if not k.startswith('results_') and not k.startswith('Unmatched_')}
            
            if len(data_sheets) < 2:
                self.log_message("❌ Need at least 2 data sheets to compare")
                return
                
            self.log_message(f"📋 Found {len(data_sheets)} data sheets:")
            for sheet_name, df in data_sheets.items():
                self.log_message(f"  • {sheet_name}: {len(df)} rows")
                
            # Auto-detect input vs master based on size
            sheet_names = list(data_sheets.keys())
            sheet1_df = data_sheets[sheet_names[0]]
            sheet2_df = data_sheets[sheet_names[1]]
            
            if len(sheet1_df) > len(sheet2_df):
                master_df = sheet1_df
                input_df = sheet2_df
                master_name = sheet_names[0]
                input_name = sheet_names[1]
            else:
                master_df = sheet2_df
                input_df = sheet1_df
                master_name = sheet_names[1]
                input_name = sheet_names[0]
                
            self.log_message(f"📊 INPUT: {input_name} ({len(input_df)} rows)")
            self.log_message(f"📊 MASTER: {master_name} ({len(master_df)} rows)")
            
            # Preprocess data
            self.log_message("🔧 Preprocessing data...")
            df1 = preprocess_data(input_df)
            df2 = preprocess_data(master_df)
            
            # Run fuzzy matching
            match_types = ['FullName', 'LastNameAddress', 'FullAddress']
            results = {}
            
            for match_type in match_types:
                self.log_message(f"\n🎯 Running {match_type} matching...")
                self.root.update()  # Keep UI responsive
                
                results_df = run_specific_match(df1, df2, match_type)
                results[match_type] = results_df
                
                if not results_df.empty:
                    self.log_message(f"✅ Found {len(results_df)} {match_type} matches")
                else:
                    self.log_message(f"⚠️  No {match_type} matches found")
                    
            # Write results to a NEW file to avoid corruption  
            self.log_message("\n💾 Writing results to new Excel file...")
            
            # Create a new filename with timestamp to avoid conflicts
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            new_filename = f"{base_name}_RESULTS_{timestamp}.xlsx"
            new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
            
            self.log_message(f"📁 Creating results file: {new_filename}")
            
            # Copy original data and add results
            try:
                with pd.ExcelWriter(new_file_path, engine='openpyxl') as writer:
                    # Copy original sheets first
                    for sheet_name, df in data_sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # Auto-resize columns for original data sheets too
                        worksheet = writer.sheets[sheet_name]
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                        
                        self.log_message(f"📋 Copied '{sheet_name}' sheet with auto-sized columns")
                    
                    # Add results sheets
                    for match_type, results_df in results.items():
                        if not results_df.empty:
                            sheet_name = f'results_{match_type}'
                            results_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            # Auto-resize columns to show full data
                            worksheet = writer.sheets[sheet_name]
                            for column in worksheet.columns:
                                max_length = 0
                                column_letter = column[0].column_letter
                                for cell in column:
                                    try:
                                        if len(str(cell.value)) > max_length:
                                            max_length = len(str(cell.value))
                                    except:
                                        pass
                                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                                worksheet.column_dimensions[column_letter].width = adjusted_width
                            
                            self.log_message(f"📝 Created '{sheet_name}' sheet with auto-sized columns")
                
                self.log_message(f"✅ Successfully wrote file: {new_file_path}")
                    
            except Exception as write_error:
                self.log_message(f"❌ FAILED TO WRITE RESULTS FILE: {write_error}")
                self.log_message(f"Traceback: {traceback.format_exc()}")
                raise write_error
                        
            self.log_message("\n🎉 FUZZY MATCHING COMPLETED SUCCESSFULLY! 🎉")
            self.log_message(f"📊 Results saved to: {new_filename}")
            
            # Show completion dialog
            messagebox.showinfo(
                "Success!", 
                f"Fuzzy matching completed!\n\n"
                f"NEW FILE CREATED:\n{new_filename}\n\n"
                f"Your original file is safe!\n"
                f"Check the new 'results_*' sheets for your matches."
            )
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
            self.log_message(error_msg)
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
            
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point for the standalone app"""
    try:
        app = FuzzyMatcherApp()
        app.run()
    except Exception as e:
        # Fallback error handling if GUI fails
        print(f"Critical error: {e}")
        print(traceback.format_exc())
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()