def make_delivery_view_message(marketplace_name: str, delivery_data: dict):
    msg = f"Маркетплейс:\n<b>{marketplace_name}</b>\n\n"
    msg += f"Поставка:\n<b>{delivery_data.get('name')}</b>\n\n"
    delivery_works = dict()
    for category in delivery_data.get("categories", dict()).values():
        cat_name = category.get("name")
        msg += f"<b>{cat_name}:</b>\n"
        for product in category.get("products", {}).values():
            for work in product.get("works", {}).values():
                delivery_works.setdefault(cat_name, {})
                delivery_works[cat_name].setdefault(work.get("name"), [])
                delivery_works[cat_name][work.get("name")].append(str(product.get("order")))
        msg += f"{'\n'.join([f'<i>{work_type}</i>:\n{', '.join(products)}' for work_type, products in delivery_works[cat_name].items()])}"
    msg += "\n\n"
    return msg



def make_confirmed_delete_message(staged_delivery):
    confirmed_works = dict()
    got_confirmed_works = False
    for cat in staged_delivery.get("categories").values():
        cat_name = cat.get("name")
        confirmed_works.setdefault(cat_name, dict())
        for product in cat.get("products", {}).values():
            for work in product.get("deleted_works", dict()).values():
                got_confirmed_works = True
                work_name = work.get("name")
                confirmed_works[cat_name].setdefault(work_name, [])
                confirmed_works[cat_name][work_name].append(product.get("order"))
    if got_confirmed_works:
        confirmed_msg = f"Удаляемые работы из поставки {staged_delivery['name']}:\n"
        for cat, works in confirmed_works.items():
            confirmed_msg += f"{cat}:\n"
            for work_name, products in works.items():
                confirmed_msg += f"{work_name}:\n"
                confirmed_msg += ", ".join([str(p_o) for p_o in products]) + "\n"
    else:
        confirmed_msg = ''
    return confirmed_msg