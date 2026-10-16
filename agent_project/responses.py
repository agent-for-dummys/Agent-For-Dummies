import time
from pydantic import BaseModel, Field


class Review(BaseModel):
    filename: str = Field(description="需要检查的文件路径")
    issues: list[str] = Field(description="发现的问题，没有问题时为空列表")


def review(model, question):
    return model.with_structured_output(Review, method="function_calling").invoke(question)


def retry_call(operation, attempts=3, sleep=time.sleep):
    if attempts < 1:
        raise ValueError("attempts 至少为 1")
    for index in range(attempts):
        try:
            return operation()
        except (TimeoutError, ConnectionError):
            if index == attempts - 1:
                raise
            sleep(min(2 ** index, 8))
