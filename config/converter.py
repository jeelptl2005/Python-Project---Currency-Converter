import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Union
from .exceptions import InvalidCurrencyError, APIError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CurrencyConverter:
    def __init__(self, api_client, cache_dir: Path = Path(".cache")):
        self.api_client = api_client
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.rates: Dict[str, Dict] = {}
        
    def _get_cache_file(self, base_currency: str) -> Path:
        return self.cache_dir / f"{base_currency.upper()}_rates.json"
    
    def _load_cached_rates(self, base_currency: str) -> Optional[Dict]:
        cache_file = self._get_cache_file(base_currency)
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if datetime.now() < datetime.fromisoformat(data['expires_at']):
                    return data
        return None
    
    def _save_rates_to_cache(self, base_currency: str, rates: Dict, expires_at: datetime):
        cache_file = self._get_cache_file(base_currency)
        data = {
            'base': rates['base'],
            'rates': rates['rates'],
            'date': rates.get('date', str(datetime.now().date())),
            'expires_at': expires_at.isoformat()
        }
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    
    async def get_exchange_rates(self, base_currency: str) -> Dict:
        base_currency = base_currency.upper()
        
        # Try to load from cache first
        cached_data = self._load_cached_rates(base_currency)
        if cached_data:
            logger.info(f"Using cached rates for {base_currency}")
            return cached_data
        
        # Fetch from API if cache is expired or missing
        try:
            logger.info(f"Fetching fresh rates for {base_currency}")
            rates = await self.api_client.get_rates(base_currency)
            expires_at = datetime.now() + timedelta(seconds=self.api_client.cache_timeout)
            self._save_rates_to_cache(base_currency, rates, expires_at)
            return rates
        except Exception as e:
            logger.error(f"Failed to fetch rates: {str(e)}")
            raise APIError(f"Could not fetch exchange rates: {str(e)}")
    
    async def convert(
        self, 
        amount: Union[float, str], 
        from_currency: str, 
        to_currency: str,
        date: Optional[str] = None
    ) -> float:
        try:
            amount = float(amount)
        except ValueError:
            raise ValueError("Amount must be a number")
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return amount
        
        rates = await self.get_exchange_rates(from_currency)
        
        if to_currency not in rates['rates']:
            raise InvalidCurrencyError(f"Currency {to_currency} not found in rates")
        
        return amount * rates['rates'][to_currency]
    
    async def get_supported_currencies(self) -> list:
        rates = await self.get_exchange_rates('USD')  # Using USD as base to get all currencies
        return list(rates['rates'].keys())
