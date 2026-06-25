from src.scrapping.scrapping_page import scrapping_page
from src.models.store_config import StoreConfig
from src.scrapping.store_enum import Stores
import asyncio

# Paginas de categoria por tienda
stores_list: list[StoreConfig] = [
    StoreConfig(
        Stores.FALLABELLA, 
        ["https://www.falabella.com.pe/falabella-pe/category/cat1470534/Zapatillas-urbanas-mujer"]
    ),
    StoreConfig(
        Stores.OECHSLE, 
        ["https://www.oechsle.pe/tecnologia/"]
    )
]

if __name__ == "__main__":
    asyncio.run(scrapping_page(stores_list)) 
    
