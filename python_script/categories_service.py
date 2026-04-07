import asyncio
import os
import uuid
import psycopg

from commands import CommandService, Command, CommandArg, Commands
from model import Category


class CategoriesService(CommandService):
    """Responsible for: \n
        - keeping track of all categories
        - adding/deleting categories
    """

    categories: list[Category]

    def load_categories(self):
        """loads categories from database"""
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                SELECT id, name FROM categories
                """)
                # map tuples to category
                categories = [Category(id=c[0], name=c[1]) for c in cur.fetchall()]
            conn.close()
        self.categories = categories

    def get_categories(self):
        """Returns list of categories"""
        return self.categories

    def add_category(self, name: str):
        """Adds a new category"""
        category = Category(id=uuid.uuid4(), name=name)
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO categories (id, name) VALUES (%s, %s)
                """, (category.id, name))
            conn.commit()
            conn.close()
        self.categories.append(category)

    def remove_category(self, name: str):
        """Removes category by name"""
        # remove from database
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            DELETE FROM categories WHERE name = %s
                            """, [name])
            conn.commit()
            conn.close()
        # remove from cache
        self.categories = [c for c in self.categories if c.name != name]

    def get_commands(self) -> list[Command]:
        return [
            Command(name=Commands.LOAD_CATEGORIES,
                    description="Reload spending categories",
                    args=[],
                    ),
            Command(name=Commands.ADD_CATEGORY,
                    description="Adds a new spending category",
                    args=[
                            CommandArg("category_name"),
                        ],
                    ),
            Command(name=Commands.REMOVE_CATEGORY,
                    description="Removes a spending category",
                    args=[
                            CommandArg("category_name",
                                       lambda : [c.name for c in self.get_categories()])
                        ],
                    ),
        ]

    async def execute(self, command: str, args: dict[str, str], app) -> None:
        if command == Commands.LOAD_CATEGORIES:
            app.text_area.start_loading("Reloading categories...")
            await asyncio.to_thread(self.load_categories)
            app.text_area.stop_loading("Reloaded categories from database")
        elif command == Commands.ADD_CATEGORY:
            app.text_area.start_loading(f"Adding {args.get("category_name")} category...")
            await asyncio.to_thread(self.add_category, args.get("category_name"))
            app.text_area.stop_loading(f"Added {args.get("category_name")} category")
        elif command == Commands.REMOVE_CATEGORY:
            app.text_area.start_loading(f"Removing {args.get("category_name")} category...")
            await asyncio.to_thread(self.remove_category, args.get("category_name"))
            app.text_area.stop_loading(f"Removed {args.get("category_name")} category")
