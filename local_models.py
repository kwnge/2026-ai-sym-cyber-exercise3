from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

class LocalModels:

    @staticmethod
    def nemo_model():
        return (
            OpenAIChatModel(
                'nvidia/nemotron-3-nano',
                provider=OpenAIProvider(
                base_url="http://127.0.0.1:1234/v1"
                )
            )
        )
    @staticmethod
    def gpt_oss_model():
        return (
            OpenAIChatModel(
                'openai/gpt-oss-20b',
                provider=OpenAIProvider(
                base_url="http://127.0.0.1:1234/v1"
                )
            )
        )