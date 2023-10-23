import re

import markdown


class MessageConverter:
    @staticmethod
    def convert_message(text):
        # url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),#]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        # html_link_pattern = r'<a href="\g<0>" target="_blank">\g<0></a>'
        # converted_text = re.sub(url_pattern, html_link_pattern, text)
        converted_text = text.replace('\n', '<br/>')
        return converted_text

    def convert_markdown(text):
        converted_text = markdown.markdown(text)
        return converted_text
