import re


def is_valid_russian_phone_number(phone_number):
    """
  Проверяет, является ли введенный текст номером телефона в России.

  Args:
    phone_number: Строка с номером телефона.

  Returns:
    True, если номер телефона действителен, False - в противном случае.
  """

    pattern = r"^7\d{10}$"
    return re.match(pattern, phone_number) is not None