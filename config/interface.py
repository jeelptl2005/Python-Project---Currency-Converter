import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime
from ..core.converter import CurrencyConverter
from ..core.exceptions import InvalidCurrencyError, APIError
from ..utils.logger import get_logger
from ..utils.helpers import validate_amount

logger = get_logger(__name__)

class CurrencyConverterGUI:
    def __init__(self, root: tk.Tk, converter: CurrencyConverter, config: dict):
        self.root = root
        self.converter = converter
        self.config = config
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Professional Currency Converter")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use(self.config.get('theme', 'clam'))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Amount entry
        ttk.Label(main_frame, text="Amount:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar(value="1.00")
        self.amount_entry = ttk.Entry(main_frame, textvariable=self.amount_var)
        self.amount_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # From currency
        ttk.Label(main_frame, text="From:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.from_currency_var = tk.StringVar(value=self.config.get('default_from_currency', 'USD'))
        self.from_currency_combobox = ttk.Combobox(main_frame, textvariable=self.from_currency_var)
        self.from_currency_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # To currency
        ttk.Label(main_frame, text="To:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.to_currency_var = tk.StringVar(value=self.config.get('default_to_currency', 'EUR'))
        self.to_currency_combobox = ttk.Combobox(main_frame, textvariable=self.to_currency_var)
        self.to_currency_combobox.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Swap button
        self.swap_button = ttk.Button(main_frame, text="↔ Swap", command=self.swap_currencies)
        self.swap_button.grid(row=1, column=2, rowspan=2, padx=5, pady=5)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert", command=self.perform_conversion)
        self.convert_button.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Result display
        self.result_var = tk.StringVar(value="")
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        ttk.Label(result_frame, text="Result:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.result_label = ttk.Label(result_frame, textvariable=self.result_var, font=('Arial', 12))
        self.result_label.pack(side=tk.LEFT, padx=5)
        
        # Historical data
        historical_frame = ttk.LabelFrame(main_frame, text="Historical Data (Optional)", padding=10)
        historical_frame.grid(row=5, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        ttk.Label(historical_frame, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.historical_date_var = tk.StringVar()
        self.historical_date_entry = ttk.Entry(historical_frame, textvariable=self.historical_date_var, width=12)
        self.historical_date_entry.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(
            row=6, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Bind events
        self.amount_entry.bind('<Return>', lambda e: self.perform_conversion())
        self.from_currency_combobox.bind('<Return>', lambda e: self.perform_conversion())
        self.to_currency_combobox.bind('<Return>', lambda e: self.perform_conversion())
        
        # Initialize currencies
        self.root.after(100, self.initialize_currencies)
    
    def swap_currencies(self):
        from_curr = self.from_currency_var.get()
        to_curr = self.to_currency_var.get()
        self.from_currency_var.set(to_curr)
        self.to_currency_var.set(from_curr)
    
    async def initialize_currencies(self):
        self.status_var.set("Loading currencies...")
        self.root.config(cursor="watch")
        try:
            currencies = await self.converter.get_supported_currencies()
            self.from_currency_combobox['values'] = currencies
            self.to_currency_combobox['values'] = currencies
            self.status_var.set(f"Loaded {len(currencies)} currencies")
        except Exception as e:
            logger.error(f"Failed to load currencies: {str(e)}")
            messagebox.showerror("Error", f"Failed to load currencies: {str(e)}")
            self.status_var.set("Currency load failed")
        finally:
            self.root.config(cursor="")
    
    def perform_conversion(self):
        amount = self.amount_var.get()
        from_curr = self.from_currency_var.get()
        to_curr = self.to_currency_var.get()
        date_str = self.historical_date_var.get() or None
        
        if not validate_amount(amount):
            messagebox.showerror("Error", "Please enter a valid amount")
            return
        
        if not from_curr or not to_curr:
            messagebox.showerror("Error", "Please select both currencies")
            return
        
        self.root.after(100, lambda: self._async_perform_conversion(amount, from_curr, to_curr, date_str))
    
    async def _async_perform_conversion(self, amount: str, from_curr: str, to_curr: str, date_str: Optional[str]):
        self.status_var.set("Converting...")
        self.root.config(cursor="watch")
        try:
            result = await self.converter.convert(amount, from_curr, to_curr, date_str)
            self.result_var.set(f"{amount} {from_curr} = {result:.4f} {to_curr}")
            self.status_var.set("Conversion successful")
        except InvalidCurrencyError as e:
            messagebox.showerror("Error", f"Invalid currency: {str(e)}")
            self.status_var.set("Invalid currency")
        except APIError as e:
            messagebox.showerror("Error", f"API error: {str(e)}")
            self.status_var.set("API error")
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            self.status_var.set("Conversion failed")
        finally:
            self.root.config(cursor="")
