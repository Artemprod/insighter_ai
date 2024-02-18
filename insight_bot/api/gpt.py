import asyncio
import openai
from langchain_openai import ChatOpenAI

from DB.Mongo.mongo_enteties import Assistant


import tiktoken
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter

from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.schema.document import Document


class GPTAAssistant:

    def __init__(self, api_key, name, instructions):
        self.assistant = self._create_assistant(name, instructions)
        openai.api_key = api_key

    @staticmethod
    def _load_file(path):
        return openai.files.create(
            file=open(path, "rb"),
            purpose='assistants'
        )

    @staticmethod
    def _create_assistant(name, instructions):
        return openai.beta.assistants.create(
            name=name,
            instructions=instructions,
            model="gpt-4",

        )

    @staticmethod
    async def create_thread():
        return openai.beta.threads.create()

    @staticmethod
    async def delete_thread(thread_id):
        openai.beta.threads.delete(thread_id=thread_id)

    @staticmethod
    def add_user_message(thread_id, message_text):
        return openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_text,
        )

    async def unify_prompt_text(self, prompt: str, text: str):
        return prompt + "\n" + "вот траснкрибация разговора:" + "\n" + text

    async def generate_answer(self, thread_id, prompt, user_message, max_retries=3):
        message = await self.unify_prompt_text(prompt=prompt, text=user_message)
        self.add_user_message(thread_id=thread_id, message_text=message)
        attempts = 0
        while attempts < max_retries:
            run = openai.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant.id,
            )
            while run.status not in ["completed", "failed"]:
                print(run.status)
                await asyncio.sleep(5)
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

            if run.status == "completed":
                # Вывод сообщений и шагов выполнения
                print("Run выполнен успешно.")
                # здесь можно обработать результаты run'а
                break
            elif run.status == "failed":
                error_message = run.last_error.message if run.last_error else "Неизвестная ошибка"
                print(f"Run завершился с ошибкой: {error_message}")
                attempts += 1
                print(f"Попытка {attempts} из {max_retries}... Перезапуск...")
                await asyncio.sleep(5)  # небольшая задержка перед следующей попыткой
        else:
            print("Все попытки выполнить Run завершились неудачно. Останавливаемся.")

        messages = openai.beta.threads.messages.list(
            thread_id=thread_id
        )
        raw_data = messages.dict()['data'][0]['content'][0]['text']['value']
        return raw_data


class GPTAPIrequest:
    MODEL_3 = "gpt-3.5-turbo-1106"
    MODEL_4 = "gpt-4"
    MODEL_4_8K = "gpt-4-0613"
    MODEL_3_16 = "gpt-3.5-turbo-16k"
    MODEL_GPT_4_LIMIT = 8192
    MODEL_GPT_3_LIMIT = 16385

    def __init__(self, api_key,
                 chunk_size=5000,
                 chunk_overlap=800):

        openai.api_key = api_key
        self._system_assistant = None
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    @property
    def system_assistant(self):
        return self._system_assistant

    @system_assistant.setter
    def system_assistant(self, assistant:Assistant):
        if not isinstance(assistant, Assistant):
            raise ValueError('Не тот асистент')
        self._system_assistant = assistant


    @staticmethod
    async def send_request_to_chatgpt(messages, max_tokens):
        print(messages)
        response = openai.chat.completions.create(
            model=GPTAPIrequest.MODEL_3,
            timeout=6000,
            messages=messages,
            n=1,
            stop=None,
            temperature=0.5,
            frequency_penalty=0,
            top_p=0.8,
            presence_penalty=-0,
            max_tokens=max_tokens

        )
        response_message = response.dict()['choices'][0]['message']['content'].strip()
        print('ответ от чата: ' + response_message)
        return response_message



    async def conversation(self, user_message, max_tokens_response=1000):
        tokens_in_text = await self.num_tokens_from_string(string=user_message, encoding_name='cl100k_base')
        print(tokens_in_text)
        if tokens_in_text > GPTAPIrequest.MODEL_GPT_4_LIMIT - max_tokens_response:
            result = await self.make_long_text(string=user_message,
                                              )
            return result

        prompt_text = [{"role": "system", "content": self.system_assistant.assistant_prompt},
                       {"role": "user", "content": f'{self.system_assistant.user_prompt} + "\n", {user_message}'}
                       ]
        response = await self.send_request_to_chatgpt(messages=prompt_text,
                                            max_tokens=max_tokens_response)
        return response


    async def split_text_into_parts(self, string, max_tokens):
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(string)
        token_parts = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
        parts = [encoding.decode(i) for i in token_parts]
        print()
        return parts

    @staticmethod
    async def combine_responses(responses):
        # Объединяет ответы в один текст
        return ' '.join(responses)

    async def make_long_text(self, string):
        # dotenv.load_dotenv()
        llm = ChatOpenAI(temperature=0, model_name="gpt-4")
        # Map
        map_template = f"""{self.system_assistant.assistant_prompt}
        {self.system_assistant.user_prompt_for_chunks}
        {'{docs}'}
        ответ на русском :"""
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=llm, prompt=map_prompt)
        # Reduce
        reduce_template = f"""{self.system_assistant.assistant_prompt}
        {self.system_assistant.user_prompt}
        {'{docs}'}
        ответ на русском:"""
        reduce_prompt = PromptTemplate.from_template(reduce_template)
        # Run chain
        reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
        # Takes a list of documents, combines them into a single string, and passes this to an LLMChain
        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_chain, document_variable_name="docs"
        )
        # Combines and iteravely reduces the mapped documents
        reduce_documents_chain = ReduceDocumentsChain(
            # This is final chain that is called.
            combine_documents_chain=combine_documents_chain,
            # If documents exceed context for `StuffDocumentsChain`
            collapse_documents_chain=combine_documents_chain,
            # The maximum number of tokens to group documents into.
            token_max=GPTAPIrequest.MODEL_GPT_4_LIMIT,
        )

        # Combining documents by mapping a chain over them, then combining results
        map_reduce_chain = MapReduceDocumentsChain(
            # Map chain
            llm_chain=map_chain,
            # Reduce chain
            reduce_documents_chain=reduce_documents_chain,
            # The variable name in the llm_chain to put the documents in
            document_variable_name="docs",
            # Return the results of the map steps in the output
            return_intermediate_steps=False,
        )

        split_docs = self.text_splitter.split_documents(await self.get_text_chunks_langchain(string))
        return map_reduce_chain.run(split_docs)
    @staticmethod
    async def get_text_chunks_langchain(text):
        text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=800)
        docs = [Document(page_content=x) for x in text_splitter.split_text(text)]
        return docs

    @staticmethod
    async def num_tokens_from_string(string: str, encoding_name: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    async def num_tokens_from_messages(self, messages, model="gpt-4-0314"):
        """Return the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens


# async def main():
    # t = """
    #      Ало! Добрый день, или завета? Добрый день.
    #      Это онлайн университет Гигбрэнс, меня зовут
    #      Ваги, садобно разговаривать. Отлично. Ай, вы
    #      оставляли заявку на обучение по продок-менышменту.
    #       Ясно, ясно, ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Ясно. Что?
    #       Да, да, бы вот входит. Аа, я за него первую очередь познакомиться в пару вопросов вам задать, чтобы делать в
    #       более продуктивный. И вот хотел бы узнать, если у вас опыт запуск продуктов своих… Ну, конкретно продуктов нет,
    #       но было реализованное для всех проектов. Я там вам пить его пожаловать, и что я работаю в прочих длинжах. То есть
    #       есть еще специалист. Да. Про же, это именно. Да, тут, к прочих длинжах, но зло несколько проектов, которые я… И я
    #       скажу, что это работает без обучения, но на практике. Я везела. Это круто. А, или же, это какая-то к доселе обучения
    #       , что именно хотите получить вот этот продактор? От продата хочу полностью менять конкретно в продактором жизни. Сейчас
    #        я думаю, что для меня эти работы вижу, что на рынке как раз не на поджатый менеджный день. Так много ваканчиков. Запросто
    #        больше. Вот, про доктор. Обучиться как раз и поменять. Про доктор, в самом деле, да, в этом плане побольше. Вы абсолютно верно
    #         сказали. Сейчас про доктор очень актуальный. А, в программе обучения ознакомились? Да, чуть-чуть мне посмотрел. Ну, я слышу, что я
    #          сейчас узнала у нас такие спортнерские программы. Я вот, в принципе, как раз вышла на несколько склон. Но это примерно и
    #           хмерт, и сейчас равный вопрос. Я могу вам тогда с вами информацию рассказать, касательно нашего продукта. И это уже можно
    #           в своем дольше отталкиваться. Хорошо? Да, давайте. Давайте. Так вот касательно нашего обучения. А оно проходит онлайн. Дум
    #           аю, это, ясно, лица 14 месяцев. То есть два раза в неделю у вас будут в обинарах 8 вечера по Москве. То есть заходим
    #            кабинет, слушаем преподаватели, задаем вопросы. Все максимально интерактивно.
    #            Если вдруг в обинарах пропустили, то ничего страшного можно посмотреть запись. И вопросы задать, соответственно, позже. После каждого в обинарах у вас будут домашние задания. Которые проверяют преподаватели. В список преподавателей видели, кстати? Да, примерно, не разноковь, но сейчас я отколишу. Ну, это я к тому, что преподаватели, это топы из крупных компаний, люди с колоссальным опытом, которым есть чем поделиться. И вот здесь с помощью мофонной преимущества. Я просто тоже на продукты учусь уже вот 5 месяцев. Я вам буду слеса. Отлеса студента говорить. Вы в основу обучения можете взять какую-то идею? Ну, абсолютно любую. Не знаю, это мобильное приложение под оставки кофе, к примеру. И вот работать с этой здесь течение всего обучения. Каждый модуль будет вашу идею собирать, ну как конструктор. То есть, допустим, первый модуль, там, линкан-вас сделать, ну, бизнес-план по-русски. Вы его делаете? Отравляете преподаватели в по-вашему приложению кофе. Он проверяет и дает развернутую обратную связь. Или завета. Вот это правильно. Это неправильно. Вот здесь я бы посоветовал извинить. То есть, действительно, они вникают ваш продукт и дают очень крупную связь полезную, ценную. И вот так течение года вы собираете такой теоретический скелет вашего продукта будущего. В конце у вас будет два месяца кросс-муциональной стажировки. Когда мы даем вам команду, например, дизайнер, маркетолог, разработчик, это вы упослекие наших других направлений. И они с вами в течение двух месяцев работают над вашим будущим продуктом. То есть, для них это, в портфолию, а для вас уже прототип МВП вашего будущего продукта. Так же, по окончанию, обучение преподаватели выбирают из группы три интересных продукта на их взгляд. И выделяется три гранта на 800-700 и 600 тысяч рублей. Гранты безочетные. То есть вы можете их тратить как на себя, так и на самом продукт. То есть считаете это дополнительная мотивация. И в этот важный момент мы еще... А вот этот диплом, он котирует и на международные. Ну, он... Смотрите, он котируется, так же какая абсолютно любой другой диплом высшего заведения. Мы даем дипломы про в переподготовке, несонный в рестер. То есть в одиным знаком у нас лицензия образовательная. И вы потом, кстати, после обучения, можете еще получить налогую вычить 13%. Это как тоже такой приятный бонус. Соответственно, вы получаете еще сертификаты по каждому модулю пройденным. Ну то, что вы, сознание, получили. А порсфоли упополняйте как минимум на один продукт. И мы предлагаем вам вообще трудоустройство, если это вопрос актуален. Помимо пока у нас актуальная новогодняя скидка. Мы всем продактом дарим дополнительное обучение или завета. Это тренажер по продуктовой аналитики. А отдельный десятьмесячный курс, где вас обучает сначала из келы пайта. А потом запускают симулятор. Это наша такая разработка некая песочница. Где есть 7 этапов, запуска вашего продукта. И делаю определенный шаг, вам дают обратную шаги. То есть, что вы сделали, куда вас это приведет? Очень крутая возможность попрактиковаться. И в дальнейшем вы как продакт уже будете более конкурентно в способной на рынке. Так как вы универсал, вы не только продакт, выщесть аналитикой, можете глубинно работать в каналитик. Это большой плюс. То есть, ну и возможность больше здесь нужно зарабатывать. Вот касательно того, что рассказал. Тут вопросы какие-нибудь появились? Какие остальные, все понятно. Ну как вам целым такое обучение? С возможностей продукции запустить. И деньги на его разработку получить дальше. Ну, собственно, интересно, но в моем случае пока нет конкретного проекта. И продукты, которые я хотела запускает. А это не проблема? Пока мне не понятно. И я могу вам так сказать. Ну касательно продукта. Ну, в моей допустим, группик-зе я обучаюсь. Ну, больше половины пришли без идеи. И просто брали в основу обучения какие-нибудь известные кейсы. Ну, алядили в реклап. Там хочу сделать свой григотар подоставки и ды. И какое-то время на буквально первый месяц. Они делали домашнее задание по этому своему продукту. Чтобы просто об навыке получить свои практически. А припали они постоянно делятся разными ресурсами. Там телегам-каналами, где продокты сидят. Разрешили форуминостранными, где можно подсматывать. Ну что, вообще на западе происходит. И я скажу так, что через два месяца, ну почти у всех уже была какая-то своя идея. В которой они продолжили работать. Так что если у вас нет идеи, то не проблемы, в аспектах забрятать тоже не нужна. Вам дадут все ресурсы, чтобы нашли какую идею можно адаптировать. Главное, эти знания получить. Главное, не только какой-то продуктуете, начали делать. Сколько заточек я уже надучил. Ну, я скажу так, не теме два выбинара, которые делятся полтора-тира два часа. Плюс домашнее задание. Ну тоже около всего двух часов. Я бы сказал, 6 часов неделю. То есть, как раз программа исозна, для людей, которые работают, что вы могли совмещать. Понимаю, это не хорошо, поставимости. По стоимости у нас еще актуальная новогодняя скидка. И соответственно, все обучение стоит вместо 280.1113. У нас 60% скидки. Вот эти 130-600. Ну плюс тренажер в подарок отдельный 10 месяч дней. Вот эти 130-600, вы можете разбить в расточку без каких-либо переплат. Если разбить на 140 месяцев, как лица обучение, у вас получится 800. Если сделать расточку длительный, сумма будет меньше. То есть, сумму не меняется. Просто плачет будет меньше. Вам какой вариант вообще был удобнее? Ну, ну, срочка, да и не было. Об откажется, вот то, что у нас с воссийской, какие-то контакты в крупном компании. Может быть, у нас есть какая-то ративная подражение. На самом деле у нас много разных контрактов. Но я могу сказать сразу, или за это новогоднюю скидку не перебьет ничего. То есть у нас 50% для партнеров наших. И с учедомтийдесяти процедной скидкой у вас стоимость обучения была бы 140-2000. То есть, новогодний офер он выгодний. Ну, я вам тоже прямо могу сказать. Нет, а он у нас здесь, и дочь, и тверга включительно. Ну, при оформлении расочки, я могу сразу сказать. У вас первую платеж через месяц. То есть вам не обязательно платить сразу. А, вы часто вы можете начать? Да, вы часто вы можете начать? Да, при ращете ремонт. Ещё раз не услышал? По расочке. Ещё раз ремонт, а сейчас я могу вот-таки ремонт, и си берегу. А если сделать на 14 месяцев, как лица обучения у вас, будет платёшь 800. А если сделать расрочку на 2-3 месяца? Ну, можно просто длительнее сделать. Там платёшь получается 400-700. Хорошо, конечно. Спасибо. А в журнете, как направить это? Во-первых, я тоже могу сказать. Да, конечно. Вы мне тогда серентироваете под дальнейшим шагам, а когда мы давно обратно связь, да? Да, давайте. А в вопросах не осталось открытых? Да, в принципе нет пока. Так, хорошо. Так, да, я всё всё вкиную. Теперь мы можем это же время созвониться. Хорошо, хорошо. Да, всё доброе. До свидания. Да, не знаю.
    #
    #     """
    # with open(r"C:\Users\artem\OneDrive\Рабочий стол\text\еще один тест .txt", 'r', encoding="utf-8") as f:
    #     t = f.read()
    # print()
    # system_assistant = LEXICON_ASSISTANTS['secretary']['assistant_prompt']
    # prompt = LEXICON_ASSISTANTS['secretary']['user_prompt']
    # a = GPTAPIrequest(api_key=load_bot_config('.env').ChatGPT.key, system_assistant_prompt=system_assistant,
    #                   prompt=prompt)
    # asyncio.create_task(a.conversation(t))


if __name__ == '__main__':
    # asyncio.run(main())
    print()
    # encoding = tiktoken.encoding_for_model(a.model_3)
    # a.conversation(user_message=t)

    print()
    # with open(r"D:\python projects\non_comertial\insighter\text\GB.txt", 'rb') as rawfile:
    #     rawdata = rawfile.read()
    #     result = chardet.detect(rawdata)
    #     encoding = result['encoding']
    #
    # # Теперь мы знаем правильную кодировку и можем открыть файл
    # with open(r"D:\python projects\non_comertial\insighter\text\GB.txt", 'r', encoding=encoding) as file:
    #     trancrib = file.read()
    #
    # d = GPTAAssistant(api_key=load_bot_config('.env').ChatGPT.key,
    #                   name="тест сервиса", instructions=LEXICON_RU['assistant_prompt'])
    # thread = d.create_thread()
    # for prompt in LEXICON_RU['user_prompt']:
    #     print()
    #     answer = d.gen_answer(thread_id=thread.id, prompt=prompt, user_message=trancrib)
    #     print(answer)
