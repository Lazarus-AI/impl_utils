from models.apis import Rikai2, RikaiExtract, Riky2
from models.batching import Batcher


def query_rikai2(file_path, prompts: list):
    model_api = Rikai2()
    batch = Batcher(model_api, file_path, prompts)
    batch.run()


def query_riky2(file_path, prompts: list):
    model_api = Riky2()
    batch = Batcher(model_api, file_path, prompts)
    batch.run()


def query_rikai_extract(file_path, prompts: list):
    model_api = RikaiExtract()
    batch = Batcher(model_api, file_path, prompts)
    batch.run()
