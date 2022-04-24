import copy
import logging
import os
import pathlib
from html import escape
from typing import List

import dotenv
import numpy as np
import torch
from flask import Flask, jsonify, request, send_from_directory
from icecream import ic
from jally.ir.document_store import base, elastic, weaviate
from jally.ir.engine import bm25

#
from jally.modeling.ir.module import dpr
from jally.processing.ir import dpr as proc_dpr
from jally.processing.ir import tool as proc_tool

# also we want to send cool inline buttons below, so we need to import:
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from teleflask import Teleflask

# because we wanna send HTML formatted messages below, we need:
from teleflask.messages import HTMLMessage, TextMessage
from telestate import TeleState, machine
from telestate.contrib.simple import SimpleDictDriver
from torch.utils.data.sampler import SequentialSampler

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

dotenv.load_dotenv()

top_k = int(os.environ.get("TOP_K", 5))

app = Flask(
    __name__,
    template_folder='build',
    static_folder='build',
    root_path=pathlib.Path(os.getcwd()) / 'jally',
)

bot = Teleflask(api_key=os.environ.get("BOT_TOKEN"), app=app)

memo = SimpleDictDriver()

machine = machine.TeleStateMachine(__name__, database_driver=memo, teleflask_or_tblueprint=bot)

machine.ASKED_QUERY = TeleState("ASKED_QUERY", machine)
machine.CONFIRM_DATA = TeleState("CONFIRM_DATA", machine)
machine.FOUND_RESULT = TeleState("FOUND_RESULT", machine)
machine.CONFIRM_DESCRIPTION = TeleState("CONFIRM_DESCRIPTION", machine)

store = weaviate.WeaviateDocStore(index="test", progress_bar=False)

ir_bm25 = bm25.BM25Retriever(store=elastic.ElasticDocStore())

device = "cuda" if torch.cuda.is_available() else "cpu"
query_model = dpr.DEncoder.load(pathlib.Path(os.getcwd()) / os.environ.get("RETRIEVER_QUERY_WEIGHTS"))
query_model = query_model.to(device)
query_model = query_model.eval()
query_processor = proc_dpr.TProcessor.load(pathlib.Path(os.getcwd()) / os.environ.get("RETRIEVER_QUERY_WEIGHTS"))
ic(query_processor.query_tokenizer)


def embed_queries(queries: List[str], processor, model, batch_size: int = 1) -> List[np.ndarray]:

    all_embeddings = []

    dicts = [{"query": q} for q in queries]

    assert len(dicts) == len(queries)
    dataset, tensor_names, _, baskets = processor.dataset_from_dicts(dicts, return_baskets=True)

    data_loader = proc_tool.NamedDataLoader(
        dataset=dataset, sampler=SequentialSampler(dataset), batch_size=1, tensor_names=tensor_names
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()

    for i, batch in enumerate(data_loader):
        batch = {key: batch[key].to(device) for key in batch}
        with torch.no_grad():
            model_output = model(**batch)
        query_embeds = model_output.cpu().numpy()

        all_embeddings.append(query_embeds)

    all_embeddings = np.concatenate(all_embeddings)

    return all_embeddings


def search_store(
    question: str,
    model,
    processor,
    device: str = "cpu",
) -> base.Document:
    queries = [copy.deepcopy(question)]
    embeddings = embed_queries(queries=queries, model=model, processor=processor)
    response = []
    for q, e in zip(queries, embeddings):
        res = store.query_by_embedding(query_emb=e)
        ic(f"for query {q} response is {res[0].meta['title']}")
        response.append(res)
    return response[0]


def rank_store(
    question: str,
):
    docs = list(ir_bm25.retrieve_top_k(query=question))[0][0]
    if len(docs) > 0:
        res = docs[0]
    else:
        res = base.Document.from_dict({"text": "", "title": "Такой книги не нашел. Уточни, пожалуйста, более подробно :-)"})
    return res


@app.route('/', defaults={'path': ''})
@app.route("/<path:path>")
def index(path):
    if path != '' and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@machine.ALL.on_command("start")
def start(update, text):
    machine.set("ASKED_QUERY")
    return TextMessage(
        "<b>Привет! </b> Мы библиотека <u>\"JALLY\"</u>. Просто напиши мне <u>о чем бы ты хотел почитать</u>...",
        parse_mode="html",
    )


@machine.ALL.command("cancel")
def cmd_cancel(update, text):
    old_action = machine.CURRENT
    machine.set("DEFAULT")
    if old_action == machine.DEFAULT:
        return TextMessage("Nothing to cancel.", parse_mode="text")
    # end if
    return TextMessage("All actions canceled.", parse_mode="text")


def hi(answer: str, docs: List[base.Document]):
    pos = 0
    while pos < len(docs):
        if docs[pos].text != answer:
            return docs[pos]
        pos += 1
    return None


@machine.ASKED_QUERY.on_message("text")
def fn_query(update, msg):
    query = msg.text.strip()

    top_docs = search_store(question=query, model=query_model, processor=query_processor)

    elastic_doc = rank_store(question=query)
    elastic_title = elastic_doc.meta["title"]
    elastic_desc = elastic_doc.text

    if elastic_desc != "":
        recommended_doc = hi(elastic_desc, top_docs)
        machine.set(
            "FOUND_RESULT",
            data={
                "query": query,
                "response": elastic_title,
                "description": elastic_desc,
                "recommend": recommended_doc.meta["title"],
                "recommend_description": recommended_doc.text,
            },
        )
        return HTMLMessage(
            f"Я нашел вот такую книгу: {elastic_title}. Поищем на нее похожие ?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👌", callback_data="confirm_true"),
                    ],
                    [
                        InlineKeyboardButton('🤦', callback_data="confirm_false"),
                    ],
                ]
            ),
        )
    else:
        machine.set("ASKED_QUERY")
        return TextMessage(f"По запросу  <u>{query} </u> не нашел ничего. \nНапиши подробнее, пожалуйста.", parse_mode="html")

    machine.set("CONFIRM_DATA", data={"query": query, "response": response, "description": description})
    return HTMLMessage(
        f"<u>Запрос:</u> {escape(query)}\n---\n<u>Response:</u> {response}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👌", callback_data="confirm_true"),
                ],
                [InlineKeyboardButton("Описание", callback_data="description")],
                [
                    InlineKeyboardButton('🤦', callback_data="confirm_false"),
                ],
            ]
        ),
    )


# end def
@machine.FOUND_RESULT.on_update("callback_query")
def fn_found_result(update):
    if update.callback_query.data == "confirm_true":
        query = machine.CURRENT.data["query"]
        response = machine.CURRENT.data["recommend"]
        recommend = machine.CURRENT.data["recommend"]
        description = machine.CURRENT.data["recommend_description"]
        machine.set("CONFIRM_DATA", data={"query": query, "response": recommend, "description": description})
        return HTMLMessage(
            f"<u>Запрос:</u> {escape(query)}\n---\n<u>Response:</u> {response}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👌", callback_data="confirm_true"),
                    ],
                    [InlineKeyboardButton("Описание", callback_data="description")],
                    [
                        InlineKeyboardButton('🤦', callback_data="confirm_false"),
                    ],
                ]
            ),
        )
    else:
        machine.ASKED_QUERY.activate()
        return TextMessage(f"Okay. Давай поищем что-нибудь другое :-)", parse_mode="html")


@machine.CONFIRM_DATA.on_update("callback_query")
def fn_confirm(update):
    if update.callback_query.data == "description":
        description = machine.CURRENT.data["description"]
        machine.CONFIRM_DESCRIPTION.activate()
        return HTMLMessage(
            f"{escape(description)}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("👌", callback_data="come_back"),
                    ]
                ]
            ),
        )
    elif update.callback_query.data == "confirm_false":
        machine.ASKED_QUERY.activate()

        return TextMessage(
            "Жаль, что тебе не понравилось 😟\nБуду улучшать свою нейросеть.\nМожет попробуем подобрать что-то еще?",
            parse_mode="text",
        )
    else:
        machine.ASKED_QUERY.activate()  # we are done
        return HTMLMessage("Рад, что тебе понравилось, обятельно приходи еще!")


@machine.CONFIRM_DATA.on_message("text")
def fn_confirm_txt(update, msg):
    query = msg.text.strip()

    doc = search_store(question=query, model=query_model, processor=query_processor)
    response = doc.meta["title"]
    description = doc.text

    machine.set("CONFIRM_DATA", data={"query": query, "response": response, "description": description})
    return HTMLMessage(
        f"<u>Запрос:</u> {escape(query)}\n---\n<u>Response:</u> {response}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👌", callback_data="confirm_true"),
                ],
                [InlineKeyboardButton("Описание", callback_data="description")],
                [
                    InlineKeyboardButton('🤦', callback_data="confirm_false"),
                ],
            ]
        ),
    )


@machine.CONFIRM_DESCRIPTION.on_update("callback_query")
def fn_description(update):
    if update.callback_query.data == "come_back":
        machine.ASKED_QUERY.activate()  # we are done
        return HTMLMessage("Рад, что тебе понравилось, обязательно приходи еще!")
