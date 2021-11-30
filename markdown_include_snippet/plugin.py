import os
import re

import mkdocs
from mkdocs.plugins import BasePlugin
from jinja2 import Template
from github import Github, GithubObject

from markdown_include_snippet.util import (
    skip_page,
    copy_markdown_images,
    get_markdown_section,
)


class MarkdownIncludeSnippetPlugin(BasePlugin):
    config_scheme = (
        ("base_path", mkdocs.config.config_options.Type(str, default="docs")),
        ("all_pages", mkdocs.config.config_options.Type(bool, default=True)),
        ("encoding", mkdocs.config.config_options.Type(str, default="utf-8")),
    )
    page = None

    def _resource_from_local(self, file: str, section: str) -> str:
        if not os.path.isabs(file):
            file = os.path.normpath(os.path.join(os.getcwd(), self.config["base_path"], file))
        try:
            with open(file, "r", encoding=self.config["encoding"]) as fr:
                content = fr.read()
                if section:
                    content = get_markdown_section(content, section)
                return content
        except Exception as e:
            raise Exception(f"No such file: {file}")

    def _markdown_snippet(self, file: str, section: str, repository: str, ref: str) -> str:
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(repository)
        f = repo.get_contents(file, ref=ref)
        content = f.decoded_content.decode("utf-8")
        if section:
            content = get_markdown_section(content, section)

        root = f"{self.config['base_path']}/{self.page.url}"
        content = copy_markdown_images(root, file, repo, content)
        return content

    def snippet(
        self,
        file: str,
        section: str = None,
        header: bool = True,
        repository: str = None,
        ref: str = GithubObject.NotSet,
    ) -> str:
        if repository:
            content = self._markdown_snippet(file=file, section=section, repository=repository, ref=ref)
        else:
            content = self._resource_from_local(file=file, section=section)
        if not header:
            return re.sub(r"^.*\n", "", content)
        return content

    def snippet_old(
        self,
        repository: str,
        file: str,
        ref: str = GithubObject.NotSet,
        section: str = None,
    ) -> str:
        return self._markdown_snippet(repository, file, ref, section)

    def on_page_markdown(self, markdown, page, config, **kwargs):
        if not self.config["all_pages"] and skip_page(markdown):
            return markdown
        self.page = page
        md_template = Template(markdown)
        return md_template.render(snippet=self.snippet)
