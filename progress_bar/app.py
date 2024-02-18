from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from progress_bar import ProgressBar  # Предполагается, что ProgressBar определен в progress_bar.py

app = FastAPI()


class StartRequest(BaseModel):  # Измененное имя класса для большей ясности
    chat_id: int
    time: int  # Добавлено время в секундах
    process_name: str


class AbortRequest(BaseModel):
    chat_id: int


progress_bars = {}


@app.post("/start")
async def start_progress_bar(request: StartRequest):
    chat_id = int(request.chat_id)
    time = int(request.time)  # Время работы прогресс-бара
    process_name = str(request.process_name)
    print("прогресс бар", progress_bars)
    print("время которое передается", time)
    print("Процесс", process_name)
    if chat_id in progress_bars and progress_bars[chat_id].running:
        # Если прогресс-бар уже запущен, сначала останавливаем его
        await progress_bars[chat_id].abort()

    if chat_id not in progress_bars or not progress_bars[chat_id].running:
        # Создаем новый экземпляр ProgressBar или перезапускаем существующий
        progress_bars[chat_id] = ProgressBar(chat_id)
        await progress_bars[chat_id].start(process_name=process_name, time=time)
        print("message Прогресс-бар запущен.")
        return {"message": "Прогресс-бар запущен."}
    else:
        # В случае каких-либо ошибок или несоответствий
        return {"message": "Ошибка при попытке запуска прогресс-бара."}


@app.post("/abort")
async def abort_progress_bar(request: AbortRequest):
    chat_id = int(request.chat_id)
    if chat_id in progress_bars and progress_bars[chat_id].running:
        await progress_bars[chat_id].abort()
        return {"message": "Прогресс-бар остановлен."}
    else:
        raise HTTPException(status_code=404, detail="Прогресс-бар не найден или уже остановлен.")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
