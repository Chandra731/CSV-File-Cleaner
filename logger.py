class TransformationLogger:
    """
    Logger to maintain a step-by-step record of all transformations applied.
    """

    def __init__(self):
        self.logs = []

    def log(self, action_description):
        self.logs.append(action_description)

    def get_log_text(self):
        return "\\n".join(self.logs)

    def export_log_txt(self, filepath):
        with open(filepath, 'w') as f:
            f.write(self.get_log_text())

    def export_log_py(self, filepath):
        """
        Export the log as a Python script that can reproduce the cleaning steps.
        Assumes the log entries are valid Python code or comments.
        """
        with open(filepath, 'w') as f:
            for line in self.logs:
                f.write(line + "\\n")
