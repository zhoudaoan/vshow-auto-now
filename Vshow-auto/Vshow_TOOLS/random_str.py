import random
import string


def create_string_number(n):
    """生成一个以字母开头的五位字符串"""
    m = random.randint(1, n)
    a = "".join([str(random.randint(0, 9)) for _ in range(m)])
    b = "".join([random.choice(string.ascii_letters) for _ in range(n - m)])
    return random.choice(string.ascii_letters) + ''.join(random.sample(list(b + a), n))


def generate_random_chinese(length: int = 50) -> str:
    """生成指定长度的随机中文字符串"""
    return ''.join(
        chr(random.randint(0x4e00, 0x9fff)) for _ in range(length)
    )