from registration import is_registered

def require_registration(bot):
    def decorator(func):
        def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id

            if not is_registered(user_id):
                bot.reply_to(
                    message,
                    "❌ Команда /find доступна только зарегистрированным пользователям.\n"
                    "Зарегистрируйся: /register"
                )
                return

            return func(message, *args, **kwargs)
        return wrapper
    return decorator

