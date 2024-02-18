from DB.Mongo.mongo_db import MongoORMConnection, MongoAssistantRepositoryORM, MongoUserRepoORM, UserDocsRepoORM
from api.progress_bar.command import ProgressBarClient
from config.bot_configs import load_bot_config, Config
from main_process.ChatGPT.gpt_dispatcher import TextTokenizer, OneRequestGPTWorker, BigDataGPTWorker, GPTDispatcher
from main_process.ChatGPT.gpt_models_information import GPTModelManager
from main_process.Whisper.openai_whisper_complain import WhisperClient
from main_process.Whisper.whisper_dispatcher import ShortMediaFilesTranscriber, LongMediaFilesTranscriber, \
    MediaRecognitionFactory
from main_process.Whisper.whisper_information import WhisperModelManager
from main_process.file_format_manager import TelegramServerFileFormatDefiner
from main_process.file_manager import TelegramMediaFileManager, ServerFileManager
from main_process.media_file_manager import MediaFileManager
# from main_process.pre_processing import SpacyTextPreprocessor, TextPreprocessorAggregator
from main_process.process_pipline import PipelineQueues, ProcesQueuePipline
from main_process.text_invoke import PdfFileHandler, TxtFileHandler, VideoFileHandler, AudioFileHandler, \
    TextInvokeFactory, FORMATS

# ______FORMATS____________________________________________
formats = FORMATS()
# ______CONFIGS____________________________________________
config_data: Config = load_bot_config('.env')
# ______DATABASE ____________________________________________

MongoORMConnection(config_data.data_base, system_type=config_data.system.system_type)
assistant_repository = MongoAssistantRepositoryORM()
user_repository = MongoUserRepoORM()
document_repository = UserDocsRepoORM()

# ______PROGRESSBAR____________________________________________
progress_bar = ProgressBarClient()

# ______TOKENIZER____________________________________________
tokenizer = TextTokenizer()

# ______PREPROCESSOR____________________________________________
# default russian language (ru)
# text_preprocessor = TextPreprocessorAggregator("ru")
# ______FILE_MANAGERS____________________________________________
file_format_manager = TelegramServerFileFormatDefiner()
server_file_manager = TelegramMediaFileManager()
media_file_manager = MediaFileManager(file_format_manager=file_format_manager)

# ______WHISPER_OBJECTS____________________________________________
whisper_model_manager = WhisperModelManager()
whisper_client = WhisperClient(whisper_manager=whisper_model_manager)

# ______TRANSCRIPTION_OBJECTS____________________________________________
short_media_file_transcriber = ShortMediaFilesTranscriber(whisper_client=whisper_client)
long_media_file_transcriber = LongMediaFilesTranscriber(whisper_client=whisper_client,
                                                        media_file_manager=media_file_manager)

# ______GPT_LLM_OBJECTS____________________________________________
gpt_model_manager = GPTModelManager()

# ______SUMMARY_OBJECTS____________________________________________
one_request_gpt = OneRequestGPTWorker(assistant_repositorysitory=assistant_repository, model_manager=gpt_model_manager)
long_request_gpt = BigDataGPTWorker(assistant_repositorysitory=assistant_repository, model_manager=gpt_model_manager,
                                    tokenizer=tokenizer)

# ______FACTORIES____________________________________________
recognition_factory = MediaRecognitionFactory(media_file_manager=media_file_manager,
                                              short_media_transcriber=short_media_file_transcriber,
                                              long_media_transcriber=long_media_file_transcriber)

gpt_dispatcher = GPTDispatcher(
    token_sizer=tokenizer,
    model_manager=gpt_model_manager,
    one_request_gpt=one_request_gpt,
    long_request_gpt=long_request_gpt,
)

# ______TEXT_INVOKERS_OBJECTS____________________________________________

pdf_handler = PdfFileHandler()
txt_handler = TxtFileHandler()
video_handler = VideoFileHandler(ai_transcriber=recognition_factory)
audio_handler = AudioFileHandler(ai_transcriber=recognition_factory)

text_invoker = TextInvokeFactory(format_definer=file_format_manager,
                                 pdf_handler=pdf_handler,
                                 txt_handler=txt_handler,
                                 video_handler=video_handler,
                                 audio_handler=audio_handler,
                                 formats=formats)

# ______PROCESS_PIPELINE____________________________________________

queue_pipeline = PipelineQueues()
pipeline_process = ProcesQueuePipline(
    queue_pipeline=queue_pipeline,
    database_document_repository=document_repository,
    server_file_manager=server_file_manager,
    text_invoker=text_invoker,
    ai_llm_request=gpt_dispatcher,
    format_definer=file_format_manager,
    progress_bar=progress_bar,
    config_data=config_data
)

#____SERVER_CONNECTION____________________________________________
# server_file_worker = ServerFileManager()
