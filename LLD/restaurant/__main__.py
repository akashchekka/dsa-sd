from __future__ import annotations

from models.menu import Menu
from models.order import Priority
from services.restaurant import Restaurant

def build_menu() -> Menu:
    menu = Menu()
    menu.add("Burger", 8.0)
    menu.add("Fries", 3.5)
    menu.add("Salad", 6.0)
    menu.add("Pizza", 11.0)
    menu.add("Steak", 15.0)
    menu.add("Soup", 5.0)
    return menu


def main() -> None:
    restaurant = Restaurant(build_menu(), num_cooks=2)

    restaurant.place_order(table_id=1, item_names=["Burger", "Fries"])
    restaurant.place_order(table_id=2, item_names=["Pizza"])
    restaurant.place_order(table_id=3, item_names=["Salad", "Soup"], priority=Priority.VIP)
    restaurant.place_order(table_id=4, item_names=["Steak"], priority=Priority.VIP)
    restaurant.place_order(table_id=5, item_names=["Fries"])

    restaurant.close()
    print("kitchen closed")


if __name__ == "__main__":
    main()
