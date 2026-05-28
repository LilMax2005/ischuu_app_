from __future__ import annotations

from app.frontend.models.entities import Product, User

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
        image="https://images.unsplash.com/photo-1674448417295-088682b6adec?q=80&w=735&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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
        image="https://images.unsplash.com/photo-1592547097938-7942b22df3db?q=80&w=1471&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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
        image="https://images.unsplash.com/photo-1705912090259-195fd30509e2?q=80&w=698&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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
        image="https://images.unsplash.com/photo-1697479670670-d2a299df749c?q=80&w=1145&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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
        image="https://media.falabella.com/falabellaCL/149893043_01/w=1200,h=1200,fit=pad",
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
        image="https://images.unsplash.com/photo-1641831705160-5d56ac4094cb?q=80&w=880&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
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
