def make_delivery_works_done_msg(delivery_name: str, works_dict: dict):
    msg = ""
    for product, works in works_dict.items():
        msg += f"Товар: {works.get("name")}\nПорядковый номер: {works.get('order')}\n"
        for work in works.get("works_done", {}).values():
            msg += f"  - {work}\n"
        msg += "\n"
    if msg:
        msg = f"\nВыполненные работы:\n{msg}\n"
    msg = f"Поставка:{delivery_name}\n{msg}"
    return msg


def make_delivery_works_staged_msg(staged_works_dict: dict):
    msg = ""
    for work in staged_works_dict.values():
        msg += f"✅{work}\n"
    if msg:
        msg = f"\n\nЗаполняемые работы:\n{msg}\n"
    return msg