# import asyncio
# from abc import ABC, abstractmethod
#
# import ffmpeg
#
#
# class VideoConverter(ABC):
#     @abstractmethod
#     async def convert_video(self, file_path,output_path ):
#         pass
#
#
# class WebmConverter(VideoConverter):
#
#     async def convert_video(self, input_path, output_path):
#         output = f'{output_path}.mp4'
#         ffmpeg.input(input_path)\
#             .output(output, format="mp4")\
#             .run()
#         return output
#
# async def main():
#     converter  = WebmConverter()
#     await converter.convert_video(input_path=r'D:\Python_projects\insighter\insight_bot\services\video_decodec\file_example_WEBM_1920_3_7MB.webm',
#                                   output_path=r'D:\Python_projects\insighter\insight_bot\services\video_decodec\123.mp4'
#                                   )
#
#
# if __name__ == '__main__':
#
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())