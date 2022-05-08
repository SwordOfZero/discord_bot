def check_skill_point(message):
    summ = 0
    if len(message) == 6:
        for i in message:
            if 8 <= i <= 15:
                check = i - 8
                if check > 5:
                    summ += (check - 5) * 2 + 5
                else:
                    summ += check
            else:
                summ -= 100
        if 0 <= summ <= 27 and sum(message) >= 48:
            return message
        else:
            return None
    else:
        return None