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
from fuzzy_matcher import (
    run_specific_match,
    preprocess_data,
    preprocess_input_variable,
    preprocess_master_with_opens,
    SchemaError,
)


class FuzzyMatcherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fuzzy Matcher")
        self.root.geometry("650x500")
        self.root.resizable(True, True)
        self.root.minsize(500, 400)
        
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
        
        # Main process button
        process_button = tk.Button(
            button_frame,
            text="📁 Select Excel File & Process",
            command=self.choose_file_and_process,
            bg="#E8F5E8", 
            fg="black",
            font=("Arial", 14, "bold"),
            padx=25,
            pady=15,
            width=25,
            relief="raised",
            bd=2
        )
        process_button.pack(pady=10)
        
        # Status text area with scrollbar
        text_frame = tk.Frame(self.root)
        text_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(
            text_frame, 
            height=12, 
            width=70,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#f0f0f0",
            font=("Courier", 10)
        )
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
            
            # Preprocess data (variable input schema)
            self.log_message("🔧 Preprocessing data (variable input schema)...")
            try:
                df1, report = preprocess_input_variable(input_df, file=file_path, sheet=input_name)
            except SchemaError as se:
                self.log_message(str(se))
                return

            df2, opens_missing = preprocess_master_with_opens(master_df)
            
            # Run fuzzy matching
            # Determine enabled match types from report
            all_types = ['FullName', 'LastNameAddress', 'FullAddress']
            match_types = []
            for mt in all_types:
                if report.get(mt, {}).get('enabled'):
                    match_types.append(mt)
                else:
                    reason = report.get(mt, {}).get('reason')
                    self.log_message(f"⏭️  Skipping {mt}: {reason}")
            results = {}
            
            for i, match_type in enumerate(match_types, 1):
                self.log_message(f"\n🎯 Running {match_type} matching... ({i}/3)")
                self.root.update()  # Keep UI responsive
                
                results_df = run_specific_match(df1, df2, match_type)
                results[match_type] = results_df
                
                self.root.update()  # Update GUI after processing
                
                if not results_df.empty:
                    self.log_message(f"✅ Found {len(results_df)} {match_type} matches")
                else:
                    self.log_message(f"⚠️  No {match_type} matches found")
                    
                self.root.update()  # Ensure message appears immediately
                    
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
                            # Append Opens as rightmost column when available or blank with reason if missing
                            if 'Opens' in df2.columns:
                                results_df = results_df.copy()
                                # Merge Opens from master by 'Sheet B Row' (Excel 1-based)
                                # Convert to 0-based index for df2 alignment
                                try:
                                    opens_map = df2['Opens']
                                    results_df['Opens'] = results_df['Sheet B Row'].apply(lambda r: opens_map.iloc[int(r) - 2] if 0 <= int(r) - 2 < len(opens_map) else "")
                                except Exception:
                                    results_df['Opens'] = ""
                            else:
                                results_df = results_df.copy()
                                results_df['Opens'] = ""  # OPENS_NO_MATCH case
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
                            
                            if opens_missing:
                                self.log_message(f"📝 Created '{sheet_name}' with 'Opens' blank (OPENS_NO_MATCH)")
                            else:
                                self.log_message(f"📝 Created '{sheet_name}' with 'Opens' column appended")
                
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