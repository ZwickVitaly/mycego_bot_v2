def make_delivery_works_done_msg(delivery_name: str, works_dict: dict):
    msg = ""
    for c_name, c in works_dict.items():
        msg += f"<b>{c_name}</b>:\n"
        for work_name, work_products in c.items():
            msg += f"{work_name}:\n"
            msg += ", ".join(work_products)
            msg += "\n"
    if msg:
        msg = f"\n<b>Выполненные работы</b>:\n\n{msg}\n"
    msg = f"Поставка:{delivery_name}\n{msg}"
    return msg


def make_delivery_works_staged_msg(staged_works_dict: dict):
    msg = ""
    for work in staged_works_dict.values():
        msg += f"✅{work}\n"
    if msg:
        msg = f"\n\nВыбранные работы:\n{msg}\n"
    return msg
