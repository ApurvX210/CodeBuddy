class ContextManager:
    def __init__(self) -> None:
        # It tell llm how to behave
        self.system_prompt : str