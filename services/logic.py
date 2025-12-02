import random
import aiohttp


async def check_username_exists(username: str) -> bool:
    """Check if Telegram username exists via t.me page."""
    clean_username = username.lstrip("@")
    url = f"https://t.me/{clean_username}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False
                
                html = await response.text()
                # Если юзернейм не существует, в HTML будет сообщение о том, что можно связаться
                # Если существует — будет информация о профиле
                return "tgme_page_photo" in html or "tgme_page_title" in html
    except Exception:
        # В случае ошибки сети — пропускаем проверку
        return True


def get_valuation_data(username: str) -> dict:
    """Generate valuation data for a Telegram username."""
    
    categories = [
        "Premium Real Word", "Crypto Native", "Corporate Brand", 
        "Luxury Personal", "Web3 Identity", "Short & Concise", 
        "Tech Startup", "Global Asset", "Visual Symmetric", "Investment Grade"
    ]
    rarities = [
        "High", "Very High", "Ultra Rare", "Exclusive", 
        "Collector's Item", "Legendary", "Blue Chip", "Top Tier"
    ]
    demands = [
        "Strong", "Very High", "Aggressive", "Trending Up", 
        "Peak Interest", "Institutional", "Hot Market"
    ]
    brandings = [
        "Excellent", "Global", "Elite", "Unicorn Status", 
        "International", "Corporate Grade", "Iconic"
    ]
    
    # Remove @ if present
    clean_username = username.lstrip("@")
    
    # Calculate values
    aesthetic_score = round(random.uniform(8.2, 9.9), 1)
    price_low = round(random.randint(1100, 3500), -1)
    price_high = price_low + random.randint(500, 1500)
    
    if price_high > 4500:
        price_high = 4200
    
    return {
        "username": f"@{clean_username}",
        "structure": f"{len(clean_username)} characters",
        "category": random.choice(categories),
        "rarity": random.choice(rarities),
        "demand": random.choice(demands),
        "score": str(aesthetic_score),
        "branding": random.choice(brandings),
        "price_low": price_low,
        "price_high": price_high,
    }
