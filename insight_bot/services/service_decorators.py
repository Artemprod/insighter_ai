import asyncio
from functools import wraps

def progress_bar_decorator(bot, chat_id, timer, process_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def update_progress_bar():
                empty_bar_char = '▱'
                filled_bar_char = '▰'
                total_length = 18  # Общая длина прогресс-бара

                progress_message = await bot.send_message(
                    chat_id,
                    f"<b>Процесс:</b> <i>{process_name}</i>\n\n"
                    f"Прогресс: [{empty_bar_char * total_length}] <b>0%</b>",
                    parse_mode='HTML'
                )

                for i in range(1, timer * 60 + 1):
                    progress = (i / (timer * 60)) * 100
                    filled_length = int(total_length * i // (timer * 60))

                    bar = filled_bar_char * filled_length + empty_bar_char * (total_length - filled_length)
                    progress_text = (
                        f"<b>Процесс:</b> <i>{process_name}</i>\n\n"
                        f"Прогресс: [{bar}] <b>{progress:.1f}%</b>"
                    )

                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message.message_id,
                        text=progress_text,
                        parse_mode='HTML'
                    )

                    await asyncio.sleep(1)  # Ожидание перед следующим обновлением

                # Финальное обновление прогресс-бара
                final_text = f"<b>Процесс:</b> <i>{process_name}</i> завершен."
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=progress_message.message_id,
                    text=final_text,
                    parse_mode='HTML'
                )

            progress_task = asyncio.create_task(update_progress_bar())
            func_task = asyncio.create_task(func(*args, **kwargs))

            # Ждем, пока одна из задач не будет завершена
            done, pending = await asyncio.wait(
                {progress_task, func_task},
                return_when=asyncio.FIRST_COMPLETED
            )

            # Отменяем все незавершенные задачи
            for task in pending:
                task.cancel()

            if func_task in done:
                # Функция завершилась до истечения таймера
                return await func_task
            else:
                # Истекло время ожидания, функция не завершилась
                return None

        return wrapper
    return decorator

async def progress_bar(bot, chat_id, timer, process_name, func_done):
    # Настройка символов для прогресс-бара
    empty_bar_char = '▱'
    filled_bar_char = '▰'
    total_length = 18  # Общая длина прогресс-бара

    # Отправляем начальное сообщение с прогресс-баром
    progress_message = await bot.send_message(
        chat_id,
        f"<b>Процесс:</b> <i>{process_name}</i>\n\n"
        f"Прогресс: [{empty_bar_char * total_length}] <b>0%</b>",
        parse_mode='HTML'
    )

    try:
        for i in range(1, timer * 60 + 1):
            # if func_done.is_set():
            #     break  # Прерываем цикл, если функция выполнена

            # Расчет процента выполнения
            progress = (i / (timer * 60)) * 100
            filled_length = int(total_length * i // (timer * 60))

            # Обновление прогресс-бара
            bar = filled_bar_char * filled_length + empty_bar_char * (total_length - filled_length)
            progress_text = (
                f"<b>Процесс:</b> <i>{process_name}</i>\n\n"
                f"Прогресс: [{bar}] <b>{progress:.1f}%</b>"
            )

            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=progress_message.message_id,
                    text=progress_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Ошибка при обновлении прогресс-бара: {e}")

            await asyncio.sleep(1)  # Ожидание перед следующим обновлением
    finally:
        # Обновление сообщения с прогресс-баром после завершения функции
        final_text = f"<b>Процесс:</b> <i>{process_name}</i> завершен."
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.message_id,
            text=final_text,
            parse_mode='HTML'
        )

