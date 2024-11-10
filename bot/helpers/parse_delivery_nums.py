from settings import logger


def try_parse_delivery_works_nums(message: str):
    pre_nums = message.split(",")
    logger.info(pre_nums)
    nums = []
    for num in pre_nums:
        if "-" in num:
            result = num.split("-")
            if len(result) != 2:
                raise ValueError
            logger.info(result)
            left, right = result[0].strip(), result[1].strip()
            if len(left) > 2 or len(right) > 2:
                raise ValueError
            left, right = int(left), int(right)
            if left > right:
                left, right = right, left
            nums.extend(list(range(left, right + 1)))
        else:
            num = num.strip()
            if len(num) > 2:
                raise ValueError
            num = int(num)
            if num <= 0:
                raise ValueError
            nums.append(num)
    nums = list(set(nums))
    nums.sort()
    return nums
