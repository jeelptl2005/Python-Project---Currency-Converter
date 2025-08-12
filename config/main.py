import asyncio
import tkinter as tk
from pathlib import Path
import configparser
from core.api_client import APIClient
from core.converter import CurrencyConverter
from gui.interface import CurrencyConverterGUI
from utils.logger import setup_logging

def load_config():
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent / 'config/config.ini')
    return config

async def main():
    # Setup logging
    setup_logging()
    
    # Load configuration
    config = load_config()
    
    # Initialize API client
    api_client = APIClient(
        base_url=config['API']['base_url'],
        api_key=config['API']['api_key'],
        cache_timeout=int(config['API']['cache_timeout'])
    )
    
    # Initialize converter
    converter = CurrencyConverter(api_client)
    
    # Create and run GUI
    root = tk.Tk()
    gui_config = {
        'default_from_currency': config['GUI']['default_from_currency'],
        'default_to_currency': config['GUI']['default_to_currency'],
        'theme': config['GUI']['theme']
    }
    app = CurrencyConverterGUI(root, converter, gui_config)
    
    # Run the main loop
    while True:
        try:
            root.update()
            await asyncio.sleep(0.1)
        except tk.TclError:
            break  # Window closed

if __name__ == "__main__":
    asyncio.run(main())
