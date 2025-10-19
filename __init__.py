# -*- coding: utf-8 -*-

import re
import subprocess
from typing import List

from albert import *


# TODO: albert::iconFromUrls() is not exported in Python API v4.0, so use stub now.
# TODO: Replace it if albert.iconFromUrls is available in future.
def iconFromUrls(_urls: List[str]) -> Icon:
    return makeStandardIcon(StandardIconType.FileIcon)


md_iid = "4.0"
md_version = "1.1"
md_name = "GPaste"
md_description = "Search and copy/paste from GPaste clipboard history"
md_license = "MIT"
md_url = "https://github.com/hideakitai/albert-plugin-python-gpaste"
md_authors = ["@hideakitai"]
md_bin_dependencies = ["gpaste-client"]
# md_lib_dependencies = []
# md_platforms = ["linux"]

DEFAULT_TRIGGER = "gp "
ICON_URL = "xdg:edit-paste"


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

    def id(self) -> str:
        return md_name

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def defaultTrigger(self) -> str:
        return DEFAULT_TRIGGER

    def handleTriggerQuery(self, query):
        if not query.isValid:
            warning("Invalid query")
            return

        gpaste_items: List[StandardItem] = []

        try:
            queries = query.string.strip().split()
            items = self.get_gpaste_history()
            if items is not None:
                if len(queries) == 0:
                    gpaste_items = [self.create_gpaste_item(item) for item in items]
                else:
                    filtered_items = self.filter_gpaste_history(items, queries)
                    gpaste_items = [self.create_gpaste_item(item) for item in filtered_items]

        except Exception as e:
            warning(f"Error in handleQuery(): {str(e)}")
            return

        query.add(gpaste_items)

    def get_gpaste_history(self):
        try:
            result = subprocess.run(["gpaste-client", "history"], capture_output=True, text=True, check=True)
            history_text = result.stdout

            history = []
            pattern = r"^([a-f0-9-]{36}):\s*(.*)$"
            current_item = None

            for line in history_text.split("\n"):
                match = re.match(pattern, line)
                if match:
                    if current_item:
                        history.append(current_item)
                    uuid, content = match.groups()
                    current_item = {"uuid": uuid, "content": content}
                elif current_item:
                    current_item["content"] += "\n" + line

            if current_item:
                history.append(current_item)

            return history

        except subprocess.CalledProcessError as e:
            warning(f"Error executing gpaste-client: {e}")
            return None

    def filter_gpaste_history(self, items, queries):
        def is_match(string, query):
            if any(char.isupper() for char in query):
                # Case-sensitive search
                return query in string
            else:
                # Case-insensitive search
                return query.lower() in string.lower()

        return [item for item in items if all(is_match(item["content"], q) for q in queries)]

    def create_gpaste_item(self, item) -> StandardItem:
        id = f"gpaste_{item['uuid']}"
        content = item["content"]
        actions = [Action("copy", "Copy to clipboard", lambda c=content: setClipboardText(c))]
        if havePasteSupport():
            actions.append(
                Action("paste", "Paste to active window", lambda c=content: setClipboardTextAndPaste(c)),
            )

        return StandardItem(
            id=id,
            text=content,
            subtext=content,
            icon_factory=lambda: iconFromUrls([ICON_URL]),
            actions=actions,
        )
