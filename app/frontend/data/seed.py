from __future__ import annotations

from app.models.entities import Product, User

PRODUCTS: list[Product] = [
    Product(
        id="1",
        name="Blind Box Naruto Shippuden",
        series="Naruto",
        price=12990,
        stock=10,
        category="Anime",
        rarity="Épica",
        description="Caja sorpresa con figuras coleccionables de Naruto.",
        is_original=True,
        image="https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=800",
    ),
    Product(
        id="2",
        name="Blind Box One Piece Wanted",
        series="One Piece",
        price=14990,
        stock=8,
        category="Anime",
        rarity="Legendaria",
        description="Colección inspirada en personajes icónicos de One Piece.",
        is_original=True,
        image="https://images.unsplash.com/photo-1569705466238-7fef662aa89b?w=800",
    ),
    Product(
        id="3",
        name="Blind Box Demon Slayer Mini",
        series="Kimetsu no Yaiba",
        price=11990,
        stock=15,
        category="Anime",
        rarity="Rara",
        description="Serie mini con personajes de Demon Slayer.",
        is_original=False,
        image="https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800",
    ),
    Product(
        id="4",
        name="Blind Box Minecraft Mobs",
        series="Minecraft",
        price=9990,
        stock=20,
        category="Videojuegos",
        rarity="Común",
        description="Figuras sorpresa de mobs y personajes de Minecraft.",
        is_original=False,
        image="https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800",
    ),
    Product(
        id="5",
        name="Blind Box Genshin Impact",
        series="Genshin Impact",
        price=15990,
        stock=9,
        category="Videojuegos",
        rarity="Épica",
        description="Blind box premium con personajes de Genshin Impact.",
        is_original=True,
        image="https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800",
    ),
    Product(
        id="6",
        name="Blind Box Studio Ghibli",
        series="Ghibli",
        price=13990,
        stock=12,
        category="Series/Películas",
        rarity="Rara",
        description="Colección temática de Studio Ghibli.",
        is_original=True,
        image="https://images.unsplash.com/photo-1535016120720-40c646be5580?w=800",
    ),
]

DEFAULT_USERS: dict[str, User] = {
    "demo@ischuu.cl": User(
        name="Cliente Demo",
        email="demo@ischuu.cl",
        password="1234",
        points=120,
        notifications_enabled=True,
        favorite_categories=["Anime", "Videojuegos"],
    )
}
