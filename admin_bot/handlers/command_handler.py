from aiogram.filters import CommandStart
from aiogram import Router, Bot
from aiogram.types import Message


from keyboards.inline_keyboards import crete_inline_keyboard_options




router = Router()


@router.message(CommandStart(), )
async def process_start_command(message: Message):
    option_keyboard = crete_inline_keyboard_options()
    await message.answer(text='что хочешь сделать', reply_markup=option_keyboard)
